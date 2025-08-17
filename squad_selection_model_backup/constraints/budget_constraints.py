# budget_constraints.py
# Budget constraint for FPL team selection

from pulp import lpSum

def add_budget_constraint(prob, vars, df_players_gw1, df_players_gw2, 
                         current_team, initial_bank=0.0):
    """
    Budget constraint for transfers considering price changes
    
    Money = initial_bank + money_from_sales - money_for_purchases
    Final squad value + remaining money <= 100m
    """
    
    # Calculate money from SALES (players transferred out)
    money_from_sales = []
    for idx in df_players_gw2.index:
        player_id = df_players_gw2.loc[idx, 'id']
        
        if player_id in current_team['player_id'].values:
            # Get the price we bought at (from current_team)
            bought_price = current_team[current_team['player_id'] == player_id]['price'].values[0]
            # Get current selling price from GW2
            current_price = df_players_gw2.loc[idx, 'price']
            
            # FPL rule: You keep 50% of profit (rounded down to 0.1m)
            if current_price > bought_price:
                sell_price = bought_price + ((current_price - bought_price) * 0.5)
            else:
                sell_price = current_price  # Full loss if price dropped
            
            # Money from selling this player (if transferred out)
            transfer_out = (
                vars['out'].get('starting_free', {}).get(idx, 0) + 
                vars['out'].get('starting_paid', {}).get(idx, 0) +
                vars['out'].get('bench_free', {}).get(idx, 0) + 
                vars['out'].get('bench_paid', {}).get(idx, 0)
            )
            
            money_from_sales.append(transfer_out * sell_price)
    
    # Calculate money for PURCHASES (players transferred in)
    money_for_purchases = []
    for idx in df_players_gw2.index:
        player_id = df_players_gw2.loc[idx, 'id']
        
        if player_id not in current_team['player_id'].values:
            # Buy at current GW2 price
            buy_price = df_players_gw2.loc[idx, 'price']
            
            # Money spent buying this player (if transferred in)
            transfer_in = (
                vars['in'].get('to_starting_free', {}).get(idx, 0) + 
                vars['in'].get('to_starting_paid', {}).get(idx, 0) +
                vars['in'].get('to_bench_free', {}).get(idx, 0) + 
                vars['in'].get('to_bench_paid', {}).get(idx, 0)
            )
            
            money_for_purchases.append(transfer_in * buy_price)
    
    # Calculate money for KEPT players (at their original prices)
    money_in_kept_players = []
    for idx in df_players_gw2.index:
        player_id = df_players_gw2.loc[idx, 'id']
        
        if player_id in current_team['player_id'].values:
            # Keep at original bought price
            bought_price = current_team[current_team['player_id'] == player_id]['price'].values[0]
            
            # Money tied up in kept players (staying or swapping within squad)
            kept = (
                vars['stay'].get('starting', {}).get(idx, 0) + 
                vars['stay'].get('bench', {}).get(idx, 0) +
                vars['swap'].get('starting_to_bench', {}).get(idx, 0) + 
                vars['swap'].get('bench_to_starting', {}).get(idx, 0)
            )
            
            money_in_kept_players.append(kept * bought_price)
    
    # Budget constraint
    total_squad_value = lpSum(money_in_kept_players) + lpSum(money_for_purchases)
    money_remaining = initial_bank + lpSum(money_from_sales) - lpSum(money_for_purchases)
    
    # Total value + bank <= 100m
    prob += total_squad_value + money_remaining <= 100.0, "Budget_Constraint"
    
    # Also ensure we don't go negative
    prob += money_remaining >= 0, "No_Negative_Bank"
    
    return prob