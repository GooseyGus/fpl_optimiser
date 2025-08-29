# objective_function.py
# Function to add the objective function to the optimization problem

from pulp import lpSum, LpVariable
from opposing_teams import add_opposing_teams_penalty_to_objective

def add_objective_function(prob, df_players, vars, penalty_points, base_opposing_penalty=1.0):
    """
    Objective: maximize expected points with transfer penalties, captain bonus, and position-weighted opposing teams penalty.

    """
    # Regular points from players who are starting (stay, swap from bench, free transfer in)
    regular_points = lpSum([
        df_players.loc[idx, 'expected_points'] * (
            vars['stay_starting'].get(idx, 0) +
            vars['bench_to_starting'].get(idx, 0) +
            vars['in_to_starting_free'].get(idx, 0)
        )
        for idx in df_players.index
    ])

    # Paid transfers into starting XI (expected points minus 4 hit)
    paid_transfer_points = lpSum([
        (df_players.loc[idx, 'expected_points'] - penalty_points) * vars['in_to_starting_paid'].get(idx, 0)
        for idx in df_players.index
    ])

    # Captain bonus (adds expected points again for the captain, i.e. double)
    captain_bonus = lpSum([
        df_players.loc[idx, 'expected_points'] * vars['captain'].get(idx, 0)
        for idx in df_players.index
    ])

    # Penalty for paid transfers into the bench (-penalty_points)
    bench_transfer_penalty = lpSum([
        penalty_points * vars['in_to_bench_paid'].get(idx, 0)
        for idx in df_players.index
    ])

    # Position-weighted opposing teams penalty (using consolidated module)
    opposing_penalty_terms = add_opposing_teams_penalty_to_objective(
        prob, df_players, vars, base_opposing_penalty
    )

    # Combine all components
    opposing_penalty = lpSum(opposing_penalty_terms) if opposing_penalty_terms else 0
    
    prob += (
        regular_points
        + paid_transfer_points
        + captain_bonus
        - bench_transfer_penalty
        - opposing_penalty
    ), "Total_Expected_Points_With_All_Penalties"

    return prob
