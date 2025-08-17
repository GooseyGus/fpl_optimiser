# constraints/size_constraints.py
from pulp import lpSum
from helper_functions import *

def add_squad_size_constraints(prob, vars, df_players):
    """
    Add squad size constraints only - 11 starting, 4 bench
    """
    # Squad size constraints
    prob += lpSum([get_starting_sum(vars, idx) for idx in df_players.index]) == 11, "Starting_XI"
    prob += lpSum([get_bench_sum(vars, idx) for idx in df_players.index]) == 4, "Bench_Size"

    # Each player can be either starting, on bench, or not selected (max 1)
    for idx in df_players.index:
        prob += get_squad_sum(vars, idx) <= 1, f"Player_{idx}_Max_One_Role"

    return prob