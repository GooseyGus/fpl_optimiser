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
    
    def calculate_team_value_from_df(self, df_players):
        """
        Calculate team's current worth using player data from a DataFrame
        
        Args:
            df_players: DataFrame containing player data with 'player_id' and 'price' columns
            
        Returns:
            float: Total team value
        """
        # Create a lookup dictionary for quick price retrieval
        price_lookup = df_players.set_index('id')['price'].to_dict()
        
        # Calculate total value
        total_value = 0
        missing_players = []
        
        for player_id in self.all_ids:
            if player_id in price_lookup:
                total_value += price_lookup[player_id]
            else:
                missing_players.append(player_id)
        
        if missing_players:
            print(f"Warning: Could not find prices for player IDs: {missing_players}")
        
        return total_value
    
    def get_team_breakdown_from_df(self, df_players):
        """
        Get detailed breakdown of team value using DataFrame prices
        
        Args:
            df_players: DataFrame containing player data
            
        Returns:
            pd.DataFrame: Team breakdown with current prices from DataFrame
        """
        # Merge current team with DataFrame prices
        team_with_current_prices = self.current_team.merge(
            df_players[['id', 'price']].rename(columns={'price': 'current_price'}),
            on='id',
            how='left'
        )
        
        # Calculate price differences if original price exists
        if 'price' in team_with_current_prices.columns:
            team_with_current_prices['price_change'] = (
                team_with_current_prices['current_price'] - team_with_current_prices['price']
            )
        
        return team_with_current_prices
    
    def explore_team_api_data(self):
        """
        Comprehensive exploration of team API data including financial breakdown
        
        Returns:
            dict: Complete team financial breakdown
        """
        # Get team picks data
        picks_resp = requests.get(f'https://fantasy.premierleague.com/api/entry/{self.team_id}/event/{self.current_gw}/picks/')
        
        if picks_resp.status_code != 200:
            raise ValueError(f"Could not fetch team {self.team_id}")
        
        picks_data = picks_resp.json()
        
        # Get team general info
        team_resp = requests.get(f'https://fantasy.premierleague.com/api/entry/{self.team_id}/')
        team_info = team_resp.json() if team_resp.status_code == 200 else {}
        
        # Get bootstrap data for current prices
        bootstrap = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
        players = {p['id']: p for p in bootstrap['elements']}
        teams = {t['id']: t for t in bootstrap['teams']}
        
        print("=== FPL TEAM FINANCIAL BREAKDOWN ===\n")
        
        # Bank balance
        bank_balance = picks_data['entry_history']['bank'] / 10
        print(f"💰 Bank Balance: £{bank_balance:.1f}m")
        
        # Team value calculations
        total_current_value = 0
        
        detailed_breakdown = []
        
        for pick in picks_data['picks']:
            player = players[pick['element']]
            team_name = teams[player['team']]['short_name']
            
            # Current market value
            current_price = player['now_cost'] / 10
            
            # Player form and stats
            form = float(player.get('form', 0))
            total_points = player.get('total_points', 0)
            selected_by_percent = float(player.get('selected_by_percent', 0))
            
            player_info = {
                'name': player['web_name'],
                'team': team_name,
                'position': ['GK', 'DEF', 'MID', 'FWD'][player['element_type'] - 1],
                'current_price': current_price,
                'total_points': total_points,
                'form': form,
                'selected_by_percent': selected_by_percent,
                'is_starting': pick['position'] <= 11,
                'multiplier': pick['multiplier'],  # Captain info
                'position_order': pick['position']
            }
            
            detailed_breakdown.append(player_info)
            total_current_value += current_price
        
        # Sort by team position (starting XI first, then bench)
        detailed_breakdown.sort(key=lambda x: x['position_order'])
        
        # Display detailed breakdown
        print(f"\n{'Player':<15} {'Team':<4} {'Pos':<3} {'Price':<6} {'Pts':<4} {'Form':<5} {'Own%':<5} {'Status'}")
        print("-" * 75)
        
        for player in detailed_breakdown:
            if player['position_order'] <= 11:
                status = "XI"
                if player['multiplier'] == 2:
                    status += " ©"  # Captain
                elif player['multiplier'] == 3:
                    status += " ⓥ"  # Vice-captain
            else:
                status = f"B{player['position_order'] - 11}"  # Bench position
            
            print(f"{player['name']:<15} {player['team']:<4} {player['position']:<3} "
                  f"£{player['current_price']:<5.1f} {player['total_points']:<4} "
                  f"{player['form']:<5.1f} {player['selected_by_percent']:<5.1f} {status}")
        
        # Team summary
        team_value_with_bank = total_current_value + bank_balance
        
        print("\n" + "=" * 50)
        print("💼 TEAM SUMMARY:")
        print(f"   Squad Value:            £{total_current_value:.1f}m")
        print(f"   Bank Balance:           £{bank_balance:.1f}m")
        print(f"   Total Team Value:       £{team_value_with_bank:.1f}m")
        print(f"   Free Transfers:         {self.free_transfers}")
        print(f"   Current Gameweek:       {self.current_gw}")
        
        # Team performance insights
        starting_xi = [p for p in detailed_breakdown if p['position_order'] <= 11]
        avg_form = sum(p['form'] for p in starting_xi) / len(starting_xi)
        total_points = sum(p['total_points'] for p in starting_xi)
        
        print(f"\n📊 PERFORMANCE INSIGHTS:")
        print(f"   Starting XI Total Points: {total_points}")
        print(f"   Average Form (Starting):  {avg_form:.2f}")
        
        # Position breakdown
        pos_breakdown = {}
        for player in starting_xi:
            pos = player['position']
            if pos not in pos_breakdown:
                pos_breakdown[pos] = {'count': 0, 'value': 0, 'points': 0}
            pos_breakdown[pos]['count'] += 1
            pos_breakdown[pos]['value'] += player['current_price']
            pos_breakdown[pos]['points'] += player['total_points']
        
        print(f"\n🔍 POSITION BREAKDOWN (Starting XI):")
        for pos in ['GK', 'DEF', 'MID', 'FWD']:
            if pos in pos_breakdown:
                data = pos_breakdown[pos]
                print(f"   {pos}: {data['count']} players, £{data['value']:.1f}m, {data['points']} pts")
        
        # Find expensive players and underperformers
        expensive_players = [p for p in starting_xi if p['current_price'] >= 8.0]
        if expensive_players:
            print(f"\n� PREMIUM PLAYERS (£8.0m+):")
            for player in expensive_players:
                points_per_million = player['total_points'] / player['current_price']
                print(f"   {player['name']}: £{player['current_price']:.1f}m, {player['total_points']} pts ({points_per_million:.1f} pts/£m)")
        
        return {
            'bank_balance': bank_balance,
            'total_current_value': total_current_value,
            'total_team_value': team_value_with_bank,
            'free_transfers': self.free_transfers,
            'current_gameweek': self.current_gw,
            'detailed_breakdown': detailed_breakdown,
            'starting_xi_points': total_points,
            'average_form': avg_form
        }
    
    def get_actual_team_value(self):
        """
        Get the current market value of all players plus bank balance
        
        Returns:
            float: Total current team value including bank
        """
        picks_resp = requests.get(f'https://fantasy.premierleague.com/api/entry/{self.team_id}/event/{self.current_gw}/picks/')
        
        if picks_resp.status_code != 200:
            raise ValueError(f"Could not fetch team {self.team_id}")
        
        picks_data = picks_resp.json()
        
        # Get bootstrap data for current prices
        bootstrap = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
        players = {p['id']: p for p in bootstrap['elements']}
        
        total_squad_value = sum(players[pick['element']]['now_cost'] / 10 for pick in picks_data['picks'])
        bank_balance = picks_data['entry_history']['bank'] / 10
        
        return total_squad_value + bank_balance
    
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
    
    # Explore team API data with comprehensive breakdown
    print("\n" + "="*60)
    team_breakdown = my_team.explore_team_api_data()
    
    # Quick comparison of different valuation methods
    print(f"\nQUICK COMPARISON:")
    print(f"Squad Value (API):    £{my_team.team_value:.1f}m")
    print(f"Total Value (+ Bank): £{my_team.get_actual_team_value():.1f}m")
    
    # Example: Calculate team value from DataFrame (commented out)
    # df_players_gw3 = pd.read_csv('data/fpl_players_gw_3.csv')
    # current_team_value = my_team.calculate_team_value_from_df(df_players_gw3)
    # print(f"Team value from GW3 data: £{current_team_value:.1f}m")