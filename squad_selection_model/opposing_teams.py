# opposing_teams.py
# Consolidated opposing teams penalty system for FPL optimization

from pulp import lpSum, LpVariable

# ============================================================================
# POSITION PENALTY MATRIX
# ============================================================================

def get_position_penalty_matrix():
    """
    Get the position penalty matrix for opposing team combinations.
    
    Returns:
        dict: Position combination penalty multipliers
    """
    return {
        # GK vs GK removed - redundant (only one can get clean sheet anyway)
        ('Defender', 'Goalkeeper'): 1.5,      # Moderate - like defender vs defender impact
        ('Goalkeeper', 'Midfielder'): 1.5,    # Moderate - like defender vs midfielder impact  
        ('Forward', 'Goalkeeper'): 2.5,       # High penalty - direct striker vs GK opposition
        ('Defender', 'Defender'): 0.5,        # Low penalty - both defending, minimal conflict
        ('Defender', 'Midfielder'): 1.5,      # Moderate penalty - some opposition
        ('Defender', 'Forward'): 2.5,         # High penalty - classic defense vs attack
        ('Midfielder', 'Midfielder'): 1.0,    # Standard penalty - neutral/balanced
        ('Forward', 'Midfielder'): 1.0,       # Standard penalty - moderate opposition
        ('Forward', 'Forward'): 0.5,          # Low penalty - both attacking, minimal conflict
    }

def get_penalty_for_positions(pos_i, pos_j):
    """
    Get penalty multiplier for a specific position combination.
    
    Args:
        pos_i: Position of first player
        pos_j: Position of second player
        
    Returns:
        float: Penalty multiplier, or None if combination should be skipped
    """
    # Create sorted position pair for consistent lookup
    pos_pair = tuple(sorted([pos_i, pos_j]))
    
    # Skip GK vs GK combinations (redundant - only one can get clean sheet)
    if pos_pair == ('Goalkeeper', 'Goalkeeper'):
        return None
    
    # Get penalty from matrix
    matrix = get_position_penalty_matrix()
    return matrix.get(pos_pair, 1.0)  # Default to 1.0 if not found

# ============================================================================
# OBJECTIVE FUNCTION INTEGRATION
# ============================================================================

def add_opposing_teams_penalty_to_objective(prob, df_players, vars, base_opposing_penalty=1.0):
    """
    Add position-weighted opposing teams penalty to the objective function.
    
    This is the main function used in objective_function.py
    
    Args:
        prob: The optimization problem
        df_players: DataFrame with player data including opponent information
        vars: Decision variables dictionary
        base_opposing_penalty: Base penalty value (multiplied by position weights)
        
    Returns:
        list: Penalty terms to subtract from objective function
    """
    opposing_penalty_terms = []
    
    if base_opposing_penalty <= 0:
        return opposing_penalty_terms
    
    print(f"Adding position-weighted opposing teams penalty (base: {base_opposing_penalty} pts)")
    
    player_indices = df_players.index.tolist()
    pair_count = 0
    penalty_breakdown = {}  # Track penalties by position combination
    
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
                
                # Get positions
                pos_i = player_i['position']
                pos_j = player_j['position']
                
                # Get penalty multiplier using centralized function
                penalty_multiplier = get_penalty_for_positions(pos_i, pos_j)
                
                # Skip if this combination should be ignored (e.g., GK vs GK)
                if penalty_multiplier is None:
                    continue
                
                actual_penalty = base_opposing_penalty * penalty_multiplier
                
                # Track penalty breakdown
                pos_pair = tuple(sorted([pos_i, pos_j]))
                if pos_pair not in penalty_breakdown:
                    penalty_breakdown[pos_pair] = {'count': 0, 'total_penalty': 0}
                penalty_breakdown[pos_pair]['count'] += 1
                penalty_breakdown[pos_pair]['total_penalty'] += actual_penalty
                
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
                
                # Add position-weighted penalty term
                opposing_penalty_terms.append(actual_penalty * pair_indicator)
                pair_count += 1
    
    print(f"  Found {pair_count} potential opposing pairs")
    
    # Print penalty breakdown by position combination
    if penalty_breakdown:
        print("  Position combination penalties:")
        for pos_pair, data in penalty_breakdown.items():
            avg_penalty = data['total_penalty'] / data['count']
            print(f"    {pos_pair[0]} vs {pos_pair[1]}: {data['count']} pairs, {avg_penalty:.1f} pts each")
    
    return opposing_penalty_terms

