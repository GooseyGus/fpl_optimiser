# output_window_updated.py
# Display squad results with transfer information

import pandas as pd
import tkinter as tk
from tkinter import ttk, scrolledtext
from pulp import LpStatus, value
import os

def display_in_window(prob, squad, vars=None, df_players=None, my_team=None):
    """
    Display squad results in a tkinter window with transfer information
    """
    # Create window
    root = tk.Tk()
    gw_text = f" - Gameweek {squad['gameweek']}" if squad['gameweek'] else ""
    root.title(f"FPL Team Selection Results{gw_text}")
    root.geometry("900x650")
    
    # Create notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Tab 1: Team Display
    team_frame = ttk.Frame(notebook)
    notebook.add(team_frame, text="Team")
    
    team_text = scrolledtext.ScrolledText(team_frame, wrap=tk.WORD, width=100, height=35, font=("Consolas", 10))
    team_text.pack(fill='both', expand=True)
    
    # Build team output with transfer info
    output = []
    output.append("="*85)
    output.append(" "*30 + "FPL TEAM SELECTION")
    if squad['gameweek']:
        output.append(" "*33 + f"GAMEWEEK {squad['gameweek']}")
    output.append("="*85)
    output.append(f"\nSTATUS: {LpStatus[prob.status]}")
    output.append(f"TOTAL EXPECTED POINTS: {value(prob.objective):.2f}")
    output.append(f"CAPTAIN: {squad['captain_name']} ({squad['captain_points']:.1f} x 2 = {squad['captain_points']*2:.1f} pts)")
    output.append(f"VICE-CAPTAIN: {squad['vice_captain_name']} ({squad['vice_captain_points']:.1f} pts)")    
    # Add transfer summary if available
    if vars and df_players is not None:
        transfers_made = get_transfer_summary(vars, df_players)
        if transfers_made['total'] > 0:
            output.append(f"\nTRANSFERS MADE: {transfers_made['total']}")
            output.append(f"  Free: {transfers_made['free']}")
            output.append(f"  Paid (-4 pts each): {transfers_made['paid']}")
            output.append(f"  Points Hit: -{transfers_made['paid'] * 4}")
    
    output.append(f"\n{'='*85}")
    output.append("STARTING XI")
    output.append("-"*85)
    output.append(f"{'Name':<20} {'Position':<12} {'Team':<15} {'£m':<6} {'xP':<5}  {'Transfer':<20} {'Role':<4}")
    output.append("-"*85)
    
    # Display Starting XI with proper transfer type
    for _, player in squad['starting_df'].iterrows():
        role = ""
        if player.get('is_captain', False):
            role = "(C)"
        elif player.get('is_vice_captain', False):
            role = "(VC)"
                
        output.append(f"{player['name']:<20} {player['position']:<12} {player['team']:<15} {player['price']:<6.1f} {player['expected_points']:<5.1f}  {player['transfer_type']:<20} {role:<4}")
    
    output.append(f"\n{'='*85}")
    output.append("BENCH (in priority order)")
    output.append("-"*85)
    output.append(f"{'#':<3} {'Name':<20} {'Position':<12} {'Team':<15} {'£m':<6} {'xP':<5}  {'Transfer':<20}")
    output.append("-"*85)
    
    # Display Bench with proper transfer type
    for _, player in squad['bench_df'].iterrows():
       
        output.append(f"{player['bench_order']:<3} {player['name']:<20} {player['position']:<12} {player['team']:<15} {player['price']:<6.1f} {player['expected_points']:<5.1f}  {player['transfer_type']:<20}")
    
    output.append(f"\n{'='*85}")
    output.append("SUMMARY")
    output.append("-"*85)
    formation = squad['formation']
    output.append(f"Formation: {formation.get('Goalkeeper', 0)}-{formation.get('Defender', 0)}-{formation.get('Midfielder', 0)}-{formation.get('Forward', 0)}")
    output.append(f"Total Cost: £{squad['total_cost']:.1f}m / £100.0m")
    output.append(f"Money Remaining: £{100.0 - squad['total_cost']:.1f}m")
    
    team_text.insert('1.0', '\n'.join(output))
    team_text.config(state='disabled')
    
    # Tab 2: Statistics
    stats_frame = ttk.Frame(notebook)
    notebook.add(stats_frame, text="Statistics")
    
    stats_text = scrolledtext.ScrolledText(stats_frame, wrap=tk.WORD, width=100, height=35, font=("Consolas", 10))
    stats_text.pack(fill='both', expand=True)
    
    # Build stats
    stats_output = []
    all_selected = pd.concat([squad['starting_df'], squad['bench_df']])
    
    stats_output.append("POSITION BREAKDOWN")
    stats_output.append("-"*60)
    stats_output.append(f"{'Role':<10} {'Name':<20} {'Team':<15} {'Price':<8} {'xP':<6}")
    stats_output.append("-"*60)
    
    for pos in ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']:
        pos_players = all_selected[all_selected['position'] == pos]
        if len(pos_players) > 0:
            stats_output.append(f"\n{pos}s:")
            for _, p in pos_players.iterrows():
                role = "STARTER" if p['role'] == 'Starting XI' else "BENCH"
                if p.name == squad['captain_idx']:
                    role += " (C)"
                elif p.name == squad['vice_captain_idx']:
                    role += " (VC)"
                stats_output.append(f"{role:<10} {p['name']:<20} {p['team']:<15} £{p['price']:<7.1f} {p['expected_points']:<6.1f}")
    
    # Add transfer details if available
    if vars and df_players is not None:
        stats_output.append(f"\n{'='*60}")
        stats_output.append("TRANSFER DETAILS")
        stats_output.append("-"*60)
        
        # Extract all transfers directly from variables
        transfers = extract_all_transfers(vars, df_players)
        
        # Players OUT
        if transfers['out_free'] or transfers['out_paid']:
            stats_output.append("\nPLAYERS OUT:")
            for p in transfers['out_free']:
                stats_output.append(f"  {p} (Free)")
            for p in transfers['out_paid']:
                stats_output.append(f"  {p} (Paid -4)")
        else:
            stats_output.append("\nPLAYERS OUT: None")
        
        # Players IN
        if transfers['in_free'] or transfers['in_paid']:
            stats_output.append("\nPLAYERS IN:")
            for p in transfers['in_free']:
                stats_output.append(f"  {p} (Free)")
            for p in transfers['in_paid']:
                stats_output.append(f"  {p} (Paid -4)")
        else:
            stats_output.append("\nPLAYERS IN: None")
        
        # Squad role changes
        if transfers['bench_to_starting'] or transfers['starting_to_bench']:
            stats_output.append("\nSQUAD ROLE CHANGES:")
            for p in transfers['bench_to_starting']:
                stats_output.append(f"  ↑ {p} (Bench → Starting)")
            for p in transfers['starting_to_bench']:
                stats_output.append(f"  ↓ {p} (Starting → Bench)")
        
        # Summary
        total_out = len(transfers['out_free']) + len(transfers['out_paid'])
        total_in = len(transfers['in_free']) + len(transfers['in_paid'])
        paid_transfers = len(transfers['out_paid']) + len(transfers['in_paid'])
        
        stats_output.append(f"\n{'-'*60}")
        stats_output.append(f"Total transfers: {total_out} OUT, {total_in} IN")
        if paid_transfers > 0:
            stats_output.append(f"Points hit: -{paid_transfers * 4} pts")
    
    stats_text.insert('1.0', '\n'.join(stats_output))
    stats_text.config(state='disabled')
    
    # Tab 3: Previous Gameweek
    prev_frame = ttk.Frame(notebook)
    notebook.add(prev_frame, text="Previous GW")
    
    prev_text = scrolledtext.ScrolledText(prev_frame, wrap=tk.WORD, width=100, height=35, font=("Consolas", 10))
    prev_text.pack(fill='both', expand=True)
    
    prev_output = []
    
    if my_team is not None:
        prev_output.append("="*70)
        prev_output.append(" "*20 + f"PREVIOUS TEAM (GAMEWEEK {squad.get('gameweek', 1) - 1})")
        prev_output.append("="*70)
        
        # Get team data from my_team
        team_df = my_team.current_team
        
        # Sort by starting/bench
        prev_starting = team_df[team_df['is_starting'] == True].copy()
        prev_bench = team_df[team_df['is_starting'] == False].copy()
        
        prev_output.append("\nSTARTING XI")
        prev_output.append("-"*70)
        prev_output.append(f"{'Name':<20} {'Position':<12} {'Team':<15} {'Price':<8} {'Points':<8} {'Role':<6}")
        prev_output.append("-"*70)
        
        for _, player in prev_starting.iterrows():
            role = "(C)" if player.get('is_captain', False) else "(VC)" if player.get('is_vice_captain', False) else ""
            points = player.get('expected_points', 0)
            prev_output.append(f"{player['name']:<20} {player['position']:<12} {player['team']:<15} £{player['price']:<7.1f} {points:<8.1f} {role:<6}")
        
        prev_output.append("\nBENCH")
        prev_output.append("-"*70)
        for _, player in prev_bench.iterrows():
            points = player.get('expected_points', 0)
            prev_output.append(f"{player.get('bench_order', '')} {player['name']:<20} {player['position']:<12} {player['team']:<15} £{player['price']:<7.1f} {points:<8.1f}")
        
        # Summary
        prev_output.append(f"\n{'='*70}")
        prev_output.append("PREVIOUS TEAM SUMMARY")
        prev_output.append("-"*70)
        prev_output.append(f"Total Squad Value: £{my_team.team_value:.1f}m")
        prev_output.append(f"Bank: £{my_team.budget:.1f}m")
        prev_output.append(f"Free Transfers: {my_team.free_transfers}")
        
        # Formation
        formation_prev = prev_starting['position'].value_counts()
        prev_output.append(f"Formation: {formation_prev.get('GK', 0)}-{formation_prev.get('DEF', 0)}-{formation_prev.get('MID', 0)}-{formation_prev.get('FWD', 0)}")
    else:
        prev_output.append("No previous gameweek data available")
        
    prev_text.insert('1.0', '\n'.join(prev_output))
    prev_text.config(state='disabled')
    
    # Close button
    close_btn = ttk.Button(root, text="Close", command=root.destroy)
    close_btn.pack(pady=5)
    
    root.mainloop()


