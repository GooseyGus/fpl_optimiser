# captain_constraints.py
# Constraints for captain selection

from pulp import lpSum

def add_captain_constraints(prob, vars, df_players):
    """
    Add constraints for captain.
    
    Rules:
    - Exactly one captain
    - Captain must be in starting XI
    """
    # Exactly one captain
    prob += lpSum([vars['captain'].get(idx, 0) for idx in df_players.index]) == 1, "One_Captain"

    # Captain must be in starting XI
    for idx in df_players.index:
        starting_sum = (
            vars['stay_starting'].get(idx, 0) +
            vars['bench_to_starting'].get(idx, 0) +
            vars['in_to_starting_free'].get(idx, 0) +
            vars['in_to_starting_paid'].get(idx, 0)
        )
        prob += vars['captain'].get(idx, 0) <= starting_sum, f"Captain_{idx}_Must_Start"

    return prob
