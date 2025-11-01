# engines/visual_engine.py
"""
Visual generation engine using Gemini 2.5 Flash Image.
Handles leader portraits, crisis illustrations, and settlement evolution.
"""

from google import genai
from google.genai import types
import os
from PIL import Image
import io
from model_config import VISUAL_MODEL
from engines.prompt_loader import load_prompt

# Initialize client (API key is configured globally via genai.configure)
def get_client():
    """Get configured genai client using the API key from environment."""
    import google.generativeai as old_genai
    # The API key is already configured in main.py, we just need to use it
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    return genai.Client(api_key=api_key)


def generate_leader_portrait(leader, civilization_context):
    """
    Generate a portrait for a leader using Gemini 2.5 Flash Image.

    Args:
        leader: Leader dict with name, age, traits, role
        civilization_context: Dict with era, culture info

    Returns:
        dict with image_path and success status
    """
    print(f"--- Generating portrait for {leader.get('name', 'Unknown')} ---")

    # Build portrait prompt
    name = leader.get('name', 'Unknown Leader')
    age = leader.get('age', 30)
    traits = leader.get('traits', [])
    role = leader.get('role', 'Leader')
    era = civilization_context.get('era', 'classical')
    culture_values = civilization_context.get('culture_values', [])

    # Age descriptors
    if age < 30:
        age_desc = "youthful"
    elif age < 50:
        age_desc = "middle-aged"
    elif age < 70:
        age_desc = "elderly"
    else:
        age_desc = "ancient"

    # Trait-based visual cues
    trait_descriptions = {
        'Brave': 'confident gaze, battle-worn features',
        'Warrior': 'scarred face, strong jawline, military bearing',
        'Wise': 'thoughtful expression, intelligent eyes',
        'Scholar': 'scholarly attire, holding a scroll or book',
        'Pious': 'serene expression, religious symbols visible',
        'Charismatic': 'warm smile, magnetic presence',
        'Diplomatic': 'refined features, elegant posture',
        'Ruthless': 'stern expression, cold eyes',
        'Cunning': 'sharp features, calculating gaze',
        'Mystic': 'otherworldly appearance, mystical elements',
        'Ancient': 'deeply lined face, white hair, frail but dignified'
    }

    visual_traits = [trait_descriptions.get(trait, '') for trait in traits if trait in trait_descriptions]
    trait_text = ', '.join(visual_traits[:3]) if visual_traits else 'dignified bearing'

    # Era-appropriate styling
    era_styles = {
        'stone_age': 'primitive furs and leather, tribal markings, stone ornaments',
        'bronze_age': 'bronze jewelry, woven fabrics, clay ornaments',
        'iron_age': 'iron torque or crown, wool garments, metalwork',
        'classical': 'toga or robes, laurel crown, classical architecture hints',
        'medieval': 'medieval crown, rich robes, heraldic symbols',
        'renaissance': 'renaissance clothing, ornate jewelry, refined aesthetics'
    }

    era_style = era_styles.get(era, 'classical robes and simple crown')

    # Enhanced age-specific visual details
    if age < 20:
        age_visual = "youthful with smooth skin, bright eyes full of idealism, untested and fresh-faced"
    elif age < 30:
        age_visual = "young adult with sharp features, eager gaze, minimal weathering"
    elif age < 45:
        age_visual = "in their prime, confident bearing, some life experience showing in the eyes"
    elif age < 60:
        age_visual = "mature with distinguished features, threads of gray in hair, wisdom in the gaze"
    elif age < 75:
        age_visual = "elderly with weathered face, gray or white hair, deep-set eyes showing years of rule"
    else:
        age_visual = "ancient with deeply lined face, white hair, stooped posture, frail but dignified, trembling hands"

    # Load and format prompt
    prompt_template = load_prompt('visuals/leader_portrait')
    prompt = prompt_template.format(
        name=name,
        age=age,
        age_desc=age_desc,
        age_visual=age_visual,
        role=role,
        era=era,
        trait_text=trait_text,
        era_style=era_style,
        culture_values=', '.join(culture_values[:2]) if culture_values else 'strength and tradition',
        traits=', '.join(traits)
    )

    try:
        client = get_client()

        response = client.models.generate_content(
            model=VISUAL_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )

        # Extract image data
        image_data = None
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_data = part.inline_data.data
                break

        if image_data:
            # Create directory if needed
            os.makedirs("static/images/leaders", exist_ok=True)

            # Generate filename
            import time
            timestamp = int(time.time())
            filename = f"leader_{name.replace(' ', '_').lower()}_{timestamp}.png"
            image_path = f"static/images/leaders/{filename}"

            # Save image
            img = Image.open(io.BytesIO(image_data))
            img.save(image_path)

            print(f"--- Portrait generated successfully: {image_path} ---")
            return {
                "image_path": image_path,
                "filename": filename,
                "success": True
            }
        else:
            raise ValueError("No image data in response")

    except Exception as e:
        print(f"Error generating leader portrait: {e}")
        import traceback
        traceback.print_exc()
        return {
            "image_path": "static/placeholder.png",
            "filename": "placeholder.png",
            "success": False,
            "error": str(e)
        }


