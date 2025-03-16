import streamlit as st
import pandas as pd
import base64
import plotly.express as px
from datetime import datetime
import requests
from io import BytesIO

st.set_page_config(page_title="Strava Inferno 🔥", layout="wide")

# --- Background Styling ---
def get_base64_image_from_url(image_url):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
    except Exception as e:
        print(f"Error loading image: {e}")
    return ""

image_url = "https://raw.githubusercontent.com/Steven-Carter-Data/50k-Strava-Tracker/main/bg_smolder.png"
base64_image = get_base64_image_from_url(image_url)

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&display=swap');
    .stApp {{
        background: url('data:image/png;base64,{base64_image}') no-repeat center center fixed;
        background-size: cover;
        font-family: 'UnifrakturCook', serif;
        color: #D4AF37;
    }}
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'UnifrakturCook', serif;
        color: #D4AF37;
        text-align: center;
    }}
    </style>
""", unsafe_allow_html=True)

# --- Title & Tabs ---
st.markdown("""
    <h1>Welcome to the Inferno</h1>
    <h3>Bourbon Chasers - The descent into madness has begun!</h3>
""", unsafe_allow_html=True)

tabs = st.tabs(["Leaderboards", "Overview"])

# --- Sidebar Setup ---
sidebar = st.sidebar
sidebar.title("Bourbon Chasers")

# Load and embed the sidebar image
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

sidebar_image = "sidebar_img.png"
try:
    base64_sidebar_image = get_base64_image(sidebar_image)
    sidebar.markdown(f"""
        <div style="text-align: center;">
            <img src='data:image/png;base64,{base64_sidebar_image}' style='max-width: 100%; border-radius: 10px;'>
        </div>
    """, unsafe_allow_html=True)
except Exception as e:
    sidebar.warning("Sidebar image not found.")

@st.cache_data(ttl=0)
def load_weekly_data():
    url = "https://github.com/Steven-Carter-Data/50k-Strava-Tracker/blob/main/TieDye_Weekly_Scoreboard.xlsx?raw=true"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return pd.read_excel(BytesIO(response.content), engine="openpyxl")
    except Exception as e:
        st.warning(f"Error loading data: {e}")
        return None

weekly_data = load_weekly_data()
if weekly_data is not None:
    weekly_data["Date"] = pd.to_datetime(weekly_data["Date"]).dt.strftime("%B %d, %Y")
    weekly_data.sort_values(by="Date", ascending=False, inplace=True)

# --- Function to Get Current Week ---
def get_current_week():
    today = datetime.today().date()
    start_date = datetime(today.year, 3, 10).date()
    if today < start_date:
        start_date = datetime(today.year - 1, 3, 10).date()
    return min(max((today - start_date).days // 7 + 1, 1), 8)

current_week = get_current_week()

# --- Leaderboard Tab ---
with tabs[0]:
    if weekly_data is not None:
        participants = sorted(weekly_data["Participant"].unique())
        selected_participant = sidebar.selectbox("Select a Bourbon Chaser", ["All"] + participants)
        selected_week_str = sidebar.selectbox("Select a Week", ["All Weeks"] + [f"Week {i}" for i in range(1, 9)], index=current_week)
        
        filtered_data = weekly_data.copy()
        if selected_week_str != "All Weeks":
            selected_week = int(selected_week_str.replace("Week ", ""))
            filtered_data = filtered_data[filtered_data["Week"] == selected_week]
        if selected_participant != "All":
            filtered_data = filtered_data[filtered_data["Participant"] == selected_participant]
        
        st.dataframe(filtered_data, use_container_width=True)

        # --- Leaderboard Calculation ---
        def calculate_leaderboard(data):
            data["Total Points"] = sum(data[f"Zone {i}"] * i for i in range(1, 6))
            leaderboard = data.groupby("Participant")["Total Points"].sum().reset_index()
            return leaderboard.sort_values(by="Total Points", ascending=False)
        
        leaderboard = calculate_leaderboard(filtered_data)
        st.dataframe(leaderboard, use_container_width=True)

        # --- Running Visualization ---
        if "Total Distance" in weekly_data.columns:
            st.header("Top Runners by Distance")
            distance_data = weekly_data.groupby("Participant")["Total Distance"].sum().reset_index()
            distance_data = distance_data.sort_values(by="Total Distance", ascending=True)
            fig = px.bar(distance_data, x="Total Distance", y="Participant", orientation="h", color_discrete_sequence=["#E25822"], template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

# --- Overview Tab ---
with tabs[1]:
    st.markdown("""
        ### **Competition Overview**
        Welcome to the **8-week** Strava Inferno Challenge!
        
        #### **Scoring System**
        - **Zone 1** → x1 points  
        - **Zone 2** → x2 points  
        - **Zone 3** → x3 points  
        - **Zone 4** → x4 points  
        - **Zone 5** → x5 points  
        
        #### **Accepted Activities**
        - 🏃 Running
        - 🚴 Biking
        - 🎒 Rucking
        - 🏊 Swimming
        - 🚣 Rowing
        - 🏋️ Lifting
        - 🏃‍♂️ Elliptical
    """)
