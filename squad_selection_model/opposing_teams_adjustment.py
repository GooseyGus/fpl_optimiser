# opposing_teams_adjustment.py
# Simple approach: adjust expected points for players from opposing teams

import pandas as pd

def apply_opposing_teams_adjustment(df_players, point_reduction=0.5, enable_adjustment=True):
    """
    Reduce expected points for players from teams playing against each other.
    
    Parameters:
    - df_players: DataFrame with player data including opponent information
    - point_reduction: Points to reduce for each player when facing opponents (default 0.5)
    - enable_adjustment: Whether to apply this adjustment (default True)
    
    Returns:
    - df_players: Modified DataFrame with adjusted expected points
    - adjustment_summary: Dictionary with details of adjustments made
    """
    
    if not enable_adjustment:
        print("Opposing teams adjustment disabled")
        return df_players, {}
    
    print(f"Applying opposing teams adjustment (reduction: {point_reduction} pts per player)")
    
    # Create a copy to avoid modifying original
    df_adjusted = df_players.copy()
    
    # Track adjustments
    adjustments = []
    fixture_summary = {}
    
    # Get unique fixtures (avoid counting same fixture twice)
    fixtures = df_adjusted[['team', 'opponent']].drop_duplicates()
    fixtures = fixtures[fixtures['opponent'] != 'No fixture']
    
    # Process each fixture
    for _, fixture in fixtures.iterrows():
        team1 = fixture['team']
        team2 = fixture['opponent']
        
        # Avoid processing the same fixture twice
        fixture_key = tuple(sorted([team1, team2]))
        if fixture_key in fixture_summary:
            continue
            
        # Get players from both teams
        team1_players = df_adjusted[df_adjusted['team'] == team1]
        team2_players = df_adjusted[df_adjusted['team'] == team2]
        
        # Adjust expected points for all players in this fixture
        team1_indices = team1_players.index
        team2_indices = team2_players.index
        
        # Apply reduction
        original_points_team1 = df_adjusted.loc[team1_indices, 'expected_points'].copy()
        original_points_team2 = df_adjusted.loc[team2_indices, 'expected_points'].copy()
        
        df_adjusted.loc[team1_indices, 'expected_points'] = (
            df_adjusted.loc[team1_indices, 'expected_points'] - point_reduction
        ).clip(lower=0)  # Don't let points go negative
        
        df_adjusted.loc[team2_indices, 'expected_points'] = (
            df_adjusted.loc[team2_indices, 'expected_points'] - point_reduction
        ).clip(lower=0)  # Don't let points go negative
        
        # Track the adjustment
        fixture_summary[fixture_key] = {
            'match': f"{team1} vs {team2}",
            'team1_players_affected': len(team1_players),
            'team2_players_affected': len(team2_players),
            'total_players_affected': len(team1_players) + len(team2_players),
            'reduction_per_player': point_reduction
        }
        
        # Add individual player adjustments to tracking
        for idx in team1_indices:
            player = df_adjusted.loc[idx]
            adjustments.append({
                'player': player['name'],
                'team': team1,
                'opponent': team2,
                'original_points': original_points_team1.loc[idx],
                'adjusted_points': player['expected_points'],
                'reduction': point_reduction
            })
            
        for idx in team2_indices:
            player = df_adjusted.loc[idx]
            adjustments.append({
                'player': player['name'],
                'team': team2,
                'opponent': team1,
                'original_points': original_points_team2.loc[idx],
                'adjusted_points': player['expected_points'],
                'reduction': point_reduction
            })
    
    # Print summary
    if fixture_summary:
        print(f"  Processed {len(fixture_summary)} fixtures:")
        total_affected = sum(f['total_players_affected'] for f in fixture_summary.values())
        
        for fixture_data in fixture_summary.values():
            print(f"    {fixture_data['match']}: {fixture_data['total_players_affected']} players affected")
        
        print(f"  Total players with reduced points: {total_affected}")
        print(f"  Average reduction per player: {point_reduction} points")
    
    adjustment_summary = {
        'fixtures': fixture_summary,
        'individual_adjustments': adjustments,
        'total_players_affected': len(adjustments),
        'total_fixtures': len(fixture_summary)
    }
    
    return df_adjusted, adjustment_summary

def print_adjustment_analysis(adjustment_summary):
    """
    Print detailed analysis of the opposing teams adjustments
    """
    if not adjustment_summary or not adjustment_summary['fixtures']:
        print("No opposing teams adjustments applied")
        return
    
    print("\n" + "="*60)
    print("OPPOSING TEAMS POINTS ADJUSTMENT ANALYSIS")
    print("="*60)
    
    for fixture_data in adjustment_summary['fixtures'].values():
        print(f"📉 {fixture_data['match']}")
        print(f"   Players affected: {fixture_data['total_players_affected']}")
        print(f"   Points reduction: -{fixture_data['reduction_per_player']} per player")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total fixtures processed: {adjustment_summary['total_fixtures']}")
    print(f"   Total players affected: {adjustment_summary['total_players_affected']}")
    print(f"   This creates a more realistic expectation when teams play each other")
    
    print("="*60)

# Example usage
if __name__ == "__main__":
    # Test with sample data
    print("This module provides opposing teams adjustment functionality")
    print("Use apply_opposing_teams_adjustment() to reduce expected points for opposing players")
