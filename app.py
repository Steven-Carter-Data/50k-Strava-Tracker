# --- START OF FILE app.py ---

import streamlit as st
import pandas as pd
import base64
import plotly.express as px
from datetime import datetime, timedelta # Ensure timedelta is imported
import openpyxl
import requests
from io import BytesIO

st.set_page_config(
    page_title="🔥 Bourbon Chasers Strava Inferno 🔥",
    layout="wide"
)

# Function to encode images in base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"Sidebar image file not found: {image_path}. Placeholder will be used.")
        return ""


# Function to load image from URL
def get_base64_image_from_url(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        if response.status_code == 200:
            encoded_image = base64.b64encode(response.content).decode()
            return encoded_image
        else:
            print(f"Error: Unable to load image. HTTP Status Code: {response.status_code}")
            return ""
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from URL {image_url}: {e}")
        return ""
    except Exception as e:
        print(f"An unexpected error occurred while fetching image: {e}")
        return ""

image_url = "https://raw.githubusercontent.com/Steven-Carter-Data/50k-Strava-Tracker/main/bg_smolder.png"
base64_image = get_base64_image_from_url(image_url)

# Insert background image into Streamlit app
if base64_image: # Only apply if image was loaded successfully
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
else:
    st.warning("Background image failed to load. Using default background.")


# Custom Font and Styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&display=swap');
    .stApp, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp .stMarkdown, .stApp .stDataFrame, .stApp .stMetric, .stApp .stTabs {{
        font-family: 'UnifrakturCook', serif;
        color: #D4AF37;
    }}
     h1, h2, h3, h4, h5, h6 {{
         font-family: 'UnifrakturCook', serif !important;
         color: #D4AF37 !important;
     }}
     .plotly .gtitle {{
         font-family: 'UnifrakturCook', serif !important;
         fill: #D4AF37 !important;
     }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px; white-space: pre-wrap; background-color: rgba(51, 51, 51, 0.7);
        border-radius: 4px 4px 0px 0px; gap: 1px; padding: 10px; color: #D4AF37; font-family: 'UnifrakturCook', serif;
    }}
    .stTabs [aria-selected="true"] {{ background-color: rgba(212, 175, 55, 0.8); color: #000000; }}
    .stDataFrame {{ background-color: rgba(51, 51, 51, 0.7); color: #D4AF37; }}
    .stDataFrame thead th {{ background-color: rgba(212, 175, 55, 0.8); color: #000000; font-family: 'UnifrakturCook', serif; }}
    .stDataFrame tbody tr:nth-child(even) {{ background-color: rgba(70, 70, 70, 0.7); }}
    .stDataFrame tbody tr:hover {{ background-color: rgba(212, 175, 55, 0.3); }}
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

# --- Sidebar Setup ---
sidebar = st.sidebar
sidebar_image_path = "sidebar_img.png"
base64_sidebar_image = get_base64_image(sidebar_image_path)
if base64_sidebar_image:
    sidebar.markdown(
        f"""<div style="text-align: center;"><img src='data:image/png;base64,{base64_sidebar_image}' style='max-width: 100%; border-radius: 10px;'></div>""",
        unsafe_allow_html=True
    )
else:
    sidebar.markdown("<p style='text-align: center; color: yellow;'>Sidebar image not loaded.</p>", unsafe_allow_html=True)
sidebar.title("Bourbon Chasers")

# --- Data Loading ---
# @st.cache_data(ttl=0) # Consider re-enabling later
def load_weekly_data():
    url = "https://github.com/Steven-Carter-Data/50k-Strava-Tracker/blob/main/TieDye_Weekly_Scoreboard.xlsx?raw=true"
    try:
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_excel(BytesIO(response.content), engine="openpyxl")
        print("Data loaded successfully.")
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching data: {e}")
        return None
    except Exception as e:
        st.error(f"Failed to load or parse Excel file. Error: {e}")
        return None

weekly_data = load_weekly_data()

# --- Data Preprocessing --- # <<<--- REPLACE THIS ENTIRE SECTION
if weekly_data is not None and not weekly_data.empty:
    print("Starting Data Preprocessing...")
    # Convert Date column to datetime, handle potential errors
    weekly_data["Date"] = pd.to_datetime(weekly_data["Date"], errors='coerce')
    initial_rows = len(weekly_data)
    weekly_data.dropna(subset=["Date"], inplace=True)
    if len(weekly_data) < initial_rows:
        print(f"Dropped {initial_rows - len(weekly_data)} rows due to invalid dates.")

    # Sort by Date first (most recent first)
    weekly_data = weekly_data.sort_values(by="Date", ascending=False)
    print("Sorted by Date.")

    # Ensure zone columns exist and are numeric, fillna(0) for safety
    zone_cols = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"]
    print("Checking and converting zone columns...")
    for col in zone_cols:
        if col not in weekly_data.columns:
            weekly_data[col] = 0 # Add missing zone columns if necessary
            print(f"Warning: Column '{col}' missing, added with zeros.")
        else:
            # Convert to numeric, coerce errors to NaN, then fill NaN with 0
            weekly_data[col] = pd.to_numeric(weekly_data[col], errors='coerce').fillna(0)
    print("Zone columns processed.")

    # --- Points Calculation and Insertion ---
    # Calculate Points Series first
    print("Calculating 'Points' Series...")
    points_calculation = (
        weekly_data["Zone 1"] * 1 + weekly_data["Zone 2"] * 2 +
        weekly_data["Zone 3"] * 3 + weekly_data["Zone 4"] * 4 +
        weekly_data["Zone 5"] * 5
    )
    # Assign the calculation to the DataFrame (adds/overwrites 'Points' column at the end)
    weekly_data["Points"] = points_calculation
    print("'Points' column calculated and added/updated.")

    # Debugging: Print columns immediately after calculation
    print("Columns AFTER calculation:", weekly_data.columns.tolist())

    # Now, move the 'Points' column if 'Zone 5' exists
    if "Zone 5" in weekly_data.columns and 'Points' in weekly_data.columns:
        print("Attempting to move 'Points' column...")
        try:
            zone5_index = weekly_data.columns.get_loc("Zone 5")
            # Pop the 'Points' column data (using a distinct variable name)
            points_col_data_to_move = weekly_data.pop('Points')
            # Insert it at the desired location using the popped data variable
            weekly_data.insert(zone5_index + 1, "Points", points_col_data_to_move)
            print(f"'Points' column inserted after 'Zone 5'. New columns: {weekly_data.columns.tolist()}")
        except Exception as e:
            print(f"ERROR during Points column move/insert: {e}")
            # If error occurs, 'Points' might remain at the end or be missing if pop succeeded but insert failed
            # Check if it exists and potentially re-add it at the end if needed
            if 'Points' not in weekly_data.columns:
                 weekly_data["Points"] = points_col_data_to_move # Try re-adding if it got lost
                 print("Re-added 'Points' column at the end after insertion error.")

    else:
        print("'Zone 5' or 'Points' column not found, 'Points' column remains at end (if calculated).")
        if 'Points' not in weekly_data.columns:
             print("Warning: 'Points' column does not exist even after calculation attempt.")
    # --- End of Points Calculation and Insertion ---

    # Make relevant columns numeric, coercing errors
    numeric_cols = ["Total Distance", "Total Duration", "Week"]
    print("Converting other numeric columns...")
    for col in numeric_cols:
         if col in weekly_data.columns:
              weekly_data[col] = pd.to_numeric(weekly_data[col], errors='coerce') # NaNs for non-numeric
         else:
              print(f"Warning: Numeric column '{col}' not found.")
    print("Numeric columns processed.")

    print("Data preprocessing complete.")
else:
    st.error("Failed to load or process the weekly data. Some features may be unavailable.")
    expected_cols = ["Date", "Participant", "Workout Type", "Total Duration", "Total Distance",
                     "Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Points", "Week"]
    weekly_data = pd.DataFrame(columns=expected_cols)
# <<<--- END OF SECTION TO REPLACE


# --- Dynamic Week Calculation ---
def get_current_week(start_date_dt):
    today = datetime.today().date()
    if isinstance(start_date_dt, datetime): start_date_dt = start_date_dt.date()
    if today < start_date_dt: return 1
    days_since_start = (today - start_date_dt).days
    week_number = (days_since_start // 7) + 1
    competition_duration_weeks = 8
    return min(max(week_number, 1), competition_duration_weeks)

competition_start_datetime = datetime(2024, 3, 10)
current_week = get_current_week(competition_start_datetime)
print(f"Current Competition Week: {current_week}")


# --- Sidebar Filters ---
if weekly_data is not None and not weekly_data.empty:
    participants = sorted(weekly_data["Participant"].unique())
    selected_participant_sb = sidebar.selectbox("Select a Bourbon Chaser", ["All"] + participants, key="sb_participant")
    all_weeks_options = [f"Week {i}" for i in range(1, 9)]
    all_weeks_options.insert(0, "All Weeks")
    default_week_index = all_weeks_options.index(f"Week {current_week}") if f"Week {current_week}" in all_weeks_options else 0
    selected_week_str_sb = sidebar.selectbox("Select a Week", all_weeks_options, index=default_week_index, key="sb_week")
else:
    sidebar.markdown("_(Data not loaded, filters unavailable)_")
    selected_participant_sb = "All"
    selected_week_str_sb = "All Weeks"


# --- Main App Tabs ---
tabs = st.tabs(["Leaderboards", "Overview", "Individual Analysis"])

# ===========================
# ======= LEADERBOARDS TAB =======
# ===========================
with tabs[0]:
    st.header("Leaderboards & Group Trends")

    if weekly_data is not None and not weekly_data.empty:

        # --- Weekly Activity Data Table ---
        st.subheader("Weekly Activity Data Log")
        st.markdown("Detailed log of all recorded activities, filterable by participant and week using the sidebar selections. Shows HR Zone times, points earned per activity, and other metrics.")
        filtered_display_data = weekly_data.copy()
        if selected_week_str_sb != "All Weeks":
            try:
                selected_week_num = int(selected_week_str_sb.replace("Week ", ""))
                if 'Week' in filtered_display_data.columns:
                     filtered_display_data['Week'] = pd.to_numeric(filtered_display_data['Week'], errors='coerce')
                     filtered_display_data = filtered_display_data[filtered_display_data["Week"] == selected_week_num]
            except ValueError: st.warning(f"Invalid week selection: {selected_week_str_sb}")
        if selected_participant_sb != "All":
             if 'Participant' in filtered_display_data.columns:
                  filtered_display_data = filtered_display_data[filtered_display_data["Participant"] == selected_participant_sb]

        if "Date" in filtered_display_data.columns:
             filtered_display_data["Date"] = pd.to_datetime(filtered_display_data["Date"], errors='coerce')
             mask = filtered_display_data["Date"].notna()
             # Create a temporary column for formatted dates
             filtered_display_data["Date_Formatted"] = None # Initialize column
             filtered_display_data.loc[mask, "Date_Formatted"] = filtered_display_data.loc[mask, "Date"].dt.strftime("%B %d, %Y")
             # Select columns, using the formatted date if available
             display_cols_list = ["Date_Formatted", "Participant", "Workout Type", "Total Duration", "Total Distance",
                             "Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Points", "Week"]
             # Filter list to only existing columns
             display_cols = [col for col in display_cols_list if col in filtered_display_data.columns]
             # Rename 'Date_Formatted' back to 'Date' for display purposes
             filtered_display_data_final = filtered_display_data[display_cols].rename(columns={"Date_Formatted": "Date"})
             st.dataframe(filtered_display_data_final, use_container_width=True, hide_index=True)
        else:
            # Fallback if Date column doesn't exist (unlikely after preprocessing)
             display_cols_list = ["Participant", "Workout Type", "Total Duration", "Total Distance",
                             "Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Points", "Week"]
             display_cols = [col for col in display_cols_list if col in filtered_display_data.columns]
             st.dataframe(filtered_display_data[display_cols], use_container_width=True, hide_index=True)


        # --- Competition Leaderboard Calculation ---
        def calculate_leaderboard(data, total_weeks):
            if data is None or data.empty or "Participant" not in data.columns or "Points" not in data.columns:
                 return pd.DataFrame(columns=["Rank", "Participant", "Points", "Points Behind"])
            leaderboard = data.groupby("Participant")["Points"].sum().reset_index()
            leaderboard = leaderboard.sort_values(by="Points", ascending=False)
            if not leaderboard.empty:
                max_points = leaderboard["Points"].iloc[0]
                leaderboard["Points Behind"] = max_points - leaderboard["Points"]
            else: leaderboard["Points Behind"] = 0
            leaderboard.reset_index(drop=True, inplace=True)
            leaderboard.insert(0, 'Rank', leaderboard.index + 1)
            if "Points Behind" in leaderboard.columns:
                points_idx = leaderboard.columns.get_loc("Points")
                points_behind_col = leaderboard.pop("Points Behind")
                leaderboard.insert(points_idx + 1, "Points Behind", points_behind_col)
            if 'Week' in data.columns and 'Points' in data.columns:
                data['Week'] = pd.to_numeric(data['Week'], errors='coerce')
                for week_num in range(1, total_weeks + 1):
                    week_points = data[data["Week"] == week_num].groupby("Participant")["Points"].sum()
                    leaderboard[f"Week {week_num} Totals"] = leaderboard["Participant"].map(week_points).fillna(0).astype(int)
            return leaderboard

        competition_total_weeks = 8
        leaderboard_df = calculate_leaderboard(weekly_data.copy(), competition_total_weeks)
        st.subheader("Strava Competition Leaderboard")
        st.markdown("Overall ranking based on **cumulative points** earned from HR Zones across all activities and weeks. Also shows points behind the leader and a breakdown of points earned each week.")
        st.dataframe(leaderboard_df, use_container_width=True, hide_index=True)


        # --- Biggest Mover Highlight ---
        st.subheader(f"🔥 Biggest Points Mover - Week {current_week}")
        st.caption(f"Highlights the participant who earned the most points specifically in Week {current_week}.")
        if current_week > 0 and not leaderboard_df.empty:
            current_week_col = f"Week {current_week} Totals"
            if current_week_col in leaderboard_df.columns and leaderboard_df[current_week_col].sum() > 0 : # Check if there are points this week
                 biggest_mover = leaderboard_df.loc[leaderboard_df[current_week_col].idxmax()]
                 st.success(f"**{biggest_mover['Participant']}** with **{biggest_mover[current_week_col]:.0f} points** earned this week!")
            else: st.info(f"No points recorded yet for Week {current_week}, or column missing.")
        else: st.info("Leaderboard data needed or competition week 1 not complete.")


        # --- Top Runners Visualization ---
        st.subheader("Top Runners by Distance and Duration")
        st.markdown("Compares participants based on their **total accumulated running distance** and **total running duration** throughout the competition. Average pace for runs is shown on the distance bars.")
        if all(col in weekly_data.columns for col in ["Total Distance", "Workout Type", "Total Duration", "Participant"]):
            run_data = weekly_data[weekly_data["Workout Type"].str.contains("Run", case=False, na=False)].copy()
            if not run_data.empty:
                run_data["Total Distance"] = pd.to_numeric(run_data["Total Distance"], errors='coerce').fillna(0)
                run_data["Total Duration"] = pd.to_numeric(run_data["Total Duration"], errors='coerce').fillna(0)
                distance_data = run_data.groupby("Participant")["Total Distance"].sum().reset_index()
                duration_data = run_data.groupby("Participant")["Total Duration"].sum().reset_index()
                combined_data = pd.merge(distance_data, duration_data, on="Participant", how="left")
                combined_data["Pace (min/mile)"] = combined_data.apply(lambda row: row["Total Duration"] / row["Total Distance"] if row["Total Distance"] > 0 else 0, axis=1)
                combined_data["Formatted Pace"] = combined_data["Pace (min/mile)"].apply(lambda x: f"{int(x)}:{int((x % 1) * 60):02d} min/mi" if x > 0 else "N/A")
                combined_data = combined_data.sort_values(by="Total Distance", ascending=True)
                melted_data = combined_data.melt(id_vars=["Participant", "Formatted Pace"], value_vars=["Total Distance", "Total Duration"], var_name="Metric", value_name="Value")
                melted_data['Display Value'] = melted_data.apply(lambda row: row['Value'] / 60 if row['Metric'] == 'Total Duration' else row['Value'], axis=1)
                melted_data['Metric Label'] = melted_data['Metric'].replace({"Total Distance": "Distance (miles)", "Total Duration": "Duration (hours)"})
                fig_runners = px.bar(
                    melted_data, x="Display Value", y="Participant", color="Metric Label", orientation="h",
                    color_discrete_map={"Distance (miles)": "#E25822", "Duration (hours)": "#FFD700"}, template="plotly_dark",
                    hover_name="Participant",
                    hover_data={ 'Participant': False, 'Metric Label': False, 'Display Value': ':.2f', 'Formatted Pace': (melted_data['Metric Label'] == 'Distance (miles)') }
                )
                text_labels = melted_data.apply(lambda row: row['Formatted Pace'] if row['Metric Label'] == 'Distance (miles)' else f"{row['Display Value']:.1f} hrs", axis=1)
                fig_runners.update_traces(text=text_labels, textposition='auto', selector=dict(type='bar'))
                fig_runners.update_layout(
                    title=dict(text="Total Running Distance & Duration by Bourbon Chaser", x=0.01, xanchor="left", font=dict(size=20, family='UnifrakturCook, serif', color='#D4AF37')),
                    xaxis_title="Value (Miles or Hours)", yaxis_title="Participant", legend_title_text="Metric", barmode='group', yaxis={'categoryorder':'total ascending'}
                )
                st.plotly_chart(fig_runners, use_container_width=True)
            else: st.info("No running data found to display the runners chart.")
        else: st.warning("Required columns for the runners chart are missing.")


        # --- Group Weekly Running Distance Progress ---
        st.subheader("Group Weekly Running Distance Progress")
        st.markdown("Tracks the **total distance run by the entire group** each week. This shows the overall trend in collective running volume throughout the competition.")
        if all(col in weekly_data.columns for col in ["Week", "Total Distance", "Workout Type"]):
             running_data_group = weekly_data[weekly_data["Workout Type"].str.contains("Run", case=False, na=False)].copy()
             if not running_data_group.empty:
                 running_data_group['Week'] = pd.to_numeric(running_data_group['Week'], errors='coerce')
                 running_data_group['Total Distance'] = pd.to_numeric(running_data_group['Total Distance'], errors='coerce').fillna(0)
                 weekly_distance = running_data_group.groupby("Week")["Total Distance"].sum().reset_index().sort_values("Week")
                 fig_weekly_miles = px.line( weekly_distance, x="Week", y="Total Distance", markers=True, labels={"Total Distance": "Total Distance (Miles)", "Week": "Competition Week"}, template="plotly_dark")
                 fig_weekly_miles.update_layout( title=dict(text="Total Group Miles Run by Week", x=0.01, xanchor='left', font=dict(family='UnifrakturCook, serif', color='#D4AF37')), yaxis_title="Total Distance (Miles)")
                 fig_weekly_miles.update_traces(line=dict(color='#E25822'))
                 st.plotly_chart(fig_weekly_miles, use_container_width=True)

                 # --- Week-to-Date Running Distance KPI ---
                 st.caption("Compares the group's total running distance logged **so far this week** against the distance logged during the **same period last week**.")
                 running_data_group["Date"] = pd.to_datetime(running_data_group["Date"], errors='coerce')
                 running_data_group.dropna(subset=["Date"], inplace=True)
                 today_date = datetime.today().date()
                 start_date_dt = competition_start_datetime.date()
                 if today_date >= start_date_dt:
                     days_since_start = (today_date - start_date_dt).days
                     current_week_num_for_calc = (days_since_start // 7) + 1
                     day_of_current_week = days_since_start % 7
                     current_week_start_dt = start_date_dt + timedelta(weeks=current_week_num_for_calc - 1)
                     current_period_end_dt = current_week_start_dt + timedelta(days=day_of_current_week)
                     prev_week_start_dt = current_week_start_dt - timedelta(weeks=1)
                     prev_period_end_dt = prev_week_start_dt + timedelta(days=day_of_current_week)
                     current_week_distance = running_data_group[ (running_data_group["Date"].dt.date >= current_week_start_dt) & (running_data_group["Date"].dt.date <= current_period_end_dt) ]["Total Distance"].sum()
                     prev_week_distance = running_data_group[ (running_data_group["Date"].dt.date >= prev_week_start_dt) & (running_data_group["Date"].dt.date <= prev_period_end_dt) ]["Total Distance"].sum()
                     if prev_week_distance > 0: pct_change_distance = ((current_week_distance - prev_week_distance) / prev_week_distance) * 100
                     elif current_week_distance > 0: pct_change_distance = 100.0
                     else: pct_change_distance = 0.0
                     kpi_color = "#00FF00" if pct_change_distance >= 0 else "#FF4136"
                     kpi_arrow = "🔼" if pct_change_distance >= 0 else "🔽"
                     st.markdown( f"""<div style='background-color:rgba(51, 51, 51, 0.7); padding:15px; border-radius:8px; text-align:center; margin-bottom: 15px;'><span style='color:#FFFFFF; font-size:20px; font-family: UnifrakturCook, serif;'>WtD Running Distance vs Prev. Week:</span><br><span style='color:{kpi_color}; font-size:26px; font-weight:bold; font-family: UnifrakturCook, serif;'>{pct_change_distance:.1f}% {kpi_arrow}</span><br><span style='color:#AAAAAA; font-size:14px; font-family: sans-serif;'>(Current: {current_week_distance:.1f} mi | Previous: {prev_week_distance:.1f} mi)</span></div>""", unsafe_allow_html=True)
                 else: st.info("Week-to-Date comparison starts after the competition begin date.")
             else: st.info("No running data available for weekly group distance progress.")
        else: st.warning("Required columns missing for Group Weekly Running Distance chart.")


        # --- Group Activity Level Progress (WtD Count) ---
        st.subheader("Group Activity Count Progress (Week-to-Date)")
        st.markdown("Compares the **total number of activities** (all types) logged by the group **so far this week** against the count from the **same period last week**.")
        weekly_data_kpi = weekly_data.copy()
        weekly_data_kpi["Date"] = pd.to_datetime(weekly_data_kpi["Date"], errors='coerce')
        weekly_data_kpi.dropna(subset=["Date"], inplace=True)
        if not weekly_data_kpi.empty:
             today_date = datetime.today().date()
             start_date_dt = competition_start_datetime.date()
             if today_date >= start_date_dt:
                 days_since_start = (today_date - start_date_dt).days
                 current_week_num_for_calc = (days_since_start // 7) + 1
                 day_of_current_week = days_since_start % 7
                 current_week_start_dt = start_date_dt + timedelta(weeks=current_week_num_for_calc - 1)
                 current_period_end_dt = current_week_start_dt + timedelta(days=day_of_current_week)
                 prev_week_start_dt = current_week_start_dt - timedelta(weeks=1)
                 prev_period_end_dt = prev_week_start_dt + timedelta(days=day_of_current_week)
                 current_week_activity_count = weekly_data_kpi[ (weekly_data_kpi["Date"].dt.date >= current_week_start_dt) & (weekly_data_kpi["Date"].dt.date <= current_period_end_dt) ].shape[0]
                 prev_week_activity_count = weekly_data_kpi[ (weekly_data_kpi["Date"].dt.date >= prev_week_start_dt) & (weekly_data_kpi["Date"].dt.date <= prev_period_end_dt) ].shape[0]
                 if prev_week_activity_count > 0: pct_change_activity = ((current_week_activity_count - prev_week_activity_count) / prev_week_activity_count) * 100
                 elif current_week_activity_count > 0: pct_change_activity = 100.0
                 else: pct_change_activity = 0.0
                 activity_color = "#00FF00" if pct_change_activity >= 0 else "#FF4136"
                 activity_arrow = "🔼" if pct_change_activity >= 0 else "🔽"
                 st.markdown(f"""<div style='background-color:rgba(51, 51, 51, 0.7); padding:15px; border-radius:8px; text-align:center; margin-bottom: 15px;'><span style='color:#FFFFFF; font-size:20px; font-family: UnifrakturCook, serif;'>WtD Activity Count vs Prev. Week:</span><br><span style='color:{activity_color}; font-size:26px; font-weight:bold; font-family: UnifrakturCook, serif;'>{pct_change_activity:.1f}% {activity_arrow}</span><br><span style='color:#AAAAAA; font-size:14px; font-family: sans-serif;'>(Current: {current_week_activity_count} | Previous: {prev_week_activity_count})</span></div>""", unsafe_allow_html=True)
             else: st.info("Week-to-Date comparison starts after the competition begin date.")
        else: st.info("No data available for Week-to-Date Activity Count.")


        # --- Group Points Progress (WtD Points) ---
        st.subheader("Group Points Progress (Week-to-Date)")
        st.markdown("Compares the **total points earned** by the group **so far this week** against the points earned during the **same period last week**.")
        if 'Points' in weekly_data_kpi.columns and not weekly_data_kpi.empty:
              today_date = datetime.today().date()
              start_date_dt = competition_start_datetime.date()
              if today_date >= start_date_dt:
                 days_since_start = (today_date - start_date_dt).days
                 current_week_num_for_calc = (days_since_start // 7) + 1
                 day_of_current_week = days_since_start % 7
                 current_week_start_dt = start_date_dt + timedelta(weeks=current_week_num_for_calc - 1)
                 current_period_end_dt = current_week_start_dt + timedelta(days=day_of_current_week)
                 prev_week_start_dt = current_week_start_dt - timedelta(weeks=1)
                 prev_period_end_dt = prev_week_start_dt + timedelta(days=day_of_current_week)
                 current_week_points = weekly_data_kpi[ (weekly_data_kpi["Date"].dt.date >= current_week_start_dt) & (weekly_data_kpi["Date"].dt.date <= current_period_end_dt) ]["Points"].sum()
                 prev_week_points = weekly_data_kpi[ (weekly_data_kpi["Date"].dt.date >= prev_week_start_dt) & (weekly_data_kpi["Date"].dt.date <= prev_period_end_dt) ]["Points"].sum()
                 if prev_week_points > 0: pct_change_points = ((current_week_points - prev_week_points) / prev_week_points) * 100
                 elif current_week_points > 0: pct_change_points = 100.0
                 else: pct_change_points = 0.0
                 points_kpi_color = "#00FF00" if pct_change_points >= 0 else "#FF4136"
                 points_kpi_arrow = "🔼" if pct_change_points >= 0 else "🔽"
                 st.markdown(f"""<div style='background-color:rgba(51, 51, 51, 0.7); padding:15px; border-radius:8px; text-align:center; margin-bottom: 15px;'><span style='color:#FFFFFF; font-size:20px; font-family: UnifrakturCook, serif;'>WtD Points Earned vs Prev. Week:</span><br><span style='color:{points_kpi_color}; font-size:26px; font-weight:bold; font-family: UnifrakturCook, serif;'>{pct_change_points:.1f}% {points_kpi_arrow}</span><br><span style='color:#AAAAAA; font-size:14px; font-family: sans-serif;'>(Current: {current_week_points:.0f} | Previous: {prev_week_points:.0f})</span></div>""", unsafe_allow_html=True)
              else: st.info("Week-to-Date comparison starts after the competition begin date.")
        else: st.info("Points data needed for Week-to-Date Points change.")

    else: st.warning("No weekly data loaded. Leaderboards and group trends cannot be displayed.")


# ===========================
# ======= OVERVIEW TAB =======
# ===========================
with tabs[1]:
    st.header("Competition Overview")
    st.markdown("""
        ### **Bourbon Chasers - The Descent into Madness**
        Welcome to the Inferno! Over the next **8 weeks** (starting March 10th, 2024), you will battle for supremacy using **Heart Rate (HR) Zones** from your activities to earn points. This scoring method aims to level the playing field across different types of endurance activities.
        #### **Scoring System**
        Points are awarded based on **time spent in each HR Zone** per activity:
        - **Zone 1:** 1 point per minute
        - **Zone 2:** 2 points per minute
        - **Zone 3:** 3 points per minute
        - **Zone 4:** 4 points per minute
        - **Zone 5:** 5 points per minute
        #### **Accepted Activities**
        Earn points from any logged activity where Strava provides HR Zone data, including common ones like:
        - 🏃 Running
        - 🚴 Biking (Counts towards points/duration, distance/pace not emphasized in leaderboards)
        - 🏊 Swimming
        - 🏋️ Weight Training / Lifting
        - 🚶 Hiking / Rucking / Walking
        - 🚣 Rowing
        - 🤸 Elliptical / Stair Stepper
        - 🧘 Yoga / Pilates
        - _And more... if HR data is available!_
        The battle is fierce, and only the most consistent will rise. Stay disciplined, push your limits safely, and have fun!
        **The descent into madness has begun! 🔥**
        """)

# =================================
# ======= INDIVIDUAL ANALYSIS TAB =======
# =================================
with tabs[2]:
    st.header("Individual Performance Breakdown")

    if weekly_data is not None and not weekly_data.empty and 'Participant' in weekly_data.columns:
        participants_list = sorted(weekly_data["Participant"].unique())
        participant_selected_ind = st.selectbox("Select Participant to Analyze", participants_list, key="ind_participant_select")
        individual_data = weekly_data[weekly_data["Participant"] == participant_selected_ind].copy()

        if not individual_data.empty:
             # --- Individual vs Group Average Time KPI ---
             st.subheader(f"{participant_selected_ind}'s Training Time vs. Group Average")
             st.markdown("Compares the **total time (duration) spent on all activities** by the selected participant against the average total time logged by **all participants** in the competition.")
             if 'Total Duration' in individual_data.columns:
                 individual_data['Total Duration'] = pd.to_numeric(individual_data['Total Duration'], errors='coerce').fillna(0)
                 participant_total_time = individual_data["Total Duration"].sum()
                 group_time_data = weekly_data.copy()
                 group_time_data['Total Duration'] = pd.to_numeric(group_time_data['Total Duration'], errors='coerce').fillna(0)
                 group_avg_total_time = group_time_data.groupby("Participant")["Total Duration"].sum().mean() if not group_time_data.groupby("Participant")["Total Duration"].sum().empty else 0
                 if group_avg_total_time > 0: percent_of_group_avg = (participant_total_time / group_avg_total_time) * 100
                 else: percent_of_group_avg = 100.0 if participant_total_time > 0 else 0.0
                 kpi_color_ind = "#00FF00" if percent_of_group_avg >= 100 else "#FFD700"
                 performance_arrow_ind = "🔼" if percent_of_group_avg >= 100 else "🔽"
                 st.markdown(f"""<div style='background-color:rgba(51, 51, 51, 0.7); padding:15px; border-radius:8px; text-align:center; margin-bottom: 15px;'><span style='color:#FFFFFF; font-size:20px; font-family: UnifrakturCook, serif;'>Total Training Time vs. Group Average:</span><br><span style='color:{kpi_color_ind}; font-size:28px; font-weight:bold; font-family: UnifrakturCook, serif;'>{percent_of_group_avg:.1f}% {performance_arrow_ind}</span><br><span style='color:#AAAAAA; font-size:14px; font-family: sans-serif;'>({participant_total_time:.0f} min vs Avg: {group_avg_total_time:.0f} min)</span></div>""", unsafe_allow_html=True)
             else: st.warning("Total Duration column missing, cannot calculate time comparison KPI.")

             # --- Individual Zone Distribution vs Group Average ---
             st.subheader(f"{participant_selected_ind}'s Time in Zone vs. Group Average")
             st.markdown("Compares the **total minutes spent in each Heart Rate Zone** by the selected participant against the average minutes spent in those zones by **all participants**.")
             zone_columns = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"]
             if all(col in individual_data.columns for col in zone_columns) and all(col in weekly_data.columns for col in zone_columns):
                 # Ensure zones are numeric for individual before summing
                 for z_col in zone_columns: individual_data[z_col] = pd.to_numeric(individual_data[z_col], errors='coerce').fillna(0)
                 participant_zones = individual_data[zone_columns].sum()
                 group_zone_data = weekly_data.copy()
                 for z_col in zone_columns: group_zone_data[z_col] = pd.to_numeric(group_zone_data[z_col], errors='coerce').fillna(0)
                 group_avg_zones = group_zone_data.groupby("Participant")[zone_columns].sum().mean() if not group_zone_data.groupby("Participant")[zone_columns].sum().empty else pd.Series(0, index=zone_columns)
                 zone_comparison_df = pd.DataFrame({ "Zone": zone_columns, f"{participant_selected_ind}": participant_zones.values, "Group Average": group_avg_zones.values }).fillna(0)
                 fig_zone_comparison = px.bar( zone_comparison_df.melt(id_vars=["Zone"], var_name="Type", value_name="Minutes"), x="Zone", y="Minutes", color="Type", barmode="group", template="plotly_dark", color_discrete_map={f"{participant_selected_ind}": "#FFD700", "Group Average": "#AAAAAA"})
                 fig_zone_comparison.update_layout( title=dict(text=f"{participant_selected_ind}'s Time per Zone vs. Group Average", x=0.01, xanchor='left', font=dict(family='UnifrakturCook, serif', color='#D4AF37')), yaxis_title="Total Minutes", xaxis_title="Heart Rate Zone", legend_title_text="")
                 st.plotly_chart(fig_zone_comparison, use_container_width=True)
             else: st.warning("One or more HR Zone columns are missing. Cannot display Zone comparison chart.")

             # --- Individual Cumulative Points Trend ---
             st.subheader(f"{participant_selected_ind}'s Cumulative Points Over Time")
             st.markdown("Shows the week-by-week **accumulation of points** for the selected participant, illustrating their scoring progression throughout the competition.")
             if all(col in individual_data.columns for col in ['Week', 'Points']):
                individual_data['Week'] = pd.to_numeric(individual_data['Week'], errors='coerce')
                individual_data.dropna(subset=['Week'], inplace=True)
                if not individual_data.empty:
                    ind_cum_points = individual_data.sort_values("Week").groupby("Week")["Points"].sum().cumsum().reset_index()
                    fig_ind_cum_points = px.line( ind_cum_points, x="Week", y="Points", markers=True, template="plotly_dark", labels={"Points": "Cumulative Points", "Week": "Competition Week"})
                    fig_ind_cum_points.update_layout( title=dict(text=f"{participant_selected_ind}'s Cumulative Points", x=0.01, xanchor='left', font=dict(family='UnifrakturCook, serif', color='#D4AF37')), yaxis_title="Cumulative Points")
                    fig_ind_cum_points.update_traces(line=dict(color='#FFD700'))
                    st.plotly_chart(fig_ind_cum_points, use_container_width=True)
                else: st.info("No valid weekly data found for this participant to plot cumulative points.")
             else: st.warning("Week or Points column missing. Cannot display cumulative points trend.")

             # --- Activity Type Breakdown (Counts & Duration) ---
             st.subheader(f"{participant_selected_ind}'s Activity Breakdown")
             st.markdown("Illustrates how the participant's logged activities are distributed by **type**, based on both the **number of sessions** and the **total time spent**.")
             if 'Workout Type' in individual_data.columns and 'Total Duration' in individual_data.columns:
                 col1, col2 = st.columns(2)
                 with col1:
                     st.markdown("##### By Number of Activities")
                     activity_counts = individual_data['Workout Type'].value_counts().reset_index()
                     activity_counts.columns = ['Workout Type', 'Count']
                     fig_act_count = px.pie(activity_counts, names='Workout Type', values='Count', template="plotly_dark", hole=0.3)
                     fig_act_count.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
                     fig_act_count.update_layout(showlegend=False, title_text='By Count', title_x=0.5, title_font_family='UnifrakturCook, serif', title_font_color='#D4AF37')
                     st.plotly_chart(fig_act_count, use_container_width=True)
                 with col2:
                     st.markdown("##### By Total Duration")
                     individual_data['Total Duration'] = pd.to_numeric(individual_data['Total Duration'], errors='coerce').fillna(0)
                     activity_duration = individual_data.groupby('Workout Type')['Total Duration'].sum().reset_index()
                     fig_act_dur = px.pie(activity_duration, names='Workout Type', values='Total Duration', template="plotly_dark", hole=0.3)
                     fig_act_dur.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
                     fig_act_dur.update_layout(showlegend=False, title_text='By Duration (min)', title_x=0.5, title_font_family='UnifrakturCook, serif', title_font_color='#D4AF37')
                     st.plotly_chart(fig_act_dur, use_container_width=True)
             else: st.warning("Workout Type or Total Duration column missing. Cannot display activity breakdown.")

             # --- Consistency Metric ---
             st.subheader(f"{participant_selected_ind}'s Consistency")
             st.markdown("Indicates the number of **distinct weeks** the participant has logged at least one activity during the competition period.")
             if 'Week' in individual_data.columns:
                 individual_data['Week'] = pd.to_numeric(individual_data['Week'], errors='coerce')
                 active_weeks = individual_data['Week'].dropna().nunique() # Ensure NaNs are dropped before nunique
                 total_competition_weeks = 8
                 st.metric(label="Active Weeks Logged", value=f"{active_weeks} out of {total_competition_weeks}")
             else: st.warning("Week column missing. Cannot calculate consistency.")
        else: st.info(f"No data found for participant: {participant_selected_ind}")
    else: st.warning("Weekly data or Participant column not available for individual analysis.")

# Optional: Add Footer or other info
st.markdown("---")
st.caption("🔥 Bourbon Chasers Strava Inferno | Data sourced from Strava activities | Dashboard by Steven Carter 🔥")

# --- END OF FILE app.py ---