# ============================================================================
# ANALYSIS AND REPORTING
# ============================================================================

def analyze_opposing_pairs_in_squad(df_players, squad, base_penalty=1.0):
    """
    Analyze opposing pairs in the final squad selection with position-weighted penalties
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
                
                # Get positions and calculate position-weighted penalty using centralized function
                pos_i = player_i['position']
                pos_j = player_j['position']
                
                penalty_multiplier = get_penalty_for_positions(pos_i, pos_j)
                
                # Skip if this combination should be ignored (e.g., GK vs GK)
                if penalty_multiplier is None:
                    continue
                    
                actual_penalty = base_penalty * penalty_multiplier
                pos_pair = tuple(sorted([pos_i, pos_j]))
                
                opposing_pairs.append((player_i, player_j, pos_pair, actual_penalty))
    
    print("\n" + "="*60)
    print("POSITION-WEIGHTED OPPOSING TEAMS ANALYSIS")
    print("="*60)
    
    if opposing_pairs:
        print(f"⚠️  {len(opposing_pairs)} opposing player pairs in your starting XI:")
        total_penalty = 0
        
        # Group by position combination for better display
        position_groups = {}
        for player_i, player_j, pos_pair, penalty in opposing_pairs:
            if pos_pair not in position_groups:
                position_groups[pos_pair] = []
            position_groups[pos_pair].append((player_i, player_j, penalty))
            total_penalty += penalty
        
        # Display by position combination
        for pos_pair, pairs in position_groups.items():
            penalty_multiplier = get_penalty_for_positions(pos_pair[0], pos_pair[1])
            if penalty_multiplier is None:
                penalty_multiplier = 0  # Shouldn't happen but safe fallback
            print(f"\n📍 {pos_pair[0]} vs {pos_pair[1]} (penalty: {penalty_multiplier}x base = {base_penalty * penalty_multiplier:.1f} pts each):")
            
            for player_i, player_j, penalty in pairs:
                print(f"  • {player_i['name']} ({player_i['team']}) vs {player_j['name']} ({player_j['team']})")
                print(f"    Match: {player_i['team']} vs {player_i['opponent']} | Penalty: -{penalty:.1f} pts")
        
        print(f"\n💰 Total position-weighted penalty: -{total_penalty:.1f} points")
        print(f"📊 Average penalty per pair: {total_penalty/len(opposing_pairs):.1f} points")
    else:
        print("✅ No opposing player pairs found in starting XI")
        print("💰 No penalty applied")
    
    print("="*60)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_penalty_matrix():
    """
    Print the current penalty matrix for reference.
    """
    matrix = get_position_penalty_matrix()
    
    print("Position Penalty Matrix:")
    print("=" * 50)
    for pos_pair, multiplier in sorted(matrix.items()):
        print(f"{pos_pair[0]} vs {pos_pair[1]}: {multiplier}x")
    print("\nSpecial Rules:")
    print("- Goalkeeper vs Goalkeeper: Skipped (redundant)")
    print("- Penalties only apply to starting XI (bench players excluded)")
    print("=" * 50)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("FPL Opposing Teams Penalty System")
    print("=" * 40)
    print_penalty_matrix()
    print("\nThis module provides position-weighted penalties for opposing team combinations.")
    print("Use add_opposing_teams_penalty_to_objective() in your optimization.")
