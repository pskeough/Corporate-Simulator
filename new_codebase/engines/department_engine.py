# engines/department_engine.py
"""
Department Engine for Corporate Decision Simulator

This engine manages the consequences of decisions that affect various
corporate departments. It handles changes in department morale based on
whether a decision favors or opposes their interests and KPIs.
"""
import json
import google.generativeai as genai
from model_config import TEXT_MODEL
from engines.prompt_loader import load_prompt

def apply_department_decision_consequences(game_state, chosen_department, affected_departments):
    """
    Applies morale changes to departments based on executive decisions,
    particularly in scenarios like budget allocation meetings.

    The favored department receives a morale boost, while opposed departments
    suffer a morale penalty.

    Args:
        chosen_department (str): The name of the department whose proposal was accepted.
        affected_departments (list): A list of names of departments whose proposals were denied.
    """
    if not hasattr(game_state, 'department_manager'):
        return

    # Boost morale for the chosen department
    morale_boost = 15
    game_state.department_manager.update_morale(chosen_department, morale_boost)
    game_state.department_manager.add_history_entry(
        chosen_department,
        "Executive decision favored your department's proposal.",
        morale_boost,
        game_state.turn_number
    )
    print(f"  ✓ {chosen_department}: +{morale_boost} morale (Decision favored them)")

    # Penalize the departments that were not chosen
    for opposed_department in affected_departments:
        base_penalty = -25

        # Check if the department already has low morale; if so, they take it harder
        department_data = game_state.department_manager.get_by_name(opposed_department)
        if department_data and department_data.get('morale', 60) < 40:
            base_penalty = -35  # Low morale departments are more sensitive to setbacks

        game_state.department_manager.update_morale(opposed_department, base_penalty)
        game_state.department_manager.add_history_entry(
            opposed_department,
            "Decision opposed your department's interests.",
            base_penalty,
            game_state.turn_number
        )
        print(f"  ✗ {opposed_department}: {base_penalty} morale (Decision opposed them)")

    # Check for cross-departmental conflict risk
    low_morale_departments = [
        d for d in game_state.department_manager.get_all()
        if d.get('morale', 60) < 30
    ]

    if len(low_morale_departments) >= 2:
        print(f"  ⚠️ WARNING: {len(low_morale_departments)} departments have very low morale. Risk of inter-departmental conflict is high.")
        # This condition can be used by the event generator to trigger specific conflict events.

def generate_department_budget_meeting(game_state):
    """
    Generates a department budget meeting event using a generative AI model.

    This function constructs a prompt containing the current state of various
    departments (their KPIs, morale) and asks the AI to create competing
    budget proposals from each.

    Args:
        game_state: The current state of the simulation.

    Returns:
        dict: A dictionary representing the budget meeting event.
    """
    if not hasattr(game_state, 'department_manager'):
        print("Warning: No department manager available. Skipping budget meeting.")
        return {}

    departments = game_state.department_manager.get_all()
    if not departments:
        print("Warning: No departments available. Skipping budget meeting.")
        return {}

    # Create a context-rich description for each department for the AI
    department_contexts = []
    for dept in departments:
        dept_name = dept.get('name', 'Unknown')
        kpis = ", ".join(dept.get("kpis", []))
        morale = dept.get("morale", 50)

        if morale >= 75:
            morale_desc = f"{morale} (High-performing and motivated)"
        elif morale >= 50:
            morale_desc = f"{morale} (Meeting expectations)"
        else:
            morale_desc = f"{morale} (Struggling and under-resourced)"

        department_contexts.append({
            'name': dept_name,
            'kpis': kpis,
            'morale_desc': morale_desc
        })

    # Format the department list for injection into the prompt
    department_list = ""
    for dc in department_contexts:
        department_list += f"- Department: {dc['name']}:\n"
        department_list += f"  - Current KPIs: {dc['kpis']}\n"
        department_list += f"  - Current Morale: {dc['morale_desc']}\n"

    prompt = load_prompt('departments/budget_meeting').format(
        department_list=department_list,
        player_title=game_state.player['title']
    )

    try:
        model = genai.GenerativeModel(TEXT_MODEL)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        result = json.loads(response.text)
        result["event_type"] = "department_budget_meeting"

        if 'title' in result:
            result['title'] = result['title'] + " -- Budget Proposal Meeting"

        # Initialize the event in the game state
        game_state.current_event = result
        game_state.event_stage = 0
        game_state.event_conversation = []

        return result
    except Exception as e:
        print(f"Error generating department budget meeting: {e}")
        return {}
