# captain_constraints.py
# Constraints for captain selection

from pulp import lpSum

def add_captain_constraints(prob, starting_vars, captain_vars, df_players):
    """
    Add constraints for captain
    
    Rules:
    - Exactly one captain
    - Captain must be in starting XI
    """
    # Exactly one captain
    prob += lpSum([captain_vars[idx] for idx in df_players.index]) == 1, "One_Captain"
    
    # Captain must be in starting XI
    for idx in df_players.index:
        prob += captain_vars[idx] <= starting_vars[idx], f"Captain_{idx}_Must_Start"
    
    return prob