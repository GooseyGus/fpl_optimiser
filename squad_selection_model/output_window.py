# output_window_updated.py
# Display squad results with transfer information using tabulate for perfect alignment

import pandas as pd
import tkinter as tk
from tkinter import ttk, scrolledtext
from pulp import LpStatus, value
from tabulate import tabulate
import os

def display_in_window(prob, squad, vars=None, df_players=None, my_team=None):
    """
    Display squad results in a tkinter window with transfer information using tabulate for perfect alignment
    """
    # Create window
    root = tk.Tk()
    gw_text = f" - Gameweek {squad['gameweek']}" if squad['gameweek'] else ""
    root.title(f"FPL Team Selection Results{gw_text}")
    root.geometry("1200x800")  # Larger window for better table display
    
    # Create notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Tab 1: Team Display
    team_frame = ttk.Frame(notebook)
    notebook.add(team_frame, text="Team")
    
    team_text = scrolledtext.ScrolledText(team_frame, wrap=tk.NONE, width=140, height=40, font=("Courier New", 9))
    team_text.pack(fill='both', expand=True)
    
    # Configure text tags for formatting
    team_text.tag_configure("bold", font=("Courier New", 9, "bold"))
    team_text.tag_configure("title", font=("Courier New", 12, "bold"))
    team_text.tag_configure("header", font=("Courier New", 10, "bold"))
    team_text.tag_configure("important", font=("Courier New", 9, "bold"), foreground="dark blue")
    
    # Insert content with formatting
    def insert_with_formatting(text_widget, content_list):
        """Insert text with appropriate formatting based on content type"""
        for item in content_list:
            if isinstance(item, tuple):
                text, tag = item
                text_widget.insert(tk.END, text + "\n", tag)
            else:
                text_widget.insert(tk.END, item + "\n")
    
    # Build team output with transfer info (using tuples for formatted text)
    output = []
    output.append(("=" * 100, "bold"))
    output.append((" " * 35 + "FPL TEAM SELECTION", "title"))
    if squad['gameweek']:
        output.append((" " * 38 + f"GAMEWEEK {squad['gameweek']}", "title"))
    output.append(("=" * 100, "bold"))
    output.append("")
    output.append((f"STATUS: {LpStatus[prob.status]}", "important"))
    output.append((f"TOTAL EXPECTED POINTS: {value(prob.objective):.2f}", "important"))

    # Look up captain and vice-captain
    if squad['captain_idx'] is not None and squad['captain_idx'] in squad['starting_df'].index:
        captain_name = squad['starting_df'].loc[squad['captain_idx'], 'name']
        captain_points = squad['starting_df'].loc[squad['captain_idx'], 'expected_points']  
        output.append((f"CAPTAIN: {captain_name} ({captain_points:.1f} x 2 = {captain_points*2:.1f} pts)", "important"))
    else:
        output.append(("CAPTAIN: None selected", "important"))

    if squad['vice_captain_idx'] is not None and squad['vice_captain_idx'] in squad['starting_df'].index:
        vice_captain_name = squad['starting_df'].loc[squad['vice_captain_idx'], 'name']
        vice_captain_points = squad['starting_df'].loc[squad['vice_captain_idx'], 'expected_points']  
        output.append((f"VICE-CAPTAIN: {vice_captain_name} ({vice_captain_points:.1f} pts)", "important"))
    else:
        output.append(("VICE-CAPTAIN: None selected", "important"))

    # Add transfer summary if available
    if vars and df_players is not None:
        transfers_made = get_transfer_summary(vars, df_players)
        if transfers_made['total'] > 0:
            output.append("")
            output.append((f"TRANSFERS MADE: {transfers_made['total']}", "header"))
            output.append(f"  Free: {transfers_made['free']}")
            output.append(f"  Paid (-4 pts each): {transfers_made['paid']}")
            output.append((f"  Points Hit: -{transfers_made['paid'] * 4}", "important"))

    output.append("")
    output.append(("=" * 100, "bold"))
    output.append(("STARTING XI", "header"))
    output.append(("=" * 100, "bold"))

    # Prepare Starting XI data for tabulate
    if not squad['starting_df'].empty:
        # Sort by position
        position_order = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
        starting_sorted = squad['starting_df'].sort_values(
            by='position', 
            key=lambda x: x.map({pos: i for i, pos in enumerate(position_order)})
        )
        
        starting_table_data = []
        for _, player in starting_sorted.iterrows():
            role = ""
            if player.get('is_captain', False):
                role = "(C)"
            elif player.get('is_vice_captain', False):
                role = "(VC)"
            
            starting_table_data.append([
                player['name'],
                player['position'],
                player['team'],
                player.get('opponent', 'No fixture'),
                f"£{player['price']:.1f}m",
                f"{player['expected_points']:.1f}",
                player['transfer_type'],
                role
            ])
        
        starting_headers = ['Name', 'Position', 'Team', 'Opponent', 'Price', 'Points', 'Transfer', 'Role']
        starting_table = tabulate(starting_table_data, headers=starting_headers, tablefmt='grid')
        output.append(starting_table)
    
    output.append("")
    output.append(("=" * 100, "bold"))
    output.append(("BENCH", "header"))
    output.append(("=" * 100, "bold"))
    
    # Prepare Bench data for tabulate
    if not squad['bench_df'].empty:
        bench_table_data = []
        for _, player in squad['bench_df'].iterrows():
            bench_table_data.append([
                player['bench_order'],
                player['name'],
                player['position'],
                player['team'],
                player.get('opponent', 'No fixture'),
                f"£{player['price']:.1f}m",
                f"{player['expected_points']:.1f}",
                player['transfer_type']
            ])
        
        bench_headers = ['#', 'Name', 'Position', 'Team', 'Opponent', 'Price', 'Points', 'Transfer']
        bench_table = tabulate(bench_table_data, headers=bench_headers, tablefmt='grid')
        output.append(bench_table)
    
    output.append("")
    output.append(("=" * 100, "bold"))
    output.append(("SUMMARY", "header"))
    output.append(("=" * 100, "bold"))
    
    formation = squad['formation']
    formation_str = f"{formation.get('Goalkeeper', 0)}-{formation.get('Defender', 0)}-{formation.get('Midfielder', 0)}-{formation.get('Forward', 0)}"
    
    summary_data = [
        ['Formation', formation_str],
        ['Total Cost', f"£{squad['total_cost']:.1f}m"],
    ]
    
    if my_team:
        summary_data.extend([
            ['Previous Team Cost', f"£{my_team.team_value:.1f}m"],
            ['Previous Bank', f"£{my_team.budget:.1f}m"]
        ])
    
    summary_table = tabulate(summary_data, tablefmt='simple')
    output.append(summary_table)
    
    # OUT TRANSFERS section
    if not squad['out_df'].empty:
        output.append("")
        output.append(("=" * 100, "bold"))
        output.append(("OUT TRANSFERS", "header"))
        output.append(("=" * 100, "bold"))
        
        out_table_data = []
        for _, player in squad['out_df'].iterrows():
            out_table_data.append([
                player['name'],
                player['position'],
                player['team'],
                player.get('opponent', 'No fixture'),
                f"£{player['price']:.1f}m",
                f"{player['expected_points']:.1f}",
                player['transfer_type']
            ])
        
        out_headers = ['Name', 'Position', 'Team', 'Opponent', 'Price', 'Points', 'Transfer Type']
        out_table = tabulate(out_table_data, headers=out_headers, tablefmt='grid')
        output.append(out_table)

    # Insert content with formatting
    insert_with_formatting(team_text, output)
    team_text.config(state='disabled')

    # Tab 2: Previous Gameweek
    prev_frame = ttk.Frame(notebook)
    notebook.add(prev_frame, text="Previous GW")
    
    prev_text = scrolledtext.ScrolledText(prev_frame, wrap=tk.NONE, width=140, height=40, font=("Courier New", 9))
    prev_text.pack(fill='both', expand=True)
    
    prev_output = []
    
    if my_team is not None:
        prev_output.append("=" * 80)
        prev_output.append(" " * 25 + f"PREVIOUS TEAM (GAMEWEEK {squad.get('gameweek', 1) - 1})")
        prev_output.append("=" * 80)
        
        # Get team data from my_team
        team_df = my_team.current_team
        
        # Sort by starting/bench
        prev_starting = team_df[team_df['is_starting'] == True].copy()
        prev_bench = team_df[team_df['is_starting'] == False].copy()
        
        # Starting XI table
        if not prev_starting.empty:
            prev_output.append("\nSTARTING XI")
            prev_output.append("=" * 80)
            
            prev_starting_data = []
            for _, player in prev_starting.iterrows():
                role = "(C)" if player.get('is_captain', False) else "(VC)" if player.get('is_vice_captain', False) else ""
                prev_starting_data.append([
                    player['name'],
                    player['position'],
                    player['team'],
                    player.get('opponent', 'No fixture'),
                    f"£{player['price']:.1f}m",
                    f"{player['expected_points']:.1f}",
                    role
                ])
            
            prev_starting_headers = ['Name', 'Position', 'Team', 'Opponent', 'Price', 'Points', 'Role']
            prev_starting_table = tabulate(prev_starting_data, headers=prev_starting_headers, tablefmt='grid')
            prev_output.append(prev_starting_table)
        
        # Bench table
        if not prev_bench.empty:
            prev_output.append("\nBENCH")
            prev_output.append("=" * 80)
            
            prev_bench_data = []
            for i, (_, player) in enumerate(prev_bench.iterrows(), 1):
                prev_bench_data.append([
                    i,
                    player['name'],
                    player['position'],
                    player['team'],
                    player.get('opponent', 'No fixture'),
                    f"£{player['price']:.1f}m",
                    f"{player['expected_points']:.1f}"
                ])
            
            prev_bench_headers = ['#', 'Name', 'Position', 'Team', 'Opponent', 'Price', 'Points']
            prev_bench_table = tabulate(prev_bench_data, headers=prev_bench_headers, tablefmt='grid')
            prev_output.append(prev_bench_table)
        
        # Summary
        prev_output.append(f"\n{'=' * 80}")
        prev_output.append("PREVIOUS TEAM SUMMARY")
        prev_output.append("=" * 80)
        
        formation_prev = prev_starting['position'].value_counts()
        prev_formation = f"{formation_prev.get('GK', 0)}-{formation_prev.get('DEF', 0)}-{formation_prev.get('MID', 0)}-{formation_prev.get('FWD', 0)}"
        
        prev_summary_data = [
            ['Total Squad Value', f"£{my_team.team_value:.1f}m"],
            ['Bank', f"£{my_team.budget:.1f}m"],
            ['Free Transfers', str(my_team.free_transfers)],
            ['Formation', prev_formation]
        ]
        
        prev_summary_table = tabulate(prev_summary_data, tablefmt='simple')
        prev_output.append(prev_summary_table)
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
