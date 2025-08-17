def add_availability_constraints(prob, vars, df_players, my_team):
    """
    Ensure only fully available players can be selected for the new squad.
    
    Rules:
    - Player must have status 'a' (available) to be brought IN or KEPT
    - Injured/suspended players can be transferred OUT
    """
    
    # Get indices of unavailable players
    unavailable_indices = df_players[df_players['status'] != 'a'].index
    
    for idx in unavailable_indices:
        player_id = df_players.loc[idx, 'id']
        
        # If unavailable player is NOT in current team, they cannot be brought in
        if not my_team.is_in_team(player_id):
            # Cannot transfer IN unavailable players
            if idx in vars['in'].get('to_starting_free', {}):
                prob += vars['in']['to_starting_free'][idx] == 0, f"Player_{idx}_Unavailable_In_Starting_Free"
            if idx in vars['in'].get('to_starting_paid', {}):
                prob += vars['in']['to_starting_paid'][idx] == 0, f"Player_{idx}_Unavailable_In_Starting_Paid"
            if idx in vars['in'].get('to_bench_free', {}):
                prob += vars['in']['to_bench_free'][idx] == 0, f"Player_{idx}_Unavailable_In_Bench_Free"
            if idx in vars['in'].get('to_bench_paid', {}):
                prob += vars['in']['to_bench_paid'][idx] == 0, f"Player_{idx}_Unavailable_In_Bench_Paid"
        
    return prob