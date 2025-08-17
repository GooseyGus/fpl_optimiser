# decision_variables.py

from pulp import LpVariable

def create_decision_variables(df_players):
    vars = {
        'stay_starting': {},
        'stay_bench': {},
        'starting_to_bench': {},
        'bench_to_starting': {},
        'out_starting_free': {},
        'out_starting_paid': {},
        'out_bench_free': {},
        'out_bench_paid': {},
        'in_to_starting_free': {},
        'in_to_starting_paid': {},
        'in_to_bench_free': {},
        'in_to_bench_paid': {},
        'captain': {}
    }
    
    for idx in df_players.index:
        vars['stay_starting'][idx]       = LpVariable(f"stay_starting_{idx}", cat='Binary')
        vars['stay_bench'][idx]          = LpVariable(f"stay_bench_{idx}", cat='Binary')
        vars['starting_to_bench'][idx]   = LpVariable(f"starting_to_bench_{idx}", cat='Binary')
        vars['bench_to_starting'][idx]   = LpVariable(f"bench_to_starting_{idx}", cat='Binary')
        
        vars['out_starting_free'][idx]   = LpVariable(f"out_starting_free_{idx}", cat='Binary')
        vars['out_starting_paid'][idx]   = LpVariable(f"out_starting_paid_{idx}", cat='Binary')
        vars['out_bench_free'][idx]      = LpVariable(f"out_bench_free_{idx}", cat='Binary')
        vars['out_bench_paid'][idx]      = LpVariable(f"out_bench_paid_{idx}", cat='Binary')
        
        vars['in_to_starting_free'][idx] = LpVariable(f"in_to_starting_free_{idx}", cat='Binary')
        vars['in_to_starting_paid'][idx] = LpVariable(f"in_to_starting_paid_{idx}", cat='Binary')
        vars['in_to_bench_free'][idx]    = LpVariable(f"in_to_bench_free_{idx}", cat='Binary')
        vars['in_to_bench_paid'][idx]    = LpVariable(f"in_to_bench_paid_{idx}", cat='Binary')
        
        vars['captain'][idx]             = LpVariable(f"captain_{idx}", cat='Binary')
    
    return vars
