def get_var_safely(vars_dict, category, subcategory, idx):
    """
    Safely get a variable, returning 0 if it doesn't exist
    Used in constraints to avoid KeyError
    """
    try:
        if subcategory:
            return vars_dict[category][subcategory].get(idx, 0)
        else:
            return vars_dict[category].get(idx, 0)
    except:
        return 0
    
# Helper functions to get total players in each role
def get_starting_total(vars, idx):
    """Sum all ways a player can be in starting XI"""
    total = 0
    total += get_var_safely(vars, 'stay', 'starting', idx)
    total += get_var_safely(vars, 'swap', 'bench_to_starting', idx)
    total += get_var_safely(vars, 'in', 'to_starting_free', idx)
    total += get_var_safely(vars, 'in', 'to_starting_paid', idx)
    return total

def get_bench_total(vars, idx):
    """Sum all ways a player can be on bench"""
    total = 0
    total += get_var_safely(vars, 'stay', 'bench', idx)
    total += get_var_safely(vars, 'swap', 'starting_to_bench', idx)
    total += get_var_safely(vars, 'in', 'to_bench_free', idx)
    total += get_var_safely(vars, 'in', 'to_bench_paid', idx)
    return total

def get_transfers_total(vars):
    """Count total transfers (free + paid)"""
    transfers = 0
    
    # Count all OUT transfers
    for category in ['starting_free', 'starting_paid', 'bench_free', 'bench_paid']:
        for idx, var in vars['out'][category].items():
            transfers += var
    
    # Or count all IN transfers (should be same)
    # for category in ['to_starting_free', 'to_starting_paid', 'to_bench_free', 'to_bench_paid']:
    #     for idx, var in vars['in'][category].items():
    #         transfers += var
    
    return transfers

def get_starting_sum(vars, idx):
    """All ways to be in starting XI - returns the actual value after solving"""
    total = 0
    
    # Check each variable and add its value if it exists
    if idx in vars['stay']['starting'] and vars['stay']['starting'][idx].value() is not None:
        total += vars['stay']['starting'][idx].value()
    
    if idx in vars['swap']['bench_to_starting'] and vars['swap']['bench_to_starting'][idx].value() is not None:
        total += vars['swap']['bench_to_starting'][idx].value()
    
    if idx in vars['in']['to_starting_free'] and vars['in']['to_starting_free'][idx].value() is not None:
        total += vars['in']['to_starting_free'][idx].value()
    
    if idx in vars['in']['to_starting_paid'] and vars['in']['to_starting_paid'][idx].value() is not None:
        total += vars['in']['to_starting_paid'][idx].value()
    
    return total

def get_bench_sum(vars, idx):
    """All ways to be on bench"""
    return (
        vars['stay']['bench'].get(idx, 0) +
        vars['swap']['starting_to_bench'].get(idx, 0) +
        vars['in']['to_bench_free'].get(idx, 0) +
        vars['in']['to_bench_paid'].get(idx, 0)
    )

def get_squad_sum(vars, idx):
    """All ways to be in the squad (starting XI or bench)"""
    return get_starting_sum(vars, idx) + get_bench_sum(vars, idx)

