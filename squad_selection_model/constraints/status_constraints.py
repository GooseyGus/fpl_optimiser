def add_status_constraints(prob, vars, df_players, my_team):
    """
    Enforce that players can only take actions consistent with their previous state:
    
    - Players not on bench last GW cannot:
        stay on bench, bench->starting, bench out (free/paid)
    
    - Players not in starting XI last GW cannot:
        stay starting, starting->bench, starting out (free/paid)
    """
    for idx in df_players.index:
        player_id = df_players.loc[idx, 'id']  # assuming 'id' column
        
        # -------- Bench constraints --------
        if not my_team.is_on_bench(player_id):
            for var_name in ['stay_bench', 'bench_to_starting', 'out_bench_free', 'out_bench_paid']:
                if var_name in vars and idx in vars[var_name]:
                    prob += vars[var_name][idx] == 0, f"Player_{idx}_Cannot_Bench_Action_{var_name}"
        
        # -------- Starter constraints --------
        if not my_team.is_in_starting(player_id):
            for var_name in ['stay_starting', 'starting_to_bench', 'out_starting_free', 'out_starting_paid']:
                if var_name in vars and idx in vars[var_name]:
                    prob += vars[var_name][idx] == 0, f"Player_{idx}_Cannot_Starter_Action_{var_name}"
    
    return prob
