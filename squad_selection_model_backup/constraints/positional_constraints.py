# constraints/positional_constraints.py
# Positional constraints for FPL team selection

from pulp import lpSum

def add_positional_constraints(prob, vars, df_players):
    """
    Add all positional constraints for FPL team selection

    Squad constraints (starting + bench):
    - 2 GKs total
    - 5 DEFs total  
    - 5 MIDs total
    - 3 FWDs total

    Starting XI constraints:
    - Exactly 1 GK
    - 3-5 DEFs
    - 2-5 MIDs
    - 1-3 FWDs
    """

    # Get player indices by position
    gk_indices = df_players[df_players['position'] == 'Goalkeeper'].index
    def_indices = df_players[df_players['position'] == 'Defender'].index
    mid_indices = df_players[df_players['position'] == 'Midfielder'].index
    fwd_indices = df_players[df_players['position'] == 'Forward'].index

    # Helper to sum all starting/bench variables for an index
    def starting_sum(idx):
        return (
            vars['stay']['starting'].get(idx, 0)
            + vars['swap']['bench_to_starting'].get(idx, 0)
            + vars['in']['to_starting_free'].get(idx, 0)
            + vars['in']['to_starting_paid'].get(idx, 0)
        )

    def bench_sum(idx):
        return (
            vars['stay']['bench'].get(idx, 0)
            + vars['swap']['starting_to_bench'].get(idx, 0)
            + vars['in']['to_bench_free'].get(idx, 0)
            + vars['in']['to_bench_paid'].get(idx, 0)
        )

    # SQUAD CONSTRAINTS (starting + bench = exact numbers)
    # Exactly 2 GKs in squad
    prob += lpSum([starting_sum(idx) + bench_sum(idx) for idx in gk_indices]) == 2, "Squad_GK_2"

    # Exactly 5 DEFs in squad
    prob += lpSum([starting_sum(idx) + bench_sum(idx) for idx in def_indices]) == 5, "Squad_DEF_5"

    # Exactly 5 MIDs in squad
    prob += lpSum([starting_sum(idx) + bench_sum(idx) for idx in mid_indices]) == 5, "Squad_MID_5"

    # Exactly 3 FWDs in squad
    prob += lpSum([starting_sum(idx) + bench_sum(idx) for idx in fwd_indices]) == 3, "Squad_FWD_3"

    # STARTING XI CONSTRAINTS
    # Exactly 1 GK in starting XI
    prob += lpSum([starting_sum(idx) for idx in gk_indices]) == 1, "Starting_GK_1"

    # 3-5 DEFs in starting XI
    prob += lpSum([starting_sum(idx) for idx in def_indices]) >= 3, "Starting_DEF_Min_3"
    prob += lpSum([starting_sum(idx) for idx in def_indices]) <= 5, "Starting_DEF_Max_5"

    # 2-5 MIDs in starting XI  
    prob += lpSum([starting_sum(idx) for idx in mid_indices]) >= 2, "Starting_MID_Min_2"
    prob += lpSum([starting_sum(idx) for idx in mid_indices]) <= 5, "Starting_MID_Max_5"

    # 1-3 FWDs in starting XI
    prob += lpSum([starting_sum(idx) for idx in fwd_indices]) >= 1, "Starting_FWD_Min_1"
    prob += lpSum([starting_sum(idx) for idx in fwd_indices]) <= 3, "Starting_FWD_Max_3"

    return prob