# team.py
import requests
import pandas as pd

class Team:
    def __init__(self, team_id, budget=0.0, free_transfers=1):
        """
        Initialize Team from FPL API
        
        Args:
            team_id: FPL team ID
            budget: Current bank balance
            free_transfers: Number of free transfers available
        """
        self.team_id = team_id
        self.budget = budget
        self.free_transfers = free_transfers
        
        # Fetch data from API
        self._fetch_team_data()
    
    def _fetch_team_data(self):
        """Fetch team data from FPL API"""
        # Get bootstrap data (all players)
        bootstrap = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
        
        # Find current gameweek
        self.current_gw = next((e['id'] for e in bootstrap['events'] if e['is_current']), 
                              next((e['id'] for e in bootstrap['events'] if e['is_next']), 1))
        
        # Get team picks
        picks_resp = requests.get(f'https://fantasy.premierleague.com/api/entry/{self.team_id}/event/{self.current_gw}/picks/')
        
        if picks_resp.status_code != 200:
            raise ValueError(f"Could not fetch team {self.team_id}")
        
        picks_data = picks_resp.json()
        
        # Create player lookup
        players = {p['id']: p for p in bootstrap['elements']}
        
        # Build current team DataFrame
        team_data = []
        for pick in picks_data['picks']:
            player = players[pick['element']]
            team_data.append({
                'player_id': pick['element'],
                'name': player['web_name'],
                'position': ['GK', 'DEF', 'MID', 'FWD'][player['element_type'] - 1],
                'team': bootstrap['teams'][player['team'] - 1]['name'],
                'price': player['now_cost'] / 10,
                'is_starting': pick['position'] <= 11,
                'expected_points': player.get('points', 0),
            })
        
        self.current_team = pd.DataFrame(team_data)
        
        # Create ID sets
        self.starting_ids = set(self.current_team[self.current_team['is_starting']]['player_id'].tolist())
        self.bench_ids = set(self.current_team[~self.current_team['is_starting']]['player_id'].tolist())
        self.all_ids = self.starting_ids | self.bench_ids
        
        # Calculate team value
        self.team_value = self.current_team['price'].sum()
    
    def is_in_starting(self, player_id):
        """Check if player is in starting XI"""
        return player_id in self.starting_ids
    
    def is_on_bench(self, player_id):
        """Check if player is on bench"""
        return player_id in self.bench_ids
    
    def is_in_team(self, player_id):
        """Check if player is in team at all"""
        return player_id in self.all_ids
    
    def get_squad_by_position(self):
        """Get squad grouped by position"""
        return self.current_team.groupby('position').agg({
            'player_id': 'count',
            'price': 'sum'
        }).rename(columns={'player_id': 'count', 'price': 'total_cost'})
    
    def __repr__(self):
        return (f"Team(id={self.team_id}, "
                f"squad_size={len(self.current_team)}, "
                f"starting={len(self.starting_ids)}, "
                f"bench={len(self.bench_ids)}, "
                f"free_transfers={self.free_transfers}, "
                f"budget={self.budget:.1f})")


# Example usage
if __name__ == "__main__":
    # Create team from API
    my_team = Team(team_id=2562804, budget=2.5, free_transfers=1)
    
    print(my_team)
    print("\nStarting XI IDs:", my_team.starting_ids)
    print("\nSquad by position:")
    print(my_team.get_squad_by_position())
    
    # Check specific player
    player_id = 357  # Example player ID
    if my_team.is_in_team(player_id):
        print(f"\nPlayer {player_id} is in the team")
        if my_team.is_in_starting(player_id):
            print("  - In starting XI")
        else:
            print("  - On bench")