import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# squad_selection_model/optimiser.py

import pandas as pd
from pulp import LpProblem, LpMaximize, PULP_CBC_CMD
from helper_functions import *
from decision_variables import create_decision_variables
from objective_function import add_objective_function
from squad_creation import create_squad
from output_window import display_in_window
from constraints import *
from squad_selection_model.team_class import Team

# Initialize team
my_team = Team(team_id=2562804, budget=0, free_transfers=1)

# Load player data for two gameweeks
df_players_gw1 = pd.read_csv('data/player_data/fpl_players_gw_1.csv')
df_players_gw2 = pd.read_csv('data/player_data/fpl_players_gw_2.csv')

# Create optimization problem
prob = LpProblem("FPL_Transfer_Optimization", LpMaximize)

# Create decision variables
vars = create_decision_variables(df_players_gw2)

# Add objective function
prob = add_objective_function(prob, df_players_gw2, vars)

# Add constraints
prob = add_squad_size_constraints(prob, vars, df_players_gw2)
prob = add_player_status_constraints(prob, vars, df_players_gw2, my_team)
prob = add_positional_constraints(prob, vars, df_players_gw2)
prob = add_free_transfer_limit_constraint(prob, vars, df_players_gw2, my_team)
prob = add_transfer_balance_constraints(prob, vars, df_players_gw2, my_team)
prob = add_team_constraints(prob, vars, df_players_gw2)
prob = add_captain_constraints(prob, vars, df_players_gw2)
prob = add_availability_constraints(prob, vars, df_players_gw2, my_team)
#prob = add_budget_constraint(prob, vars, df_players_gw1, df_players_gw2, current_team, initial_bank=0.0)
#prob = add_transfer_balance_constraints(prob, vars, df_players_gw2, current_team)
#prob = add_free_transfer_limit_constraint(prob, vars, df_players_gw2, 1)


# Solve the problem
prob.solve(PULP_CBC_CMD(msg=False))

# Create squad with post-processing
squad = create_squad(prob, df_players_gw2, vars)

# Display results 
display_in_window(prob, squad, vars, df_players_gw2, my_team)