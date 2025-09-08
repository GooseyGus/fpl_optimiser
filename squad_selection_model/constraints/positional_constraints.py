from pulp import lpSum

def add_positional_constraints(prob, vars, df_players):
    """
    Positional constraints.
    """

    # Get indices by position
    gk_indices = df_players[df_players['position'] == 'Goalkeeper'].index
    def_indices = df_players[df_players['position'] == 'Defender'].index
    mid_indices = df_players[df_players['position'] == 'Midfielder'].index
    fwd_indices = df_players[df_players['position'] == 'Forward'].index

    # Helper to sum all starting variables for a player
    def starting_sum(idx):
        return (
            vars['stay_starting'].get(idx, 0)
            + vars['bench_to_starting'].get(idx, 0)
            + vars['in_to_starting_free'].get(idx, 0)
            + vars['in_to_starting_paid'].get(idx, 0)
        )

    # Helper to sum all bench variables for a player
    def bench_sum(idx):
        return (
            vars['stay_bench'].get(idx, 0)
            + vars['starting_to_bench'].get(idx, 0)
            + vars['in_to_bench_free'].get(idx, 0)
            + vars['in_to_bench_paid'].get(idx, 0)
        )

    # -------------------
    # Squad constraints
    # -------------------
    prob += lpSum([starting_sum(idx) + bench_sum(idx) for idx in gk_indices]) == 2, "Squad_GK_2"
    prob += lpSum([starting_sum(idx) + bench_sum(idx) for idx in def_indices]) == 5, "Squad_DEF_5"
    prob += lpSum([starting_sum(idx) + bench_sum(idx) for idx in mid_indices]) == 5, "Squad_MID_5"
    prob += lpSum([starting_sum(idx) + bench_sum(idx) for idx in fwd_indices]) == 3, "Squad_FWD_3"

    # -------------------
    # Starting XI constraints
    # -------------------
    prob += lpSum([starting_sum(idx) for idx in gk_indices]) == 1, "Starting_GK_1"
    prob += lpSum([starting_sum(idx) for idx in def_indices]) >= 3, "Starting_DEF_Min_3"
    prob += lpSum([starting_sum(idx) for idx in def_indices]) <= 4, "Starting_DEF_Max_5"
    prob += lpSum([starting_sum(idx) for idx in mid_indices]) >= 2, "Starting_MID_Min_2"
    prob += lpSum([starting_sum(idx) for idx in mid_indices]) <= 5, "Starting_MID_Max_5"
    prob += lpSum([starting_sum(idx) for idx in fwd_indices]) >= 1, "Starting_FWD_Min_1"
    prob += lpSum([starting_sum(idx) for idx in fwd_indices]) <= 3, "Starting_FWD_Max_3"

    return prob
