# constraints/size_constraints.py
from pulp import lpSum

def add_squad_size_constraints(prob, vars, df_players):
    """
    Add squad size constraints only - 11 starting, 4 bench
    """
    # Squad size constraints
    starting_xi = lpSum([
        vars['stay_starting'].get(idx, 0) +
        vars['in_to_starting_free'].get(idx, 0) +
        vars['in_to_starting_paid'].get(idx, 0) +
        vars['bench_to_starting'].get(idx, 0)
        for idx in df_players.index
    ])

    prob += starting_xi == 11, "Starting_XI"
    
    
    bench_players = lpSum([
        vars['stay_bench'].get(idx, 0) +
        vars['in_to_bench_free'].get(idx, 0) +
        vars['in_to_bench_paid'].get(idx, 0) +
        vars['starting_to_bench'].get(idx, 0)
        for idx in df_players.index
    ])

    prob += bench_players == 4, "Bench_Size"


    for idx in df_players.index:
        prob += lpSum([
            vars['stay_starting'].get(idx, 0),
            vars['stay_bench'].get(idx, 0),
            vars['starting_to_bench'].get(idx, 0),
            vars['bench_to_starting'].get(idx, 0),
            vars['out_starting_free'].get(idx, 0),
            vars['out_starting_paid'].get(idx, 0),
            vars['out_bench_free'].get(idx, 0),
            vars['out_bench_paid'].get(idx, 0),
            vars['in_to_starting_free'].get(idx, 0),
            vars['in_to_starting_paid'].get(idx, 0),
            vars['in_to_bench_free'].get(idx, 0),
            vars['in_to_bench_paid'].get(idx, 0)
        ]) <= 1, f"OneDecisionPerPlayer_{idx}"
        
    return prob