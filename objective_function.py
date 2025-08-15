# objective_function.py
# Function to add the objective function to the optimization problem

from pulp import lpSum

def add_objective_function(prob, df_players, starting_vars, captain_vars):
    """
    Add objective function to maximize expected points

    """
    regular_points = lpSum([df_players.loc[idx, 'expected_points'] * starting_vars[idx] 
                           for idx in df_players.index])
    
    captain_bonus = lpSum([df_players.loc[idx, 'expected_points'] * captain_vars[idx] 
                            for idx in df_players.index])
    
    prob += regular_points + captain_bonus, "Total_Expected_Points_With_Captain"

    
    return prob