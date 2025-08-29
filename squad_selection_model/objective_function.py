# objective_function.py
# Function to add the objective function to the optimization problem

from pulp import lpSum, LpVariable

def add_objective_function(prob, df_players, vars, penalty_points, opposing_teams_penalty=0.5):
    """
    Objective: maximize expected points with transfer penalties, captain bonus, and opposing teams penalty.
    
    Note: Expected points are already adjusted for opposing teams before optimization.
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

    # Opposing teams penalty
    opposing_penalty_terms = []
    if opposing_teams_penalty > 0:
        print(f"Adding opposing teams penalty: -{opposing_teams_penalty} pts per opposing pair")
        
        player_indices = df_players.index.tolist()
        pair_count = 0
        
        for i in player_indices:
            for j in player_indices:
                if i >= j:  # Avoid duplicate pairs
                    continue
                    
                player_i = df_players.loc[i]
                player_j = df_players.loc[j]
                
                # Check if these players are from opposing teams
                if (player_i.get('opponent_id') == player_j.get('team_id') and 
                    player_j.get('opponent_id') == player_i.get('team_id') and
                    player_i.get('opponent') != 'No fixture'):
                    
                    # Create binary indicator variable for this opposing pair
                    pair_indicator = LpVariable(f"opposing_pair_{i}_{j}", cat='Binary')
                    
                    # Calculate when each player is in starting XI
                    player_i_starting = (
                        vars['stay_starting'].get(i, 0) +
                        vars['bench_to_starting'].get(i, 0) +
                        vars['in_to_starting_free'].get(i, 0) +
                        vars['in_to_starting_paid'].get(i, 0)
                    )
                    
                    player_j_starting = (
                        vars['stay_starting'].get(j, 0) +
                        vars['bench_to_starting'].get(j, 0) +
                        vars['in_to_starting_free'].get(j, 0) +
                        vars['in_to_starting_paid'].get(j, 0)
                    )
                    
                    # Add constraints to link indicator to player selections
                    prob += pair_indicator <= player_i_starting, f"pair_constraint_i_{i}_{j}"
                    prob += pair_indicator <= player_j_starting, f"pair_constraint_j_{i}_{j}"
                    prob += pair_indicator >= player_i_starting + player_j_starting - 1, f"pair_constraint_both_{i}_{j}"
                    
                    # Add penalty term
                    opposing_penalty_terms.append(opposing_teams_penalty * pair_indicator)
                    pair_count += 1
        
        print(f"  Found {pair_count} potential opposing pairs")

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
