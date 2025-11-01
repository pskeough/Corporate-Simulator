import google.generativeai as genai
import json
from PIL import Image
import io
import base64
from engines.context_builder import build_image_context
from model_config import IMAGE_MODEL

def generate_settlement_image(game_state):
    """
    Generates a new settlement visualization based on the current game state
    using the configured image generation model, then resizes it.
    """
    print("--- Generating new settlement image via Gemini API ---")
    model = genai.GenerativeModel(IMAGE_MODEL)

    # Build optimized visual context
    context = build_image_context(game_state)

    # Determine settlement size descriptor
    pop = context['civilization']['population']
    if pop < 100:
        size_desc = "small primitive camp"
    elif pop < 500:
        size_desc = "modest village"
    elif pop < 2000:
        size_desc = "thriving town"
    elif pop < 10000:
        size_desc = "large settlement"
    else:
        size_desc = "sprawling city"

    # Extract key visual elements from recent history
    recent_event_context = ""
    if context['recent_major_events']['events']:
        latest = context['recent_major_events']['events'][-1]
        recent_event_context = f"\nRecent historical context: {latest.get('narrative', '')[:100]}"

    # Extract contextual details
    culture_values = context['culture'].get('values', [])
    primary_values = ', '.join(culture_values[:3]) if culture_values else 'survival and tradition'

    # Structured image prompt with enhanced narrative guidance
    prompt = f"""Generate a richly detailed, atmospheric view of {context['civilization']['name']}, a {size_desc} in the {context['civilization']['era']} era.

**VISUAL NARRATIVE PURPOSE:** Capture the unique identity of this civilization. This is not a generic settlement - it's {context['civilization']['name']}, shaped by its culture, terrain, and history.

SETTLEMENT IDENTITY:
- Civilization: {context['civilization']['name']}
- Era: {context['civilization']['era']}
- Technology Level: {context['civilization']['tech_tier']} (CRITICAL: architecture style must be era-authentic)
- Population: {context['civilization']['population']:,} souls (settlement size MUST match this - {size_desc})
- Cultural Character: Values {primary_values}

ENVIRONMENTAL SETTING:
- Terrain: {context['world']['terrain']} (integrate this terrain visually - rivers, hills, forests, etc.)
- Climate: {context['world']['climate']} (affects vegetation, weather, sky, atmosphere)
- Natural Resources: {', '.join(context['world'].get('resources', ['basic resources']))} (show mines, farms, quarries, etc.){recent_event_context}

CULTURAL & RELIGIOUS LANDSCAPE:
- Primary Religion: {context['religion']['name']} (religious structures should be prominent)
- Holy Sites: {', '.join(context['religion'].get('holy_sites', ['sacred grounds']))} (incorporate into layout)
- Social Structure: {context['culture']['social_structure']} (show class divisions - palaces vs dwellings)
- Cultural Aesthetic: Values like "{primary_values}" should influence architecture (e.g., martial culture = fortifications, artistic culture = decorative elements, religious culture = grand temples)

VISUAL STORYTELLING REQUIREMENTS:
1. **Era-Authentic Architecture**: {context['civilization']['tech_tier']} must dictate building style
   - stone_age: Primitive huts, campfires, animal hide tents
   - bronze_age: Mud brick, early stone, simple walls
   - iron_age: Solid stone buildings, defensive fortifications
   - classical: Grand architecture, organized city planning, columns
   - medieval: Castles, cathedrals, dense medieval urban core
   - renaissance: Ornate buildings, public squares, artistic details

2. **Population-Appropriate Scale**: {context['civilization']['population']:,} people = {size_desc}

3. **Terrain Integration**: Settlement works WITH {context['world']['terrain']} (not generic flat land)

4. **Climate Atmosphere**: {context['world']['climate']} affects everything - vegetation, sky, weather, colors

5. **Cultural Identity**: The values "{primary_values}" should be VISIBLE in the layout and architecture

6. **Religious Presence**: {context['religion']['name']} worship creates visible landmarks

TECHNICAL REQUIREMENTS:
- Perspective: Isometric or elevated top-down showing full settlement
- Art Style: Painterly, strategy game aesthetic (think Civilization, Age of Empires)
- Lighting: Atmospheric (golden hour, dramatic clouds, natural lighting)
- Detail: Rich foreground detail, atmospheric background
- NO text, UI, labels, or modern elements
- Color palette matching {context['civilization']['era']} era and {context['world']['climate']} climate

**REACTIVITY REQUIREMENT:**
This is {context['civilization']['name']} - make it DISTINCTIVE. Its {context['civilization']['tech_tier']} technology, {context['world']['terrain']} terrain, {context['world']['climate']} climate, and focus on "{primary_values}" should create a unique visual signature.

Generate a single, breathtaking settlement scene that tells this civilization's story."""

    try:
        response = model.generate_content(prompt)

        image_data = None
        # Robustly search for the image data in the response parts
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_data = part.inline_data.data
                    break

        if image_data:
            image_path = "static/settlement.png"

            # Open the image from the binary data using Pillow
            img = Image.open(io.BytesIO(image_data))

            # Resize the image to be 200% larger using a high-quality filter
            new_size = (img.width * 2, img.height * 2)
            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Save the resized image
            resized_img.save(image_path)

            print(f"--- Settlement image successfully generated, resized, and saved to {image_path} ---")
            return {"image_path": image_path, "success": True}
        else:
            raise ValueError("No image data found in the API response.")

    except Exception as e:
        print(f"!!!!!!!!!! GEMINI API ERROR (Image Generation) !!!!!!!!!!!")
        print(f"Error generating image: {e}")
        return {"image_path": "static/placeholder.png", "success": False, "error": str(e)}

def edit_settlement_image(game_state, current_image_path):
    """
    Edits an existing settlement visualization based on new game state changes.
    (Placeholder for future implementation)
    """
    print("--- Editing settlement image (placeholder) ---")
    # Future implementation will involve image-to-image generation or editing
    # For now, it will just return the existing image or a placeholder.
    return {"image_path": current_image_path, "success": True, "message": "Image editing not yet implemented, returning current image."}

