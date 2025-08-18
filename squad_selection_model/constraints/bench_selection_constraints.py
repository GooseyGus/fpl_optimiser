# bench_selection_constraints.py: Only select players for the bench if they had at least 59 minutes in fpl_players_gw_2.csv

from pulp import LpProblem, LpVariable, lpSum, LpStatus, LpBinary
def add_bench_selection_constraints(prob, vars, df_players):
    """
    Add constraints to ensure that only players who played at least 59 minutes in the first gameweek
    can be selected for the bench.
    """
    # Create a binary variable for each player indicating if they are eligible for the bench
    bench_eligible = LpVariable.dicts("BenchEligible", df_players.index, cat=LpBinary)

    # Add constraints to ensure only players with at least 59 minutes can be on the bench
    for idx in df_players.index:
        prob += (bench_eligible[idx] <= (df_players.loc[idx, 'minutes'] >= 59)), f"BenchEligibility_{idx}"

    # Ensure that if a player is on the bench, they must be eligible
    for idx in df_players.index:
        prob += (vars['stay_bench'][idx] <= bench_eligible[idx]), f"StayBenchEligibility_{idx}"

    return prob