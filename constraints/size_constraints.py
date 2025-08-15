# constrainst/size_constraints.py
# Constraints related to squad composition

from pulp import lpSum

def add_squad_size_constraints(prob, starting_vars, bench_vars, df_players):
    """
    Add all constraints related to squad selection:
    - 11 players in starting XI
    - 4 players on bench
    - Each player can only be in one role (starting, bench, or not selected)
    """
    
    # Exactly 11 players in starting XI
    prob += lpSum([starting_vars[idx] for idx in df_players.index]) == 11, "Starting_XI"
    
    # Exactly 4 players on bench
    prob += lpSum([bench_vars[idx] for idx in df_players.index]) == 4, "Bench_Size"
    
    # Each player can be either starting, on bench, or not selected (max 1)
    for idx in df_players.index:
        prob += starting_vars[idx] + bench_vars[idx] <= 1, f"Player_{idx}_Max_One_Role"
    
    return prob