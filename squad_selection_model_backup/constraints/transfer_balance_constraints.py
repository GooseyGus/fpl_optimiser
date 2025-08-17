# constraints.py - Transfer Balance Constraints
from pulp import lpSum

def add_transfer_balance_constraints(prob, vars, df_players, my_team):
    """
    Ensure transfer balance for each type of transfer.
    Every OUT must have a corresponding IN.
    """
    
    # Get indices for current team and new players
    current_team_indices = []
    new_player_indices = []
    
    for idx in df_players.index:
        player_id = df_players.loc[idx, 'id']
        if my_team.is_in_team(player_id):
            current_team_indices.append(idx)
        else:
            new_player_indices.append(idx)
    
    # CONSTRAINT 1: Starting XI Free Transfers Balance
    # Every starting player transferred out (free) needs a replacement transferred in (free)
    starting_out_free = lpSum([vars['out']['starting_free'][idx] for idx in current_team_indices])
    starting_in_free = lpSum([vars['in']['to_starting_free'][idx] for idx in new_player_indices])
    prob += starting_out_free == starting_in_free, "Starting_Free_Transfer_Balance"
    
    # CONSTRAINT 2: Starting XI Paid Transfers Balance  
    # Every starting player transferred out (paid) needs a replacement transferred in (paid)
    starting_out_paid = lpSum([vars['out']['starting_paid'][idx] for idx in current_team_indices])
    starting_in_paid = lpSum([vars['in']['to_starting_paid'][idx] for idx in new_player_indices])
    prob += starting_out_paid == starting_in_paid, "Starting_Paid_Transfer_Balance"
    
    # CONSTRAINT 3: Bench Free Transfers Balance
    # Every bench player transferred out (free) needs a replacement transferred in (free)
    bench_out_free = lpSum([vars['out']['bench_free'][idx] for idx in current_team_indices])
    bench_in_free = lpSum([vars['in']['to_bench_free'][idx] for idx in new_player_indices])
    prob += bench_out_free == bench_in_free, "Bench_Free_Transfer_Balance"
    
    # CONSTRAINT 4: Bench Paid Transfers Balance
    # Every bench player transferred out (paid) needs a replacement transferred in (paid)
    bench_out_paid = lpSum([vars['out']['bench_paid'][idx] for idx in current_team_indices])
    bench_in_paid = lpSum([vars['in']['to_bench_paid'][idx] for idx in new_player_indices])
    prob += bench_out_paid == bench_in_paid, "Bench_Paid_Transfer_Balance"
    
    # CONSTRAINT 5: Internal Swaps Balance
    # Every bench→starting swap must have a corresponding starting→bench swap
    bench_to_starting = lpSum([vars['swap']['bench_to_starting'][idx] for idx in current_team_indices])
    starting_to_bench = lpSum([vars['swap']['starting_to_bench'][idx] for idx in current_team_indices])
    prob += bench_to_starting == starting_to_bench, "Bench_Starting_Swap_Balance"
        
    return prob