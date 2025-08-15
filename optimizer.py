# optimizer.py
# Main script to run the FPL team selection optimization

import pandas as pd
from pulp import LpProblem, LpMaximize, PULP_CBC_CMD
from objective_function import *
from decision_variables import *
from constraints import *
from squad_creation import create_squad
from output_window import display_in_window

# Load data
df_players = pd.read_csv('data/fpl_players_gw_1.csv')

# Create optimization problem
prob = LpProblem("FPL_Team_Selection", LpMaximize)

# Create decision variables
starting_vars, bench_vars, captain_vars = create_decision_variables(df_players)

# Add objective function
prob = add_objective_function(prob, df_players, starting_vars, captain_vars)

# Add constraints
prob = add_squad_size_constraints(prob, starting_vars, bench_vars, df_players)
prob = add_positional_constraints(prob, starting_vars, bench_vars, df_players)
prob = add_team_constraints(prob, starting_vars, bench_vars, df_players)
prob = add_budget_constraint(prob, starting_vars, bench_vars, df_players)
prob = add_captain_constraints(prob, starting_vars, captain_vars, df_players)
prob = add_availability_constraints(prob, starting_vars, bench_vars, df_players)

# Solve the problem
prob.solve(PULP_CBC_CMD(msg=False))

# Create squad with post-processing
squad = create_squad(prob, df_players, starting_vars, bench_vars, captain_vars)

# Display results
display_in_window(prob, squad)