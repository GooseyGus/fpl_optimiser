import pulp
def extract_decision_variable_results(vars):
    """Extract decision variable results from optimization"""
    results = {}
    
    for var_type, player_vars in vars.items():
        active_ids = [
            idx for idx, var in player_vars.items()
            if var.value() is not None and var.value() > 0
        ]
        results[var_type] = active_ids
    
    return results

def create_transfer_type_mapping(decision_results):

    index_to_transfer_type = {}
    
    # Map each index to its transfer type
    transfer_type_mappings = {
        'stay_starting': 'Stay (Starting)',
        'stay_bench': 'Stay (Bench)',
        'in_to_starting_free': 'Transfer In (Free)',
        'in_to_starting_paid': 'Transfer In (Paid)',
        'in_to_bench_free': 'Transfer In to Bench (Free)',
        'in_to_bench_paid': 'Transfer In to Bench (Paid)',
        'bench_to_starting': 'Sub: Bench to Starting',
        'starting_to_bench': 'Sub: Starting to Bench',
        'out_starting_free': 'Transfer Out (Free)',
        'out_starting_paid': 'Transfer Out (Paid)',
        'out_bench_free': 'Transfer Out from Bench (Free)',
        'out_bench_paid': 'Transfer Out from Bench (Paid)'
    }
    
    for var_type, transfer_label in transfer_type_mappings.items():
        indices = decision_results.get(var_type, [])
        for idx in indices:
            index_to_transfer_type[idx] = transfer_label
    
    return index_to_transfer_type

def create_output_dataframes(decision_results, df_players, prob):
    # Create transfer type mapping
    transfer_type_map = create_transfer_type_mapping(decision_results)
    
    # Get starting player indices
    starting_indices = (
        decision_results.get('stay_starting', []) +
        decision_results.get('in_to_starting_free', []) +
        decision_results.get('in_to_starting_paid', []) +
        decision_results.get('bench_to_starting', [])
    )
    
    # Get bench player indices
    bench_indices = (
        decision_results.get('stay_bench', []) +
        decision_results.get('in_to_bench_free', []) +
        decision_results.get('in_to_bench_paid', []) +
        decision_results.get('starting_to_bench', [])
    )

    # get out indicies
    out_indices = (
        decision_results.get('out_starting_free', []) +
        decision_results.get('out_starting_paid', []) +
        decision_results.get('out_bench_free', []) +
        decision_results.get('out_bench_paid', [])
    )
    
    # Create dataframes
    starting_df = df_players.iloc[starting_indices].copy()
    bench_df = df_players.iloc[bench_indices].copy()
    out_df = df_players.iloc[out_indices].copy() 
    
    # Add transfer type to dataframes
    starting_df['transfer_type'] = starting_df.index.map(transfer_type_map)
    bench_df['transfer_type'] = bench_df.index.map(transfer_type_map)
    out_df['transfer_type'] = out_df.index.map(transfer_type_map)

    starting_df['role'] = 'Starting XI'
    bench_df['role'] = 'Bench'
    out_df['role'] = 'Out'
    
    # Get gameweek from df_players
    gameweek = df_players['gameweek'].iloc[0] if 'gameweek' in df_players.columns else None
    
    # Get captain
    captain_idx = decision_results.get('captain', [None])[0]
    
    # Calculate formation from starting lineup
    formation = calculate_formation(starting_df)
    
    # Get vice-captain (highest xP starter from different team than captain)
    vice_captain_idx = select_vice_captain(starting_df, captain_idx, df_players)
    
    # Add captain and vice-captain flags to dataframes
    starting_df['is_captain'] = starting_df.index == captain_idx
    starting_df['is_vice_captain'] = starting_df.index == vice_captain_idx
    bench_df['is_captain'] = False  # Captains should never be on bench
    bench_df['is_vice_captain'] = False  # Vice-captains should never be on bench
    
    # Add bench order (1-4)
    bench_df['bench_order'] = range(1, len(bench_df) + 1)
    
    # Get optimization status
    optimization_status = pulp.LpStatus[prob.status] if prob else "Unknown"
    
    # Calculate total cost
    total_cost = calculate_total_cost(starting_df, bench_df)
    
    return (starting_df, bench_df, out_df,  captain_idx, vice_captain_idx, 
            formation, gameweek, optimization_status, total_cost)

def calculate_formation(starting_df):

    position_counts = starting_df['position'].value_counts()
    
    # Get counts for each position
    goalkeepers = position_counts.get('Goalkeeper', 0)
    defenders = position_counts.get('Defender', 0)
    midfielders = position_counts.get('Midfielder', 0)
    forwards = position_counts.get('Forward', 0)
    
    # Create formation dictionary with both formats
    formation = {
        'string': f"{defenders}-{midfielders}-{forwards}",
        'Goalkeeper': goalkeepers,
        'Defender': defenders,
        'Midfielder': midfielders,
        'Forward': forwards,
        # Alternative keys if your code uses different naming
        'GKP': goalkeepers,
        'DEF': defenders,
        'MID': midfielders,
        'FWD': forwards
    }
    
    return formation

def select_vice_captain(starting_df, captain_idx, df_players):
    if captain_idx is None:
        return None
    
    # Get captain's team
    captain_team = df_players.iloc[captain_idx]['team']
    
    # Filter starting players from different teams
    eligible_vc = starting_df[starting_df['team'] != captain_team]
    
    if eligible_vc.empty:
        # If all starters are from same team, pick highest xP non-captain
        eligible_vc = starting_df[starting_df.index != captain_idx]
    
    # Sort by expected points (xP) and get the highest
    if not eligible_vc.empty:
        vice_captain_idx = eligible_vc.nlargest(1, 'expected_points').index[0]
        return vice_captain_idx
    
    return None

def calculate_total_cost(starting_df, bench_df):

    # Check for different possible column names for cost
    cost_columns = ['now_cost', 'price', 'cost', 'value']
    
    starting_cost = 0
    bench_cost = 0
    
    for col in cost_columns:
        if col in starting_df.columns:
            starting_cost = starting_df[col].sum()
            break
    
    for col in cost_columns:
        if col in bench_df.columns:
            bench_cost = bench_df[col].sum()
            break
    
    return starting_cost + bench_cost

# Main usage example
def process_optimization_results(vars, df_players, prob):
    
    # Step 1: Extract decision variable results using your preferred method
    decision_results = extract_decision_variable_results(vars)

    # Create output dataframes and variables
    (starting_df, bench_df, out_df, captain_idx, vice_captain_idx, 
     formation, gameweek, optimization_status, total_cost) = create_output_dataframes(
        decision_results, df_players, prob
    )
        
    # Return all outputs as a dictionary for easy access
    return {
        'starting_df': starting_df,
        'bench_df': bench_df,
        'out_df': out_df,
        'captain_idx': captain_idx,
        'vice_captain_idx': vice_captain_idx,
        'formation': formation,
        'gameweek': gameweek,
        'optimization_status': optimization_status,
        'total_cost': total_cost,
        'decision_results': decision_results  # Include raw results for reference
    }

