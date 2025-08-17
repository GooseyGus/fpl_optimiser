# squad_creation.py
# Extract and organize optimization results

import pandas as pd

def create_squad(prob, df_players, starting_vars, bench_vars, captain_vars):
    """
    Extract optimization results and post-process squad selections
    """
    # Extract solution
    starters = [idx for idx in df_players.index if starting_vars[idx].value() == 1]
    bench = [idx for idx in df_players.index if bench_vars[idx].value() == 1]
    captain_idx = [idx for idx in df_players.index if captain_vars[idx].value() == 1][0]
    
    # Post-process: Select vice-captain (highest xP starter from different team than captain)
    captain_team = df_players.loc[captain_idx, 'team']
    potential_vcs = [idx for idx in starters 
                     if idx != captain_idx and df_players.loc[idx, 'team'] != captain_team]
    vice_captain_idx = max(potential_vcs, key=lambda x: df_players.loc[x, 'expected_points'])
    
    # Create dataframes
    starting_df = df_players.loc[starters].copy()
    bench_df = df_players.loc[bench].copy()
    
    # Add roles
    starting_df['role'] = 'Starting XI'
    bench_df['role'] = 'Bench'
    
    # Mark captain and vice-captain
    starting_df['is_captain'] = starting_df.index == captain_idx
    starting_df['is_vice_captain'] = starting_df.index == vice_captain_idx
    
    # Sort starting XI by position and points
    position_order = {'Goalkeeper': 1, 'Defender': 2, 'Midfielder': 3, 'Forward': 4}
    starting_df['pos_order'] = starting_df['position'].map(position_order)
    starting_df = starting_df.sort_values(['pos_order', 'expected_points'], ascending=[True, False])
    
    # Order bench for automatic substitutions
    # Strategy: Order by expected points, but ensure GK is first if on bench
    bench_df['pos_order'] = bench_df['position'].map(position_order)
    
    # Separate GK and outfield bench players
    bench_gk = bench_df[bench_df['position'] == 'Goalkeeper']
    bench_outfield = bench_df[bench_df['position'] != 'Goalkeeper']
    
    # Sort outfield by expected points (highest first)
    bench_outfield = bench_outfield.sort_values('expected_points', ascending=False)
    
    # Combine: GK first (if exists), then outfield by points
    if len(bench_gk) > 0:
        bench_df = pd.concat([bench_gk, bench_outfield])
    else:
        bench_df = bench_outfield
    
    # Add bench order numbers
    bench_df['bench_order'] = range(1, len(bench_df) + 1)
    
    # Create squad dictionary with all info
    squad = {
        'starting_df': starting_df,
        'bench_df': bench_df,
        'captain_idx': captain_idx,
        'vice_captain_idx': vice_captain_idx,
        'captain_name': df_players.loc[captain_idx, 'name'],
        'vice_captain_name': df_players.loc[vice_captain_idx, 'name'],
        'captain_points': df_players.loc[captain_idx, 'expected_points'],
        'vice_captain_points': df_players.loc[vice_captain_idx, 'expected_points'],
        'total_cost': starting_df['price'].sum() + bench_df['price'].sum(),
        'formation': starting_df['position'].value_counts().sort_index(),
        'gameweek': df_players['gameweek'].iloc[0] if 'gameweek' in df_players.columns else None,
    }
    
    return squad