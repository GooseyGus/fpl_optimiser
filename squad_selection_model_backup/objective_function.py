# objective_function.py
# Function to add the objective function to the optimization problem

from pulp import lpSum

def add_objective_function(
    prob,
    df_players,
    vars
):
    """
    Add objective function to maximize expected points with transfer penalties and captain bonus.
    """
    
    # Regular points from players who are starting (from various sources)
    regular_points = lpSum([
        df_players.loc[idx, 'expected_points'] * (
            vars['stay']['starting'].get(idx, 0) +
            vars['swap']['bench_to_starting'].get(idx, 0) +
            vars['in']['to_starting_free'].get(idx, 0)
        )
        for idx in df_players.index
    ])

    # Points from paid transfers in (minus 4 point hit)
    paid_transfer_points = lpSum([
        vars['in']['to_starting_paid'].get(idx, 0) * (df_players.loc[idx, 'expected_points'] - 4)
        for idx in df_players.index
    ])

    # Captain bonus
    captain_bonus = lpSum([
        df_players.loc[idx, 'expected_points'] * vars['captain'].get(idx, 0)
        for idx in df_players.index
    ])

    # Paid transfer to bench penalty (minus 4 points for transferring to bench)
    bench_transfer_penalty = lpSum([
        4 * vars['in']['to_bench_paid'].get(idx, 0)
        for idx in df_players.index
    ])

    prob += regular_points + paid_transfer_points + captain_bonus - bench_transfer_penalty, "Total_Expected_Points_With_Transfers_And_Captain"

    return prob