import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd
from pulp import LpProblem, LpMaximize, PULP_CBC_CMD
from decision_variables import create_decision_variables
from objective_function import add_objective_function
from constraints import *
from squad_creator import *
from team_class import Team
from output_window import display_in_window
from fdr import CSVFDRCalculator

# Initialize team
my_team = Team(team_id=2562804, budget=0, free_transfers=1)

df_players = pd.read_csv('data/fpl_players_gw_5.csv')

# Initialize FDR calculator
fdr_calculator = CSVFDRCalculator()
print(f"📊 FDR Calculator initialized with {len(fdr_calculator.team_fdr_ratings)} teams")   

# Create optimization problem
prob = LpProblem("FPL_Transfer_Optimisation", LpMaximize)

# Create decision variables
vars = create_decision_variables(df_players)

# Add objective function with FDR penalties
prob = add_objective_function(
    prob, df_players, vars, 
    penalty_points=4, 
    base_opposing_penalty=0.5,
    fdr_calculator=fdr_calculator,
    fdr_penalty_weight=1.0  # Adjust this to control FDR impact
)

# Add constraints
prob = add_squad_size_constraints(prob, vars, df_players)
prob = add_captain_constraints(prob, vars, df_players)
prob = add_equal_flow_constraints(prob, vars, df_players)
prob = add_status_constraints(prob, vars, df_players, my_team)
prob = add_positional_constraints(prob, vars, df_players)
prob = add_free_transfer_limit_constraint(prob, vars, df_players, my_team)
prob = add_availability_constraints(prob, vars, df_players, my_team)
prob = add_budget_constraint(prob, vars, df_players, my_team.current_team)
prob = add_team_constraints(prob, vars, df_players)

# Example usage with custom parameters:
'''
prob = add_bench_selection_constraints(
    prob, vars, df_players,         
    min_minutes=0,           # Lower minutes requirement
    min_price=0,           # Minimum £4.0m
    max_price=100,           # Maximum £5.5m (tighter budget)
    min_expected_points=7.1,  # Lower points threshold
    max_expected_points=100,  # Avoid premium players
    min_ownership=0,        # No minimum ownership
    max_ownership=100,       # Avoid very popular players
    allow_injured=False,      # No injured players
    min_form=0             # Require some form
)
'''
# Solve the problem
prob.solve(PULP_CBC_CMD(msg=False))

# Print transfer summary
transfer_types = [
    ('out_starting_paid', 'Sold', ''),
    ('out_bench_paid', 'Sold', ' from bench'),
    ('in_to_starting_paid', 'Bought', ''),
    ('in_to_bench_paid', 'Bought', ''),
    ('in_to_starting_free', 'Bought', ''),
    ('in_to_bench_free', 'Bought', ''),
    ('out_starting_free', 'Sold', ''),
    ('out_bench_free', 'Sold', ' from bench')
]

for idx in df_players.index:
    for var_name, action, location in transfer_types:
        if vars[var_name][idx].value() > 0:
            player = df_players.loc[idx]
            print(f"{action}: {player['name']}{location} for £{player['price']}m ({var_name})")

print(f"Initial bank: £{0}m")

squad = process_optimization_results(vars, df_players, prob)

# Analyze opposing teams in final squad (using consolidated module)
from opposing_teams import analyze_opposing_pairs_in_squad
analyze_opposing_pairs_in_squad(df_players, squad, base_penalty=1.0)

# Analyze FDR impact in final squad
print("\n🎯 FDR ANALYSIS OF SELECTED SQUAD")
print("=" * 50)
starting_df = squad['starting_df']
total_fdr_bonus = 0

for idx, player in starting_df.iterrows():
    team_id = player['team_id']
    fdr_rating = fdr_calculator.team_fdr_ratings.get(team_id, 0)
    fdr_bonus = fdr_calculator.get_fdr_penalty_points(team_id, 1.0)
    total_fdr_bonus += fdr_bonus
    
    bonus_indicator = "💚" if fdr_bonus > 0 else "❤️" if fdr_bonus < 0 else "💛"
    print(f"{bonus_indicator} {player['name']} ({player['team']}): {fdr_rating:.1f} FDR ({fdr_bonus:+.1f})")

print(f"\n📊 Total FDR Bonus/Penalty: {total_fdr_bonus:+.1f} points")

if total_fdr_bonus > 0:
    print("✅ Squad benefits from easier fixtures!")
elif total_fdr_bonus < 0:
    print("⚠️  Squad faces difficult fixtures")
else:
    print("➡️  Squad has neutral fixture difficulty")

display_in_window(prob, squad, vars, df_players, my_team)