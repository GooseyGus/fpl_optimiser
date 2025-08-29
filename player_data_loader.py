# data_loader.py
# Load and process FPL data from the API

import requests
import pandas as pd
from datetime import datetime

def load_fpl_data():
    """
    Load FPL data from the API including player status/news, gameweek info, and fixtures
    """
    # Fetch FPL data
    response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
    data = response.json()
    
    # Fetch fixture data
    fixtures_response = requests.get('https://fantasy.premierleague.com/api/fixtures/')
    fixtures = fixtures_response.json()
    
    # Extract the data we need
    players = data['elements']
    teams = data['teams']
    positions = data['element_types']
    events = data['events']
    
    # Get gameweek info
    current_gw = next((e for e in events if e['is_current']), None)
    next_gw = next((e for e in events if e['is_next']), None)
    
    # Print gameweek context
    print("="*60)
    print("FPL DATA CONTEXT")
    print("="*60)
    if current_gw:
        print(f"Current Gameweek: {current_gw['id']} - {current_gw['name']}")
    if next_gw:
        print(f"Next Gameweek: {next_gw['id']} - {next_gw['name']}")
        deadline = datetime.fromisoformat(next_gw['deadline_time'].replace('Z', '+00:00'))
        print(f"Next Deadline: {deadline.strftime('%a %d %b %Y at %H:%M')}")
    print("="*60 + "\n")
    
    # Create lookup dictionaries
    team_dict = {team['id']: team['name'] for team in teams}
    position_dict = {pos['id']: pos['singular_name'] for pos in positions}
    
    # Process fixtures for next gameweek
    opponent_dict = {}  # team_id -> opponent_team_id
    if next_gw:
        next_gw_fixtures = [f for f in fixtures if f['event'] == next_gw['id']]
        print(f"Processing {len(next_gw_fixtures)} fixtures for GW {next_gw['id']}:")
        
        for fixture in next_gw_fixtures:
            home_team = fixture['team_h']
            away_team = fixture['team_a']
            home_name = team_dict.get(home_team, f"Team {home_team}")
            away_name = team_dict.get(away_team, f"Team {away_team}")
            
            # Map each team to their opponent
            opponent_dict[home_team] = away_team
            opponent_dict[away_team] = home_team
            
            print(f"  {home_name} vs {away_name}")
        
        print()  # Add blank line after fixtures
    
    # Create DataFrame with all relevant fields
    df_players = pd.DataFrame([{
        'id': player['id'],
        'name': player['web_name'],
        'position': position_dict[player['element_type']],
        'team': team_dict[player['team']],
        'team_id': player['team'],
        'opponent_id': opponent_dict.get(player['team']),
        'opponent': team_dict.get(opponent_dict.get(player['team']), 'No fixture') if opponent_dict.get(player['team']) else 'No fixture',
        'price': player['now_cost'] / 10,
        'expected_points': player['ep_next'],
        'selected_by_percent': player['selected_by_percent'],
        'status': player['status'],  # a=available, i=injured, s=suspended, u=unavailable
        'gameweek': next_gw['id'] if next_gw else None,  # Add gameweek to each row
        'minutes': player.get('minutes', 0),  # Add minutes played
    } for player in players])
            
    return df_players

def save_fpl_data(df_players, base_path='data/'):
    """
    Save FPL data to CSV with gameweek in filename
    """
    gw = df_players['gameweek'].iloc[0] if 'gameweek' in df_players.columns else 'unknown'
    filename = f"{base_path}fpl_players_gw_{gw}.csv"
    df_players.to_csv(filename, index=False)
    print(f"\nSaved to: {filename}")
    return filename

# Example usage
if __name__ == "__main__":
    df_players = load_fpl_data()
    # Save to CSV with gameweek in filename
    save_fpl_data(df_players)