# availability_constraints.py
# Constraints to ensure only fully available players are selected

from pulp import lpSum

def add_availability_constraints(prob, starting_vars, bench_vars, df_players):
    """
    Ensure only fully available players can be selected
    
    Rules:
    - Player must have status 'a' (available)
    - No injured, suspended, or doubtful players
    """
    
    # Get indices of unavailable players
    unavailable_indices = df_players[(df_players['status'] != 'a')].index
    
    # Constraint: Unavailable players cannot be selected (starting or bench)
    for idx in unavailable_indices:
        prob += starting_vars[idx] + bench_vars[idx] == 0, f"Player_{idx}_Unavailable"
    
    return prob