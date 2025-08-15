# decision_variables.py
# Function to create decision variables for each player 

from pulp import LpVariable

def create_decision_variables(df_players):
    starting_vars = {}  # Binary: 1 if player is in starting XI
    bench_vars = {}     # Binary: 1 if player is on bench
    captain_vars = {}      # Binary: 1 if player is captain
    
    for idx in df_players.index:
        starting_vars[idx] = LpVariable(f"starting_{idx}", cat='Binary')
        bench_vars[idx] = LpVariable(f"bench_{idx}", cat='Binary')
        captain_vars[idx] = LpVariable(f"captain_{idx}", cat='Binary')
        
    return starting_vars, bench_vars, captain_vars