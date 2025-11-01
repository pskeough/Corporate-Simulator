# Example: Adding a Building with Bonuses

## Goal
Add a "Granary" building that provides +10 food per turn.

## Steps

### 1. Define the building bonus
Edit `engines/bonus_definitions.py`:

```python
BUILDING_BONUSES = {
    'Granary': {
        'food_per_turn': 10,
        'description': 'Stores surplus food for lean times',
        'cost': {'wealth': 300, 'food': 100},
        'era_required': 'bronze_age'
    }
}
```

### 2. Add to infrastructure
Buildings are tracked in `game_state.technology['infrastructure']`. When constructed, append to this list:

```python
game_state.technology['infrastructure'].append('Granary')
```

### 3. BonusEngine handles the rest!

The BonusEngine automatically:
- Detects 'Granary' in infrastructure
- Looks up bonus in `BUILDING_BONUSES`
- Adds +10 to food_per_turn calculations

**No engine code modification needed!**

## Verification

Run `test_bonus_engine.py` to see the bonus appear:

```bash
python test_bonus_engine.py
```

Expected output:
```
Active Bonuses:
  food_per_turn: +10
    +10 from building: Granary
```

## Complete Example: Adding Multiple Buildings

```python
# In bonus_definitions.py
BUILDING_BONUSES = {
    'Granary': {
        'food_per_turn': 10,
        'description': 'Stores surplus food for lean times',
        'cost': {'wealth': 300, 'food': 100},
        'era_required': 'stone_age'
    },
    'Library': {
        'science_per_turn': 5,
        'description': 'Preserves knowledge and enables research',
        'cost': {'wealth': 500},
        'era_required': 'bronze_age'
    },
    'Market': {
        'wealth_per_turn': 8,
        'description': 'Facilitates trade and commerce',
        'cost': {'wealth': 400},
        'era_required': 'bronze_age'
    },
    'Temple': {
        'culture_per_turn': 3,
        'happiness': 5,
        'description': 'Spiritual center that uplifts the people',
        'cost': {'wealth': 350, 'food': 50},
        'era_required': 'stone_age'
    }
}
```

## Adding Building Construction (Phase 4)

To make buildings constructible in-game, you'll need:

1. **UI for building menu** - Show available buildings with costs
2. **Construction action** - Handler to build when player chooses
3. **Resource deduction** - Check and spend costs
4. **Infrastructure update** - Add to `technology['infrastructure']`

Example construction handler:

```python
@app.route('/api/construct_building', methods=['POST'])
def construct_building():
    data = request.get_json()
    building_name = data.get('building_name')

    # Get building definition
    from engines.bonus_definitions import BUILDING_BONUSES
    building = BUILDING_BONUSES.get(building_name)

    if not building:
        return jsonify({"error": "Unknown building"}), 400

    # Check resource costs
    from engines.resource_engine import check_resource_constraints
    can_afford, missing = check_resource_constraints(game, building['cost'])

    if not can_afford:
        return jsonify({"error": f"Insufficient resources: {missing}"}), 400

    # Deduct costs
    for resource, amount in building['cost'].items():
        game.civilization['resources'][resource] -= amount

    # Add to infrastructure
    game.technology['infrastructure'].append(building_name)

    # Save state
    game.save()

    return jsonify({
        "success": True,
        "building": building_name,
        "bonuses": {k: v for k, v in building.items() if k.endswith('_per_turn')}
    })
```

## Testing Your Building

1. Add building definition to `bonus_definitions.py`
2. Manually add to infrastructure for testing:
   ```python
   # In Python REPL or test script
   from game_state import GameState
   game = GameState()
   game.technology['infrastructure'].append('Granary')
   game.save()
   ```
3. Run bonus test: `python test_bonus_engine.py`
4. Check dashboard API: `/api/dashboard` should show active bonuses

## Advanced: Conditional Bonuses

For Phase 4+, you might want bonuses that depend on conditions:

```python
# Future enhancement
'Lighthouse': {
    'wealth_per_turn': 5,
    'description': 'Guides ships to safe harbor',
    'cost': {'wealth': 400},
    'era_required': 'bronze_age',
    'requires_terrain': 'coastal'  # Only works near water
}
```

This would require enhancing BonusEngine to check terrain conditions.

## Summary

Adding buildings is now **configuration, not code**:
1. ✅ Edit `bonus_definitions.py`
2. ✅ Add to infrastructure list
3. ✅ BonusEngine automatically applies bonuses
4. ❌ No need to modify calculation logic!

This is the power of the extensible bonus system! 🎯
