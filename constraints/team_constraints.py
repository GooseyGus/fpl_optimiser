# team_constraints.py
# Constraint for maximum players per team

from pulp import lpSum

def add_team_constraints(prob, starting_vars, bench_vars, df_players, max_per_team=3):
    """
    Add constraint limiting players from the same team
    
    FPL Rule: Maximum 3 players from any single team in your squad
    """
    
    # Get all unique teams
    teams = df_players['team'].unique()
    
    # For each team, limit total players (starting + bench) to max_per_team
    for team in teams:
        team_indices = df_players[df_players['team'] == team].index
        prob += lpSum([starting_vars[idx] + bench_vars[idx] for idx in team_indices]) <= max_per_team, f"Max_{team.replace(' ', '_')}_players"
    
    return prob