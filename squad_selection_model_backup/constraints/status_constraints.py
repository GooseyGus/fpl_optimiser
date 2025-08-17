# constraints/status_constraints.py
from pulp import lpSum

def add_player_status_constraints(prob, vars, df_players, my_team):
    """
    Only player ids in the current team can be:
      - stay starting
      - starting to bench
      - transfer out free
      - transfer out paid

    Only player ids in the current bench can be:
      - stay bench
      - bench to starting
      - transfer out bench free
      - transfer out bench paid
    """
    
    for idx in df_players.index:
        player_id = df_players.loc[idx, 'id']
        
        # Constraint: Players NOT in current starting XI cannot do starting-related actions
        if not my_team.is_in_starting(player_id):
            if idx in vars['stay']['starting']:
                prob += vars['stay']['starting'][idx] == 0, f"Player_{idx}_cannot_stay_starting"
            if idx in vars['swap']['starting_to_bench']:
                prob += vars['swap']['starting_to_bench'][idx] == 0, f"Player_{idx}_cannot_swap_to_bench"
            if idx in vars['out']['starting_free']:
                prob += vars['out']['starting_free'][idx] == 0, f"Player_{idx}_cannot_out_starting_free"
            if idx in vars['out']['starting_paid']:
                prob += vars['out']['starting_paid'][idx] == 0, f"Player_{idx}_cannot_out_starting_paid"
        
        # Constraint: Players NOT on current bench cannot do bench-related actions
        if not my_team.is_on_bench(player_id):
            if idx in vars['stay']['bench']:
                prob += vars['stay']['bench'][idx] == 0, f"Player_{idx}_cannot_stay_bench"
            if idx in vars['swap']['bench_to_starting']:
                prob += vars['swap']['bench_to_starting'][idx] == 0, f"Player_{idx}_cannot_swap_to_starting"
            if idx in vars['out']['bench_free']:
                prob += vars['out']['bench_free'][idx] == 0, f"Player_{idx}_cannot_out_bench_free"
            if idx in vars['out']['bench_paid']:
                prob += vars['out']['bench_paid'][idx] == 0, f"Player_{idx}_cannot_out_bench_paid"
          
    return prob