# fpl_team_fetcher.py
# Fetch any FPL team using their team ID

import requests
import pandas as pd
from datetime import datetime

def get_team_info(team_id):
    """
    Get basic team information and current gameweek team
    """
    # Team overview endpoint
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error: Team ID {team_id} not found")
        return None
    
    data = response.json()
    
    # Handle potential None values for new teams or start of season
    team_value = data.get('last_deadline_value')
    bank_value = data.get('last_deadline_bank')
    
    team_info = {
        'id': data['id'],
        'team_name': data['name'],
        'player_name': f"{data['player_first_name']} {data['player_last_name']}",
        'overall_points': data.get('summary_overall_points'),  # Can be None before season starts
        'overall_rank': data.get('summary_overall_rank'),  # Can be None before season starts
        'team_value': team_value / 10 if team_value else 100.0,  # Default to 100m if None
        'bank': bank_value / 10 if bank_value else 0.0,  # Default to 0 if None
        'total_transfers': data.get('last_deadline_total_transfers', 0),
        'current_event': data.get('current_event', 1)
    }
    
    return team_info

def get_team_picks(team_id, gameweek=None):
    """
    Get the team's picks for a specific gameweek
    """
    # Get current gameweek if not specified
    if gameweek is None:
        bootstrap_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        bootstrap_data = requests.get(bootstrap_url).json()
        
        # Try to find current or next gameweek
        current_gw = next((e for e in bootstrap_data['events'] if e['is_current']), None)
        next_gw = next((e for e in bootstrap_data['events'] if e['is_next']), None)
        
        if current_gw:
            gameweek = current_gw['id']
            print(f"Fetching current gameweek: {gameweek}")
        elif next_gw:
            gameweek = next_gw['id']
            print(f"Season hasn't started. Next gameweek: {gameweek}")
            print("Note: Team picks may not be finalized yet")
        else:
            # Try the most recent finished gameweek
            finished = [e for e in bootstrap_data['events'] if e['finished']]
            if finished:
                gameweek = finished[-1]['id']
                print(f"Using most recent gameweek: {gameweek}")
            else:
                gameweek = 1
                print("Defaulting to gameweek 1")
    
    # Try to get team picks for the gameweek
    picks_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gameweek}/picks/"
    response = requests.get(picks_url)
    
    if response.status_code != 200:
        print(f"\nCould not fetch picks for gameweek {gameweek}")
        print("This might be because:")
        print("- The season hasn't started yet")
        print("- The team hasn't set their squad for this gameweek")
        print("- This is a new team without any picks yet")
        
        # Try to get the most recent gameweek with picks
        print("\nTrying to find a gameweek with picks...")
        for gw in range(min(gameweek, 38), 0, -1):
            test_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gw}/picks/"
            test_response = requests.get(test_url)
            if test_response.status_code == 200:
                print(f"Found picks for gameweek {gw}")
                return test_response.json()
        
        print("No picks found for any gameweek")
        return None
    
    return response.json()

def get_all_players():
    """
    Get all player data from FPL
    """
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)
    data = response.json()
    
    # Create player lookup dictionary
    players = {}
    for player in data['elements']:
        players[player['id']] = {
            'id': player['id'],
            'name': player['web_name'],
            'team': data['teams'][player['team'] - 1]['name'],
            'position': data['element_types'][player['element_type'] - 1]['singular_name'],
            'price': player['now_cost'] / 10,
            'selected_by': player['selected_by_percent'],
            'total_points': player['total_points'],
            'form': player['form'],
            'status': player['status']
        }
    
    return players