def _parse_crisis_prompts(prompt_file_content):
    """
    Parse the crisis illustration prompt file into a dictionary.

    Args:
        prompt_file_content: The full content of crisis_illustration.txt

    Returns:
        Dictionary mapping crisis types to their prompts
    """
    crisis_prompts = {}

    # Split by the delimiter (---) and process each section
    sections = prompt_file_content.split('---')

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Process each line
        lines = section.split('\n')
        crisis_type = None
        prompt_lines = []

        for line in lines:
            # Skip comment lines (start with #, but not ##)
            if line.strip().startswith('#') and not line.strip().startswith('## '):
                continue

            if line.startswith('## '):
                # Extract crisis type and normalize it
                crisis_type = line.replace('## ', '').strip().lower()
            elif crisis_type and line.strip():  # Only add non-empty lines
                prompt_lines.append(line)

        if crisis_type and prompt_lines:
            crisis_prompts[crisis_type] = '\n'.join(prompt_lines).strip()

    return crisis_prompts


def generate_crisis_illustration(crisis_type, civilization_context):
    """
    Generate a dramatic illustration for a crisis event.

    Args:
        crisis_type: Type of crisis (famine, economic_collapse, etc.)
        civilization_context: Dict with era, population, etc.

    Returns:
        dict with image_path and success status
    """
    print(f"--- Generating crisis illustration: {crisis_type} ---")

    era = civilization_context.get('era', 'classical')
    civ_name = civilization_context.get('name', 'civilization')
    terrain = civilization_context.get('terrain', 'plains')

    # Load and parse crisis prompts from file
    crisis_file_content = load_prompt('visuals/crisis_illustration')
    crisis_prompts = _parse_crisis_prompts(crisis_file_content)

    # Select the appropriate prompt template based on crisis type
    prompt_template = crisis_prompts.get(crisis_type, crisis_prompts.get('famine', ''))

    # Format the prompt with variables
    prompt = prompt_template.format(era=era, terrain=terrain)

    try:
        client = get_client()

        response = client.models.generate_content(
            model=VISUAL_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )

        # Extract image
        image_data = None
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_data = part.inline_data.data
                break

        if image_data:
            os.makedirs("static/images/crises", exist_ok=True)

            filename = f"crisis_{crisis_type}_{era}.png"
            image_path = f"static/images/crises/{filename}"

            # Save (or check if already exists to use cache)
            if not os.path.exists(image_path):
                img = Image.open(io.BytesIO(image_data))
                img.save(image_path)
                print(f"--- Crisis illustration saved: {image_path} ---")
            else:
                print(f"--- Using cached crisis illustration: {image_path} ---")

            return {
                "image_path": image_path,
                "filename": filename,
                "success": True
            }
        else:
            raise ValueError("No image data in response")

    except Exception as e:
        print(f"Error generating crisis illustration: {e}")
        import traceback
        traceback.print_exc()
        return {
            "image_path": "static/placeholder.png",
            "filename": "placeholder.png",
            "success": False,
            "error": str(e)
        }


