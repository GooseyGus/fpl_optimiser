"""
fdr.py
FDR (Fixture Difficulty Rating) module for FPL optimization
Calculates FDR-based penalties and bonuses for the objective function
"""

import requests
import pandas as pd
from pulp import lpSum

class FDRCalculator:
    """Calculate FDR ratings and penalties for optimization"""
    
    def __init__(self, start_gw=None, weeks=5):
        """
        Initialize FDR calculator
        
        Args:
            start_gw (int): Starting gameweek (default: current GW)
            weeks (int): Number of weeks to analyze (default: 5)
        """
        self.start_gw = start_gw
        self.weeks = weeks
        self.team_fdr_ratings = {}
        self.current_gw = None
        
    def fetch_fdr_data(self):
        """Fetch FDR data from FPL API"""
        try:
            # Get bootstrap data for current gameweek
            response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
            data = response.json()
            
            # Get current gameweek
            events = data['events']
            self.current_gw = next((gw['id'] for gw in events if gw['is_current']), 1)
            
            if self.start_gw is None:
                self.start_gw = self.current_gw
            
            # Get teams
            teams = {team['id']: team['name'] for team in data['teams']}
            
            # Get fixtures
            fixtures_response = requests.get('https://fantasy.premierleague.com/api/fixtures/')
            fixtures = fixtures_response.json()
            
            # Calculate FDR ratings
            self.team_fdr_ratings = self._calculate_team_fdr(fixtures, teams)
            
            return True
            
        except Exception as e:
            print(f"Error fetching FDR data: {e}")
            return False
    
    def _calculate_team_fdr(self, fixtures, teams):
        """Calculate average FDR for each team over the specified period"""
        if self.start_gw is None:
            return {}
            
        end_gw = self.start_gw + self.weeks - 1
        team_fdrs = {}
        
        # Collect FDR ratings for each team
        for fixture in fixtures:
            gw = fixture['event']
            if not gw or gw < self.start_gw or gw > end_gw:
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
        
        return team_fdr_averages
    
    def get_fdr_multiplier(self, team_id):
        """
        Get FDR multiplier for a team
        Lower FDR = easier fixtures = positive multiplier
        Higher FDR = harder fixtures = negative multiplier
        """
        if team_id not in self.team_fdr_ratings:
            return 0.0  # Neutral if no FDR data
        
        fdr = self.team_fdr_ratings[team_id]
        
        # Convert FDR to multiplier (inverted scale)
        # FDR 1.0 = +2.0 bonus, FDR 5.0 = -2.0 penalty
        # Linear scale: multiplier = 3.0 - fdr
        multiplier = 3.0 - fdr
        
        # Cap the multiplier between -2.0 and +2.0
        return max(-2.0, min(2.0, multiplier))
    
    def get_fdr_penalty_points(self, team_id, base_points=1.0):
        """
        Get FDR penalty/bonus points for a team
        
        Args:
            team_id (int): Team ID
            base_points (float): Base penalty points to scale
            
        Returns:
            float: Penalty points (negative = penalty, positive = bonus)
        """
        multiplier = self.get_fdr_multiplier(team_id)
        return multiplier * base_points


def add_fdr_penalty_to_objective(prob, df_players, vars, fdr_calculator, base_penalty=0.5):
    """
    Add FDR-based penalties/bonuses to the objective function
    
    Args:
        prob: PuLP problem instance
        df_players: DataFrame with player data
        vars: Dictionary of decision variables
        fdr_calculator: FDRCalculator instance
        base_penalty: Base penalty points for FDR scaling
        
    Returns:
        list: FDR penalty terms for the objective function
    """
    if not fdr_calculator.team_fdr_ratings:
        print("Warning: No FDR data available")
        return []
    
    fdr_terms = []
    
    # Apply FDR penalty/bonus to all starting players
    for var_type in ['stay_starting', 'bench_to_starting', 'in_to_starting_free', 'in_to_starting_paid']:
        if var_type in vars:
            for idx, var in vars[var_type].items():
                if idx in df_players.index:
                    team_id = df_players.loc[idx, 'team_id']
                    fdr_penalty = fdr_calculator.get_fdr_penalty_points(team_id, base_penalty)
                    
                    # Add FDR term (positive for good fixtures, negative for bad)
                    fdr_terms.append(fdr_penalty * var)
    
    return fdr_terms


def create_fdr_calculator(start_gw=None, weeks=5):
    """
    Create and initialize an FDR calculator
    
    Args:
        start_gw (int): Starting gameweek
        weeks (int): Number of weeks to analyze
        
    Returns:
        FDRCalculator: Initialized calculator or None if failed
    """
    calculator = FDRCalculator(start_gw, weeks)
    
    if calculator.fetch_fdr_data():
        end_gw = calculator.start_gw + weeks - 1 if calculator.start_gw else "?"
        print(f"✅ FDR data loaded for GW {calculator.start_gw}-{end_gw}")
        
        # Show FDR summary
        if calculator.team_fdr_ratings:
            sorted_teams = sorted(calculator.team_fdr_ratings.items(), key=lambda x: x[1])
            print("\n📊 FDR Rankings (Lower = Easier):")
            for i, (team_id, fdr) in enumerate(sorted_teams[:5]):
                multiplier = calculator.get_fdr_multiplier(team_id)
                print(f"  {i+1}. Team {team_id}: {fdr:.2f} FDR ({multiplier:+.1f} bonus)")
            
            print("  ...")
            for i, (team_id, fdr) in enumerate(sorted_teams[-3:]):
                multiplier = calculator.get_fdr_multiplier(team_id)
                print(f"  {len(sorted_teams)-2+i}. Team {team_id}: {fdr:.2f} FDR ({multiplier:+.1f} penalty)")
        
        return calculator
    else:
        print("❌ Failed to load FDR data")
        return None


def get_team_fdr_from_csv(csv_path='data/fpl_players_gw_3_with_fdr.csv'):
    """
    Get team FDR ratings from the CSV file we created earlier
    
    Args:
        csv_path (str): Path to CSV with FDR data
        
    Returns:
        dict: Mapping of team_id to FDR rating
    """
    try:
        df = pd.read_csv(csv_path)
        team_fdr_map = df[['team_id', 'team_fdr_5gw']].drop_duplicates().set_index('team_id')['team_fdr_5gw'].to_dict()
        
        print(f"✅ Loaded FDR data from CSV for {len(team_fdr_map)} teams")
        return team_fdr_map
        
    except Exception as e:
        print(f"❌ Error loading FDR from CSV: {e}")
        return {}


class CSVFDRCalculator:
    """FDR Calculator that uses pre-calculated CSV data"""
    
    def __init__(self, csv_path='data/fpl_players_gw_3_with_fdr.csv'):
        self.team_fdr_ratings = get_team_fdr_from_csv(csv_path)
        
    def get_fdr_multiplier(self, team_id):
        """Get FDR multiplier for a team"""
        if team_id not in self.team_fdr_ratings:
            return 0.0
        
        fdr = self.team_fdr_ratings[team_id]
        multiplier = 3.0 - fdr
        return max(-2.0, min(2.0, multiplier))
    
    def get_fdr_penalty_points(self, team_id, base_points=1.0):
        """Get FDR penalty/bonus points for a team"""
        multiplier = self.get_fdr_multiplier(team_id)
        return multiplier * base_points
