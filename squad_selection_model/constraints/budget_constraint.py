# budget_constraint.py

from pulp import lpSum

def add_budget_constraint(prob, vars, df_players_gw1, df_players_gw2, 
                         current_team, initial_bank=0):
    """
    Budget constraint for transfers considering price changes
    
    Money = initial_bank + money_from_sales - money_for_purchases
    """
    
    # Calculate money from SALES (players transferred out)
    money_from_sales = lpSum(
        vars['out_starting_free'][idx] * df_players_gw2.loc[idx, 'price'] +
        vars['out_starting_paid'][idx] * df_players_gw2.loc[idx, 'price'] +
        vars['out_bench_free'][idx] * df_players_gw2.loc[idx, 'price'] +
        vars['out_bench_paid'][idx] * df_players_gw2.loc[idx, 'price']
        for idx in df_players_gw2.index if idx in current_team['player_id'].values
    )
    
    # Calculate money for PURCHASES (players transferred in)
    money_for_purchases = lpSum(
        vars['in_to_starting_free'][idx] * df_players_gw2.loc[idx, 'price'] +
        vars['in_to_starting_paid'][idx] * df_players_gw2.loc[idx, 'price'] +
        vars['in_to_bench_free'][idx] * df_players_gw2.loc[idx, 'price'] +
        vars['in_to_bench_paid'][idx] * df_players_gw2.loc[idx, 'price']
        for idx in df_players_gw2.index if idx not in current_team['player_id'].values
    )
    

    # Calculate price of whole team:
    total_team_cost = lpSum(
        df_players_gw2.loc[idx, 'price'] * vars['stay_starting'][idx] +
        df_players_gw2.loc[idx, 'price'] * vars['stay_bench'][idx] +
        df_players_gw2.loc[idx, 'price'] * vars['in_to_starting_free'][idx] +
        df_players_gw2.loc[idx, 'price'] * vars['in_to_starting_paid'][idx] +
        df_players_gw2.loc[idx, 'price'] * vars['in_to_bench_free'][idx] +
        df_players_gw2.loc[idx, 'price'] * vars['in_to_bench_paid'][idx] +
        df_players_gw2.loc[idx, 'price'] * vars['starting_to_bench'][idx] +
        df_players_gw2.loc[idx, 'price'] * vars['bench_to_starting'][idx]
        for idx in df_players_gw2.index
    )

    prob += (
        total_team_cost <= 100 , "Budget_Constraint"
    )

    
    return prob