def generate_settlement_evolution(game_state, year_marker):
    """
    Generate an updated settlement image showing civilization evolution.
    Enhanced version of the existing settlement generator with versioning.

    Args:
        game_state: Full game state
        year_marker: Year for filename tracking

    Returns:
        dict with image_path and success status
    """
    print(f"--- Generating settlement evolution image for year {year_marker} ---")

    from engines.context_builder import build_image_context

    context = build_image_context(game_state)

    # Determine settlement size
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

    era = context['civilization']['era']
    tech_tier = context['civilization']['tech_tier']

    # Extract recent infrastructure for visual references
    recent_infrastructure = context['technology'].get('infrastructure', [])
    infrastructure_visual = ""
    if recent_infrastructure:
        latest_buildings = recent_infrastructure[-3:]
        infrastructure_visual = f"\n- Prominently feature recently built infrastructure: {', '.join(latest_buildings)}"

    # Cultural aesthetic guidance
    culture_values = context['culture'].get('values', [])
    cultural_aesthetic = ""
    if culture_values:
        values_str = ', '.join(culture_values[:3])
        cultural_aesthetic = f"\n- Cultural aesthetic influenced by values: {values_str} (e.g., 'Martial Pride' = military structures prominent, 'Artistic Excellence' = decorative architecture, 'Religious Devotion' = grand temples)"

    # Load and format prompt
    prompt_template = load_prompt('visuals/settlement_evolution')
    prompt = prompt_template.format(
        civ_name=context['civilization']['name'],
        year_marker=year_marker,
        size_desc=size_desc,
        era=era,
        tech_tier=tech_tier,
        population=f"{context['civilization']['population']:,}",
        culture_values=', '.join(culture_values[:3]) if culture_values else 'survival and growth',
        terrain=context['world']['terrain'],
        climate=context['world']['climate'],
        resources=', '.join(context['world'].get('resources', ['basic resources'])),
        religion_name=context['religion']['name'],
        holy_sites=', '.join(context['religion'].get('holy_sites', ['sacred grounds'])),
        social_structure=context['culture']['social_structure'],
        cultural_aesthetic=cultural_aesthetic,
        infrastructure_visual=infrastructure_visual,
        recent_infrastructure=', '.join(recent_infrastructure[-2:]) if recent_infrastructure else 'none yet'
    )

    try:
        client = get_client()

        response = client.models.generate_content(
            model=VISUAL_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )

        image_data = None
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_data = part.inline_data.data
                break

        if image_data:
            os.makedirs("static/images/settlements", exist_ok=True)

            filename = f"settlement_{year_marker}_{era}.png"
            image_path = f"static/images/settlements/{filename}"

            img = Image.open(io.BytesIO(image_data))

            # Resize to 2x for better display quality
            new_size = (img.width * 2, img.height * 2)
            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
            resized_img.save(image_path)

            # Also update the main settlement.png for backward compatibility
            resized_img.save("static/settlement.png")

            print(f"--- Settlement evolution image saved: {image_path} ---")

            # Cleanup old settlements (keep only last 5)
            cleanup_old_settlements()

            return {
                "image_path": image_path,
                "filename": filename,
                "success": True,
                "year": year_marker
            }
        else:
            raise ValueError("No image data in response")

    except Exception as e:
        print(f"Error generating settlement evolution: {e}")
        import traceback
        traceback.print_exc()
        return {
            "image_path": "static/placeholder.png",
            "filename": "placeholder.png",
            "success": False,
            "error": str(e)
        }


def cleanup_old_settlements():
    """Keep only the 5 most recent settlement images to save disk space."""
    settlements_dir = "static/images/settlements"

    if not os.path.exists(settlements_dir):
        return

    # Get all settlement images
    settlements = [f for f in os.listdir(settlements_dir) if f.startswith("settlement_") and f.endswith(".png")]

    if len(settlements) > 5:
        # Sort by modification time
        settlements.sort(key=lambda x: os.path.getmtime(os.path.join(settlements_dir, x)))

        # Remove oldest
        to_remove = settlements[:-5]
        for filename in to_remove:
            try:
                os.remove(os.path.join(settlements_dir, filename))
                print(f"  Cleaned up old settlement: {filename}")
            except Exception as e:
                print(f"  Could not remove {filename}: {e}")


