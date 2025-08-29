# Position-Weighted Opposing Teams Penalty System

## Overview
The FPL optimizer now uses a sophisticated position-weighted penalty system that applies different penalties based on the positional combinations of opposing players. This more accurately reflects the real-world impact of selecting players from teams playing against each other.

## Refined Penalty Matrix

| Position Combination | Penalty Multiplier | Reasoning |
|---------------------|-------------------|-----------|
| **Goalkeeper vs Defender** | 1.5x | Moderate - similar to defender vs defender dynamics |
| **Goalkeeper vs Midfielder** | 1.5x | Moderate - similar to defender vs midfielder dynamics |
| **Goalkeeper vs Forward** | 2.5x | **Highest penalty** - Direct opposition (GK vs striker) |
| **Defender vs Defender** | 0.5x | **Lowest penalty** - Both defending, minimal conflict |
| **Defender vs Midfielder** | 1.5x | Moderate opposition - some conflict of interest |
| **Defender vs Forward** | 2.5x | **High penalty** - Classic defense vs attack opposition |
| **Midfielder vs Midfielder** | 1.0x | Standard penalty - neutral/balanced opposition |
| **Midfielder vs Forward** | 1.0x | Standard penalty - moderate opposition |
| **Forward vs Forward** | 0.5x | **Low penalty** - Both attacking, minimal conflict |

### Removed Combinations
- **Goalkeeper vs Goalkeeper**: Removed as redundant - only one can get a clean sheet anyway

### Key Design Principles
1. **Direct Opposition = Higher Penalties**: Defender vs Forward, GK vs Forward
2. **Same Role = Lower Penalties**: Defender vs Defender, Forward vs Forward  
3. **Mixed Roles = Moderate Penalties**: Midfielder combinations, GK vs Defender/Midfielder

## Implementation

### Base Penalty
- Set a base penalty value (e.g., 1.0 or 2.0 points)
- Each position combination applies a multiplier to this base

### Examples with Base Penalty = 2.0
- **Striker vs Defender**: 2.0 × 2.5 = **5.0 points penalty**
- **Striker vs Striker**: 2.0 × 0.5 = **1.0 points penalty**
- **Midfielder vs Midfielder**: 2.0 × 1.0 = **2.0 points penalty**
- **Goalkeeper vs Forward**: 2.0 × 2.5 = **5.0 points penalty**

## Benefits

1. **More Realistic**: Reflects actual football dynamics
2. **Strategic Depth**: Allows for some opposing combinations when the penalty is low
3. **Flexible**: Can adjust base penalty to control overall aggressiveness
4. **Detailed Analysis**: Shows breakdown by position combination
5. **Bench Players Safe**: Penalties only apply to starting XI - bench players are not penalized

## Important Notes

### Bench Player Confirmation ✅
**The penalty system ONLY applies to players in the starting XI.** If one of the opposing players is on the bench, no penalty is applied. This is by design - bench players don't directly oppose each other during the match.

### Matrix Refinement
The matrix has been refined based on football logic:
- Removed redundant GK vs GK (only one can get clean sheet anyway)
- Simplified GK combinations to match similar role dynamics
- Focused on actual tactical opposition levels

## File Structure

The opposing teams penalty system is now consolidated into a single file:
- `squad_selection_model/opposing_teams.py` - Complete opposing teams penalty system

### Consolidated Functions
- `get_position_penalty_matrix()` - Position penalty definitions
- `get_penalty_for_positions()` - Individual position pair penalty lookup
- `add_opposing_teams_penalty_to_objective()` - Integration with optimization
- `analyze_opposing_pairs_in_squad()` - Final squad analysis
- `print_penalty_matrix()` - Utility for displaying current penalties

## Usage

```python
# In objective_function.py
from opposing_teams import add_opposing_teams_penalty_to_objective

# In optimiser.py  
from opposing_teams import analyze_opposing_pairs_in_squad

# Add penalty to optimization
opposing_penalty_terms = add_opposing_teams_penalty_to_objective(
    prob, df_players, vars, base_opposing_penalty=1.0
)

# Analyze final squad
analyze_opposing_pairs_in_squad(df_players, squad, base_penalty=1.0)
```

## Output Analysis
The system now provides detailed analysis showing:
- Number of opposing pairs by position combination
- Individual penalty for each pair
- Total penalty applied
- Average penalty per pair

This gives you full visibility into how the penalty system is affecting your team selection.
