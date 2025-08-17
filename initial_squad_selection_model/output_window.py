# output_window.py
# Display squad results in a window

import pandas as pd
import tkinter as tk
from tkinter import ttk, scrolledtext
from pulp import LpStatus, value

def display_in_window(prob, squad):
    """
    Display squad results in a tkinter window
    """
    # Create window
    root = tk.Tk()
    gw_text = f" - Gameweek {squad['gameweek']}" if squad['gameweek'] else ""
    root.title(f"FPL Team Selection Results{gw_text}")
    root.geometry("800x600")
    
    # Create notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Tab 1: Team Display
    team_frame = ttk.Frame(notebook)
    notebook.add(team_frame, text="Team")
    
    team_text = scrolledtext.ScrolledText(team_frame, wrap=tk.WORD, width=80, height=30, font=("Consolas", 10))
    team_text.pack(fill='both', expand=True)
    
    # Build team output
    output = []
    output.append("="*70)
    output.append(" "*25 + "FPL TEAM SELECTION")
    if squad['gameweek']:
        output.append(" "*28 + f"GAMEWEEK {squad['gameweek']}")
    output.append("="*70)
    output.append(f"\n📊 STATUS: {LpStatus[prob.status]}")
    output.append(f"📈 TOTAL EXPECTED POINTS: {value(prob.objective):.2f}")
    output.append(f"⚡ CAPTAIN: {squad['captain_name']} ({squad['captain_points']:.1f} x 2 = {squad['captain_points']*2:.1f} pts)")
    output.append(f"📌 VICE-CAPTAIN: {squad['vice_captain_name']} ({squad['vice_captain_points']:.1f} pts)")
    
    output.append(f"\n{'='*70}")
    output.append("STARTING XI")
    output.append("-"*70)
    output.append(f"{'Name':<20} {'Position':<12} {'Team':<15} {'£m':<6} {'xP':<5}  {'Role':<4}")
    output.append("-"*70)
    
    for _, player in squad['starting_df'].iterrows():
        role = ""
        if player['is_captain']:
            role = "(C)"
        elif player['is_vice_captain']:
            role = "(VC)"
        output.append(f"{player['name']:<20} {player['position']:<12} {player['team']:<15} {player['price']:<6.1f} {player['expected_points']:<5.1f}  {role:<4}")
    
    output.append(f"\n{'='*70}")
    output.append("BENCH (in priority order)")
    output.append("-"*70)
    output.append(f"{'#':<3} {'Name':<20} {'Position':<12} {'Team':<15} {'£m':<6} {'xP':<5}")
    output.append("-"*70)
    for _, player in squad['bench_df'].iterrows():
        output.append(f"{player['bench_order']:<3} {player['name']:<20} {player['position']:<12} {player['team']:<15} {player['price']:<6.1f} {player['expected_points']:<5.1f}")
    
    output.append(f"\n{'='*70}")
    output.append("SUMMARY")
    output.append("-"*70)
    formation = squad['formation']
    output.append(f"Formation: {formation.get('Goalkeeper', 0)}-{formation.get('Defender', 0)}-{formation.get('Midfielder', 0)}-{formation.get('Forward', 0)}")
    output.append(f"Total Cost: £{squad['total_cost']:.1f}m / £100.0m")
    output.append(f"Money Remaining: £{100.0 - squad['total_cost']:.1f}m")
    
    team_text.insert('1.0', '\n'.join(output))
    team_text.config(state='disabled')
    
    # Tab 2: Statistics
    stats_frame = ttk.Frame(notebook)
    notebook.add(stats_frame, text="Statistics")
    
    stats_text = scrolledtext.ScrolledText(stats_frame, wrap=tk.WORD, width=80, height=30, font=("Consolas", 10))
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
                role = "⭐" if p['role'] == 'Starting XI' else "🪑"
                if p.name == squad['captain_idx']:
                    role += " (C)"
                elif p.name == squad['vice_captain_idx']:
                    role += " (VC)"
                stats_output.append(f"{role:<10} {p['name']:<20} {p['team']:<15} £{p['price']:<7.1f} {p['expected_points']:<6.1f}")
    
    stats_text.insert('1.0', '\n'.join(stats_output))
    stats_text.config(state='disabled')
    
    # Close button
    close_btn = ttk.Button(root, text="Close", command=root.destroy)
    close_btn.pack(pady=5)
    
    root.mainloop()