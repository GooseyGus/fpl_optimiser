# squad_selection_model/constraints/transfer_limit_constraints.py
from pulp import lpSum

def add_free_transfer_limit_constraint(prob, vars, df_players, my_team):
    """
    Limit the number of free transfers
    
    Rules:
    - Maximum free transfers available (usually 1, can accumulate up to 5)
    - Remaining transfers must be paid (-4 points each)
    """
    
    # Cap free transfers at 5 (FPL rule: max accumulation is 5)
    max_free_transfers = min(my_team.free_transfers, 5)
    
    # Count total free transfers IN (correct dictionary keys!)
    free_transfers_in = lpSum([
        vars['in']['to_starting_free'].get(idx, 0) +
        vars['in']['to_bench_free'].get(idx, 0)
        for idx in df_players.index
    ])
    
    # Count total free transfers OUT
    free_transfers_out = lpSum([
        vars['out']['starting_free'].get(idx, 0) +
        vars['out']['bench_free'].get(idx, 0)
        for idx in df_players.index
    ])
    
    # Free transfers IN must equal OUT (balance)
    prob += free_transfers_in == free_transfers_out, "Free_Transfer_Balance"
    
    # Free transfers cannot exceed available (capped at 5)
    prob += free_transfers_in <= max_free_transfers, f"Max_{max_free_transfers}_Free_Transfers"
    
    return prob