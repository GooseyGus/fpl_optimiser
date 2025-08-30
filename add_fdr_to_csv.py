#!/usr/bin/env python3
"""
Script to append FDR ratings to the existing fpl_players_gw_3.csv file.
Adds a new column with the average FDR for each team over the next 5 gameweeks.
"""

import pandas as pd
import requests

def get_team_fdr_ratings(start_gw=3, weeks=5):
    """
    Get FDR ratings for each team over the next 5 gameweeks
    """
    print(f"🎯 Calculating FDR ratings from GW {start_gw} for {weeks} weeks...")
    
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
        
        # Process fixtures for the specified period
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
        
        # Calculate averages
        team_fdr_averages = {}
        for team_id, difficulties in team_fdrs.items():
            if difficulties:
                avg_fdr = sum(difficulties) / len(difficulties)
                team_fdr_averages[team_id] = round(avg_fdr, 2)
                print(f"  {teams[team_id]}: {avg_fdr:.2f} FDR ({len(difficulties)} fixtures)")
        
        return team_fdr_averages
        
    except Exception as e:
        print(f"❌ Error fetching FDR data: {e}")
        return {}

def append_fdr_to_csv(csv_path='data/fpl_players_gw_3.csv'):
    """
    Add FDR column to the existing CSV file
    """
    print(f"\n📊 Loading player data from {csv_path}...")
    
    try:
        # Load existing CSV
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} players")
        
        # Get FDR ratings
        team_fdr_ratings = get_team_fdr_ratings()
        
        if not team_fdr_ratings:
            print("❌ Failed to get FDR ratings")
            return
        
        # Add FDR column
        df['team_fdr_5gw'] = df['team_id'].map(team_fdr_ratings)
        
        # Check for any missing mappings
        missing_fdr = df[df['team_fdr_5gw'].isna()]
        if len(missing_fdr) > 0:
            print(f"⚠️  Warning: {len(missing_fdr)} players missing FDR ratings")
            print(missing_fdr[['web_name', 'team', 'team_id']].head())
        
        # Save updated CSV
        output_path = csv_path.replace('.csv', '_with_fdr.csv')
        df.to_csv(output_path, index=False)
        
        print(f"\n✅ Updated CSV saved to: {output_path}")
        print(f"Added FDR column: team_fdr_5gw")
        
        # Show sample of updated data
        print("\n📋 Sample of updated data:")
        sample_cols = ['web_name', 'team', 'expected_points', 'team_fdr_5gw']
        print(df[sample_cols].head(10).to_string(index=False))
        
        # Show FDR distribution
        print(f"\n📈 FDR Distribution:")
        fdr_summary = df.groupby('team_fdr_5gw').size().sort_index()
        for fdr, count in fdr_summary.items():
            try:
                if fdr is not None and str(fdr) != 'nan':
                    print(f"  FDR {fdr}: {count} players")
            except:
                continue
        
        return df
        
    except Exception as e:
        print(f"❌ Error processing CSV: {e}")
        return None

if __name__ == "__main__":
    print("🏈 FPL FDR CSV Updater")
    print("=" * 50)
    
    # Update the CSV with FDR ratings
    updated_df = append_fdr_to_csv()
    
    if updated_df is not None:
        print("\n🎯 FDR Analysis Complete!")
        print("New file created with FDR ratings for next 5 gameweeks")
    else:
        print("\n❌ Failed to update CSV with FDR ratings")
