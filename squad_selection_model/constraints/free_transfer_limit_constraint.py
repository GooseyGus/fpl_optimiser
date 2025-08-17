from pulp import lpSum

def add_free_transfer_limit_constraint(prob, vars, df_players, my_team):
    """
    Limit the number of free transfers in the upcoming gameweek (flat 13-variable structure).
    """
    # Maximum free transfers you can use this week (FPL cap 5)
    max_free_transfers = min(my_team.free_transfers, 5)

    # Total free transfers IN this week
    free_transfers_in = lpSum([
        vars['in_to_starting_free'].get(idx, 0) +
        vars['in_to_bench_free'].get(idx, 0)
        for idx in df_players.index
    ])

    # Constraint: cannot exceed available free transfers
    prob += free_transfers_in <= max_free_transfers, f"Max_{max_free_transfers}_Free_Transfers"

    return prob
