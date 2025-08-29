# opposing_teams_penalty.py
# Simple penalty for selecting players from opposing teams using indicator variables

from pulp import lpSum, LpVariable

def add_opposing_teams_penalty_to_objective(prob, df_players, vars, penalty_per_pair=0.5):
    """
    Add penalty to objective function for each pair of opposing players selected.
    
    Uses binary indicator variables to detect when both opposing players are selected.
    """
    
    print(f"Adding opposing teams penalty: -{penalty_per_pair} pts per opposing pair")
    
    # Get all possible player pairs
    player_indices = df_players.index.tolist()
    penalty_terms = []
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
                # pair_indicator can only be 1 if both players are selected
                prob += pair_indicator <= player_i_starting, f"pair_constraint_i_{i}_{j}"
                prob += pair_indicator <= player_j_starting, f"pair_constraint_j_{i}_{j}"
                
                # Force pair_indicator to 1 when both players are selected
                prob += pair_indicator >= player_i_starting + player_j_starting - 1, f"pair_constraint_both_{i}_{j}"
                
                # Add penalty term
                penalty_terms.append(penalty_per_pair * pair_indicator)
                pair_count += 1
    
    print(f"  Found {pair_count} potential opposing pairs")
    
    # Add penalty to the existing objective
    if penalty_terms:
        total_penalty = lpSum(penalty_terms)
        
        # Get current objective and subtract penalty
        current_objective = prob.objective
        prob += current_objective - total_penalty
        
        print(f"  Opposing teams penalty added to objective function")
    
    return prob

def analyze_opposing_pairs_in_squad(df_players, squad):
    """
    Analyze opposing pairs in the final squad selection
    """
    if squad['starting_df'].empty:
        return
    
    starting_players = squad['starting_df']
    opposing_pairs = []
    
    for i, player_i in starting_players.iterrows():
        for j, player_j in starting_players.iterrows():
            if i >= j:
                continue
                
            if (player_i.get('opponent_id') == player_j.get('team_id') and 
                player_j.get('opponent_id') == player_i.get('team_id') and
                player_i.get('opponent') != 'No fixture'):
                
                opposing_pairs.append((player_i, player_j))
    
    print("\n" + "="*60)
    print("OPPOSING TEAMS ANALYSIS")
    print("="*60)
    
    if opposing_pairs:
        print(f"⚠️  {len(opposing_pairs)} opposing player pairs in your starting XI:")
        total_penalty = 0
        for player_i, player_j in opposing_pairs:
            print(f"  • {player_i['name']} ({player_i['team']}) vs {player_j['name']} ({player_j['team']})")
            print(f"    Match: {player_i['team']} vs {player_i['opponent']}")
            total_penalty += 0.5  # Assuming 0.5 penalty per pair
        
        print(f"\n💰 Total penalty applied: -{total_penalty:.1f} points")
    else:
        print("✅ No opposing player pairs found in starting XI")
        print("💰 No penalty applied")
    
    print("="*60)
