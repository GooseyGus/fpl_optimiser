# budget_constraints.py
# Budget constraint for FPL team selection

from pulp import lpSum

def add_budget_constraint(prob, starting_vars, bench_vars, df_players, budget=100.0):
    """
    Add budget constraint for total squad cost
    
    FPL Rule: Total squad value cannot exceed £100m
    """
    
    # Sum of all selected players' prices (starting + bench) must be <= budget
    prob += lpSum([(starting_vars[idx] + bench_vars[idx]) * df_players.loc[idx, 'price'] 
                   for idx in df_players.index]) <= budget, f"Budget_Max_{budget}m"
    
    return prob