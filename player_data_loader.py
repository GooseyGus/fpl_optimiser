# data_loader.py
# Load and process FPL data from the API

import requests
import pandas as pd
from datetime import datetime

def load_fpl_data(gameweek=None):
    """
    Load FPL data from the API for current or specific gameweek
    
    Args:
        gameweek: Specific gameweek to load (None for current/next)
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
    target_gw = next((e for e in events if e['id'] == gameweek), None) if gameweek else next_gw
    
    # Print gameweek context
    print("="*60)
    print("FPL DATA CONTEXT")
    print("="*60)
    if current_gw:
        print(f"Current Gameweek: {current_gw['id']} - {current_gw['name']}")
    if target_gw:
        print(f"Target Gameweek: {target_gw['id']} - {target_gw['name']}")
        deadline = datetime.fromisoformat(target_gw['deadline_time'].replace('Z', '+00:00'))
        print(f"Deadline: {deadline.strftime('%a %d %b %Y at %H:%M')}")
    print("="*60 + "\n")
    
    # Create lookup dictionaries
    team_dict = {team['id']: team['name'] for team in teams}
    position_dict = {pos['id']: pos['singular_name'] for pos in positions}
    
    # Process fixtures for target gameweek
    opponent_dict = {}  # team_id -> opponent_team_id
    if target_gw:
        target_gw_fixtures = [f for f in fixtures if f['event'] == target_gw['id']]
        print(f"Processing {len(target_gw_fixtures)} fixtures for GW {target_gw['id']}:")
        
        for fixture in target_gw_fixtures:
            home_team = fixture['team_h']
            away_team = fixture['team_a']
            home_name = team_dict.get(home_team, f"Team {home_team}")
            away_name = team_dict.get(away_team, f"Team {away_team}")
            
            # Map each team to their opponent
            opponent_dict[home_team] = away_team
            opponent_dict[away_team] = home_team
            
            print(f"  {home_name} vs {away_name}")
        
        print()  # Add blank line after fixtures
    
    # If fetching historical data, get player stats for that gameweek
    if gameweek and gameweek < (current_gw['id'] if current_gw else 100):
        print(f"Fetching historical data for Gameweek {gameweek}...")
        
        # Get gameweek event status with player stats for that week
        gw_data_response = requests.get(f'https://fantasy.premierleague.com/api/event/{gameweek}/live/')
        gw_data = gw_data_response.json()
        
        # Create a lookup for player stats in that gameweek
        player_gw_stats = {p['id']: p['stats'] for p in gw_data['elements']}
        
        # Update player data with historical stats
        for player in players:
            player_id = player['id']
            if player_id in player_gw_stats:
                stats = player_gw_stats[player_id]
                player['gw_minutes'] = stats.get('minutes', 0)
                player['gw_points'] = stats.get('total_points', 0)
    
    # Create DataFrame with all relevant fields - KEEPING ALL ORIGINAL FIELDS
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
        'gameweek': target_gw['id'] if target_gw else None,
        'minutes': player.get('gw_minutes', player.get('minutes', 0)),
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
    #df_players = load_fpl_data()
    # Save to CSV with gameweek in filename
    #save_fpl_data(df_players)

    # Get data for Gameweek 5
    df_gw5 = load_fpl_data(gameweek=5)
    save_fpl_data(df_gw5, base_path='data/')