def get_settlement_gallery(limit=5):
    """
    Get list of recent settlement images for gallery display.

    Returns:
        List of dicts with filename, year, era, path
    """
    settlements_dir = "static/images/settlements"

    if not os.path.exists(settlements_dir):
        return []

    settlements = [f for f in os.listdir(settlements_dir) if f.startswith("settlement_") and f.endswith(".png")]

    # Sort by modification time (newest first)
    settlements.sort(key=lambda x: os.path.getmtime(os.path.join(settlements_dir, x)), reverse=True)

    gallery = []
    for filename in settlements[:limit]:
        # Parse filename: settlement_[year]_[era].png
        parts = filename.replace("settlement_", "").replace(".png", "").split("_")
        year = parts[0] if len(parts) > 0 else "0"
        era = parts[1] if len(parts) > 1 else "unknown"

        gallery.append({
            "filename": filename,
            "year": year,
            "era": era,
            "path": f"images/settlements/{filename}"
        })

    return gallery


def generate_advisor_portrait(advisor, civilization_context):
    """
    Generate a portrait for an Inner Circle advisor using Gemini 2.5 Flash Image.
    Uses the same style system as leader portraits for consistency.

    Args:
        advisor: Advisor dict with name, role, personality_traits, etc.
        civilization_context: Dict with era, culture info

    Returns:
        dict with image_path, filename, and success status
    """
    print(f"--- Generating advisor portrait for {advisor.get('name', 'Unknown')} ---")

    # Extract advisor info
    name = advisor.get('name', 'Unknown Advisor')
    role = advisor.get('role', 'Advisor')
    traits = advisor.get('personality_traits', [])
    era = civilization_context.get('era', 'classical')
    culture_values = civilization_context.get('culture_values', [])

    # Infer age from role and traits (advisors are typically mature)
    if 'Elder' in role or 'Ancient' in traits:
        age = 65
        age_desc = "elderly"
        age_visual = "elderly with weathered face, gray or white hair, deep-set eyes showing years of experience"
    elif 'High Priest' in role or 'Grand' in role:
        age = 50
        age_desc = "mature"
        age_visual = "mature with distinguished features, threads of gray in hair, wisdom in the gaze"
    else:
        age = 40
        age_desc = "in their prime"
        age_visual = "in their prime, confident bearing, experience showing in the eyes"

    # Trait-based visual cues
    trait_descriptions = {
        'Pragmatic': 'calculating gaze, composed expression',
        'Cunning': 'sharp features, intelligent eyes',
        'Discreet': 'subtle presence, observant gaze',
        'Ambitious': 'determined expression, forward posture',
        'Disciplined': 'stern features, military bearing',
        'Direct': 'straightforward gaze, honest expression',
        'Loyal': 'trustworthy presence, steady eyes',
        'Stern': 'serious expression, commanding presence',
        'Pious': 'serene expression, religious symbols visible',
        'Compassionate': 'warm eyes, gentle features',
        'Traditionalist': 'formal attire, conservative bearing',
        'Serene': 'peaceful expression, calm demeanor'
    }

    visual_traits = [trait_descriptions.get(trait, '') for trait in traits if trait in trait_descriptions]
    trait_text = ', '.join(visual_traits[:3]) if visual_traits else 'dignified bearing'

    # Era-appropriate styling (same as leader portraits)
    era_styles = {
        'stone_age': 'primitive furs and leather, tribal markings, stone ornaments',
        'bronze_age': 'bronze jewelry, woven fabrics, clay ornaments',
        'iron_age': 'iron jewelry or insignia, wool garments, metalwork',
        'classical': 'classical robes, refined jewelry, toga or formal attire',
        'medieval': 'medieval attire, formal robes, period-appropriate regalia',
        'renaissance': 'renaissance clothing, ornate jewelry, refined aesthetics'
    }

    era_style = era_styles.get(era, 'classical robes and formal attire')

    # Role-specific visual elements
    role_visuals = {
        'Spymaster': 'dark clothing, subtle insignia, observant presence, hint of mystery',
        'Grand Marshal': 'military regalia, armor elements, medals, commanding bearing',
        'High Priestess': 'religious robes, holy symbols, serene presence, ceremonial attire',
        'High Priest': 'religious robes, holy symbols, wise presence, ceremonial attire',
        'Advisor': 'formal robes, scholarly appearance, dignified bearing',
        'Chancellor': 'administrative robes, scrolls or documents, official bearing',
        'General': 'military uniform, battle-worn features, strategic gaze'
    }

    role_visual = role_visuals.get(role, 'formal attire befitting their position')

    # Load and format prompt
    prompt_template = load_prompt('visuals/advisor_portrait')
    prompt = prompt_template.format(
        name=name,
        age=age,
        age_desc=age_desc,
        age_visual=age_visual,
        role=role,
        era=era,
        trait_text=trait_text,
        role_visual=role_visual,
        era_style=era_style,
        culture_values=', '.join(culture_values[:2]) if culture_values else 'wisdom and service',
        traits=', '.join(traits[:3])
    )

    try:
        client = get_client()

        response = client.models.generate_content(
            model=VISUAL_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )

        # Extract image data
        image_data = None
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_data = part.inline_data.data
                break

        if image_data:
            # Create directory if needed
            os.makedirs("static/images/advisors", exist_ok=True)

            # Generate filename
            import time
            timestamp = int(time.time())
            filename = f"advisor_{name.replace(' ', '_').lower()}_{timestamp}.png"
            image_path = f"static/images/advisors/{filename}"

            # Save image
            img = Image.open(io.BytesIO(image_data))
            img.save(image_path)

            print(f"--- Advisor portrait generated successfully: {image_path} ---")
            return {
                "image_path": image_path,
                "filename": filename,
                "success": True
            }
        else:
            raise ValueError("No image data in response")

    except Exception as e:
        print(f"Error generating advisor portrait: {e}")
        import traceback
        traceback.print_exc()
        return {
            "image_path": "static/placeholder.png",
            "filename": "placeholder.png",
            "success": False,
            "error": str(e)
        }


