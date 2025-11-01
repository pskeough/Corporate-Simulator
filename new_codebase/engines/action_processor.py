# engines/action_processor.py
"""
Action Processor Module for Corporate Decision Simulator

This module handles the processing of player decisions, determining their
outcomes, and managing the consequences within the corporate simulation.
It serves as the core logic unit for applying the results of AI-generated
narratives to the game state.
"""

import google.generativeai as genai
import json
from json import JSONDecodeError
import re
from engines.context_builder import build_action_context
from engines.state_validator import validate_updates, get_validation_summary
from engines.event_generator import api_call_with_retry
from engines.state_updater import apply_updates
from engines.prompt_loader import load_prompt
from model_config import TEXT_MODEL

def process_player_action(game_state, action, event_title, event_narrative):
    """
    Determines the outcome of a player's action and applies it to the game state.
    This function orchestrates context building, AI interaction, state validation,
    and the application of all resulting changes.

    Args:
        game_state: The current state of the simulation.
        action (str): The specific action the player has chosen.
        event_title (str): The title of the event being resolved.
        event_narrative (str): The narrative text presented to the player.

    Returns:
        dict: The outcome of the action, including the narrative and any state updates.
    """
    print(f"--- Asking AI for outcome of '{action}' (FINAL RESOLUTION) ---")
    model = genai.GenerativeModel(TEXT_MODEL)

    # Build the context for the AI prompt
    context = build_action_context(game_state)

    # Summarize any preceding conversation for richer context
    conversation_summary = ""
    if game_state.event_conversation:
        conversation_summary = "\n".join([
            f"- Player: {entry['player']}\n- AI Response: {entry['ai']}"
            for entry in game_state.event_conversation
        ])
        conversation_summary = f"\n<CONVERSATION_HISTORY>\nBefore making this final decision, the player investigated the situation:\n{conversation_summary}\n</CONVERSATION_HISTORY>\n"

    # Extract and contextualize key corporate state variables
    headcount = context['corporation']['headcount']
    budget = context['corporation']['budget']
    political_capital = context['player']['political_capital']
    player_title = context['player']['title']

    # Determine the current financial status of the corporation
    budget_per_employee = budget / max(headcount, 1)
    financial_state = ""
    if budget_per_employee < 1000: # Example threshold
        financial_state = "The company's budget is extremely tight, and layoffs are a real possibility. "
    elif political_capital < 100:
        financial_state = "Your personal political capital is low, making it hard to push for new initiatives. "
    elif budget_per_employee > 10000 and political_capital > 500:
        financial_state = "The company is highly profitable, and you have significant influence. "

    # Format values for clear presentation in the prompt
    headcount_formatted = f"{headcount:,}"
    budget_formatted = f"${budget:,.2f}"
    political_capital_formatted = f"{political_capital:,}"
    stated_values = ', '.join(context['company_culture']['stated_values'][:3])
    player_skills = ', '.join(context['player']['skills'])
    acquired_skills = ', '.join(context['skills_and_assets']['player']['acquired_skills'][-3:])

    # Load the appropriate prompt template and inject the context
    prompt_template = load_prompt('actions/process_corporate_decision') # Refactored prompt name
    prompt = prompt_template.format(
        event_title=event_title,
        event_narrative=event_narrative,
        conversation_summary=conversation_summary,
        action=action,
        corporation_name=context['corporation']['name'],
        current_fiscal_quarter=context['simulation']['current_fiscal_quarter'],
        player_name=context['player']['name'],
        player_title=player_title,
        headcount=headcount_formatted,
        budget=budget_formatted,
        political_capital=political_capital_formatted,
        financial_state=financial_state,
        tech_stack_tier=context['corporation']['tech_stack_tier'],
        stated_values=stated_values,
        player_skills=player_skills,
        mission_statement=context['corporate_mission']['mission_statement_name'],
        acquired_skills=acquired_skills,
        market_conditions=context['market_and_competitors']['market_landscape']['conditions']
    )

    try:
        # Use a retry wrapper for robustness
        def make_api_call():
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.6  # Slightly more deterministic for corporate setting
                }
            )
            return response

        response = api_call_with_retry(make_api_call, max_retries=3, initial_delay=2.0)

        # Sanitize the AI's response to ensure it's clean JSON
        raw_text = response.text.strip()

        # Remove XML-style reasoning tags that the model might add
        raw_text = re.sub(r'^<[^>]+>.*?</[^>]+>\s*', '', raw_text, flags=re.DOTALL)

        # Extract JSON from Markdown code fences
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
        if json_match:
            raw_text = json_match.group(1)
        else: # Fallback for raw JSON without fences
            raw_text = re.sub(r'^```json\s*', '', raw_text)
            raw_text = re.sub(r'```\s*$', '', raw_text)

        raw_text = raw_text.strip()
        print(f"DEBUG: Sanitized AI response (first 200 chars): {raw_text[:200]}")

        outcome = json.loads(raw_text)

        # Handle cases where the AI might nest the output
        if "output" in outcome and isinstance(outcome["output"], dict):
            outcome = outcome["output"]

        print(f"--- AI Outcome Received ---\n{json.dumps(outcome, indent=2)}\n-----------------------------")

    except JSONDecodeError as e:
        print(f"!!!!!!!!!! JSON PARSING ERROR (Outcome) !!!!!!!!!!!\nFailed to parse AI response: {e}")
        print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
        return {
            "narrative": "The outcome of your decision is unclear due to a communication breakdown. The project remains in limbo.",
            "updates": {},
            "status": "error"
        }
    except Exception as e:
        error_msg = str(e).lower()
        print(f"!!!!!!!!!! API ERROR (Outcome) !!!!!!!!!!!\n{e}")

        # Provide user-friendly error messages based on common API issues
        if "authentication" in error_msg:
            narrative = "⚠️ Authentication Error: The connection to the AI model failed. Please check your API key and restart."
        elif "quota" in error_msg or "rate limit" in error_msg:
            narrative = "⚠️ Rate Limit Exceeded: The system is currently processing a high volume of decisions. Please try again in a moment."
        else:
            narrative = f"⚠️ System Error: Unable to process your decision due to a technical issue. The status quo is maintained... (Error: {str(e)[:100]})"

        print(f"NOTE: {narrative}")
        return {
            "narrative": narrative,
            "updates": {},
            "status": "error"
        }

    try:
        # Validate and apply updates to the game state
        if "updates" in outcome and outcome["updates"]:
            is_valid, cleaned_updates, errors = validate_updates(outcome["updates"], game_state)

            if errors:
                print(f"--- Validation Warnings ---")
                validation_summary = get_validation_summary(errors)
                print(validation_summary)

            if cleaned_updates:
                print("--- Applying Validated Updates ---")
                apply_updates(game_state, cleaned_updates)
            else:
                print("--- No valid updates to apply ---")
        else:
            print("--- No state updates from AI ---")

        # Check for consequences of interactions with key personnel
        if hasattr(game_state, 'current_event') and game_state.current_event.get('event_type') == 'personnel_vignette':
            person_name = game_state.current_event.get('person_name')
            if person_name and hasattr(game_state, 'key_personnel_manager') and hasattr(game_state, 'department_manager'):
                person = game_state.key_personnel_manager.get_by_name(person_name)
                if person:
                    department_id = person.get('department_id')
                    if department_id:
                        # Positive interaction boosts morale in that person's department
                        morale_change = 5
                        success = game_state.department_manager.update_morale(department_id, morale_change)
                        if success:
                            game_state.department_manager.add_history_entry(
                                department_id,
                                f"Positive interaction with {person_name}",
                                morale_change,
                                game_state.turn_number
                            )
                            department = game_state.department_manager.get_by_id(department_id)
                            department_name = department.get('name', 'Unknown Department')
                            print(f"  💬 Vignette completed: {department_name} morale +{morale_change} (now {department['morale']})")
                        else:
                            print(f"  ⚠️ Warning: Failed to update morale for department {department_id}")
                    else:
                         print(f"  ℹ️ Person {person_name} has no department affiliation")
                else:
                    print(f"  ⚠️ Warning: Person {person_name} not found in key_personnel.json")

        # Check if this was a budget meeting decision and apply consequences
        if hasattr(game_state, 'current_event') and game_state.current_event.get('event_type') == 'department_budget_meeting':
            petitions = game_state.current_event.get('petitions', [])

            chosen_department = None
            for petition in petitions:
                department_name = petition.get('department', '')
                if department_name.lower() in action.lower():
                    chosen_department = department_name
                    break

            if chosen_department:
                opposed_departments = [p.get('department') for p in petitions if p.get('department') != chosen_department]
                print(f"--- Applying budget decision consequences: {chosen_department} favored ---")
                from engines.department_engine import apply_department_decision_consequences
                apply_department_decision_consequences(game_state, chosen_department, opposed_departments)

        # Track long-term consequences of this action
        from engines.consequence_engine import apply_consequences, detect_major_policy_change

        consequences = apply_consequences(game_state, action, event_title, outcome.get("narrative", ""))

        # Check if this action constitutes a major new corporate policy
        major_policy = detect_major_policy_change(action, event_title, outcome.get("narrative", ""))
        if major_policy:
            print(f"\n🏛️ MAJOR POLICY DETECTED: {major_policy['type']} ({major_policy['importance']})")
            print(f"   Significance Score: {major_policy['significance_score']}")

            from engines.policy_engine import PolicyEngine
            from engines.history_compression_engine import HistoryCompressionEngine

            policy_engine = PolicyEngine(game_state)
            effects = _infer_policy_effects(major_policy, game_state)

            policy = policy_engine.create_policy(
                policy_type=major_policy['type'],
                title=_generate_policy_title(major_policy),
                enactment_text=major_policy['action_text'],
                enacted_by=game_state.player['name'],
                effects=effects,
                importance=major_policy['importance']
            )

            impact_narrative = policy_engine.add_policy_to_state(policy)
            print(f"   📜 New corporate policy enacted: {policy['title']}")
            print(f"   ⚖️ {impact_narrative}")

            if major_policy['importance'] == 'company_defining':
                history_engine = HistoryCompressionEngine(game_state)
                history_engine.archive_policy(policy)
                print(f"   📚 Archived as a company-defining moment")

        # Check department KPIs against the outcome of the turn
        _check_department_kpis(game_state, outcome, action, event_title)

        # Extract and save strategic focus from high-level meetings
        if "meeting" in event_title.lower() or "strategy session" in event_title.lower():
            policy_keywords = {
                'aggressive growth': ['growth', 'expand', 'market share', 'acquisition'],
                'cost reduction': ['cut costs', 'layoffs', 'budget freeze', 'efficiency'],
                'product innovation': ['innovate', 'r&d', 'new feature', 'research'],
                'customer retention': ['retention', 'churn', 'customer satisfaction', 'support']
            }

            action_lower = action.lower()
            detected_focus = None
            for focus, keywords in policy_keywords.items():
                if any(keyword in action_lower for keyword in keywords):
                    detected_focus = focus
                    break

            if detected_focus:
                game_state.strategic_focus = detected_focus
                print(f"  📜 Strategic focus set to: {detected_focus}")
            elif game_state.strategic_focus is None:
                game_state.strategic_focus = "general_operations"
                print(f"  📜 Strategic focus defaulted to: general_operations")

        # Log event to company history
        log_entry = {
            "fiscal_quarter": game_state.simulation['current_fiscal_quarter'],
            "title": event_title,
            "action": action,
            "narrative": outcome.get("narrative", "The consequences are unclear.")
        }
        game_state.history_long["events"].append(log_entry)

        # Apply corporate overhead and revenue generation
        from engines.resource_engine import apply_overhead, apply_revenue_generation

        production = apply_revenue_generation(game_state)
        print(f"  📈 Revenue & Capital Generation: +${production['budget']:,.2f} budget, +{production['political_capital']} political capital")

        consumption_status = apply_overhead(game_state)
        print(f"  📉 Corporate Overhead: -${consumption_status['budget_consumed']:,.2f} budget")

        # Apply morale changes based on financial health
        from engines.resource_engine import calculate_financial_ morale_impact
        morale_impact = calculate_financial_morale_impact(game_state)
        if morale_impact != 0:
            game_state.company_morale = max(0, min(100, game_state.company_morale + morale_impact))
            if morale_impact < 0:
                print(f"  😞 Company morale decreased by {abs(morale_impact)} (financial strain)")
            else:
                print(f"  😊 Company morale increased by {morale_impact} (profitability)")

        # Apply department morale happiness modifier
        department_bonuses = game_state.department_manager.get_department_bonuses(game_state)
        game_state.company_morale += department_bonuses['morale_modifier']
        game_state.company_morale = max(0, min(100, game_state.company_morale))
        if department_bonuses['morale_modifier'] != 0:
            print(f"  🙂 Department performance changed company morale by {department_bonuses['morale_modifier']:+d}")

        if consumption_status['warnings']:
            outcome['financial_warnings'] = consumption_status['warnings']
            outcome['consumption_effects'] = {}

            if 'layoffs' in consumption_status:
                outcome['consumption_effects']['headcount_loss'] = consumption_status['layoffs']
                print(f"  ☠️ Budget Crisis! Layoffs occurred: -{consumption_status['layoffs']} headcount")

            if 'projects_cancelled' in consumption_status:
                outcome['consumption_effects']['projects_cancelled'] = consumption_status['projects_cancelled']
                print(f"  🏚️ Bankruptcy! Projects cancelled: {', '.join(consumption_status['projects_cancelled'])}")

        # Automatic state progression for player and simulation
        game_state.player['years_at_company'] += 0.25 # Each turn is a quarter
        game_state.player['years_in_role'] += 0.25
        # Logic to advance the fiscal quarter will be handled in a dedicated time progression engine
        game_state.turn_number += 1

        # Apply career progression effects
        from engines.player_engine import apply_career_progression_effects, calculate_player_effectiveness

        career_changes = apply_career_progression_effects(game_state)
        if career_changes:
            for change in career_changes:
                print(f"  👤 Player career: {change}")

        # Calculate player effectiveness for bonuses
        effectiveness = calculate_player_effectiveness(game_state.player)
        print(f"  💪 Player effectiveness: {effectiveness:.2f}x")

        # Check if player has been in role for a long time and suggest career move
        years_in_role = game_state.player['years_in_role']
        if years_in_role > 5:
            print(f"  ⚠ Career Warning: Player has been in role for {years_in_role} years. Consider seeking a promotion or new role.")

        return outcome
    except Exception as e:
        print(f"!!!!!!!!!! STATE UPDATE ERROR !!!!!!!!!!!\n{e}")
        return {"narrative": f"A critical error occurred while applying the decision's consequences: {e}", "updates": {}, "status": "error"}

