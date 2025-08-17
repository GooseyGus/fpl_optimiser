# decision_variables_organized.py
# Organized decision variables using dictionary structure

from pulp import LpVariable

def create_decision_variables(df_players):
    vars = {}
    
    # Initialize all variable dictionaries
    vars['stay'] = {'starting': {}, 'bench': {}}
    vars['swap'] = {'starting_to_bench': {}, 'bench_to_starting': {}}
    vars['out'] = {'starting_free': {}, 'starting_paid': {}, 'bench_free': {}, 'bench_paid': {}}
    vars['in'] = {'to_starting_free': {}, 'to_starting_paid': {}, 'to_bench_free': {}, 'to_bench_paid': {}}
    vars['captain'] = {}
    
    # Create ALL variables for EVERY player - no conditions!
    for idx in df_players.index:
        # Stay variables
        vars['stay']['starting'][idx] = LpVariable(f"stay_starting_{idx}", cat='Binary')
        vars['stay']['bench'][idx] = LpVariable(f"stay_bench_{idx}", cat='Binary')
        
        # Swap variables  
        vars['swap']['starting_to_bench'][idx] = LpVariable(f"starting_to_bench_{idx}", cat='Binary')
        vars['swap']['bench_to_starting'][idx] = LpVariable(f"bench_to_starting_{idx}", cat='Binary')
        
        # Out variables
        vars['out']['starting_free'][idx] = LpVariable(f"out_starting_free_{idx}", cat='Binary')
        vars['out']['starting_paid'][idx] = LpVariable(f"out_starting_paid_{idx}", cat='Binary')
        vars['out']['bench_free'][idx] = LpVariable(f"out_bench_free_{idx}", cat='Binary')
        vars['out']['bench_paid'][idx] = LpVariable(f"out_bench_paid_{idx}", cat='Binary')
        
        # In variables
        vars['in']['to_starting_free'][idx] = LpVariable(f"in_to_starting_free_{idx}", cat='Binary')
        vars['in']['to_starting_paid'][idx] = LpVariable(f"in_to_starting_paid_{idx}", cat='Binary')
        vars['in']['to_bench_free'][idx] = LpVariable(f"in_to_bench_free_{idx}", cat='Binary')
        vars['in']['to_bench_paid'][idx] = LpVariable(f"in_to_bench_paid_{idx}", cat='Binary')
        
        # Captain
        vars['captain'][idx] = LpVariable(f"captain_{idx}", cat='Binary')
    
    return vars
