# opposing_teams_constraint.py
# Constraint to reduce expected points when selecting players from opposing teams

from pulp import lpSum, LpVariable

def add_opposing_teams_constraint(prob, df_players, vars, point_reduction=0.5, enable_constraint=True):
    """
    Add constraint that reduces expected points when selecting players from teams 
    playing against each other in the same gameweek.
    
    Parameters:
    - prob: The optimization problem
    - df_players: DataFrame with player data including opponent information
    - vars: Decision variables dictionary
    - point_reduction: Points to reduce for each opposing player pair (default 0.5)
    - enable_constraint: Whether to apply this constraint (default True)
    
    The constraint works by:
    1. Identifying all possible pairs of players from opposing teams
    2. Creating binary variables for when both players are selected
    3. Reducing the objective function by point_reduction for each such pair
    """
    
    if not enable_constraint:
        print("Opposing teams constraint disabled")
        return prob
    
    print(f"Adding opposing teams constraint (reduction: {point_reduction} pts per pair)")
    
    # Get all valid player indices
    player_indices = df_players.index.tolist()
    
    # Create variables to track opposing player pairs
    opposing_pairs = {}
    pair_count = 0
    
    # Find all pairs of players from opposing teams
    for i in player_indices:
        for j in player_indices:
            if i >= j:  # Avoid duplicate pairs and self-pairs
                continue
                
            player_i = df_players.loc[i]
            player_j = df_players.loc[j]
            
            # Check if these players are from opposing teams
            if (player_i['opponent_id'] == player_j['team_id'] and 
                player_j['opponent_id'] == player_i['team_id'] and
                player_i['opponent'] != 'No fixture'):
                
                # Create binary variable for this opposing pair
                pair_var = LpVariable(f"opposing_pair_{i}_{j}", cat='Binary')
                opposing_pairs[(i, j)] = pair_var
                pair_count += 1
                
                # Add constraints to link the pair variable to individual selections
                # The pair is active only if both players are selected in starting XI
                
                # Get all ways a player can be in starting XI
                player_i_in_starting = (
                    vars['stay_starting'].get(i, 0) +
                    vars['bench_to_starting'].get(i, 0) +
                    vars['in_to_starting_free'].get(i, 0) +
                    vars['in_to_starting_paid'].get(i, 0)
                )
                
                player_j_in_starting = (
                    vars['stay_starting'].get(j, 0) +
                    vars['bench_to_starting'].get(j, 0) +
                    vars['in_to_starting_free'].get(j, 0) +
                    vars['in_to_starting_paid'].get(j, 0)
                )
                
                # Pair variable constraints
                # pair_var <= player_i_in_starting
                prob += pair_var <= player_i_in_starting, f"opposing_pair_constraint_i_{i}_{j}"
                
                # pair_var <= player_j_in_starting  
                prob += pair_var <= player_j_in_starting, f"opposing_pair_constraint_j_{i}_{j}"
                
                # pair_var >= player_i_in_starting + player_j_in_starting - 1
                # This ensures pair_var = 1 only when both players are selected
                prob += pair_var >= player_i_in_starting + player_j_in_starting - 1, f"opposing_pair_constraint_both_{i}_{j}"
    
    print(f"  Found {pair_count} potential opposing player pairs")
    
    # Add penalty to objective function
    if opposing_pairs:
        opposing_penalty = lpSum([point_reduction * pair_var for pair_var in opposing_pairs.values()])
        
        # Store the penalty for use in objective function
        # We'll subtract this from the total points
        if not hasattr(prob, '_opposing_penalty'):
            prob._opposing_penalty = opposing_penalty
        
        print(f"  Opposing teams penalty component added to objective")
    
    return prob

def get_opposing_teams_penalty(prob):
    """
    Get the opposing teams penalty component for use in objective function
    """
    return getattr(prob, '_opposing_penalty', 0)

def print_opposing_teams_analysis(df_players, squad):
    """
    Print analysis of opposing teams in the selected squad
    """
    print("\n" + "="*60)
    print("OPPOSING TEAMS ANALYSIS")
    print("="*60)
    
    if squad['starting_df'].empty:
        print("No starting XI data available")
        return
    
    starting_players = squad['starting_df']
    opposing_pairs = []
    
    # Check for opposing players in starting XI
    for i, player_i in starting_players.iterrows():
        for j, player_j in starting_players.iterrows():
            if i >= j:
                continue
                
            if (player_i.get('opponent_id') == player_j.get('team_id') and 
                player_j.get('opponent_id') == player_i.get('team_id') and
                player_i.get('opponent') != 'No fixture'):
                
                opposing_pairs.append((player_i, player_j))
    
    if opposing_pairs:
        print(f"⚠️  WARNING: {len(opposing_pairs)} opposing player pairs in your starting XI:")
        for player_i, player_j in opposing_pairs:
            print(f"  • {player_i['name']} ({player_i['team']}) vs {player_j['name']} ({player_j['team']})")
            print(f"    Match: {player_i['team']} vs {player_i['opponent']}")
        
        total_penalty = len(opposing_pairs) * 0.5  # Assuming default 0.5 reduction
        print(f"\n  Estimated points impact: -{total_penalty:.1f} points")
    else:
        print("✅ No opposing player pairs found in starting XI")
    
    print("="*60)
