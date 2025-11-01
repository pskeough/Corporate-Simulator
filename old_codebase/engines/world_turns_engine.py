import json
from json import JSONDecodeError
import google.generativeai as genai
from model_config import TEXT_MODEL
from engines.bonus_engine import BonusEngine
from engines.bonus_definitions import BonusType

class WorldTurnsEngine:
    def calculate_rates_with_bonus_engine(self, game_state):
        """
        NEW: Calculate resource rates using BonusEngine.
        Runs in parallel with old logic for verification.
        """
        population = game_state.civilization['population']
        happiness = game_state.population_happiness

        # Use bonus engine for character bonuses
        bonus_engine = BonusEngine()
        science_bonuses = bonus_engine.calculate_bonuses(game_state, BonusType.SCIENCE_PER_TURN)
        culture_bonuses = bonus_engine.calculate_bonuses(game_state, BonusType.CULTURE_PER_TURN)

        # BALANCE_OVERHAUL: Happiness affects productivity with tiered penalties
        if happiness >= 70:
            happiness_multiplier = 1.0
        elif happiness >= 50:
            happiness_multiplier = 0.75  # -25% penalty
        elif happiness >= 30:
            happiness_multiplier = 0.60  # -40% penalty
        else:
            happiness_multiplier = 0.50  # -50% penalty (severe unrest)

        # Calculate rates with happiness multiplier
        science_per_turn = ((population / 1000) * (happiness / 100) + science_bonuses['total']) * happiness_multiplier
        culture_per_turn = ((population / 1000) * (happiness / 100) + culture_bonuses['total']) * happiness_multiplier

        return {
            'science': science_per_turn,
            'culture': culture_per_turn,
            'science_sources': science_bonuses['sources'],
            'culture_sources': culture_bonuses['sources']
        }

    def simulate_turn(self, game_state, last_action_details):
        """
        Calculates the resource rates for a turn based on the current game state.
        """
        # Calculate resource rates using BonusEngine
        rates = self.calculate_rates_with_bonus_engine(game_state)
        science_per_turn = rates['science']
        culture_per_turn = rates['culture']

        # Check if this was a council meeting
        is_council = last_action_details.get('event_type') == 'council_meeting'

        # Construct AI prompt for world changes
        game_state_json = json.dumps(game_state.to_dict(), indent=2)

        if is_council:
            # COUNCIL MEETING: Analyze conversation to determine advisor reactions
            conversation = last_action_details.get('conversation', [])
            conv_text = "\n".join([
                f"Player: {entry['player']}\nAdvisor Response: {entry['ai']}"
                for entry in conversation
            ])

            ai_prompt = f"""
Given the current game state:
{game_state_json}

And this COUNCIL MEETING conversation:
{conv_text}

Player's final decision: {last_action_details['action']}
Outcome: {last_action_details['outcome']}

Analyze the DIALOGUE CHOICES the player made during the council meeting. Determine how each Inner Circle advisor would react based on:
- Whether the player agreed with their position
- Whether the final decision aligned with their stance
- The tone of the player's questions/responses to them

Generate balanced inner_circle_updates with:
- Advisors aligned with player's choices: +3 to +8 loyalty/opinion_change
- Advisors opposed by player's choices: -3 to -8 loyalty/opinion_change
- Include a brief "memory" of this council meeting for each advisor

Also determine faction and neighboring civilization reactions.

Your response must be a valid JSON object with the following structure:
{{
  "faction_updates": [
    {{
      "name": "string",
      "approval_change": "integer",
      "reason": "Brief human-readable explanation for the change"
    }}
  ],
  "inner_circle_updates": [
    {{
      "name": "string",
      "loyalty_change": "integer (max ±8)",
      "opinion_change": "integer (max ±8)",
      "memory": "Brief description of this council meeting from their perspective"
    }}
  ],
  "neighboring_civilization_updates": [
    {{
      "name": "string",
      "relationship_change": "integer"
    }}
  ]
}}
"""
        else:
            # NON-COUNCIL EVENTS: Use existing logic
            ai_prompt = f"""
Given the current game state:
{game_state_json}

And the last player action:
{last_action_details}

Determine the indirect consequences of this action. Return a JSON object detailing subtle changes to the following:
- Faction approval and support.
- Inner Circle character metrics (loyalty, influence) and a new memory to add to their "history".
- The relationship status of neighboring civilizations.

Your response must be a valid JSON object with the following structure:
{{
  "faction_updates": [
    {{
      "name": "string",
      "approval_change": "integer",
      "reason": "Brief human-readable explanation for the change"
    }}
  ],
  "inner_circle_updates": [
    {{
      "name": "string",
      "loyalty_change": "integer",
      "opinion_change": "integer"
    }}
  ],
  "neighboring_civilization_updates": [
    {{
      "name": "string",
      "relationship_change": "integer"
    }}
  ]
}}
"""

        # Call Gemini API to get world updates
        try:
            model = genai.GenerativeModel(TEXT_MODEL)
            response = model.generate_content(
                ai_prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.7
                }
            )
            ai_updates = json.loads(response.text)
            print(f"--- World Turn Simulation Complete ---")
        except JSONDecodeError as e:
            print(f"!!!!!!!!!! JSON PARSING ERROR (World Turn) !!!!!!!!!!!\n{e}")
            print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
            ai_updates = None
        except Exception as e:
            print(f"!!!!!!!!!! GEMINI API ERROR (World Turn) !!!!!!!!!!!\n{e}")
            ai_updates = None

        return ai_updates