def extract_all_transfers(vars, df_players):
    """
    Simply check every variable to see what transfers happened
    """
    transfers = {
        'kept_starting': [],
        'kept_bench': [],
        'bench_to_starting': [],
        'starting_to_bench': [],
        'in_free': [],
        'in_paid': [],
        'out_free': [],
        'out_paid': []
    }
    
    for idx in df_players.index:
        player_name = df_players.loc[idx, 'name']
        player_team = df_players.loc[idx, 'team']
        player_str = f"{player_name} ({player_team})"
        
        # Check stay variables
        if idx in vars['stay'].get('starting', {}):
            if vars['stay']['starting'][idx].value() == 1:
                transfers['kept_starting'].append(player_str)
        
        if idx in vars['stay'].get('bench', {}):
            if vars['stay']['bench'][idx].value() == 1:
                transfers['kept_bench'].append(player_str)
        
        # Check swap variables
        if idx in vars['swap'].get('bench_to_starting', {}):
            if vars['swap']['bench_to_starting'][idx].value() == 1:
                transfers['bench_to_starting'].append(player_str)
        
        if idx in vars['swap'].get('starting_to_bench', {}):
            if vars['swap']['starting_to_bench'][idx].value() == 1:
                transfers['starting_to_bench'].append(player_str)
        
        # Check IN variables
        for subcat in ['to_starting_free', 'to_bench_free']:
            if idx in vars['in'].get(subcat, {}):
                if vars['in'][subcat][idx].value() == 1:
                    transfers['in_free'].append(player_str)
        
        for subcat in ['to_starting_paid', 'to_bench_paid']:
            if idx in vars['in'].get(subcat, {}):
                if vars['in'][subcat][idx].value() == 1:
                    transfers['in_paid'].append(player_str)
        
        # Check OUT variables
        for subcat in ['starting_free', 'bench_free']:
            if idx in vars['out'].get(subcat, {}):
                if vars['out'][subcat][idx].value() == 1:
                    transfers['out_free'].append(player_str)
        
        for subcat in ['starting_paid', 'bench_paid']:
            if idx in vars['out'].get(subcat, {}):
                if vars['out'][subcat][idx].value() == 1:
                    transfers['out_paid'].append(player_str)
    
    return transfers



def check_var(vars, category, subcategory, idx):
    """Helper to check if a variable is set to 1"""
    if category in vars and subcategory in vars[category]:
        var = vars[category][subcategory].get(idx)
        if var and hasattr(var, 'value') and var.value():
            return var.value() == 1
    return False


def get_transfer_summary(vars, df_players):
    """Get summary of transfers made"""
    transfers = {'total': 0, 'free': 0, 'paid': 0}
    
    if vars is None or df_players is None:
        return transfers
    
    # Count transfers (divide by 2 since we count both in and out)
    free_count = 0
    paid_count = 0
    
    for idx in df_players.index:
        # Count free transfers OUT
        if (check_var(vars, 'out', 'starting_free', idx) or 
            check_var(vars, 'out', 'bench_free', idx)):
            free_count += 1
        
        # Count paid transfers OUT
        if (check_var(vars, 'out', 'starting_paid', idx) or 
            check_var(vars, 'out', 'bench_paid', idx)):
            paid_count += 1
    
    transfers['free'] = free_count
    transfers['paid'] = paid_count
    transfers['total'] = free_count + paid_count
    
    return transfers

