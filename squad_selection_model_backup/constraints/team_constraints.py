# team_constraints.py
# Constraint for maximum players per team
from helper_functions import get_squad_sum

from pulp import lpSum

def add_team_constraints(prob, vars, df_players, max_per_team=3):
    """
    Add constraint limiting players from the same team
    
    FPL Rule: Maximum 3 players from any single team in your squad
    """    
    teams = df_players['team'].unique()
    
    for team in teams:
        team_indices = df_players[df_players['team'] == team].index
        prob += lpSum([get_squad_sum(vars, idx) for idx in team_indices]) <= max_per_team, f"Max_{team.replace(' ', '_')}_players"
    
    return prob