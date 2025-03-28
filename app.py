import streamlit as st
import pandas as pd
import base64
import plotly.express as px
from datetime import datetime
import openpyxl
import requests
from io import BytesIO

st.set_page_config(
    page_title="🔥 Bourbon Chasers Strava Inferno 🔥",
    layout="wide"
)

# Function to encode images in base64
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Load and embed the background image
def get_base64_image_from_url(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        encoded_image = base64.b64encode(response.content).decode()
        print(encoded_image[:100])  # Debugging: Print first 100 characters
        return encoded_image
    else:
        print(f"Error: Unable to load image. HTTP Status Code: {response.status_code}")
        return ""

image_url = "https://raw.githubusercontent.com/Steven-Carter-Data/50k-Strava-Tracker/main/bg_smolder.png"

# # **Debugging Step: Show Image in Streamlit**
# st.image(image_url, caption="Test: Direct Image from URL")

base64_image = get_base64_image_from_url(image_url)

# Insert background image into Streamlit app
st.markdown(
    f"""
    <style>
    .stApp {{
        background: url('data:image/png;base64,{base64_image}') no-repeat center center fixed !important;
        background-size: cover !important;
        background-position: center !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&display=swap');

    .stApp {
        background: url('data:image/png;base64,{base64_image}') no-repeat center center fixed;
        background-size: cover;
        font-family: 'UnifrakturCook', serif;
        color: #D4AF37;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'UnifrakturCook', serif;
        color: #D4AF37;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title header 
st.markdown(
    """
    <h1 style="text-align: center; font-family: 'UnifrakturCook', serif; font-size: 60px; font-weight: bold; color: #D4AF37; max-width: 90%; margin: auto; word-wrap: break-word;">
    Welcome to the Inferno
    </h1>
    """,
    unsafe_allow_html=True
)

# Title Sub-header
st.markdown(
    '<h3 style="text-align: center; font-family: UnifrakturCook, serif; font-size: 25px; font-weight: bold; color: #D4AF37;">'
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
    url = "https://github.com/Steven-Carter-Data/50k-Strava-Tracker/blob/main/TieDye_Weekly_Scoreboard.xlsx?raw=true"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error for bad responses (4xx, 5xx)
        
        # Read the Excel file from the response content
        return pd.read_excel(BytesIO(response.content), engine="openpyxl")

    except Exception as e:
        st.warning(f"TieDye_Weekly_Scoreboard.xlsx not found. Please check the URL or upload it manually. Error: {e}")
        return None


weekly_data = load_weekly_data()

# if weekly_data is not None:
#     # Ensure Date column is in datetime format
#     weekly_data["Date"] = pd.to_datetime(weekly_data["Date"])

#     # Sort data so the most recent date appears at the top
#     weekly_data = weekly_data.sort_values(by="Date", ascending=False)

#     st.header("Weekly Activity Data (Most Recent First)")
#     st.dataframe(weekly_data, use_container_width=True)

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
tabs = st.tabs(["Leaderboards", "Overview", "Individual Analysis"])

with tabs[0]:  # Leaderboards tab
    if weekly_data is not None:
        # Format Date column to display only Month, Day, Year
        weekly_data["Date"] = pd.to_datetime(weekly_data["Date"]).dt.strftime("%B %d, %Y")
        
        # Sort data so the most recent date appears at the top
        weekly_data = weekly_data.sort_values(by="Date", ascending=False)
        
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

    st.header("Group Weekly Running Distance Progress")
    st.subheader("The change in total running distance by week across the group.")

    # Ensure the 'Week' and 'Total Distance' columns are numeric
    weekly_data["Week"] = pd.to_numeric(weekly_data["Week"], errors='coerce')
    weekly_data["Total Distance"] = pd.to_numeric(weekly_data["Total Distance"], errors='coerce')

    # Filter running activities only
    running_data = weekly_data[weekly_data["Workout Type"] == "Run"]

    # Aggregate total weekly distance for the group
    weekly_distance = running_data.groupby("Week")["Total Distance"].sum().reset_index()
    weekly_distance = weekly_distance.sort_values("Week")

    weekly_distance["Pct Change"] = weekly_distance["Total Distance"].pct_change() * 100
    weekly_distance["Pct Change"].fillna(0, inplace=True)  # Handle NaN for first week

    fig_weekly_miles = px.line(
        weekly_distance,
        x="Week",
        y="Total Distance",
        markers=True,
        title="Total Miles Run by Week",
        labels={"Total Distance": "Total Distance (Miles)", "Week": "Week"},
        template="plotly_dark"
    )
    st.plotly_chart(fig_weekly_miles, use_container_width=True)

    # Display the most recent week's percentage change
    latest_week = weekly_distance.iloc[-1]
    pct_change_latest = latest_week["Pct Change"]

    # Format KPI
    kpi_color = "#00FF00" if pct_change_latest >= 0 else "#FF4136"
    kpi_arrow = "🔼" if pct_change_latest >= 0 else "🔽"

    st.markdown(
        f"""
        <div style='background-color:#333333;padding:15px;border-radius:8px;text-align:center;'>
            <span style='color:#FFFFFF;font-size:22px;'>Week-over-Week Change:</span>
            <span style='color:{kpi_color};font-size:26px;font-weight:bold;'>{pct_change_latest:.1f}% {kpi_arrow}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


    st.header("Group Activity Level Progress by Week")
    st.subheader("The weekly increase or decrease in the number of activities across the group.")

    # Count total number of activities per week
    weekly_activities = weekly_data.groupby("Week").size().reset_index(name="Num Activities").sort_values("Week")

    weekly_activities["Pct Change"] = weekly_activities["Num Activities"].pct_change() * 100
    weekly_activities["Pct Change"].fillna(0, inplace=True)  # Handle NaN for first week

    # Display the latest week's percentage change in activities
    latest_week_activity = weekly_activities.iloc[-1]
    activities_pct_change_latest = latest_week_activity["Pct Change"]

    # KPI formatting
    activity_color = "#00FF00" if activities_pct_change_latest >= 0 else "#FF4136"
    activity_arrow = "🔼" if activities_pct_change_latest >= 0 else "🔽"

    st.markdown(
        f"""
        <div style='background-color:#333333;padding:15px;border-radius:8px;text-align:center;margin-top:10px;'>
            <span style='color:#FFFFFF;font-size:22px;'>Week-over-Week Activity Change:</span>
            <span style='color:{activity_color};font-size:26px;font-weight:bold;'>
                {activities_pct_change_latest:.1f}% {activity_arrow}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


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

with tabs[2]:  # Individual Analysis Tab
    st.header("Individual Performance Breakdown")

    # Participant selection
    participant_selected = st.selectbox(
        "Select Participant", sorted(weekly_data["Participant"].unique())
    )

    # Filter data for the selected participant
    individual_data = weekly_data[weekly_data["Participant"] == participant_selected]

    # Calculate total training time for the participant
    participant_total_time = individual_data["Total Duration"].sum()

    # Calculate group average total training time
    group_avg_total_time = weekly_data.groupby("Participant")["Total Duration"].sum().mean()

    # Calculate participant vs group avg (%)
    percent_of_group_avg = (participant_total_time / group_avg_total_time) * 100

    # Display KPI for total training duration vs group average
    kpi_color = "#00FF00" if percent_of_group_avg >= 100 else "#FF4136"
    performance_arrow = "🔼" if percent_of_group_avg >= 100 else "🔽"

    st.markdown(
        f"""
        <div style='background-color:#333333;padding:15px;border-radius:8px;text-align:center;margin-top:10px;'>
            <span style='color:#FFFFFF;font-size:22px;'>Your Total Training Time vs. Group Average:</span><br>
            <span style='color:{kpi_color};font-size:28px;font-weight:bold;'>
                {percent_of_group_avg:.1f}% {performance_arrow}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Aggregate participant zone times
    zone_columns = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"]
    participant_zones = individual_data[zone_columns].sum()

    # Calculate group average for zones
    group_avg_zones = weekly_data.groupby("Participant")[zone_columns].sum().mean()

    # Prepare DataFrame for comparison
    zone_comparison_df = pd.DataFrame({
        "Zone": zone_columns,
        participant_selected: participant_zones.values,
        "Group Average": group_avg_zones.values
    })

    # Plot bar chart
    fig_zone_comparison = px.bar(
        zone_comparison_df.melt(id_vars=["Zone"], var_name="Type", value_name="Minutes"),
        x="Zone",
        y="Minutes",
        color="Type",
        barmode="group",
        template="plotly_dark",
        title=f"{participant_selected}'s Time per Zone vs. Group Average"
    )

    st.plotly_chart(fig_zone_comparison, use_container_width=True)

