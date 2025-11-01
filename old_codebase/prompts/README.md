# AI Prompts Directory

This directory contains all AI prompts used by the civilization game engines. Prompts are externalized from Python code to allow easy editing without modifying source code.

## Directory Structure

```
prompts/
├── events/          - Event generation prompts
├── council/         - Council meeting prompts
├── actions/         - Player action processing prompts
├── callbacks/       - Callback event prompts (consequences)
├── characters/      - Character vignette prompts
├── crises/          - Crisis event prompts
├── factions/        - Faction audience prompts
├── timeskip/        - Time skip narrative prompts
├── visuals/         - Image generation prompts
└── world/           - World generation prompts
```

## How Prompts Work

### Format Variables
All prompts use Python's `.format()` syntax for variable substitution:
- Variables are enclosed in curly braces: `{variable_name}`
- Example: `"Leader: {leader_name}"` becomes `"Leader: Caesar"`

### Variable Documentation
Each prompt file includes a header documenting required variables:
```
# VARIABLES REQUIRED:
# - civ_name: Name of the civilization (string)
# - leader_name: Name of the leader (string)
# - population: Population count (integer)
```

### Loading Prompts in Code
```python
from engines.prompt_loader import load_prompt

# Load the prompt
prompt_template = load_prompt('events/generate_event')

# Fill in variables
prompt = prompt_template.format(
    civ_name="Rome",
    leader_name="Caesar",
    population=5000
)

# Send to AI model
response = model.generate_content(prompt)
```

## Editing Prompts

### Best Practices
1. **Preserve Variable Names**: Don't change `{variable_name}` without updating the engine code
2. **Test After Editing**: Run the game to ensure prompts work correctly
3. **Document Changes**: Use git commits to track prompt modifications
4. **Maintain Formatting**: Keep markdown formatting (`**bold**`, `*italics*`) intact

### Formatting Guidelines
- Use `**bold**` for emphasis on important names, critical moments
- Use `*italics*` for atmospheric descriptions, internal thoughts
- Use line breaks (`\n`) to separate ideas and create dramatic pauses
- Use bullet lists (`- item`) for multiple points

## Prompt Categories

### Events (`events/`)
- `generate_event.txt` - Main event generation prompt
- `generate_event_stage.txt` - Event stage progression prompt

### Council (`council/`)
- `council_meeting.txt` - Regular council meeting prompt
- `first_turn_briefing.txt` - Special first turn event prompt

### Actions (`actions/`)
- `process_player_action.txt` - Player decision outcome prompt

### Callbacks (`callbacks/`)
- `broken_promise.txt` - Broken promise consequence
- `enemy_revenge.txt` - Enemy revenge event
- `ally_request.txt` - Ally requesting aid
- `debt_collection.txt` - Debt collection event

### Characters (`characters/`)
- `character_vignette.txt` - Personal character dialogue prompt

### Crises (`crises/`)
- `famine.txt` - Catastrophic famine crisis
- `food_shortage.txt` - Food shortage warning
- `severe_food_shortage.txt` - Severe food crisis
- `economic_collapse.txt` - Total economic collapse
- `economic_crisis.txt` - Economic crisis
- `economic_warning.txt` - Economic warning
- `succession_crisis.txt` - Leader succession crisis
- `compound_crisis.txt` - Multiple simultaneous crises

### Factions (`factions/`)
- `faction_audience.txt` - Faction petition event

### Timeskip (`timeskip/`)
- `timeskip_500_years.txt` - 500-year time skip narrative

### Visuals (`visuals/`)
- `leader_portrait.txt` - Leader portrait generation
- `advisor_portrait.txt` - Advisor portrait generation
- `crisis_illustration.txt` - Crisis scene illustration
- `settlement_evolution.txt` - Settlement evolution image

### World (`world/`)
- `ai_description.txt` - World opening description

## Troubleshooting

### "PROMPT FILE NOT FOUND" Error
- Verify the prompt file exists in the correct subdirectory
- Check filename matches exactly (case-sensitive on some systems)
- Ensure `.txt` extension is present

### Formatting Issues
- Check for missing closing braces `}`
- Verify variable names match what the engine provides
- Test prompt with sample data before gameplay

### AI Generation Issues
- Review prompt clarity and specificity
- Ensure JSON output format is correctly specified
- Check that all required context is included

## Contributing

When adding new prompts:
1. Create prompt file in appropriate subdirectory
2. Add variable documentation header
3. Update this README with prompt description
4. Test thoroughly with the game engine
5. Commit with descriptive message

