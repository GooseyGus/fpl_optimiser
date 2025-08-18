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

    # Look up captain and vice-captain
    if squad['captain_idx'] is not None and squad['captain_idx'] in squad['starting_df'].index:
        captain_name = squad['starting_df'].loc[squad['captain_idx'], 'name']
        captain_points = squad['starting_df'].loc[squad['captain_idx'], 'expected_points']  
        output.append(f"CAPTAIN: {captain_name} ({captain_points:.1f} x 2 = {captain_points*2:.1f} pts)")
    else:
        output.append("CAPTAIN: None selected")

    if squad['vice_captain_idx'] is not None and squad['vice_captain_idx'] in squad['starting_df'].index:
        vice_captain_name = squad['starting_df'].loc[squad['vice_captain_idx'], 'name']
        vice_captain_points = squad['starting_df'].loc[squad['vice_captain_idx'], 'expected_points']  
        output.append(f"VICE-CAPTAIN: {vice_captain_name} ({vice_captain_points:.1f} pts)")
    else:
        output.append("VICE-CAPTAIN: None selected")

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
    output.append(f"{'Name':<20} {'Position':<12} {'Team':<15} {'£m':<6} {'expected_points':<5}  {'Transfer':<20} {'Role':<4}")
    output.append("-"*85)


    # Display Starting XI with proper transfer type


    # sort squad['starting_df'] by position
    position_order = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
    squad['starting_df'] = squad['starting_df'].sort_values(by='position', key=lambda x: x.map({pos: i for i, pos in enumerate(position_order)}))

    for _, player in squad['starting_df'].iterrows():
        role = ""
        if player.get('is_captain', False):
            role = "(C)"
        elif player.get('is_vice_captain', False):
            role = "(VC)"

                
        output.append(f"{player['name']:<20} {player['position']:<12} {player['team']:<15} {player['price']:<6.1f} {player['expected_points']:<5.1f}  {player['transfer_type']:<20} {role:<4}")
    
    output.append(f"\n{'='*85}")
    output.append("BENCH")
    output.append("-"*85)
    output.append(f"{'#':<3} {'Name':<20} {'Position':<12} {'Team':<15} {'£m':<6} {'expected_points':<5}  {'Transfer':<20}")
    output.append("-"*85)
    
    # Display Bench with proper transfer type
    for _, player in squad['bench_df'].iterrows():
       
        output.append(f"{player['bench_order']:<3} {player['name']:<20} {player['position']:<12} {player['team']:<15} {player['price']:<6.1f} {player['expected_points']:<5.1f}  {player['transfer_type']:<20}")
    
    output.append(f"\n{'='*85}")
    output.append("SUMMARY")
    output.append("-"*85)
    formation = squad['formation']
    output.append(f"Formation: {formation.get('Goalkeeper', 0)}-{formation.get('Defender', 0)}-{formation.get('Midfielder', 0)}-{formation.get('Forward', 0)}")
    output.append(f"Total Cost: £{squad['total_cost']:.1f}m ")

    
    # add previous team cost
    if my_team:
        output.append(f"Previous Team Cost: £{my_team.team_value:.1f}m")
        output.append(f"Previous Bank Remaining: £{my_team.budget:.1f}m")

    output.append("="*85)
    output.append("OUT TRANSFERS")
    output.append("-"*85)
    output.append(f"{'Name':<20} {'Position':<12} {'Team':<15} {'£m':<6} {'expected_points':<5}  {'Transfer Type':<20}")
    output.append("-"*85)
    
    for _, player in squad['out_df'].iterrows():
        output.append(f"{player['name']:<20} {player['position']:<12} {player['team']:<15} {player['price']:<6.1f} {player['expected_points']:<5.1f} {player['transfer_type']:<20}")


    team_text.insert('1.0', '\n'.join(output))
    team_text.config(state='disabled')




    
    # Tab 2 Previous Gameweek
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
            prev_output.append(f"{player['name']:<20} {player['position']:<12} {player['team']:<15} £{player['price']:<7.1f} {player['expected_points']:<8.1f} {role:<6}")
        
        prev_output.append("\nBENCH")
        prev_output.append("-"*70)
        for _, player in prev_bench.iterrows():
            points = player.get('expected_points', 0)
            prev_output.append(f"{player.get('bench_order', '')} {player['name']:<20} {player['position']:<12} {player['team']:<15} £{player['price']:<7.1f} {player['expected_points']:<8.1f}")
        
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

