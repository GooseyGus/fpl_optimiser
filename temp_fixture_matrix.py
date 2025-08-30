#!/usr/bin/env python3
"""
Temporary script to load fixture matrix for the rest of the FPL season.
Each column represents a gameweek, showing which teams play and their opponents.
Handles double gameweeks (teams playing twice) and blank gameweeks (teams not playing).
"""

import requests
import pandas as pd
from datetime import datetime

def load_fixture_matrix():
    """
    Load and display the fixture matrix for the rest of the season
    """
    print("🏈 Loading FPL Fixture Matrix for Rest of Season")
    print("=" * 60)
    
    try:
        # Fetch FPL data
        print("Fetching FPL data...")
        response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
        data = response.json()
        
        # Fetch fixtures
        fixtures_response = requests.get('https://fantasy.premierleague.com/api/fixtures/')
        fixtures = fixtures_response.json()
        
        # Get teams and gameweeks
        teams = {team['id']: team['name'] for team in data['teams']}
        events = data['events']
        
        # Find current gameweek
        current_gw = next((e['id'] for e in events if e['is_current']), 1)
        print(f"Current Gameweek: {current_gw}")
        
        # Get all remaining gameweeks
        remaining_gws = [e['id'] for e in events if e['id'] >= current_gw and not e['finished']]
        print(f"Remaining Gameweeks: {min(remaining_gws)} to {max(remaining_gws)} ({len(remaining_gws)} weeks)")
        print()
        
        # Build fixture matrix
        fixture_matrix = {}
        
        # Initialize matrix - each team for each remaining gameweek
        for team_id in teams.keys():
            fixture_matrix[team_id] = {gw: [] for gw in remaining_gws}
        
        # Process fixtures
        future_fixtures = [f for f in fixtures if f['event'] and f['event'] in remaining_gws]
        print(f"Processing {len(future_fixtures)} remaining fixtures...")
        
        for fixture in future_fixtures:
            gw = fixture['event']
            home_team = fixture['team_h']
            away_team = fixture['team_a']
            
            # Add opponents to matrix
            fixture_matrix[home_team][gw].append(f"vs {teams[away_team]} (H)")
            fixture_matrix[away_team][gw].append(f"vs {teams[home_team]} (A)")
        
        # Create DataFrame for display
        matrix_data = []
        for team_id, team_name in teams.items():
            row = {'Team': team_name}
            for gw in remaining_gws:
                fixtures = fixture_matrix[team_id][gw]
                if len(fixtures) == 0:
                    row[f'GW{gw}'] = "BLANK"
                elif len(fixtures) == 1:
                    row[f'GW{gw}'] = fixtures[0]
                else:
                    # Double gameweek
                    row[f'GW{gw}'] = f"DGW: {' & '.join(fixtures)}"
            matrix_data.append(row)
        
        df = pd.DataFrame(matrix_data)
        
        # Display results
        print("\n🗓️  FIXTURE MATRIX")
        print("=" * 80)
        print("Legend: H=Home, A=Away, DGW=Double Gameweek, BLANK=No fixture")
        print("=" * 80)
        
        # Set display options for better formatting
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 25)
        
        print(df.to_string(index=False))
        
        # Summary statistics
        print("\n📊 FIXTURE SUMMARY")
        print("=" * 40)
        
        for gw in remaining_gws:
            gw_col = f'GW{gw}'
            blanks = df[gw_col].str.contains('BLANK').sum()
            doubles = df[gw_col].str.contains('DGW').sum()
            singles = len(df) - blanks - doubles
            
            print(f"GW {gw:2d}: {singles:2d} single, {doubles:2d} double, {blanks:2d} blank")
        
        # Find teams with most double gameweeks
        print("\n🔥 DOUBLE GAMEWEEK CHAMPIONS")
        print("=" * 40)
        dgw_counts = {}
        for _, row in df.iterrows():
            team = row['Team']
            dgw_count = sum(1 for gw in remaining_gws if 'DGW' in row[f'GW{gw}'])
            dgw_counts[team] = dgw_count
        
        sorted_dgw = sorted(dgw_counts.items(), key=lambda x: x[1], reverse=True)
        for team, count in sorted_dgw[:10]:
            if count > 0:
                print(f"{team}: {count} double gameweeks")
        
        # Find teams with most blank gameweeks
        print("\n😴 BLANK GAMEWEEK VICTIMS")
        print("=" * 40)
        blank_counts = {}
        for _, row in df.iterrows():
            team = row['Team']
            blank_count = sum(1 for gw in remaining_gws if 'BLANK' in row[f'GW{gw}'])
            blank_counts[team] = blank_count
        
        sorted_blanks = sorted(blank_counts.items(), key=lambda x: x[1], reverse=True)
        for team, count in sorted_blanks[:10]:
            if count > 0:
                print(f"{team}: {count} blank gameweeks")
        
        # Save to CSV
        filename = f"fixture_matrix_gw{current_gw}_onwards.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 Saved fixture matrix to: {filename}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error loading fixture matrix: {e}")
        return None

def analyze_gameweek_patterns():
    """
    Analyze patterns in gameweek scheduling
    """
    print("\n🔍 ANALYZING GAMEWEEK PATTERNS")
    print("=" * 50)
    
    try:
        fixtures_response = requests.get('https://fantasy.premierleague.com/api/fixtures/')
        fixtures = fixtures_response.json()
        
        # Group fixtures by gameweek
        gw_fixture_counts = {}
        for fixture in fixtures:
            gw = fixture['event']
            if gw:
                gw_fixture_counts[gw] = gw_fixture_counts.get(gw, 0) + 1
        
        print("Fixtures per gameweek:")
        for gw in sorted(gw_fixture_counts.keys()):
            count = gw_fixture_counts[gw]
            teams_playing = count * 2
            teams_blank = 20 - teams_playing
            
            status = ""
            if teams_blank > 0:
                status += f"({teams_blank} teams blank)"
            if teams_playing > 20:
                status += f"(Double gameweek detected!)"
            
            print(f"GW {gw:2d}: {count:2d} fixtures, {teams_playing:2d} teams playing {status}")
            
    except Exception as e:
        print(f"Error analyzing patterns: {e}")

if __name__ == "__main__":
    # Load and display fixture matrix
    fixture_df = load_fixture_matrix()
    
    # Optional: analyze patterns
    print("\n" + "=" * 80)
    analyze_gameweek_patterns()
    
    print("\n✅ Fixture matrix analysis complete!")
