"""
Script to append FDR ratings to the existing fpl_players_gw_X.csv file.
Adds a new column with the average FDR for each team over the next N gameweeks.
"""

import pandas as pd
import requests
from datetime import datetime

def get_current_gameweek():
    """
    Get the current gameweek from FPL API
    """
    try:
        response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
        data = response.json()
        events = data['events']
        
        # Find current gameweek
        current_gw = next((e for e in events if e['is_current']), None)
        if current_gw:
            return current_gw['id']
        
        # If no current, find next
        next_gw = next((e for e in events if e['is_next']), None)
        if next_gw:
            return next_gw['id']
        
        # Fallback to first gameweek
        return 1
        
    except Exception as e:
        print(f"Error getting current gameweek: {e}")
        return 1

def get_team_fdr_ratings(start_gw=None, weeks=5):
    """
    Get FDR ratings for each team over the next N gameweeks
    
    Args:
        start_gw: Gameweek to start from (None = current/next GW)
        weeks: Number of gameweeks to look ahead
    """
    if start_gw is None:
        start_gw = get_current_gameweek()
        print(f"Using current gameweek: GW {start_gw}")
    else:
        print(f"Using specified gameweek: GW {start_gw}")
    
    print(f"Calculating FDR ratings from GW {start_gw} for {weeks} weeks...")
    
    try:
        # Fetch FPL data
        response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
        data = response.json()
        
        # Fetch fixtures
        fixtures_response = requests.get('https://fantasy.premierleague.com/api/fixtures/')
        fixtures = fixtures_response.json()
        
        # Get teams
        teams = {team['id']: team['name'] for team in data['teams']}
        
        end_gw = start_gw + weeks - 1
        team_fdrs = {}
        
        print(f"Analyzing fixtures GW {start_gw} to GW {end_gw}...")
        
        # Process fixtures for the specified period
        fixture_count = 0
        for fixture in fixtures:
            gw = fixture['event']
            if not gw or gw < start_gw or gw > end_gw:
                continue
                
            home_team = fixture['team_h']
            away_team = fixture['team_a']
            home_difficulty = fixture['team_h_difficulty']
            away_difficulty = fixture['team_a_difficulty']
            
            # Initialize if needed
            if home_team not in team_fdrs:
                team_fdrs[home_team] = []
            if away_team not in team_fdrs:
                team_fdrs[away_team] = []
                
            team_fdrs[home_team].append(home_difficulty)
            team_fdrs[away_team].append(away_difficulty)
            fixture_count += 1
        
        print(f"Processed {fixture_count} fixtures")
        
        # Calculate averages
        team_fdr_averages = {}
        for team_id, difficulties in team_fdrs.items():
            if difficulties:
                avg_fdr = sum(difficulties) / len(difficulties)
                team_fdr_averages[team_id] = round(avg_fdr, 2)
                print(f"  {teams[team_id]}: {avg_fdr:.2f} FDR ({len(difficulties)} fixtures)")
        
        return team_fdr_averages
        
    except Exception as e:
        print(f"Error fetching FDR data: {e}")
        return {}

def append_fdr_to_df(csv_path=None, start_gw=None, weeks=5, save_csv=False):
    """
    Add FDR column to the existing CSV file and return the DataFrame
    
    Args:
        csv_path: Path to CSV file (None = auto-detect based on gameweek)
        start_gw: Gameweek to start from (None = current)
        weeks: Number of gameweeks to look ahead
        save_csv: Whether to save the updated DataFrame to CSV (default: False)
    
    Returns:
        pandas.DataFrame: Updated DataFrame with FDR column
    """
    # Auto-detect CSV path if not provided
    if csv_path is None:
        if start_gw is None:
            start_gw = get_current_gameweek()
        csv_path = f'data/fpl_players_gw_{start_gw}.csv'
    
    print(f"\nLoading player data from {csv_path}...")
    
    try:
        # Load existing CSV
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} players")
        
        # Get FDR ratings
        team_fdr_ratings = get_team_fdr_ratings(start_gw, weeks)
        
        if not team_fdr_ratings:
            print("Failed to get FDR ratings")
            return None
        
        # Add FDR column
        fdr_column_name = f'team_fdr_{weeks}gw'
        df[fdr_column_name] = df['team_id'].map(team_fdr_ratings)
        
        # Check for any missing mappings
        missing_fdr = df[df[fdr_column_name].isna()]
        if len(missing_fdr) > 0:
            print(f"Warning: {len(missing_fdr)} players missing FDR ratings")
            # Use available columns for the warning
            available_cols = [col for col in ['name', 'web_name', 'team', 'team_id'] if col in df.columns]
            if available_cols:
                print(missing_fdr[available_cols].head())
        
        # Save updated CSV if requested
        if save_csv:
            output_path = csv_path.replace('.csv', f'_with_fdr_{weeks}gw.csv')
            df.to_csv(output_path, index=False)
            print(f"\nUpdated CSV saved to: {output_path}")
        
        print(f"Added FDR column: {fdr_column_name}")
        
        # Show sample of updated data - use available columns
        print("\nSample of updated data:")
        available_sample_cols = [col for col in ['name', 'web_name', 'team', 'expected_points', fdr_column_name] if col in df.columns]
        if available_sample_cols:
            print(df[available_sample_cols].head(10).to_string(index=False))
        
        # Show FDR distribution
        print(f"\nFDR Distribution:")
        fdr_summary = df.groupby(fdr_column_name).size().sort_index()
        for fdr, count in fdr_summary.items():
            try:
                if fdr is not None and str(fdr) != 'nan':
                    print(f"  FDR {fdr}: {count} players")
            except:
                continue
        
        return df
        
    except Exception as e:
        print(f"Error processing CSV: {e}")
        return None

if __name__ == "__main__":
    print("FPL FDR CSV Updater")
    print("=" * 50)
    
    # Configuration options
    START_GW = 4  # None = use current gameweek, or specify like 3, 4, etc.
    WEEKS_AHEAD = 5  # Number of gameweeks to look ahead
    CSV_PATH = 'data/fpl_players_gw_4.csv'  # None = auto-detect, or specify like 'data/fpl_players_gw_4.csv'
    SAVE_CSV = False  # Set to True if you want to save to CSV, False to just return DataFrame
    
    print(f"Configuration:")
    print(f"  Start GW: {START_GW if START_GW else 'Current'}")
    print(f"  Weeks ahead: {WEEKS_AHEAD}")
    print(f"  CSV path: {CSV_PATH if CSV_PATH else 'Auto-detect'}")
    print(f"  Save CSV: {SAVE_CSV}")
    print()
    
    # Update the DataFrame with FDR ratings
    updated_df = append_fdr_to_df(CSV_PATH, START_GW, WEEKS_AHEAD, SAVE_CSV)
    
    if updated_df is not None:
        updated_df.to_csv('data/fpl_players_gw_4.csv', index=False)
        print("\nFDR Analysis Complete!")
        print(f"DataFrame updated with FDR ratings for next {WEEKS_AHEAD} gameweeks")
        print(f"Shape: {updated_df.shape}")
        
        # You can now use the updated_df in your optimization code
        # For example:
        # optimization_model(updated_df)
        
    else:
        print("\nFailed to update DataFrame with FDR ratings")