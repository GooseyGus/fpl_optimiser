# app.py
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="FPL Team Analyzer", page_icon="⚽")

st.title("⚽ FPL Team Analyzer")
st.write("Enter your FPL Team ID to analyze your squad")

# Input for team ID
team_id = st.text_input("Enter your FPL Team ID:", placeholder="e.g. 2562804")

if team_id:
    try:
        # Fetch team info
        url = f"https://fantasy.premierleague.com/api/entry/{team_id}/"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Display team info
            st.success(f"✅ Found team: {data['name']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Manager", f"{data['player_first_name']} {data['player_last_name']}")
            with col2:
                points = data.get('summary_overall_points', 'N/A')
                st.metric("Total Points", points)
            with col3:
                rank = data.get('summary_overall_rank', 'N/A')
                if rank != 'N/A':
                    rank = f"{rank:,}"
                st.metric("Overall Rank", rank)
            
            st.write("More features coming soon!")
        else:
            st.error(f"❌ Team ID {team_id} not found")
            
    except Exception as e:
        st.error(f"Error: {e}")