# ============================================================================
# ASYNC IMAGE UPDATE FUNCTIONS (Background Threading)
# ============================================================================

def update_leader_portrait_async(game_state):
    """
    Trigger background leader portrait regeneration.
    This runs in a separate thread to avoid blocking gameplay.
    """
    import threading

    def _generate_and_update():
        try:
            leader = game_state.civilization['leader']

            # Build civilization context for portrait generation
            civ_context = {
                'era': game_state.civilization['meta']['era'],
                'culture_values': game_state.culture.get('values', [])
            }

            # Generate new portrait
            result = generate_leader_portrait(leader, civ_context)

            if result['success']:
                # Update the leader's portrait reference
                game_state.civilization['leader']['portrait'] = result['filename']

                # Update the tracker
                from engines.image_update_manager import get_tracker
                tracker = get_tracker()
                tracker.update_portrait_state(game_state)

                print(f"  ✓ Leader portrait updated successfully: {result['filename']}")
            else:
                print(f"  ✗ Failed to update leader portrait: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"  ✗ Error in background portrait update: {e}")
            import traceback
            traceback.print_exc()

    # Start background thread
    thread = threading.Thread(target=_generate_and_update, daemon=True)
    thread.start()


def update_settlement_image_async(game_state):
    """
    Trigger background settlement image regeneration.
    This runs in a separate thread to avoid blocking gameplay.
    """
    import threading

    def _generate_and_update():
        try:
            year_marker = game_state.civilization['meta']['year']

            # Generate new settlement image
            result = generate_settlement_evolution(game_state, year_marker)

            if result['success']:
                # Update the tracker
                from engines.image_update_manager import get_tracker
                tracker = get_tracker()
                tracker.update_settlement_state(game_state)

                print(f"  ✓ Settlement image updated successfully: {result['filename']}")
            else:
                print(f"  ✗ Failed to update settlement image: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"  ✗ Error in background settlement update: {e}")
            import traceback
            traceback.print_exc()

    # Start background thread
    thread = threading.Thread(target=_generate_and_update, daemon=True)
    thread.start()
