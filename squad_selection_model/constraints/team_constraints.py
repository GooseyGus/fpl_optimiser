# team_constraints.py: adds the constraint that the team must have no more than 3 players from the same team
from pulp import lpSum


def add_team_constraints(prob, vars, df_players):
    """
    Ensure no more than 3 players from the same team are selected.
    
    Rules:
    - For each team, the sum of players in the squad must be <= 3
    """
    
    # Group players by their team
    teams = df_players['team'].unique()
    
    for team in teams:
        team_indices = df_players[df_players['team'] == team].index
        
        # Add constraint for this team
        prob += (
            lpSum(vars['stay_starting'][idx] + 
                  vars['stay_bench'][idx] +
                vars['in_to_starting_free'][idx] + 
                vars['in_to_starting_paid'][idx] +
                   vars['in_to_bench_free'][idx] + 
                   vars['in_to_bench_paid'][idx] +
                     vars['starting_to_bench'][idx] +
                     vars['bench_to_starting'][idx] 
                   for idx in team_indices) <= 3,
            f"Max_3_Players_From_Team_{team}"
        )
    
    return prob