def _check_department_kpis(game_state, outcome, action='', event_title=''):
    """
    Analyzes turn outcome against department KPIs and updates morale.
    This simulates how departments react to company-wide events based on their goals.

    Args:
        game_state: Current game state with department_manager.
        outcome (dict): Contains 'updates' and 'narrative' from the turn.
        action (str): The player's action string.
        event_title (str): The title of the event.
    """
    updates = outcome.get('updates', {})
    if not updates:
        return

    event_narrative = outcome.get('narrative', '')
    print("--- Checking Department KPIs Against Turn Outcome ---")

    for department in game_state.department_manager.get_all():
        department_name = department.get('name', 'Unknown Department')
        kpis = department.get('kpis', [])
        if not kpis:
            continue

        morale_change = 0
        reasons = []

        for kpi in kpis:
            kpi_lower = kpi.lower()

            # --- Sales & Marketing KPIs ---
            if any(kw in kpi_lower for kw in ['sales', 'revenue', 'client acquisition', 'lead generation']):
                budget_change = updates.get('corporation.budget', 0)
                if budget_change > 100000: # Significant revenue event
                    morale_change += 5
                    reasons.append(f"Revenue increased by ${budget_change:,.2f}, supporting sales goals")

            # --- Engineering & R&D KPIs ---
            if any(kw in kpi_lower for kw in ['launch', 'feature', 'uptime', 'bug']):
                 if "new feature" in event_narrative.lower() or "product launch" in event_title.lower():
                     morale_change += 5
                     reasons.append("Successful product launch aligns with Engineering KPIs")

            # --- HR & Operations KPIs ---
            if any(kw in kpi_lower for kw in ['headcount', 'retention', 'employee satisfaction', 'efficiency']):
                headcount_change = updates.get('corporation.headcount', 0)
                if headcount_change > 0:
                    morale_change += 3
                    reasons.append("Hiring new employees supports HR goals")
                elif headcount_change < 0:
                    morale_change -= 10 # Layoffs are very bad for HR morale
                    reasons.append("Layoffs are contrary to employee retention goals")

        if morale_change != 0:
            success = game_state.department_manager.update_morale(department_name, morale_change)
            if success:
                reason_text = "; ".join(reasons) if reasons else "Turn outcome affected department KPIs"
                game_state.department_manager.add_history_entry(
                    department_name,
                    reason_text,
                    morale_change,
                    game_state.turn_number
                )
                print(f"  📊 {department_name}: {morale_change:+d} morale ({reason_text[:60]}...)")
            else:
                print(f"  ⚠️ Failed to update morale for {department_name}")

    print("--- Department KPI Check Complete ---")

