# fpl_team_diagnostics.py
# Diagnostic tool to see all available data for an FPL team

import requests
import json
from datetime import datetime

def diagnose_team(team_id):
    """
    Check all available data for a team
    """
    print("="*60)
    print(f"FPL TEAM DIAGNOSTICS - Team ID: {team_id}")
    print("="*60)
    
    # 1. Basic team info
    print("\n1. BASIC TEAM INFO")
    print("-"*40)
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f" Team {team_id} not found")
        return
    
    data = response.json()
    
    # Print all available fields
    print(f"Team exists!")
    print(f"  Name: {data.get('name')}")
    print(f"  Manager: {data.get('player_first_name')} {data.get('player_last_name')}")
    print(f"  ID: {data.get('id')}")
    print(f"  Started Event: {data.get('started_event')}")
    print(f"  Current Event: {data.get('current_event')}")
    print(f"  Total Transfers: {data.get('last_deadline_total_transfers')}")
    
    print("\n  All available fields:")
    for key, value in data.items():
        if value is not None and value != 0 and value != "":
            print(f"    {key}: {value}")
    
    # 2. Check history
    print("\n2. TEAM HISTORY")
    print("-"*40)
    history_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/history/"
    history_response = requests.get(history_url)
    
    if history_response.status_code == 200:
        history_data = history_response.json()
        
        if history_data.get('current'):
            print(f" Has {len(history_data['current'])} gameweek(s) of history")
            for gw in history_data['current'][:3]:
                print(f"  GW{gw['event']}: {gw.get('points', 0)} points")
        else:
            print(" No gameweek history yet")
        
        if history_data.get('past'):
            print(f"Has {len(history_data['past'])} previous season(s)")
        else:
            print("✗ No previous seasons")
            
        if history_data.get('chips'):
            print(f" Has used {len(history_data['chips'])} chip(s)")
        else:
            print(" No chips used")
    else:
        print(" Could not fetch history")
    
    # 3. Check transfers
    print("\n3. TRANSFERS")
    print("-"*40)
    transfers_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/transfers/"
    transfers_response = requests.get(transfers_url)
    
    if transfers_response.status_code == 200:
        transfers = transfers_response.json()
        if transfers:
            print(f" Has {len(transfers)} transfer(s)")
            for t in transfers[:3]:
                print(f"  GW{t.get('event')}: Player {t.get('element_in')} in, {t.get('element_out')} out")
        else:
            print(" No transfers yet")
    else:
        print(" Could not fetch transfers")
    
    # 4. Try to get picks for different gameweeks
    print("\n4. SQUAD PICKS")
    print("-"*40)
    
    found_picks = False
    for gw in range(1, 39):  # Check all possible gameweeks
        picks_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gw}/picks/"
        picks_response = requests.get(picks_url)
        
        if picks_response.status_code == 200:
            if not found_picks:
                print(f" Found picks starting from GW{gw}")
                found_picks = True
            picks_data = picks_response.json()
            if picks_data.get('picks'):
                print(f"  GW{gw}: {len(picks_data['picks'])} players picked")
                if gw >= 3:  # Stop after showing a few
                    break
    
    if not found_picks:
        print(" No picks found for any gameweek")
        print("\nThis means:")
        print("- You haven't selected your initial squad yet, OR")
        print("- The season hasn't started and squads aren't locked in yet")
    
    # 5. Check current season status
    print("\n5. SEASON STATUS")
    print("-"*40)
    bootstrap_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    bootstrap_data = requests.get(bootstrap_url).json()
    
    current_gw = next((e for e in bootstrap_data['events'] if e['is_current']), None)
    next_gw = next((e for e in bootstrap_data['events'] if e['is_next']), None)
    
    if current_gw:
        print(f" Current gameweek: {current_gw['id']} - {current_gw['name']}")
        deadline = datetime.fromisoformat(current_gw['deadline_time'].replace('Z', '+00:00'))
        print(f"  Deadline: {deadline}")
    elif next_gw:
        print(f" Next gameweek: {next_gw['id']} - {next_gw['name']}")
        deadline = datetime.fromisoformat(next_gw['deadline_time'].replace('Z', '+00:00'))
        print(f"  Deadline: {deadline}")
        print("   Season hasn't started yet")
    else:
        print(" No active gameweek")
    
    print("\n" + "="*60)
    print("DIAGNOSIS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    team_id = 2562804  # Your team ID
    diagnose_team(team_id)