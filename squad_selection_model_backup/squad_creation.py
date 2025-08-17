# squad_creation.py
import pandas as pd
from pulp import LpStatus

def create_squad(prob, df_players, vars):
    """
    Extract optimization results and post-process squad selections
    """
    
    # Check if optimization was successful
    if LpStatus[prob.status] != 'Optimal':
        print(f"Warning: Optimization status is {LpStatus[prob.status]}")
        return None
    
    # Helper function to safely get variable value
    def get_var_value(var):
        """Safely get variable value, return 0 if None"""
        return var.value() if var and var.value() is not None else 0
    
    # Helper functions to check if player is in starting/bench
    def is_starting(idx):
        return (
            get_var_value(vars['stay']['starting'].get(idx)) == 1 or
            get_var_value(vars['swap']['bench_to_starting'].get(idx)) == 1 or
            get_var_value(vars['in']['to_starting_free'].get(idx)) == 1 or
            get_var_value(vars['in']['to_starting_paid'].get(idx)) == 1
        )
    
    def is_bench(idx):
        return (
            get_var_value(vars['stay']['bench'].get(idx)) == 1 or
            get_var_value(vars['swap']['starting_to_bench'].get(idx)) == 1 or
            get_var_value(vars['in']['to_bench_free'].get(idx)) == 1 or
            get_var_value(vars['in']['to_bench_paid'].get(idx)) == 1
        )
    
    def get_transfer_type(idx):
        """Get the transfer type for a player based on which variable is 1"""
        # Check all transfer types
        transfer_checks = [
            ('Stay starting', vars['stay']['starting'].get(idx)),
            ('Stay bench', vars['stay']['bench'].get(idx)),
            ('Bench→Start', vars['swap']['bench_to_starting'].get(idx)),
            ('Start→Bench', vars['swap']['starting_to_bench'].get(idx)),
            ('In starting (free)', vars['in']['to_starting_free'].get(idx)),
            ('In starting (paid)', vars['in']['to_starting_paid'].get(idx)),
            ('In bench (free)', vars['in']['to_bench_free'].get(idx)),
            ('In bench (paid)', vars['in']['to_bench_paid'].get(idx)),
        ]
        
        for label, var in transfer_checks:
            if get_var_value(var) == 1:
                return label
        return "None"
    
    # Extract solution
    starters = [idx for idx in df_players.index if is_starting(idx)]
    bench = [idx for idx in df_players.index if is_bench(idx)]
    
    # Debug: Check squad size
    print(f"Squad size: {len(starters)} starting + {len(bench)} bench = {len(starters) + len(bench)} total")
    if len(starters) != 11:
        print(f"WARNING: Starting XI has {len(starters)} players instead of 11!")
    if len(bench) != 4:
        print(f"WARNING: Bench has {len(bench)} players instead of 4!")
    
    # Find captain
    captain_idx = None
    captain_count = 0
    for idx in df_players.index:
        if get_var_value(vars['captain'].get(idx)) == 1:
            captain_idx = idx
            captain_count += 1
    
    if captain_count > 1:
        print(f"WARNING: {captain_count} captains selected!")
    elif captain_count == 0:
        print("WARNING: No captain selected!")
    
    # Post-process: Select vice-captain (highest xP starter from different team than captain)
    vice_captain_idx = None
    if captain_idx and len(starters) > 1:
        captain_team = df_players.loc[captain_idx, 'team']
        potential_vcs = [idx for idx in starters 
                        if idx != captain_idx and df_players.loc[idx, 'team'] != captain_team]
        
        # If no one from different team, allow same team
        if not potential_vcs:
            potential_vcs = [idx for idx in starters if idx != captain_idx]
        
        if potential_vcs:
            vice_captain_idx = max(potential_vcs, key=lambda x: df_players.loc[x, 'expected_points'])
    
    # Create dataframes
    starting_df = df_players.loc[starters].copy() if starters else pd.DataFrame()
    bench_df = df_players.loc[bench].copy() if bench else pd.DataFrame()
    
    if not starting_df.empty:
        # Add transfer type for each player
        starting_df['transfer_type'] = [get_transfer_type(idx) for idx in starters]
        starting_df['role'] = 'Starting XI'
        starting_df['is_captain'] = starting_df.index == captain_idx
        starting_df['is_vice_captain'] = starting_df.index == vice_captain_idx
        
        # Sort starting XI by position and points
        position_order = {'Goalkeeper': 1, 'Defender': 2, 'Midfielder': 3, 'Forward': 4}
        starting_df['pos_order'] = starting_df['position'].map(position_order)
        starting_df = starting_df.sort_values(['pos_order', 'expected_points'], ascending=[True, False])
    
    if not bench_df.empty:
        bench_df['transfer_type'] = [get_transfer_type(idx) for idx in bench]
        bench_df['role'] = 'Bench'
        
        # Order bench
        position_order = {'Goalkeeper': 1, 'Defender': 2, 'Midfielder': 3, 'Forward': 4}
        bench_df['pos_order'] = bench_df['position'].map(position_order)
        
        # Separate GK and outfield
        bench_gk = bench_df[bench_df['position'] == 'Goalkeeper']
        bench_outfield = bench_df[bench_df['position'] != 'Goalkeeper']
        bench_outfield = bench_outfield.sort_values('expected_points', ascending=False)
        
        # Combine: GK first, then outfield
        bench_df = pd.concat([bench_gk, bench_outfield]) if len(bench_gk) > 0 else bench_outfield
        bench_df['bench_order'] = range(1, len(bench_df) + 1)
    
    # Create squad dictionary
    squad = {
        'starting_df': starting_df,
        'bench_df': bench_df,
        'captain_idx': captain_idx,
        'vice_captain_idx': vice_captain_idx,
        'captain_name': df_players.loc[captain_idx, 'name'] if captain_idx else "None",
        'vice_captain_name': df_players.loc[vice_captain_idx, 'name'] if vice_captain_idx else "None",
        'captain_points': df_players.loc[captain_idx, 'expected_points'] if captain_idx else 0,
        'vice_captain_points': df_players.loc[vice_captain_idx, 'expected_points'] if vice_captain_idx else 0,
        'total_cost': starting_df['price'].sum() + bench_df['price'].sum() if not starting_df.empty else 0,
        'formation': starting_df['position'].value_counts().sort_index() if not starting_df.empty else None,
        'gameweek': df_players['gameweek'].iloc[0] if 'gameweek' in df_players.columns else None,
        'optimization_status': LpStatus[prob.status],
        'objective_value': prob.objective.value()
    }
    
    return squad