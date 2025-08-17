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

# Initialize team
my_team = Team(team_id=2562804, budget=0, free_transfers=1)

# Load player data for two gameweeks
df_players_gw1 = pd.read_csv('data/player_data/fpl_players_gw_1.csv')
df_players_gw2 = pd.read_csv('data/player_data/fpl_players_gw_2.csv')
#injure Matthews, id 255
df_players_gw2.loc[df_players_gw2['id'] == 255, 'status'] = 'i'


# Create optimization problem
prob = LpProblem("FPL_Transfer_Optimisation", LpMaximize)

# Create decision variables
vars = create_decision_variables(df_players_gw2)

# Add objective function
prob = add_objective_function(prob, df_players_gw2, vars)

# Add constraints
prob = add_squad_size_constraints(prob, vars, df_players_gw2)
prob = add_captain_constraints(prob, vars, df_players_gw2)
prob = add_equal_flow_constraints(prob, vars, df_players_gw2)
prob = add_status_constraints(prob, vars, df_players_gw2, my_team)
prob = add_positional_constraints(prob, vars, df_players_gw2)
prob = add_free_transfer_limit_constraint(prob, vars, df_players_gw2, my_team)
prob = add_availability_constraints(prob, vars, df_players_gw2, my_team)
prob = add_budget_constraint(prob, vars, df_players_gw1, df_players_gw2, my_team.current_team)
prob = add_team_constraints(prob, vars, df_players_gw2)

# Solve the problem
prob.solve(PULP_CBC_CMD(msg=False))

# After solving, check the actual values
for idx in df_players_gw2.index:
    if vars['out_starting_paid'][idx].value() > 0:
        print(f"Sold: {df_players_gw2.loc[idx, 'name']} for £{df_players_gw2.loc[idx, 'price']}m (out_starting_paid)")
    if vars['out_bench_paid'][idx].value() > 0:
        print(f"Sold: {df_players_gw2.loc[idx, 'name']} from bench for £{df_players_gw2.loc[idx, 'price']}m (out_bench_paid)")
    if vars['in_to_starting_paid'][idx].value() > 0:
        print(f"Bought: {df_players_gw2.loc[idx, 'name']} for £{df_players_gw2.loc[idx, 'price']}m (in_to_starting_paid)")
    if vars['in_to_bench_paid'][idx].value() > 0:
        print(f"Bought: {df_players_gw2.loc[idx, 'name']} for £{df_players_gw2.loc[idx, 'price']}m (in_to_bench_paid)")
    if vars['in_to_starting_free'][idx].value() > 0:
        print(f"Bought: {df_players_gw2.loc[idx, 'name']} for £{df_players_gw2.loc[idx, 'price']}m (in_to_starting_free)")
    if vars['in_to_bench_free'][idx].value() > 0:
        print(f"Bought: {df_players_gw2.loc[idx, 'name']} for £{df_players_gw2.loc[idx, 'price']}m (in_to_bench_free)")
    if vars['out_starting_free'][idx].value() > 0:
        print(f"Sold: {df_players_gw2.loc[idx, 'name']} for £{df_players_gw2.loc[idx, 'price']}m (out_starting_free)")
    if vars['out_bench_free'][idx].value() > 0:
        print(f"Sold: {df_players_gw2.loc[idx, 'name']} from bench for £{df_players_gw2.loc[idx, 'price']}m (out_bench_free)")



print(f"Initial bank: £{0}m")

squad = process_optimization_results(vars, df_players_gw2, prob)

display_in_window(prob, squad, vars, df_players_gw2, my_team)