# bench_selection_constraints.py: Only select players for the bench if they had at least 59 minutes in fpl_players_gw_2.csv

from pulp import LpProblem, LpVariable, lpSum, LpStatus, LpBinary

def add_bench_selection_constraints(prob, vars, df_players, 
                                  min_minutes=59, 
                                  min_price=4.0, 
                                  max_price=6.0,
                                  min_expected_points=1.0,
                                  max_expected_points=8.0,
                                  min_ownership=0.1,
                                  max_ownership=50.0,
                                  allow_injured=False,
                                  min_form=0.0):
    """
    Add comprehensive constraints for bench player selection.
    
    Parameters:
    - min_minutes: Minimum minutes played in previous gameweek (default: 59)
    - min_price: Minimum player price for bench eligibility (default: 4.0)
    - max_price: Maximum player price for bench eligibility (default: 6.0) 
    - min_expected_points: Minimum expected points for next gameweek (default: 1.0)
    - max_expected_points: Maximum expected points (to avoid expensive players on bench) (default: 8.0)
    - min_ownership: Minimum ownership percentage (default: 0.1)
    - max_ownership: Maximum ownership percentage (to avoid popular players on bench) (default: 50.0)
    - allow_injured: Whether to allow injured/doubtful players on bench (default: False)
    - min_form: Minimum form rating (default: 0.0)
    """
    
    # Create binary variables for different eligibility criteria
    bench_eligible = LpVariable.dicts("BenchEligible", df_players.index, cat=LpBinary)
    minutes_eligible = LpVariable.dicts("MinutesEligible", df_players.index, cat=LpBinary)
    price_eligible = LpVariable.dicts("PriceEligible", df_players.index, cat=LpBinary)
    points_eligible = LpVariable.dicts("PointsEligible", df_players.index, cat=LpBinary)
    ownership_eligible = LpVariable.dicts("OwnershipEligible", df_players.index, cat=LpBinary)
    availability_eligible = LpVariable.dicts("AvailabilityEligible", df_players.index, cat=LpBinary)
    form_eligible = LpVariable.dicts("FormEligible", df_players.index, cat=LpBinary)

    for idx in df_players.index:
        player = df_players.loc[idx]
        
        # 1. MINUTES CONSTRAINT - Must have played at least minimum minutes
        if 'minutes' in df_players.columns:
            prob += (minutes_eligible[idx] <= (player['minutes'] >= min_minutes)), f"MinutesEligibility_{idx}"
        else:
            prob += (minutes_eligible[idx] == 1), f"MinutesEligibility_{idx}_NoData"
        
        # 2. PRICE CONSTRAINTS - Must be within price range (bench players should be cheap)
        prob += (price_eligible[idx] <= (player['price'] >= min_price)), f"MinPriceEligibility_{idx}"
        prob += (price_eligible[idx] <= (player['price'] <= max_price)), f"MaxPriceEligibility_{idx}"
        
        # 3. EXPECTED POINTS CONSTRAINTS - Not too high (expensive) or too low (useless)
        if 'expected_points' in df_players.columns:
            prob += (points_eligible[idx] <= (player['expected_points'] >= min_expected_points)), f"MinPointsEligibility_{idx}"
            prob += (points_eligible[idx] <= (player['expected_points'] <= max_expected_points)), f"MaxPointsEligibility_{idx}"
        else:
            prob += (points_eligible[idx] == 1), f"PointsEligibility_{idx}_NoData"
        
        # 4. OWNERSHIP CONSTRAINTS - Avoid very popular players on bench
        if 'selected_by_percent' in df_players.columns:
            ownership_pct = float(player['selected_by_percent'])
            prob += (ownership_eligible[idx] <= (ownership_pct >= min_ownership)), f"MinOwnershipEligibility_{idx}"
            prob += (ownership_eligible[idx] <= (ownership_pct <= max_ownership)), f"MaxOwnershipEligibility_{idx}"
        else:
            prob += (ownership_eligible[idx] == 1), f"OwnershipEligibility_{idx}_NoData"
        
        # 5. AVAILABILITY CONSTRAINTS - Exclude injured/suspended players if specified
        if not allow_injured and 'status' in df_players.columns:
            is_available = player['status'] in ['a', 'available', 'Available']
            prob += (availability_eligible[idx] <= is_available), f"AvailabilityEligibility_{idx}"
        else:
            prob += (availability_eligible[idx] == 1), f"AvailabilityEligibility_{idx}_NoData"
        
        # 6. FORM CONSTRAINTS - Must have minimum form
        if 'form' in df_players.columns:
            prob += (form_eligible[idx] <= (float(player['form']) >= min_form)), f"FormEligibility_{idx}"
        else:
            prob += (form_eligible[idx] == 1), f"FormEligibility_{idx}_NoData"
        
        # 7. OVERALL ELIGIBILITY - Player must meet ALL criteria
        prob += (bench_eligible[idx] <= minutes_eligible[idx]), f"BenchEligibility_Minutes_{idx}"
        prob += (bench_eligible[idx] <= price_eligible[idx]), f"BenchEligibility_Price_{idx}"
        prob += (bench_eligible[idx] <= points_eligible[idx]), f"BenchEligibility_Points_{idx}"
        prob += (bench_eligible[idx] <= ownership_eligible[idx]), f"BenchEligibility_Ownership_{idx}"
        prob += (bench_eligible[idx] <= availability_eligible[idx]), f"BenchEligibility_Availability_{idx}"
        prob += (bench_eligible[idx] <= form_eligible[idx]), f"BenchEligibility_Form_{idx}"
        
        # If player meets all criteria, they can be eligible
        prob += (bench_eligible[idx] >= 
                minutes_eligible[idx] + price_eligible[idx] + points_eligible[idx] + 
                ownership_eligible[idx] + availability_eligible[idx] + form_eligible[idx] - 5), f"BenchEligibility_All_{idx}"

    # Apply eligibility to bench selection variables
    for idx in df_players.index:
        # Only eligible players can stay on bench
        if 'stay_bench' in vars:
            prob += (vars['stay_bench'][idx] <= bench_eligible[idx]), f"StayBenchEligibility_{idx}"
        
        # Only eligible players can be moved to bench
        if 'in_to_bench_free' in vars:
            prob += (vars['in_to_bench_free'][idx] <= bench_eligible[idx]), f"InToBenchFreeEligibility_{idx}"
        
        if 'in_to_bench_paid' in vars:
            prob += (vars['in_to_bench_paid'][idx] <= bench_eligible[idx]), f"InToBenchPaidEligibility_{idx}"

    

    return prob