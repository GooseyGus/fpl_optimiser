from pulp import lpSum

def add_equal_flow_constraints(prob, vars, df_players):
    """
    Ensure that "in" and "out" flows are balanced for each transfer type.
    Also balances starting <-> bench swaps.
    """
    # 1. Starting <-> Bench swaps
    prob += lpSum([vars['starting_to_bench'].get(idx, 0) for idx in df_players.index]) == \
            lpSum([vars['bench_to_starting'].get(idx, 0) for idx in df_players.index]), "Flow_Swap_Start_Bench"

    # 2. In free to starting == Out free from starting
    prob += lpSum([vars['in_to_starting_free'].get(idx, 0) for idx in df_players.index]) == \
            lpSum([vars['out_starting_free'].get(idx, 0) for idx in df_players.index]), "Flow_InStartFree_OutStartFree"

    # 3. In paid to starting == Out paid from starting
    prob += lpSum([vars['in_to_starting_paid'].get(idx, 0) for idx in df_players.index]) == \
            lpSum([vars['out_starting_paid'].get(idx, 0) for idx in df_players.index]), "Flow_InStartPaid_OutStartPaid"

    # 4. In free to bench == Out free from bench
    prob += lpSum([vars['in_to_bench_free'].get(idx, 0) for idx in df_players.index]) == \
            lpSum([vars['out_bench_free'].get(idx, 0) for idx in df_players.index]), "Flow_InBenchFree_OutBenchFree"

    # 5. In paid to bench == Out paid from bench
    prob += lpSum([vars['in_to_bench_paid'].get(idx, 0) for idx in df_players.index]) == \
            lpSum([vars['out_bench_paid'].get(idx, 0) for idx in df_players.index]), "Flow_InBenchPaid_OutBenchPaid"

    return prob
