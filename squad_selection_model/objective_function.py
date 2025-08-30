# objective_function.py
# Function to add the objective function to the optimization problem

from pulp import lpSum, LpVariable
from opposing_teams import add_opposing_teams_penalty_to_objective
from fdr import add_fdr_penalty_to_objective

def add_objective_function(prob, df_players, vars, penalty_points, base_opposing_penalty=1.0, fdr_calculator=None, fdr_penalty_weight=0.5):
    """
    Objective: maximize expected points with transfer penalties, captain bonus, position-weighted opposing teams penalty, and FDR-based penalties.

    Args:
        prob: PuLP problem instance
        df_players: DataFrame with player data
        vars: Dictionary of decision variables
        penalty_points: Points penalty for paid transfers
        base_opposing_penalty: Base penalty for opposing teams
        fdr_calculator: FDR calculator instance (optional)
        fdr_penalty_weight: Weight for FDR penalties (default: 0.5)
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

    # FDR-based penalties/bonuses
    fdr_penalty_terms = []
    if fdr_calculator is not None:
        fdr_penalty_terms = add_fdr_penalty_to_objective(
            prob, df_players, vars, fdr_calculator, fdr_penalty_weight
        )

    # Combine all components
    opposing_penalty = lpSum(opposing_penalty_terms) if opposing_penalty_terms else 0
    fdr_bonus = lpSum(fdr_penalty_terms) if fdr_penalty_terms else 0
    
    prob += (
        regular_points
        + paid_transfer_points
        + captain_bonus
        - bench_transfer_penalty
        - opposing_penalty
        + fdr_bonus
    ), "Total_Expected_Points_With_All_Penalties"

    return prob
