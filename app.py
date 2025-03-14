import streamlit as st
import pandas as pd
import base64
import plotly.express as px
from datetime import datetime
import openpyxl

st.set_page_config(
    page_title="STRAVA_TRACKER",
    layout="wide"
)

# Function to encode images in base64
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Load and embed the background image
background_image = "bg_smolder.png"
base64_image = get_base64_image(background_image)

st.markdown(
    f"""
    <style>
    .stApp {{
        background: url('data:image/png;base64,{base64_image}') no-repeat center center fixed;
        background-size: cover;
        background-position: center;
        font-family: 'Garamond', 'Georgia', serif;
        color: #D4AF37;
    }}
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Old English Text MT', serif;
        color: #D4AF37;
    }}
    .stDataFrame {{
        font-family: 'Garamond', 'Georgia', serif;
        color: white;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Title header 
st.markdown(
    '<h1 style="text-align: center; font-family: Old English Text MT, serif; font-size: 85px; font-weight: bold; color: #D4AF37;">'
    'Welcome to the Inferno</h1>',
    unsafe_allow_html=True
)

# Title Sub-header
st.markdown(
    '<h3 style="text-align: center; font-family: Old English Text MT, serif; font-size: 25px; font-weight: bold; color: #D4AF37;">'
    'Bourbon Chasers - The descent into madness has begun!</h3>',
    unsafe_allow_html=True
)

# Sidebar setup
sidebar = st.sidebar

# Load and embed the sidebar image
sidebar_image = "sidebar_img.png"  # Make sure this file exists in the same directory
base64_sidebar_image = get_base64_image(sidebar_image)

sidebar.markdown(
    f"""
    <div style="text-align: center;">
        <img src='data:image/png;base64,{base64_sidebar_image}' style='max-width: 100%; border-radius: 10px;'>
    </div>
    """,
    unsafe_allow_html=True
)

sidebar.title("Bourbon Chasers")

# Load TieDye_Weekly.xlsx
@st.cache_data(ttl=0)
def load_weekly_data():
    url = "https://github.com/Steven-Carter-Data/50k-Strava-Tracker/blob/main/TieDye_Weekly_Scoreboard.xlsx"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error for bad responses (4xx, 5xx)
        
        # Read the Excel file from the response content
        return pd.read_excel(BytesIO(response.content), engine="openpyxl")

    except Exception as e:
        st.warning(f"TieDye_Weekly_Scoreboard.xlsx not found. Please check the URL or upload it manually. Error: {e}")
        return None


weekly_data = load_weekly_data()

# Ensure the Week column is numeric if it exists
if weekly_data is not None and "Week" in weekly_data.columns:
    weekly_data["Week"] = pd.to_numeric(weekly_data["Week"], errors='coerce')

# Determine current week dynamically
def get_current_week():
    today = datetime.today().date()

    # Determine the competition year dynamically
    current_year = today.year

    # Ensure we calculate from the most recent competition start
    start_date = datetime(current_year, 3, 10).date()

    # If today is before the start date, use the previous year's start date
    if today < start_date:
        start_date = datetime(current_year - 1, 3, 10).date()

    # Calculate the number of weeks elapsed
    days_since_start = (today - start_date).days
    week_number = (days_since_start // 7) + 1

    # Ensure the week is within the valid range (1 to 8)
    return min(max(week_number, 1), 8)

current_week = get_current_week()


# Tabs for navigation
tabs = st.tabs(["Leaderboards", "Overview"])

with tabs[0]:  # Leaderboards tab
    if weekly_data is not None:
        # Format Date column to display only Month, Day, Year
        weekly_data["Date"] = pd.to_datetime(weekly_data["Date"]).dt.strftime("%B %d, %Y")
        
        # Add participant filter in the sidebar
        participants = sorted(weekly_data["Participant"].unique())
        selected_participant = sidebar.selectbox("Select a Bourbon Chaser", ["All"] + participants)
        
        # Add week filter in the sidebar with 8 weeks and "All Weeks" option
        all_weeks = [f"Week {i}" for i in range(1, 9)]
        all_weeks.insert(0, "All Weeks")
        selected_week_str = sidebar.selectbox("Select a Week", all_weeks, index=all_weeks.index(f"Week {current_week}"))

        
        st.header("Weekly Activity Data")
        
        # Convert selected week back to a number for filtering
        if selected_week_str == "All Weeks":
            filtered_weekly_data = weekly_data
        else:
            selected_week = int(selected_week_str.replace("Week ", ""))
            filtered_weekly_data = weekly_data[weekly_data["Week"] == selected_week]
        
        if selected_participant != "All":
            filtered_weekly_data = filtered_weekly_data[filtered_weekly_data["Participant"] == selected_participant]
        
        st.dataframe(filtered_weekly_data, use_container_width=True)
        
        # Calculate leaderboard dynamically
        def calculate_leaderboard(data, current_week):
            # Calculate total points
            data["Total Points"] = (
                data["Zone 1"] * 1 +
                data["Zone 2"] * 2 +
                data["Zone 3"] * 3 +
                data["Zone 4"] * 4 +
                data["Zone 5"] * 5
            )
            
            # Compute total points leaderboard
            leaderboard = data.groupby("Participant")["Total Points"].sum().reset_index()
            leaderboard = leaderboard.sort_values(by="Total Points", ascending=False)
            
            # Add weekly totals dynamically up to the current week
            for week in range(1, current_week + 1):
                week_points = data[data["Week"] == week].groupby("Participant")["Total Points"].sum()
                leaderboard[f"Week {week} Totals"] = leaderboard["Participant"].map(week_points).fillna(0)

            return leaderboard

        
        leaderboard = calculate_leaderboard(weekly_data, current_week)

        st.header("Strava Competition Leaderboard")
        st.dataframe(leaderboard, use_container_width=True)

        # Visualization: Who has run the most distance
        if "Total Distance" in weekly_data.columns and "Workout Type" in weekly_data.columns and "Total Duration" in weekly_data.columns:
            st.header("Top Runners by Distance and Duration (Runs Only)")

            # Filter only running activities
            run_data = weekly_data[weekly_data["Workout Type"] == "Run"]

            # Aggregate total running distance and duration per participant
            distance_data = run_data.groupby("Participant")["Total Distance"].sum().reset_index()
            duration_data = run_data.groupby("Participant")["Total Duration"].sum().reset_index()

            # Merge both datasets
            combined_data = pd.merge(distance_data, duration_data, on="Participant")

            # Calculate pace (minutes per mile) with handling for zero distance
            combined_data["Pace (min/mile)"] = combined_data["Total Duration"] / combined_data["Total Distance"]
            combined_data["Pace (min/mile)"] = combined_data["Pace (min/mile)"].replace([float('inf'), -float('inf')], 0).fillna(0)

            # Convert pace to mm:ss format
            combined_data["Formatted Pace"] = combined_data["Pace (min/mile)"].apply(lambda x: f"{int(x)}:{int((x % 1) * 60):02d} min/mile")

            # **Sort by Total Distance (Descending)**
            combined_data = combined_data.sort_values(by="Total Distance", ascending=True)

            # Create a melted dataframe for grouped bar chart
            melted_data = combined_data.melt(id_vars=["Participant", "Formatted Pace"], 
                                            value_vars=["Total Distance", "Total Duration"], 
                                            var_name="Metric", value_name="Value")

            # Convert Total Duration to hours for better visualization
            melted_data.loc[melted_data["Metric"] == "Total Duration", "Value"] = melted_data.loc[melted_data["Metric"] == "Total Duration", "Value"] / 60
            melted_data.replace({"Total Distance": "Distance (miles)", "Total Duration": "Duration (hours)"}, inplace=True)

            # **Ensure Participant Order Matches Sorted Total Distance**
            melted_data["Participant"] = pd.Categorical(melted_data["Participant"], categories=combined_data["Participant"], ordered=True)

            # Create Plotly grouped bar chart with dark theme
            fig = px.bar(
                melted_data,
                x="Value",
                y="Participant",
                color="Metric",
                orientation="h",
                color_discrete_sequence=["#E25822", "#FFD700"],  
                template="plotly_dark",
                text=melted_data.apply(lambda row: f"{row['Formatted Pace']}" if row["Metric"] == "Distance (miles)" else f"{row['Value']:.2f}", axis=1)  # Show pace for Distance bars
            )

            fig.update_layout(
                title=dict(
                    text="Total Running Distance and Duration by Bourbon Chaser",
                    x=0,  
                    xanchor="left",
                    font=dict(size=22)  
                )
            )


            # Display chart
            st.plotly_chart(fig, use_container_width=True)


    else:
        st.warning("No data available. Please upload TieDye_Weekly.xlsx.")

with tabs[1]:  # Overview tab
    st.header("Competition Overview")

    st.markdown(
        """
        ### **Bourbon Chasers - The Descent into Madness**
        Welcome to the Inferno! Over the next **8 weeks**, you will battle for supremacy using **Heart Rate (HR) Zones** to earn points. 
        This scoring method ensures that all accepted activities contribute fairly to the competition.

        #### **Scoring System**
        Points are awarded based on HR Zones as follows:

        - **Zone 1** → x1 points  
        - **Zone 2** → x2 points  
        - **Zone 3** → x3 points  
        - **Zone 4** → x4 points  
        - **Zone 5** → x5 points  

        #### **Accepted Activities**
        You can earn points from the following activities:
        - 🏃 **Running**
        - 🚴 **Biking**
        - 🎒 **Rucking**
        - 🏊 **Swimming**
        - 🚣 **Rowing**
        - 🏋️ **Lifting**
        - 🏃‍♂️ **Elliptical**

        The battle is fierce, and only the strongest will rise. Stay disciplined and push your limits.  
        **The descent into madness has begun! 🔥**
        """
    )