def fetch_fpl_team(team_id, gameweek=None):
    """
    Main function to fetch complete team data
    """
    print("="*60)
    print("FETCHING FPL TEAM DATA")
    print("="*60)
    
    # Get team info
    team_info = get_team_info(team_id)
    if not team_info:
        return None
    
    print(f"\nTeam: {team_info['team_name']}")
    print(f"Manager: {team_info['player_name']}")
    if team_info['overall_points'] is not None:
        print(f"Overall Points: {team_info['overall_points']}")
    if team_info['overall_rank'] is not None:
        print(f"Overall Rank: {team_info['overall_rank']:,}")
    print(f"Team Value: £{team_info['team_value']:.1f}m")
    print(f"Bank: £{team_info['bank']:.1f}m")
    
    # Get team picks
    picks_data = get_team_picks(team_id, gameweek)
    if not picks_data:
        return None
    
    # Get all players for lookup
    all_players = get_all_players()
    
    # Process picks
    squad = []
    for pick in picks_data['picks']:
        player_id = pick['element']
        player_info = all_players.get(player_id, {})
        
        squad.append({
            'id': player_id,
            'name': player_info.get('name', 'Unknown'),
            'position': player_info.get('position', 'Unknown'),
            'team': player_info.get('team', 'Unknown'),
            'price': player_info.get('price', 0),
            'is_captain': pick['is_captain'],
            'is_vice_captain': pick['is_vice_captain'],
            'multiplier': pick['multiplier'],
            'starting_xi': pick['position'] <= 11,
            'bench_order': pick['position'] - 11 if pick['position'] > 11 else 0,
            'total_points': player_info.get('total_points', 0),
            'form': player_info.get('form', 0),
            'selected_by': player_info.get('selected_by', 0)
        })
    
    # Create DataFrame
    df_squad = pd.DataFrame(squad)
    
    # Sort by starting XI first, then bench order
    df_squad = df_squad.sort_values(['starting_xi', 'bench_order'], ascending=[False, True])
    
    print(f"\n" + "="*60)
    print(f"GAMEWEEK {picks_data['event']['id']} SQUAD")
    print("="*60)
    
    # Display squad
    print("\nSTARTING XI:")
    print("-"*40)
    starting = df_squad[df_squad['starting_xi']]
    for _, player in starting.iterrows():
        captain_badge = " (C)" if player['is_captain'] else ""
        captain_badge = " (VC)" if player['is_vice_captain'] else captain_badge
        print(f"{player['name']:<20} {player['position']:<12} {player['team']:<15} £{player['price']:.1f}m{captain_badge}")
    
    print("\nBENCH:")
    print("-"*40)
    bench = df_squad[~df_squad['starting_xi']]
    for _, player in bench.iterrows():
        print(f"{player['bench_order']}. {player['name']:<18} {player['position']:<12} {player['team']:<15} £{player['price']:.1f}m")
    
    # Calculate totals
    total_value = df_squad['price'].sum()
    print(f"\nTotal Squad Value: £{total_value:.1f}m")
    print(f"Money in Bank: £{team_info['bank']:.1f}m")
    
    # Save to CSV
    filename = f"fpl_team_{team_id}_gw{picks_data['event']['id']}.csv"
    df_squad.to_csv(filename, index=False)
    print(f"\nTeam saved to: {filename}")
    
    return {
        'team_info': team_info,
        'squad': df_squad,
        'picks_data': picks_data,
        'gameweek': picks_data['event']['id']
    }

def fetch_team_history(team_id):
    """
    Get team's transfer history and past gameweeks
    """
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/history/"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error: Could not fetch history for team {team_id}")
        return None
    
    data = response.json()
    
    # Current season history
    if data.get('current') and len(data['current']) > 0:
        print("\nSEASON HISTORY:")
        print("-"*40)
        for gw in data['current'][-5:]:  # Last 5 gameweeks
            points = gw.get('points', 0)
            rank = gw.get('overall_rank')
            value = gw.get('value', 0)
            
            rank_str = f"{rank:,}" if rank else "N/A"
            print(f"GW{gw['event']}: {points} pts, Rank: {rank_str}, Value: £{value/10:.1f}m")
    else:
        print("\nNo gameweek history available yet (season hasn't started)")
    
    # Chips used
    if data.get('chips'):
        print("\nCHIPS USED:")
        for chip in data['chips']:
            print(f"- {chip['name']} (GW{chip['event']})")
    
    return data

# Example usage
if __name__ == "__main__":
    # You can find your team ID in the URL when viewing your team
    # e.g., https://fantasy.premierleague.com/entry/123456/event/21
    # The team ID would be 123456
    
    team_id = 2562804
    
    try:
        team_id = int(team_id)
        
        # Fetch current team
        result = fetch_fpl_team(team_id)
        
        if result:
            fetch_team_history(team_id)
            
    except ValueError:
        print("Invalid team ID. Please enter a number.")
    except Exception as e:
        print(f"Error: {e}")