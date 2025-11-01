import json
import google.generativeai as genai
from model_config import TEXT_MODEL
from utils.prompt_loader import load_prompt

class TreeGenerator:
    """
    Generates technology and civics trees using an AI model.
    """

    def generate_tech_tree(self, config: dict) -> dict:
        """
        Generates a technology tree based on the provided configuration.

        Args:
            config: A dictionary containing configuration details like 'era', 'genre_control', etc.

        Returns:
            A dictionary representing the parsed JSON of the technology tree.
        """
        era = config.get("era", "Ancient")
        genre_control = config.get("genre_control", "Standard fantasy")

        prompt = load_prompt('trees/generate_tech_tree').format(era=era, genre_control=genre_control)

        print(f"--- Tech Tree Prompt ---\n{prompt}\n------------------------")

        try:
            model = genai.GenerativeModel(TEXT_MODEL)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Error generating tech tree: {e}")
            # Fallback to a minimal tech tree
            return [
                {
                    "id": "tech_placeholder",
                    "name": "Placeholder Tech",
                    "description": "Error generating tree. Using placeholder.",
                    "cost": 0,
                    "prerequisites": [],
                    "era": era
                }
            ]

    def generate_civics_tree(self, config: dict) -> dict:
        """
        Generates a civics tree based on the provided configuration.

        Args:
            config: A dictionary containing configuration details like 'era', 'genre_control', etc.

        Returns:
            A dictionary representing the parsed JSON of the civics tree.
        """
        era = config.get("era", "Ancient")
        genre_control = config.get("genre_control", "Standard fantasy")

        prompt = load_prompt('trees/generate_civics_tree').format(era=era, genre_control=genre_control)

        print(f"--- Civics Tree Prompt ---\n{prompt}\n-------------------------")

        try:
            model = genai.GenerativeModel(TEXT_MODEL)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Error generating civics tree: {e}")
            # Fallback to a minimal civics tree
            return [
                {
                    "id": "civic_placeholder",
                    "name": "Placeholder Civic",
                    "description": "Error generating tree. Using placeholder.",
                    "cost": 0,
                    "prerequisites": [],
                    "era": era
                }
            ]
