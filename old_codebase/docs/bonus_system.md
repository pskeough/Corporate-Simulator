# Bonus System Documentation

## Overview
The BonusEngine provides centralized calculation of all game bonuses from multiple sources.

## Architecture

### Components
- `engines/bonus_definitions.py` - Defines all bonus types and values
- `engines/bonus_engine.py` - Aggregates bonuses from all sources
- `engines/world_turns_engine.py` - Uses BonusEngine for per-turn calculations

### Bonus Sources
1. **Characters** (Inner Circle) - Role-based bonuses
2. **Buildings** (Infrastructure) - Placeholder for future implementation
3. **Technologies** (Discoveries) - Placeholder for future implementation
4. **Leader Traits** - Placeholder for future implementation

## Adding New Bonuses

### For Characters (Current)
Edit `engines/bonus_definitions.py`:

```python
CHARACTER_ROLE_BONUSES = {
    'New Role': {
        'science_per_turn': 10,
        'description': 'Role description'
    }
}
```

### For Buildings (Future - Phase 4)
Edit `engines/bonus_definitions.py`:

```python
BUILDING_BONUSES = {
    'Library': {
        'science_per_turn': 5,
        'description': 'Libraries preserve knowledge',
        'cost': {'wealth': 500},
        'era_required': 'bronze_age'
    }
}
```

**No code changes needed** - BonusEngine automatically picks up new definitions!

### For Technologies (Future - Phase 4)
Edit `engines/bonus_definitions.py`:

```python
TECHNOLOGY_BONUSES = {
    'Writing': {
        'science_per_turn': 3,
        'culture_per_turn': 2,
        'description': 'Recording knowledge'
    }
}
```

## Bonus Types

- `food_per_turn` - Food production per turn
- `wealth_per_turn` - Wealth production per turn
- `science_per_turn` - Science points per turn
- `culture_per_turn` - Culture points per turn
- `population_growth` - Population growth modifier
- `happiness` - Happiness modifier

## Testing

Run the test script to verify bonus calculations:

```bash
python test_bonus_engine.py
```

This will:
- Load the current game state
- Calculate all active bonuses
- Verify bonuses match expected values
- Display a detailed bonus summary

## Future Extensions

- [ ] Multiplier bonuses (e.g., +20% food production)
- [ ] Conditional bonuses (e.g., "if near river")
- [ ] Stacking rules (e.g., diminishing returns)
- [ ] Temporary bonuses (e.g., event-based buffs)

## Usage Example

```python
from game_state import GameState
from engines.bonus_engine import BonusEngine
from engines.bonus_definitions import BonusType

# Load game state
game = GameState()

# Create bonus engine
engine = BonusEngine()

# Get science bonuses
science = engine.calculate_bonuses(game, BonusType.SCIENCE_PER_TURN)
print(f"Total science bonus: +{science['total']}")

# Show sources
for source_type, source_name, value in science['sources']:
    print(f"  +{value} from {source_type}: {source_name}")

# Get all active bonuses
all_bonuses = engine.get_all_active_bonuses(game)
print(engine.format_bonus_summary(game))
```

## API Integration

The dashboard API (`/api/dashboard`) automatically includes bonus data:

```json
{
  "active_bonuses": {
    "science_per_turn": {
      "total": 5,
      "sources": [
        {"type": "character", "name": "Scholar Name", "value": 5}
      ]
    }
  }
}
```

## Implementation Notes

### Phase 3 (Current)
- ✅ Bonus definitions centralized
- ✅ BonusEngine aggregates from all sources
- ✅ world_turns_engine.py uses BonusEngine
- ✅ Dashboard API exposes bonus data
- ✅ Parallel verification ensures equivalence

### Phase 4 (Future)
- Building construction system
- Technology tree with prerequisites
- Full migration away from hardcoded formulas

## Troubleshooting

### Bonuses not appearing?
1. Check that the bonus source exists (character role, building, etc.)
2. Verify bonus definition in `bonus_definitions.py`
3. Run `test_bonus_engine.py` to see detailed output
4. Check game state files in `context/` directory

### Mismatch warnings?
If you see "⚠ BONUS MISMATCH" in console:
1. Compare old vs new calculations
2. Check for edge cases in bonus logic
3. Verify BonusEngine correctly reads game state
4. Report issue with specific values

## TODO Phase 4: Implement building construction system
## TODO Phase 4: Add technology tree with prerequisites
## TODO Phase 4: Implement leader trait evolution