def _generate_policy_title(major_policy):
    """Generates a corporate-sounding title for a new policy."""
    title = major_policy.get('event_title', 'Executive Decision')
    action_text = major_policy.get('action_text', '')

    if 'hiring freeze' in action_text.lower():
        return "Corporate Mandate on Hiring"
    elif 'return to office' in action_text.lower():
        return "Return-to-Office Policy Update"
    elif 'performance improvement' in action_text.lower():
        return "New Performance Improvement Plan (PIP) Framework"
    else:
        return f"The {title} Initiative"

def _infer_policy_effects(major_policy, game_state):
    """
    Infers the mechanical effects of a new corporate policy from its text.

    Args:
        major_policy (dict): Information about the detected policy change.
        game_state: The current game state.

    Returns:
        dict: A dictionary of effects to be applied to the game state.
    """
    action_text = major_policy.get('action_text', '').lower()
    policy_type = major_policy.get('type', 'operational')

    effects = {}

    # HR Policies
    if 'hiring freeze' in action_text:
        effects['hiring_status'] = 'frozen'
    elif 'layoffs' in action_text:
        # The number of layoffs would be in the 'updates', this just sets a flag
        effects['workforce_mood'] = 'anxious'
    elif 'remote work' in action_text and 'ending' in action_text:
        effects['work_policy'] = 'return_to_office'

    # Financial Policies
    if 'budget cuts' in action_text or 'spending freeze' in action_text:
        effects['budget_allocation'] = 'austerity'

    # Unspoken Rules (from cultural shifts)
    unspoken_rules = []
    if 'work-life balance' in action_text and 'deprioritized' in action_text:
        unspoken_rules.append("Overtime is unofficially expected")

    if unspoken_rules:
        effects['unspoken_rules'] = unspoken_rules

    return effects
