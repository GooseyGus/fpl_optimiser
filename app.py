# simple_fpl_app.py
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="FPL Team Fetcher", page_icon="⚽")

st.title("FPL Team Fetcher")


# Input fields
col1, col2, col3 = st.columns(3)

with col1:
    team_id = st.text_input("Team ID", placeholder="e.g. 2562804")

with col2:
    budget = st.number_input("Bank (£m)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)

with col3:
    free_transfers = st.selectbox("Free Transfers", [1, 2], index=0)

# Instructions
with st.expander("ℹ️ How to find your Team ID"):
    st.markdown("""
    1. Go to [Fantasy Premier League](https://fantasy.premierleague.com)
    2. Click on "My Team" or "Points"
    3. Look at the URL in your browser
    4. Find the number after `/entry/` - that's your Team ID
    
    Example: `https://fantasy.premierleague.com/entry/2562804/event/20`
    
    Team ID = **2562804**
    """)


# Fetch button
if st.button("Get Team Data", type="primary"):
    if team_id:
        try:
            # Get general team info (no auth needed!)
            team_resp = requests.get(f'https://fantasy.premierleague.com/api/entry/{team_id}/')
            
            if team_resp.status_code == 200:
                team_data = team_resp.json()
                
                # Get all player data
                bootstrap_resp = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
                bootstrap = bootstrap_resp.json()
                
                # Find current gameweek
                current_gw = next((e['id'] for e in bootstrap['events'] if e['is_current']), 
                                 next((e['id'] for e in bootstrap['events'] if e['is_next']), 1))
                
                # Get team picks for current gameweek
                picks_resp = requests.get(f'https://fantasy.premierleague.com/api/entry/{team_id}/event/{current_gw}/picks/')
                
                if picks_resp.status_code == 200:
                    picks_data = picks_resp.json()
                    
                    # Create lookups
                    players = {p['id']: p for p in bootstrap['elements']}
                    teams = {t['id']: t['name'] for t in bootstrap['teams']}
                    positions = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
                    
                    # Show team info
                    st.success(f"Found team: **{team_data['name']}**")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Points", team_data.get('summary_overall_points', 0))
                    with col2:
                        st.metric("Overall Rank", f"{team_data.get('summary_overall_rank', 0):,}")
                    with col3:
                        st.metric("Bank", f"£{budget}m")
                    with col4:
                        st.metric("Free Transfers", free_transfers)
                    
                    # Build squad data
                    squad_data = []
                    for pick in picks_data['picks']:
                        player = players.get(pick['element'], {})
                        squad_data.append({
                            'player_id': pick['element'],
                            'name': player.get('web_name', 'Unknown'),
                            'position': positions.get(player.get('element_type'), '?'),
                            'team': teams.get(player.get('team'), 'Unknown'),
                            'price': player.get('now_cost', 0) / 10,
                            'squad_position': 'starting' if pick['position'] <= 11 else 'bench',
                            'is_captain': pick.get('is_captain', False),
                            'is_vice_captain': pick.get('is_vice_captain', False)
                        })
                    
                    df = pd.DataFrame(squad_data)
                    
                    # Display squad
                    st.markdown("---")
                    st.markdown("### Your Squad")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Starting XI**")
                        starting = df[df['squad_position'] == 'starting'].copy()
                        starting['name'] = starting.apply(
                            lambda x: x['name'] + ' (C)' if x['is_captain'] else x['name'] + ' (VC)' if x['is_vice_captain'] else x['name'], 
                            axis=1
                        )
                        st.dataframe(
                            starting[['name', 'position', 'team', 'price']], 
                            hide_index=True,
                            use_container_width=True
                        )
                    
                    with col2:
                        st.markdown("**Bench**")
                        bench = df[df['squad_position'] == 'bench']
                        st.dataframe(
                            bench[['name', 'position', 'team', 'price']], 
                            hide_index=True,
                            use_container_width=True
                        )
                    
                    # Export section
                    st.markdown("---")
                    st.markdown("### 📥 Export for Optimizer")
                    
                    # Add metadata to export
                    df['budget'] = budget
                    df['free_transfers'] = free_transfers
                    df['gw'] = current_gw
                    
                    # CSV download
                    csv = df.to_csv(index=False)
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.download_button(
                            label="⬇️ Download CSV",
                            data=csv,
                            file_name=f"fpl_team_{team_id}_gw{current_gw}.csv",
                            mime="text/csv"
                        )
                    with col2:
                        st.info(f"Ready for optimization: GW{current_gw} with {free_transfers} FT and £{budget}m bank")
                    
                else:
                    st.error("Could not fetch squad data. Team might not have been picked yet.")
            else:
                st.error(f"Team ID {team_id} not found. Please check and try again.")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a Team ID")


