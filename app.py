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
        # Optional: Return a placeholder or empty string
        return "" # Or return a default base64 image string if you have one


# Function to load image from URL
def get_base64_image_from_url(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        if response.status_code == 200:
            encoded_image = base64.b64encode(response.content).decode()
            # print(encoded_image[:100]) # Debugging
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

    /* Apply background only if image loads, handled above */

    /* Apply font styles regardless of background */
    .stApp, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp .stMarkdown, .stApp .stDataFrame, .stApp .stMetric, .stApp .stTabs /* Add other elements if needed */ {{
        font-family: 'UnifrakturCook', serif;
        color: #D4AF37; /* Gold color for text */
    }}

    /* Specific overrides if needed */
     h1, h2, h3, h4, h5, h6 {{
         font-family: 'UnifrakturCook', serif !important; /* Ensure override */
         color: #D4AF37 !important;
     }}

     /* Style Plotly chart titles if needed (might require more specific CSS selectors or theme adjustments) */
     .plotly .gtitle {
         font-family: 'UnifrakturCook', serif !important;
         fill: #D4AF37 !important; /* SVG uses fill for color */
     }

     /* Style Streamlit elements */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px; /* Space between tabs */
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: rgba(51, 51, 51, 0.7); /* Semi-transparent dark background */
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding: 10px;
        color: #D4AF37; /* Gold text */
        font-family: 'UnifrakturCook', serif;
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(212, 175, 55, 0.8); /* Semi-transparent gold background for selected */
        color: #000000; /* Black text for selected */
    }

    /* Dataframe styling */
    .stDataFrame {
        background-color: rgba(51, 51, 51, 0.7); /* Semi-transparent background for tables */
        color: #D4AF37;
    }
    .stDataFrame thead th {
       background-color: rgba(212, 175, 55, 0.8); /* Gold header */
       color: #000000; /* Black header text */
       font-family: 'UnifrakturCook', serif;
    }
    .stDataFrame tbody tr:nth-child(even) {
        background-color: rgba(70, 70, 70, 0.7); /* Slightly different shade for even rows */
    }
     .stDataFrame tbody tr:hover {
        background-color: rgba(212, 175, 55, 0.3); /* Highlight on hover */
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

# --- Sidebar Setup ---
sidebar = st.sidebar

# Load and embed the sidebar image
sidebar_image_path = "sidebar_img.png" # Ensure this file exists
base64_sidebar_image = get_base64_image(sidebar_image_path)

if base64_sidebar_image:
    sidebar.markdown(
        f"""
        <div style="text-align: center;">
            <img src='data:image/png;base64,{base64_sidebar_image}' style='max-width: 100%; border-radius: 10px;'>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    sidebar.markdown("<p style='text-align: center; color: yellow;'>Sidebar image not loaded.</p>", unsafe_allow_html=True)


sidebar.title("Bourbon Chasers")

# --- Data Loading ---
# Load TieDye_Weekly.xlsx
# @st.cache_data(ttl=0) # Removed caching for now during active development/debugging
def load_weekly_data():
    url = "https://github.com/Steven-Carter-Data/50k-Strava-Tracker/blob/main/TieDye_Weekly_Scoreboard.xlsx?raw=true"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error for bad responses (4xx, 5xx)
        # Read the Excel file from the response content
        df = pd.read_excel(BytesIO(response.content), engine="openpyxl")
        print("Data loaded successfully.")
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching data: {e}")
        return None
    except FileNotFoundError: # Although unlikely with URL, good practice
        st.error(f"Excel file not found at the URL.")
        return None
    except Exception as e:
        st.error(f"Failed to load or parse Excel file. Error: {e}")
        return None

weekly_data = load_weekly_data()

# --- Data Preprocessing ---
if weekly_data is not None and not weekly_data.empty:
    print("Preprocessing data...")
    # Convert Date column to datetime, handle potential errors
    weekly_data["Date"] = pd.to_datetime(weekly_data["Date"], errors='coerce')
    # Drop rows where Date conversion failed (optional, depends on requirements)
    weekly_data.dropna(subset=["Date"], inplace=True)

    # Sort by Date first (most recent first), then maybe by Participant if needed
    weekly_data = weekly_data.sort_values(by="Date", ascending=False)

    # Calculate Points
    zone_cols = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"]
    # Ensure zone columns exist and are numeric, fillna(0) for safety
    for col in zone_cols:
        if col not in weekly_data.columns:
            weekly_data[col] = 0 # Add missing zone columns if necessary
        else:
            weekly_data[col] = pd.to_numeric(weekly_data[col], errors='coerce').fillna(0)

    weekly_data["Points"] = (
        weekly_data["Zone 1"] * 1 + weekly_data["Zone 2"] * 2 +
        weekly_data["Zone 3"] * 3 + weekly_data["Zone 4"] * 4 +
        weekly_data["Zone 5"] * 5
    )

    # Calculate Points (this already adds/updates the 'Points' column, usually at the end)
    weekly_data["Points"] = (
        weekly_data["Zone 1"] * 1 + weekly_data["Zone 2"] * 2 +
        weekly_data["Zone 3"] * 3 + weekly_data["Zone 4"] * 4 +
        weekly_data["Zone 5"] * 5
    )

    # Now, move the 'Points' column if 'Zone 5' exists
    if "Zone 5" in weekly_data.columns and 'Points' in weekly_data.columns:
        zone5_index = weekly_data.columns.get_loc("Zone 5")
        # Pop the 'Points' column data
        points_col_data = weekly_data.pop('Points')
        # Insert it at the desired location using the popped data
        weekly_data.insert(zone5_index + 1, "Points", points_col_data)
    # else: If 'Zone 5' doesn't exist or 'Points' wasn't calculated for some reason,
    # 'Points' will remain where it was (usually appended at the end by the calculation above),
    # or won't exist if the calculation failed. This logic is fine.

    # Make relevant columns numeric, coercing errors
    numeric_cols = ["Total Distance", "Total Duration", "Week"]
    for col in numeric_cols:
         if col in weekly_data.columns:
              weekly_data[col] = pd.to_numeric(weekly_data[col], errors='coerce') # NaNs for non-numeric

    # Format Date column for display *AFTER* all date calculations are done
    # We'll format it just before displaying in the dataframe

    print("Data preprocessing complete.")
else:
    st.error("Failed to load or process the weekly data. Some features may be unavailable.")
    # Create an empty DataFrame with expected columns to prevent downstream errors
    expected_cols = ["Date", "Participant", "Workout Type", "Total Duration", "Total Distance",
                     "Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Points", "Week"]
    weekly_data = pd.DataFrame(columns=expected_cols)


# --- Dynamic Week Calculation ---
def get_current_week(start_date_dt):
    today = datetime.today().date()
    # Ensure start_date_dt is a date object
    if isinstance(start_date_dt, datetime):
        start_date_dt = start_date_dt.date()

    if today < start_date_dt:
       # Maybe competition hasn't started yet according to the fixed date?
       # Or adjust logic if start date can be in the future relative to today.
       # For now, assume competition starts on or before today if code runs.
       # If start date is fixed and in the future, week might be 0 or negative.
       return 1 # Or handle as appropriate, maybe return 0 or raise error?

    days_since_start = (today - start_date_dt).days
    week_number = (days_since_start // 7) + 1
    competition_duration_weeks = 8 # Define total weeks
    return min(max(week_number, 1), competition_duration_weeks)

# Define the competition start date
# Use a fixed, known start date for consistency
competition_start_datetime = datetime(2024, 3, 10) # Example: March 10th, 2024
current_week = get_current_week(competition_start_datetime)
print(f"Current Competition Week: {current_week}")


# --- Sidebar Filters --- (Place after data loading and week calc)
if weekly_data is not None and not weekly_data.empty:
    participants = sorted(weekly_data["Participant"].unique())
    selected_participant_sb = sidebar.selectbox("Select a Bourbon Chaser", ["All"] + participants, key="sb_participant")

    all_weeks_options = [f"Week {i}" for i in range(1, 9)] # Assuming 8 weeks total
    all_weeks_options.insert(0, "All Weeks")
    # Default to the current calculated week
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

        # Apply filters based on sidebar selections
        filtered_display_data = weekly_data.copy() # Work on a copy for display filtering

        if selected_week_str_sb != "All Weeks":
            try:
                selected_week_num = int(selected_week_str_sb.replace("Week ", ""))
                # Ensure 'Week' column is numeric before filtering
                if 'Week' in filtered_display_data.columns:
                     filtered_display_data['Week'] = pd.to_numeric(filtered_display_data['Week'], errors='coerce')
                     filtered_display_data = filtered_display_data[filtered_display_data["Week"] == selected_week_num]
                else:
                     st.warning("Week column not found for filtering.")
            except ValueError:
                 st.warning(f"Invalid week selection: {selected_week_str_sb}")

        if selected_participant_sb != "All":
             if 'Participant' in filtered_display_data.columns:
                  filtered_display_data = filtered_display_data[filtered_display_data["Participant"] == selected_participant_sb]
             else:
                  st.warning("Participant column not found for filtering.")


        # Format Date for display *just before* showing the dataframe
        if "Date" in filtered_display_data.columns:
             filtered_display_data["Date"] = filtered_display_data["Date"].dt.strftime("%B %d, %Y")

        # Select and order columns for display if needed
        display_cols = ["Date", "Participant", "Workout Type", "Total Duration", "Total Distance",
                        "Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Points", "Week"]
        # Filter to only columns that actually exist in the dataframe
        display_cols = [col for col in display_cols if col in filtered_display_data.columns]
        st.dataframe(filtered_display_data[display_cols], use_container_width=True, hide_index=True)


        # --- Competition Leaderboard Calculation ---
        def calculate_leaderboard(data, total_weeks):
            if data is None or data.empty or "Participant" not in data.columns or "Points" not in data.columns:
                 return pd.DataFrame(columns=["Rank", "Participant", "Points", "Points Behind"]) # Return empty structure

            leaderboard = data.groupby("Participant")["Points"].sum().reset_index()
            leaderboard = leaderboard.sort_values(by="Points", ascending=False)

            # Calculate "Points Behind"
            if not leaderboard.empty:
                max_points = leaderboard["Points"].iloc[0] # Get top score
                leaderboard["Points Behind"] = max_points - leaderboard["Points"]
            else:
                leaderboard["Points Behind"] = 0

            # Add Rank
            leaderboard.reset_index(drop=True, inplace=True)
            leaderboard.insert(0, 'Rank', leaderboard.index + 1)

            # Insert "Points Behind" column immediately after "Points"
            if "Points Behind" in leaderboard.columns: # Check if column exists before popping
                points_idx = leaderboard.columns.get_loc("Points")
                points_behind_col = leaderboard.pop("Points Behind")
                leaderboard.insert(points_idx + 1, "Points Behind", points_behind_col)

            # Add weekly totals
            if 'Week' in data.columns and 'Points' in data.columns:
                data['Week'] = pd.to_numeric(data['Week'], errors='coerce') # Ensure Week is numeric
                for week_num in range(1, total_weeks + 1):
                    week_points = data[data["Week"] == week_num].groupby("Participant")["Points"].sum()
                    leaderboard[f"Week {week_num} Totals"] = leaderboard["Participant"].map(week_points).fillna(0).astype(int) # Fill NaNs with 0

            return leaderboard

        # Assuming competition duration is 8 weeks for column generation
        competition_total_weeks = 8
        leaderboard_df = calculate_leaderboard(weekly_data.copy(), competition_total_weeks) # Use a copy

        # --- Display Leaderboard ---
        st.subheader("Strava Competition Leaderboard")
        st.markdown("Overall ranking based on **cumulative points** earned from HR Zones across all activities and weeks. Also shows points behind the leader and a breakdown of points earned each week.")
        st.dataframe(leaderboard_df, use_container_width=True, hide_index=True)


        # --- Biggest Mover Highlight ---
        st.subheader(f"🔥 Biggest Points Mover and Shaker - Week {current_week}")
        st.caption(f"Highlights the participant who earned the most points specifically in Week {current_week}.")
        if current_week > 0 and not leaderboard_df.empty:
            current_week_col = f"Week {current_week} Totals"
            if current_week_col in leaderboard_df.columns:
                 # Find the participant with the max points in the current week's column
                 biggest_mover = leaderboard_df.loc[leaderboard_df[current_week_col].idxmax()]
                 st.success(f"**{biggest_mover['Participant']}** with **{biggest_mover[current_week_col]:.0f} points** earned this week!")
            else:
                 st.info(f"Week {current_week} data not yet available or column missing.")
        elif current_week == 0:
             st.info("Competition hasn't started yet (Week 0).")
        else:
             st.info("Leaderboard data needed to calculate Biggest Mover.")


        # --- Top Runners Visualization ---
        st.subheader("Top Runners by Distance and Duration")
        st.markdown("Compares participants based on their **total accumulated running distance** and **total running duration** throughout the competition. Average pace for runs is shown on the distance bars.")
        # Ensure columns exist and filter for "Run" type
        if all(col in weekly_data.columns for col in ["Total Distance", "Workout Type", "Total Duration", "Participant"]):
            run_data = weekly_data[weekly_data["Workout Type"].str.contains("Run", case=False, na=False)].copy() # Filter for runs

            if not run_data.empty:
                # Ensure data is numeric before aggregation
                run_data["Total Distance"] = pd.to_numeric(run_data["Total Distance"], errors='coerce').fillna(0)
                run_data["Total Duration"] = pd.to_numeric(run_data["Total Duration"], errors='coerce').fillna(0)

                distance_data = run_data.groupby("Participant")["Total Distance"].sum().reset_index()
                duration_data = run_data.groupby("Participant")["Total Duration"].sum().reset_index() # Duration in minutes

                # Merge and calculate pace
                combined_data = pd.merge(distance_data, duration_data, on="Participant", how="left") # Use left merge to keep all runners
                # Avoid division by zero for pace calculation
                combined_data["Pace (min/mile)"] = combined_data.apply(
                    lambda row: row["Total Duration"] / row["Total Distance"] if row["Total Distance"] > 0 else 0, axis=1
                )
                # Format pace
                combined_data["Formatted Pace"] = combined_data["Pace (min/mile)"].apply(
                    lambda x: f"{int(x)}:{int((x % 1) * 60):02d} min/mi" if x > 0 else "N/A"
                 )

                combined_data = combined_data.sort_values(by="Total Distance", ascending=True) # Ascending for horizontal bar chart growth

                # Prepare data for Plotly (melt)
                melted_data = combined_data.melt(id_vars=["Participant", "Formatted Pace"],
                                                value_vars=["Total Distance", "Total Duration"],
                                                var_name="Metric", value_name="Value")

                # Convert Duration to Hours for the chart axis label, but keep original for potential tooltips if needed
                melted_data['Display Value'] = melted_data.apply(lambda row: row['Value'] / 60 if row['Metric'] == 'Total Duration' else row['Value'], axis=1)
                melted_data['Metric Label'] = melted_data['Metric'].replace({"Total Distance": "Distance (miles)", "Total Duration": "Duration (hours)"})


                # Create hover text
                melted_data['Hover Text'] = melted_data.apply(
                    lambda row: f"<b>{row['Participant']}</b><br>{row['Metric Label']}: {row['Display Value']:.2f}<br>Avg Pace: {row['Formatted Pace']}" if row['Metric'] == 'Total Distance' else f"<b>{row['Participant']}</b><br>{row['Metric Label']}: {row['Display Value']:.2f}",
                    axis=1
                )

                # Create the bar chart
                fig_runners = px.bar(
                    melted_data,
                    x="Display Value",
                    y="Participant",
                    color="Metric Label", # Use the formatted label for legend
                    orientation="h",
                    color_discrete_map={"Distance (miles)": "#E25822", "Duration (hours)": "#FFD700"}, # Map colors explicitly
                    template="plotly_dark",
                    # Add hover text:
                    hover_name="Participant", # Shows participant name bolded at top
                    hover_data={ # Customize hover data, hide defaults if needed
                         'Participant': False, # Already in hover_name
                         'Metric Label': False, # Already shown by color legend
                         'Display Value': ':.2f', # Format numeric value
                         'Formatted Pace': (melted_data['Metric Label'] == 'Distance (miles)') # Conditionally show pace only for distance
                    }
                    # Use custom hovertemplate for full control (alternative to hover_data)
                    # hover_template = melted_data['Hover Text'].tolist() # Requires careful matching
                )

                # Add text labels (Pace on distance, value on duration)
                fig_runners.update_traces(textposition='auto') # Let Plotly handle placement initially
                fig_runners.update_traces(
                    text=melted_data.apply(lambda row: row['Formatted Pace'] if row['Metric Label'] == 'Distance (miles)' else f"{row['Display Value']:.1f} hrs", axis=1),
                    selector=dict(type='bar') # Apply text to bar traces
                )


                fig_runners.update_layout(
                    title=dict(
                        text="Total Running Distance & Duration by Bourbon Chaser",
                        x=0.01, # Align title left
                        xanchor="left",
                        font=dict(size=20, family='UnifrakturCook, serif', color='#D4AF37')
                    ),
                    xaxis_title="Value (Miles or Hours)",
                    yaxis_title="Participant",
                    legend_title_text="Metric",
                    barmode='group', # Or 'stack' if preferred, group is usually clearer here
                    yaxis={'categoryorder':'total ascending'} # Keep the sort order from dataframe
                )
                st.plotly_chart(fig_runners, use_container_width=True)
            else:
                st.info("No running data found to display the runners chart.")
        else:
            st.warning("Required columns for the runners chart are missing (Total Distance, Workout Type, Total Duration, Participant).")


        # --- Group Weekly Running Distance Progress ---
        st.subheader("Group Weekly Running Distance Progress")
        st.markdown("Tracks the **total distance run by the entire group** each week. This shows the overall trend in collective running volume throughout the competition.")
        # Ensure required columns are present
        if all(col in weekly_data.columns for col in ["Week", "Total Distance", "Workout Type"]):
             running_data_group = weekly_data[weekly_data["Workout Type"].str.contains("Run", case=False, na=False)].copy()
             if not running_data_group.empty:
                 running_data_group['Week'] = pd.to_numeric(running_data_group['Week'], errors='coerce')
                 running_data_group['Total Distance'] = pd.to_numeric(running_data_group['Total Distance'], errors='coerce').fillna(0)

                 weekly_distance = running_data_group.groupby("Week")["Total Distance"].sum().reset_index()
                 weekly_distance = weekly_distance.sort_values("Week")

                 fig_weekly_miles = px.line(
                     weekly_distance,
                     x="Week",
                     y="Total Distance",
                     markers=True,
                     # title="Total Group Miles Run by Week", # Title set in layout for styling
                     labels={"Total Distance": "Total Distance (Miles)", "Week": "Competition Week"},
                     template="plotly_dark"
                 )
                 fig_weekly_miles.update_layout(
                    title=dict(text="Total Group Miles Run by Week", x=0.01, xanchor='left', font=dict(family='UnifrakturCook, serif', color='#D4AF37')),
                    yaxis_title="Total Distance (Miles)"
                 )
                 fig_weekly_miles.update_traces(line=dict(color='#E25822')) # Use a running color
                 st.plotly_chart(fig_weekly_miles, use_container_width=True)

                 # --- Week-to-Date Running Distance KPI ---
                 st.caption("Compares the group's total running distance logged **so far this week** against the distance logged during the **same period last week** (e.g., Monday-Wednesday this week vs. Monday-Wednesday last week).")
                 # Ensure 'Date' is datetime for comparison
                 running_data_group["Date"] = pd.to_datetime(running_data_group["Date"], errors='coerce')
                 running_data_group.dropna(subset=["Date"], inplace=True) # Remove rows where date conversion failed

                 today_date = datetime.today().date()
                 start_date_dt = competition_start_datetime.date() # Use the defined start date

                 # Calculate current and previous week date ranges based on today's progress within the week
                 if today_date >= start_date_dt:
                     days_since_start = (today_date - start_date_dt).days
                     current_week_num_for_calc = (days_since_start // 7) + 1
                     day_of_current_week = days_since_start % 7 # 0=Sunday, 1=Monday... if start is Sunday

                     current_week_start_dt = start_date_dt + timedelta(weeks=current_week_num_for_calc - 1)
                     current_period_end_dt = current_week_start_dt + timedelta(days=day_of_current_week)

                     prev_week_start_dt = current_week_start_dt - timedelta(weeks=1)
                     prev_period_end_dt = prev_week_start_dt + timedelta(days=day_of_current_week)

                     # Sum distances within these date ranges
                     current_week_distance = running_data_group[
                         (running_data_group["Date"].dt.date >= current_week_start_dt) & (running_data_group["Date"].dt.date <= current_period_end_dt)
                     ]["Total Distance"].sum()

                     prev_week_distance = running_data_group[
                         (running_data_group["Date"].dt.date >= prev_week_start_dt) & (running_data_group["Date"].dt.date <= prev_period_end_dt)
                     ]["Total Distance"].sum()

                     # Calculate percentage change
                     if prev_week_distance > 0:
                         pct_change_distance = ((current_week_distance - prev_week_distance) / prev_week_distance) * 100
                     elif current_week_distance > 0:
                         pct_change_distance = 100.0 # Positive change if current > 0 and previous was 0
                     else:
                         pct_change_distance = 0.0 # No change if both are 0

                     kpi_color = "#00FF00" if pct_change_distance >= 0 else "#FF4136" # Green/Red
                     kpi_arrow = "🔼" if pct_change_distance >= 0 else "🔽"

                     st.markdown(
                         f"""
                         <div style='background-color:rgba(51, 51, 51, 0.7); padding:15px; border-radius:8px; text-align:center; margin-bottom: 15px;'>
                             <span style='color:#FFFFFF; font-size:20px; font-family: UnifrakturCook, serif;'>WtD Running Distance vs Prev. Week:</span><br>
                             <span style='color:{kpi_color}; font-size:26px; font-weight:bold; font-family: UnifrakturCook, serif;'>
                                 {pct_change_distance:.1f}% {kpi_arrow}
                             </span><br>
                             <span style='color:#AAAAAA; font-size:14px; font-family: sans-serif;'>(Current: {current_week_distance:.1f} mi | Previous: {prev_week_distance:.1f} mi)</span>
                         </div>
                         """,
                         unsafe_allow_html=True
                     )
                 else:
                      st.info("Week-to-Date comparison starts after the competition begin date.")

             else:
                 st.info("No running data available to calculate weekly group distance progress or WtD KPI.")
        else:
             st.warning("Required columns missing for Group Weekly Running Distance chart (Week, Total Distance, Workout Type).")


        # --- Group Activity Level Progress (WtD Count) ---
        st.subheader("Group Activity Count Progress (Week-to-Date)")
        st.markdown("Compares the **total number of activities** (all types) logged by the group **so far this week** against the count from the **same period last week**.")
        # Ensure 'Date' is datetime
        weekly_data_kpi = weekly_data.copy() # Use a fresh copy
        weekly_data_kpi["Date"] = pd.to_datetime(weekly_data_kpi["Date"], errors='coerce')
        weekly_data_kpi.dropna(subset=["Date"], inplace=True)

        if not weekly_data_kpi.empty:
             today_date = datetime.today().date()
             start_date_dt = competition_start_datetime.date()

             if today_date >= start_date_dt:
                 # Reuse date calculation logic from distance KPI
                 days_since_start = (today_date - start_date_dt).days
                 current_week_num_for_calc = (days_since_start // 7) + 1
                 day_of_current_week = days_since_start % 7

                 current_week_start_dt = start_date_dt + timedelta(weeks=current_week_num_for_calc - 1)
                 current_period_end_dt = current_week_start_dt + timedelta(days=day_of_current_week)

                 prev_week_start_dt = current_week_start_dt - timedelta(weeks=1)
                 prev_period_end_dt = prev_week_start_dt + timedelta(days=day_of_current_week)

                 # Count activities within these date ranges
                 current_week_activity_count = weekly_data_kpi[
                     (weekly_data_kpi["Date"].dt.date >= current_week_start_dt) & (weekly_data_kpi["Date"].dt.date <= current_period_end_dt)
                 ].shape[0]

                 prev_week_activity_count = weekly_data_kpi[
                     (weekly_data_kpi["Date"].dt.date >= prev_week_start_dt) & (weekly_data_kpi["Date"].dt.date <= prev_period_end_dt)
                 ].shape[0]

                 # Calculate percentage change
                 if prev_week_activity_count > 0:
                     pct_change_activity = ((current_week_activity_count - prev_week_activity_count) / prev_week_activity_count) * 100
                 elif current_week_activity_count > 0:
                     pct_change_activity = 100.0
                 else:
                     pct_change_activity = 0.0

                 activity_color = "#00FF00" if pct_change_activity >= 0 else "#FF4136"
                 activity_arrow = "🔼" if pct_change_activity >= 0 else "🔽"

                 st.markdown(
                     f"""
                     <div style='background-color:rgba(51, 51, 51, 0.7); padding:15px; border-radius:8px; text-align:center; margin-bottom: 15px;'>
                         <span style='color:#FFFFFF; font-size:20px; font-family: UnifrakturCook, serif;'>WtD Activity Count vs Prev. Week:</span><br>
                         <span style='color:{activity_color}; font-size:26px; font-weight:bold; font-family: UnifrakturCook, serif;'>
                             {pct_change_activity:.1f}% {activity_arrow}
                         </span><br>
                         <span style='color:#AAAAAA; font-size:14px; font-family: sans-serif;'>(Current: {current_week_activity_count} | Previous: {prev_week_activity_count})</span>
                     </div>
                     """,
                     unsafe_allow_html=True
                 )
             else:
                 st.info("Week-to-Date comparison starts after the competition begin date.")
        else:
             st.info("No data available to calculate Week-to-Date Activity Count.")


        # --- Group Points Progress (WtD Points) ---
        st.subheader("Group Points Progress (Week-to-Date)")
        st.markdown("Compares the **total points earned** by the group **so far this week** against the points earned during the **same period last week**.")
        if 'Points' in weekly_data_kpi.columns and not weekly_data_kpi.empty: # Reuse df from previous KPI
             # Dates are already calculated and filtered
              today_date = datetime.today().date()
              start_date_dt = competition_start_datetime.date()

              if today_date >= start_date_dt:
                 # Reuse date ranges from previous KPIs
                 days_since_start = (today_date - start_date_dt).days
                 current_week_num_for_calc = (days_since_start // 7) + 1
                 day_of_current_week = days_since_start % 7

                 current_week_start_dt = start_date_dt + timedelta(weeks=current_week_num_for_calc - 1)
                 current_period_end_dt = current_week_start_dt + timedelta(days=day_of_current_week)

                 prev_week_start_dt = current_week_start_dt - timedelta(weeks=1)
                 prev_period_end_dt = prev_week_start_dt + timedelta(days=day_of_current_week)


                 # Sum points within these date ranges
                 current_week_points = weekly_data_kpi[
                     (weekly_data_kpi["Date"].dt.date >= current_week_start_dt) & (weekly_data_kpi["Date"].dt.date <= current_period_end_dt)
                 ]["Points"].sum()

                 prev_week_points = weekly_data_kpi[
                     (weekly_data_kpi["Date"].dt.date >= prev_week_start_dt) & (weekly_data_kpi["Date"].dt.date <= prev_period_end_dt)
                 ]["Points"].sum()

                 # Calculate percentage change
                 if prev_week_points > 0:
                     pct_change_points = ((current_week_points - prev_week_points) / prev_week_points) * 100
                 elif current_week_points > 0:
                     pct_change_points = 100.0
                 else:
                     pct_change_points = 0.0

                 points_kpi_color = "#00FF00" if pct_change_points >= 0 else "#FF4136"
                 points_kpi_arrow = "🔼" if pct_change_points >= 0 else "🔽"

                 st.markdown(
                     f"""
                     <div style='background-color:rgba(51, 51, 51, 0.7); padding:15px; border-radius:8px; text-align:center; margin-bottom: 15px;'>
                         <span style='color:#FFFFFF; font-size:20px; font-family: UnifrakturCook, serif;'>WtD Points Earned vs Prev. Week:</span><br>
                         <span style='color:{points_kpi_color}; font-size:26px; font-weight:bold; font-family: UnifrakturCook, serif;'>
                             {pct_change_points:.1f}% {points_kpi_arrow}
                         </span><br>
                          <span style='color:#AAAAAA; font-size:14px; font-family: sans-serif;'>(Current: {current_week_points:.0f} | Previous: {prev_week_points:.0f})</span>
                     </div>
                     """,
                     unsafe_allow_html=True
                 )
              else:
                 st.info("Week-to-Date comparison starts after the competition begin date.")

        else:
             st.info("Points data needed to calculate Week-to-Date Points change.")


    else: # Handle case where weekly_data is None or empty from the start
        st.warning("No weekly data loaded. Leaderboards and group trends cannot be displayed.")


# ===========================
# ======= OVERVIEW TAB =======
# ===========================
with tabs[1]:
    st.header("Competition Overview")
    # This markdown already serves as a good description. Keep as is.
    st.markdown(
        """
        ### **Bourbon Chasers - The Descent into Madness**
        Welcome to the Inferno! Over the next **8 weeks** (starting March 10th, 2024), you will battle for supremacy using **Heart Rate (HR) Zones** from your activities to earn points.
        This scoring method aims to level the playing field across different types of endurance activities.

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
        """
    )

# =================================
# ======= INDIVIDUAL ANALYSIS TAB =======
# =================================
with tabs[2]:
    st.header("Individual Performance Breakdown")

    if weekly_data is not None and not weekly_data.empty and 'Participant' in weekly_data.columns:
        # Participant Selection Dropdown within the tab
        participants_list = sorted(weekly_data["Participant"].unique())
        participant_selected_ind = st.selectbox(
            "Select Participant to Analyze", participants_list, key="ind_participant_select"
        )

        # Filter data for the selected participant
        individual_data = weekly_data[weekly_data["Participant"] == participant_selected_ind].copy()

        if not individual_data.empty:

             # --- Individual vs Group Average Time KPI ---
             st.subheader(f"{participant_selected_ind}'s Training Time vs. Group Average")
             st.markdown("Compares the **total time (duration) spent on all activities** by the selected participant against the average total time logged by **all participants** in the competition.")
             if 'Total Duration' in individual_data.columns:
                 participant_total_time = individual_data["Total Duration"].sum()
                 # Calculate group average total time robustly
                 group_avg_total_time = weekly_data.groupby("Participant")["Total Duration"].sum().mean() if not weekly_data.groupby("Participant")["Total Duration"].sum().empty else 0

                 if group_avg_total_time > 0:
                     percent_of_group_avg = (participant_total_time / group_avg_total_time) * 100
                 else:
                     percent_of_group_avg = 100.0 if participant_total_time > 0 else 0.0 # Handle division by zero

                 kpi_color_ind = "#00FF00" if percent_of_group_avg >= 100 else "#FFD700" # Green / Yellow (less harsh than red)
                 performance_arrow_ind = "🔼" if percent_of_group_avg >= 100 else "🔽"

                 st.markdown(
                     f"""
                     <div style='background-color:rgba(51, 51, 51, 0.7); padding:15px; border-radius:8px; text-align:center; margin-bottom: 15px;'>
                         <span style='color:#FFFFFF; font-size:20px; font-family: UnifrakturCook, serif;'>Total Training Time vs. Group Average:</span><br>
                         <span style='color:{kpi_color_ind}; font-size:28px; font-weight:bold; font-family: UnifrakturCook, serif;'>
                             {percent_of_group_avg:.1f}% {performance_arrow_ind}
                         </span><br>
                         <span style='color:#AAAAAA; font-size:14px; font-family: sans-serif;'>({participant_total_time:.0f} min vs Avg: {group_avg_total_time:.0f} min)</span>
                     </div>
                     """,
                     unsafe_allow_html=True
                 )
             else:
                 st.warning("Total Duration column missing, cannot calculate time comparison KPI.")


             # --- Individual Zone Distribution vs Group Average ---
             st.subheader(f"{participant_selected_ind}'s Time in Zone vs. Group Average")
             st.markdown("Compares the **total minutes spent in each Heart Rate Zone** by the selected participant against the average minutes spent in those zones by **all participants**.")
             zone_columns = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"]
             # Check if zone columns exist
             if all(col in individual_data.columns for col in zone_columns):
                 participant_zones = individual_data[zone_columns].sum()
                 # Calculate group average robustly
                 group_avg_zones = weekly_data.groupby("Participant")[zone_columns].sum().mean() if not weekly_data.groupby("Participant")[zone_columns].sum().empty else pd.Series(0, index=zone_columns)

                 zone_comparison_df = pd.DataFrame({
                     "Zone": zone_columns,
                     f"{participant_selected_ind}": participant_zones.values,
                     "Group Average": group_avg_zones.values
                 }).fillna(0) # Ensure no NaNs if a participant had no time in a zone

                 fig_zone_comparison = px.bar(
                     zone_comparison_df.melt(id_vars=["Zone"], var_name="Type", value_name="Minutes"),
                     x="Zone",
                     y="Minutes",
                     color="Type",
                     barmode="group",
                     template="plotly_dark",
                     color_discrete_map={f"{participant_selected_ind}": "#FFD700", "Group Average": "#AAAAAA"}, # Gold vs Grey
                     # title=f"{participant_selected_ind}'s Time per Zone vs. Group Average" # Title in layout
                 )
                 fig_zone_comparison.update_layout(
                     title=dict(text=f"{participant_selected_ind}'s Time per Zone vs. Group Average", x=0.01, xanchor='left', font=dict(family='UnifrakturCook, serif', color='#D4AF37')),
                     yaxis_title="Total Minutes",
                     xaxis_title="Heart Rate Zone",
                     legend_title_text="" # Remove legend title "Type"
                 )
                 st.plotly_chart(fig_zone_comparison, use_container_width=True)
             else:
                 st.warning("One or more HR Zone columns are missing. Cannot display Zone comparison chart.")


             # --- Individual Cumulative Points Trend ---
             st.subheader(f"{participant_selected_ind}'s Cumulative Points Over Time")
             st.markdown("Shows the week-by-week **accumulation of points** for the selected participant, illustrating their scoring progression throughout the competition.")
             if all(col in individual_data.columns for col in ['Week', 'Points']):
                individual_data['Week'] = pd.to_numeric(individual_data['Week'], errors='coerce')
                individual_data.dropna(subset=['Week'], inplace=True) # Drop rows where Week is not numeric
                if not individual_data.empty:
                    ind_cum_points = individual_data.sort_values("Week").groupby("Week")["Points"].sum().cumsum().reset_index()
                    fig_ind_cum_points = px.line(
                        ind_cum_points,
                        x="Week",
                        y="Points",
                        title=f"{participant_selected_ind}'s Cumulative Points Over Time", # Title in layout
                        markers=True,
                        template="plotly_dark",
                        labels={"Points": "Cumulative Points", "Week": "Competition Week"}
                    )
                    fig_ind_cum_points.update_layout(
                         title=dict(text=f"{participant_selected_ind}'s Cumulative Points", x=0.01, xanchor='left', font=dict(family='UnifrakturCook, serif', color='#D4AF37')),
                         yaxis_title="Cumulative Points"
                    )
                    fig_ind_cum_points.update_traces(line=dict(color='#FFD700')) # Gold line
                    st.plotly_chart(fig_ind_cum_points, use_container_width=True)
                else:
                     st.info("No valid weekly data found for this participant to plot cumulative points.")
             else:
                 st.warning("Week or Points column missing. Cannot display cumulative points trend.")


             # --- Activity Type Breakdown (Counts & Duration) ---
             st.subheader(f"{participant_selected_ind}'s Activity Breakdown")
             st.markdown("Illustrates how the participant's logged activities are distributed by **type**, based on both the **number of sessions** and the **total time spent**.")
             if 'Workout Type' in individual_data.columns and 'Total Duration' in individual_data.columns:
                 col1, col2 = st.columns(2)
                 with col1:
                     st.markdown("##### By Number of Activities")
                     activity_counts = individual_data['Workout Type'].value_counts().reset_index()
                     activity_counts.columns = ['Workout Type', 'Count']
                     fig_act_count = px.pie(activity_counts, names='Workout Type', values='Count',
                                           # title='Activity Count by Type', # Keep title minimal for pie
                                           template="plotly_dark", hole=0.3) # Donut chart
                     fig_act_count.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
                     fig_act_count.update_layout(showlegend=False, title_text='By Count', title_x=0.5, title_font_family='UnifrakturCook, serif', title_font_color='#D4AF37')
                     st.plotly_chart(fig_act_count, use_container_width=True)

                 with col2:
                     st.markdown("##### By Total Duration")
                     activity_duration = individual_data.groupby('Workout Type')['Total Duration'].sum().reset_index()
                     fig_act_dur = px.pie(activity_duration, names='Workout Type', values='Total Duration',
                                         # title='Total Duration by Activity Type (minutes)',
                                         template="plotly_dark", hole=0.3)
                     fig_act_dur.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
                     fig_act_dur.update_layout(showlegend=False, title_text='By Duration (min)', title_x=0.5, title_font_family='UnifrakturCook, serif', title_font_color='#D4AF37')
                     st.plotly_chart(fig_act_dur, use_container_width=True)
             else:
                 st.warning("Workout Type or Total Duration column missing. Cannot display activity breakdown.")


             # --- Consistency Metric ---
             st.subheader(f"{participant_selected_ind}'s Consistency")
             st.markdown("Indicates the number of **distinct weeks** the participant has logged at least one activity during the competition period.")
             if 'Week' in individual_data.columns:
                 active_weeks = individual_data['Week'].nunique()
                 total_competition_weeks = 8 # Or derive from data: weekly_data['Week'].nunique() if reliable
                 st.metric(label="Active Weeks Logged", value=f"{active_weeks} out of {total_competition_weeks}")
             else:
                 st.warning("Week column missing. Cannot calculate consistency.")

        else: # Handle case where selected participant has no data
             st.info(f"No data found for participant: {participant_selected_ind}")

    else: # Handle case where weekly_data is None or participant column missing
         st.warning("Weekly data or Participant column not available for individual analysis.")


# Optional: Add Footer or other info
st.markdown("---")
st.caption("🔥 Bourbon Chasers Strava Inferno | Data sourced from Strava activities | Analysis by [Your Name/Group] 🔥")

# --- END OF FILE app.py ---


# # --- START OF V.1 ---

# import streamlit as st
# import pandas as pd
# import base64
# import plotly.express as px
# from datetime import datetime
# import openpyxl
# import requests
# from io import BytesIO
# from datetime import timedelta

# st.set_page_config(
#     page_title="🔥 Bourbon Chasers Strava Inferno 🔥",
#     layout="wide"
# )

# # Function to encode images in base64
# def get_base64_image(image_path):
#     with open(image_path, "rb") as image_file:
#         return base64.b64encode(image_file.read()).decode()

# # Load and embed the background image
# def get_base64_image_from_url(image_url):
#     response = requests.get(image_url)
#     if response.status_code == 200:
#         encoded_image = base64.b64encode(response.content).decode()
#         print(encoded_image[:100])  # Debugging: Print first 100 characters
#         return encoded_image
#     else:
#         print(f"Error: Unable to load image. HTTP Status Code: {response.status_code}")
#         return ""

# image_url = "https://raw.githubusercontent.com/Steven-Carter-Data/50k-Strava-Tracker/main/bg_smolder.png"

# base64_image = get_base64_image_from_url(image_url)

# # Insert background image into Streamlit app
# st.markdown(
#     f"""
#     <style>
#     .stApp {{
#         background: url('data:image/png;base64,{base64_image}') no-repeat center center fixed !important;
#         background-size: cover !important;
#         background-position: center !important;
#     }}
#     </style>
#     """,
#     unsafe_allow_html=True
# )

# st.markdown(
#     """
#     <style>
#     @import url('https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&display=swap');

#     .stApp {{
#         background: url('data:image/png;base64,{base64_image}') no-repeat center center fixed;
#         background-size: cover;
#         font-family: 'UnifrakturCook', serif;
#         color: #D4AF37;
#     }}
#     h1, h2, h3, h4, h5, h6 {{
#         font-family: 'UnifrakturCook', serif;
#         color: #D4AF37;
#     }}
#     </style>
#     """,
#     unsafe_allow_html=True
# )

# # Title header 
# st.markdown(
#     """
#     <h1 style="text-align: center; font-family: 'UnifrakturCook', serif; font-size: 60px; font-weight: bold; color: #D4AF37; max-width: 90%; margin: auto; word-wrap: break-word;">
#     Welcome to the Inferno
#     </h1>
#     """,
#     unsafe_allow_html=True
# )

# # Title Sub-header
# st.markdown(
#     '<h3 style="text-align: center; font-family: UnifrakturCook, serif; font-size: 25px; font-weight: bold; color: #D4AF37;">'
#     'Bourbon Chasers - The descent into madness has begun!</h3>',
#     unsafe_allow_html=True
# )

# # Sidebar setup
# sidebar = st.sidebar

# # Load and embed the sidebar image
# sidebar_image = "sidebar_img.png"  # Make sure this file exists in the same directory
# base64_sidebar_image = get_base64_image(sidebar_image)

# sidebar.markdown(
#     f"""
#     <div style="text-align: center;">
#         <img src='data:image/png;base64,{base64_sidebar_image}' style='max-width: 100%; border-radius: 10px;'>
#     </div>
#     """,
#     unsafe_allow_html=True
# )

# sidebar.title("Bourbon Chasers")

# # Load TieDye_Weekly.xlsx
# @st.cache_data(ttl=0)
# def load_weekly_data():
#     url = "https://github.com/Steven-Carter-Data/50k-Strava-Tracker/blob/main/TieDye_Weekly_Scoreboard.xlsx?raw=true"
#     try:
#         response = requests.get(url)
#         response.raise_for_status()  # Raise error for bad responses (4xx, 5xx)
        
#         # Read the Excel file from the response content
#         return pd.read_excel(BytesIO(response.content), engine="openpyxl")

#     except Exception as e:
#         st.warning(f"TieDye_Weekly_Scoreboard.xlsx not found. Please check the URL or upload it manually. Error: {e}")
#         return None

# weekly_data = load_weekly_data()

# if weekly_data is not None:
#     # Convert Date column to datetime for proper sorting
#     weekly_data["Date"] = pd.to_datetime(weekly_data["Date"])
#     # Sort by the DataFrame’s index in descending order
#     weekly_data = weekly_data.sort_index(ascending=False)
#     # Insert "Points" column right after "Zone 5" column
#     if "Zone 5" in weekly_data.columns:
#         zone5_index = weekly_data.columns.get_loc("Zone 5")
#         weekly_data.insert(zone5_index + 1, "Points", 
#             weekly_data["Zone 1"] * 1 + weekly_data["Zone 2"] * 2 + 
#             weekly_data["Zone 3"] * 3 + weekly_data["Zone 4"] * 4 + 
#             weekly_data["Zone 5"] * 5)
#     # Format Date column to display only Month, Day, Year
#     weekly_data["Date"] = weekly_data["Date"].dt.strftime("%B %d, %Y")

# # Determine current week dynamically
# def get_current_week():
#     today = datetime.today().date()
#     current_year = today.year
#     start_date = datetime(current_year, 3, 10).date()
#     if today < start_date:
#         start_date = datetime(current_year - 1, 3, 10).date()
#     days_since_start = (today - start_date).days
#     week_number = (days_since_start // 7) + 1
#     return min(max(week_number, 1), 8)

# current_week = get_current_week()

# # Tabs for navigation
# tabs = st.tabs(["Leaderboards", "Overview", "Individual Analysis"])

# with tabs[0]:  # Leaderboards tab
#     if weekly_data is not None:
#         # The weekly_data is already sorted and formatted with the new "Points" column

#         # Add participant filter in the sidebar
#         participants = sorted(weekly_data["Participant"].unique())
#         selected_participant = sidebar.selectbox("Select a Bourbon Chaser", ["All"] + participants)
        
#         # Add week filter in the sidebar with 8 weeks and "All Weeks" option
#         all_weeks = [f"Week {i}" for i in range(1, 9)]
#         all_weeks.insert(0, "All Weeks")
#         selected_week_str = sidebar.selectbox("Select a Week", all_weeks, index=all_weeks.index(f"Week {current_week}"))

#         st.header("Weekly Activity Data")
        
#         if selected_week_str == "All Weeks":
#             filtered_weekly_data = weekly_data
#         else:
#             selected_week = int(selected_week_str.replace("Week ", ""))
#             filtered_weekly_data = weekly_data[weekly_data["Week"] == selected_week]
        
#         if selected_participant != "All":
#             filtered_weekly_data = filtered_weekly_data[filtered_weekly_data["Participant"] == selected_participant]
        
#         st.dataframe(filtered_weekly_data, use_container_width=True)
        
#         # Calculate leaderboard dynamically using the "Points" column
#         def calculate_leaderboard(data, current_week):
#             if "Points" not in data.columns:
#                 data["Points"] = (
#                     data["Zone 1"] * 1 +
#                     data["Zone 2"] * 2 +
#                     data["Zone 3"] * 3 +
#                     data["Zone 4"] * 4 +
#                     data["Zone 5"] * 5
#                 )
#             leaderboard = data.groupby("Participant")["Points"].sum().reset_index()
#             leaderboard = leaderboard.sort_values(by="Points", ascending=False)

#             leaderboard.reset_index(drop=True, inplace=True)
#             leaderboard.insert(0, 'Rank', leaderboard.index + 1)

#             # Calculate "Points Behind" for each participant
#             max_points = leaderboard["Points"].max()
#             leaderboard["Points Behind"] = max_points - leaderboard["Points"]

#             # Insert "Points Behind" column immediately after "Points"
#             points_idx = leaderboard.columns.get_loc("Points")
#             points_behind = leaderboard.pop("Points Behind")
#             leaderboard.insert(points_idx + 1, "Points Behind", points_behind)

#             for week in range(1, current_week + 1):
#                 week_points = data[data["Week"] == week].groupby("Participant")["Points"].sum()
#                 leaderboard[f"Week {week} Totals"] = leaderboard["Participant"].map(week_points).fillna(0)
#             return leaderboard
        
#         leaderboard = calculate_leaderboard(weekly_data, current_week)

#         st.header("Strava Competition Leaderboard")
#         st.dataframe(leaderboard, use_container_width=True)

#         # COMMENT WHAT THIS DOES
#         if current_week > 1:
#             prev_week_col = f"Week {current_week - 1} Totals"
#             current_week_col = f"Week {current_week} Totals"
#             if prev_week_col in leaderboard.columns and current_week_col in leaderboard.columns:
#                 # Calculate points gained specifically in the current week
#                 leaderboard['Latest Week Gain'] = leaderboard[current_week_col]
#                 # Find the biggest mover and shaker based on this week's points
#                 biggest_mover = leaderboard.loc[leaderboard['Latest Week Gain'].idxmax()]
#                 st.subheader(f"🔥 Biggest Mover and Shaker of Week {current_week}: {biggest_mover['Participant']} ({biggest_mover['Latest Week Gain']:.0f} points)")
#             else:
#                 st.info("Previous week data not available to calculate Biggest Mover.") # handles week 1 case

#         # Visualization: Who has run the most distance
#         if "Total Distance" in weekly_data.columns and "Workout Type" in weekly_data.columns and "Total Duration" in weekly_data.columns:
#             st.header("Top Runners by Distance and Duration (Runs Only)")
#             run_data = weekly_data[weekly_data["Workout Type"] == "Run"]
#             distance_data = run_data.groupby("Participant")["Total Distance"].sum().reset_index()
#             duration_data = run_data.groupby("Participant")["Total Duration"].sum().reset_index()
#             combined_data = pd.merge(distance_data, duration_data, on="Participant")
#             combined_data["Pace (min/mile)"] = combined_data["Total Duration"] / combined_data["Total Distance"]
#             combined_data["Pace (min/mile)"] = combined_data["Pace (min/mile)"].replace([float('inf'), -float('inf')], 0).fillna(0)
#             combined_data["Formatted Pace"] = combined_data["Pace (min/mile)"].apply(lambda x: f"{int(x)}:{int((x % 1) * 60):02d} min/mile")
#             combined_data = combined_data.sort_values(by="Total Distance", ascending=True)
#             melted_data = combined_data.melt(id_vars=["Participant", "Formatted Pace"], 
#                                             value_vars=["Total Distance", "Total Duration"], 
#                                             var_name="Metric", value_name="Value")
#             melted_data.loc[melted_data["Metric"] == "Total Duration", "Value"] = melted_data.loc[melted_data["Metric"] == "Total Duration", "Value"] / 60
#             melted_data.replace({"Total Distance": "Distance (miles)", "Total Duration": "Duration (hours)"}, inplace=True)
#             melted_data["Participant"] = pd.Categorical(melted_data["Participant"], categories=combined_data["Participant"], ordered=True)
#             fig = px.bar(
#                 melted_data,
#                 x="Value",
#                 y="Participant",
#                 color="Metric",
#                 orientation="h",
#                 color_discrete_sequence=["#E25822", "#FFD700"],  
#                 template="plotly_dark",
#                 text=melted_data.apply(lambda row: f"{row['Formatted Pace']}" if row["Metric"] == "Distance (miles)" else f"{row['Value']:.2f}", axis=1)
#             )
#             fig.update_layout(
#                 title=dict(
#                     text="Total Running Distance and Duration by Bourbon Chaser",
#                     x=0,  
#                     xanchor="left",
#                     font=dict(size=22)
#                 )
#             )
#             st.plotly_chart(fig, use_container_width=True)

#     else:
#         st.warning("No data available. Please upload TieDye_Weekly_Scoreboard.xlsx.")

#     st.header("Group Weekly Running Distance Progress")
#     st.subheader("The change in total running distance by week across the group.")
#     weekly_data["Week"] = pd.to_numeric(weekly_data["Week"], errors='coerce')
#     weekly_data["Total Distance"] = pd.to_numeric(weekly_data["Total Distance"], errors='coerce')
#     running_data = weekly_data[weekly_data["Workout Type"] == "Run"]
#     weekly_distance = running_data.groupby("Week")["Total Distance"].sum().reset_index()
#     weekly_distance = weekly_distance.sort_values("Week")
#     weekly_distance["Pct Change"] = weekly_distance["Total Distance"].pct_change() * 100
#     weekly_distance["Pct Change"].fillna(0, inplace=True)
#     fig_weekly_miles = px.line(
#         weekly_distance,
#         x="Week",
#         y="Total Distance",
#         markers=True,
#         title="Total Miles Run by Week",
#         labels={"Total Distance": "Total Distance (Miles)", "Week": "Week"},
#         template="plotly_dark"
#     )
#     st.plotly_chart(fig_weekly_miles, use_container_width=True)

#     # Ensure the Date column is in datetime format for running_data
#     running_data["Date"] = pd.to_datetime(running_data["Date"])

#     # Get today's date
#     today_date = datetime.today().date()

#     # Recalculate competition start date (same logic as get_current_week)
#     current_year = today_date.year
#     start_date = datetime(current_year, 3, 10).date()
#     if today_date < start_date:
#         start_date = datetime(current_year - 1, 3, 10).date()

#     # Calculate the start date of the current competition week
#     current_week_start = start_date + timedelta(weeks=current_week - 1)

#     # Determine the same offset as today within the current week
#     offset = today_date - current_week_start

#     # Calculate the start and end of the corresponding period in the previous week
#     prev_week_start = current_week_start - timedelta(weeks=1)
#     prev_week_end = prev_week_start + offset

#     # Sum the running distances from the current week up to today and for the previous week up to the same weekday
#     current_week_distance = running_data[
#         (running_data["Date"].dt.date >= current_week_start) & (running_data["Date"].dt.date <= today_date)
#     ]["Total Distance"].sum()

#     prev_week_distance = running_data[
#         (running_data["Date"].dt.date >= prev_week_start) & (running_data["Date"].dt.date <= prev_week_end)
#     ]["Total Distance"].sum()

#     # Calculate the week-to-date percentage change
#     if prev_week_distance > 0:
#         pct_change_latest = ((current_week_distance - prev_week_distance) / prev_week_distance) * 100
#     else:
#         pct_change_latest = 0

#     # Format KPI display
#     kpi_color = "#00FF00" if pct_change_latest >= 0 else "#FF4136"
#     kpi_arrow = "🔼" if pct_change_latest >= 0 else "🔽"

#     st.markdown(
#         f"""
#         <div style='background-color:#333333;padding:15px;border-radius:8px;text-align:center;'>
#             <span style='color:#FFFFFF;font-size:22px;'>Week-to-Date Change:</span>
#             <span style='color:{kpi_color};font-size:26px;font-weight:bold;'>{pct_change_latest:.1f}% {kpi_arrow}</span>
#         </div>
#         """,
#         unsafe_allow_html=True
#     )

#     st.header("---------------")

#     #st.header("Group Activity Level Progress by Week to Date")
#     #st.subheader("The weekly increase or decrease in the number of activities across the group exactly a week ago.")
    
#     # Ensure the Date column is in datetime format for weekly_data
#     weekly_data["Date"] = pd.to_datetime(weekly_data["Date"])

#     # Get today's date
#     today_date = datetime.today().date()

#     # Calculate competition start date (using same logic as get_current_week)
#     current_year = today_date.year
#     start_date = datetime(current_year, 3, 10).date()
#     if today_date < start_date:
#         start_date = datetime(current_year - 1, 3, 10).date()

#     # Calculate the start date of the current competition week
#     current_week_start = start_date + timedelta(weeks=current_week - 1)

#     # Determine the same offset as today within the current week
#     offset = today_date - current_week_start

#     # Define the same period for the previous week
#     prev_week_start = current_week_start - timedelta(weeks=1)
#     prev_week_end = prev_week_start + offset

#     # Count activities for the current week up to today
#     current_week_activity_count = weekly_data[
#         (weekly_data["Date"].dt.date >= current_week_start) & (weekly_data["Date"].dt.date <= today_date)
#     ].shape[0]

#     # Count activities for the previous week up to the same day offset
#     prev_week_activity_count = weekly_data[
#         (weekly_data["Date"].dt.date >= prev_week_start) & (weekly_data["Date"].dt.date <= prev_week_end)
#     ].shape[0]

#     # Calculate the week-to-date percentage change
#     if prev_week_activity_count > 0:
#         pct_change_activity = ((current_week_activity_count - prev_week_activity_count) / prev_week_activity_count) * 100
#     else:
#         pct_change_activity = 0

#     # Format KPI display
#     activity_color = "#00FF00" if pct_change_activity >= 0 else "#FF4136"
#     activity_arrow = "🔼" if pct_change_activity >= 0 else "🔽"

#     st.markdown(
#         f"""
#         <div style='background-color:#333333;padding:15px;border-radius:8px;text-align:center;margin-top:10px;'>
#             <span style='color:#FFFFFF;font-size:22px;'>Week-to-Date Activity Change:</span>
#             <span style='color:{activity_color};font-size:26px;font-weight:bold;'>
#                 {pct_change_activity:.1f}% {activity_arrow}
#             </span>
#         </div>
#         """,
#         unsafe_allow_html=True
#     )

#     current_week_points = weekly_data[
#         (weekly_data["Date"].dt.date >= current_week_start) & (weekly_data["Date"].dt.date <= today_date)
#     ]["Points"].sum() # Assuming Points column exists

#     prev_week_points = weekly_data[
#         (weekly_data["Date"].dt.date >= prev_week_start) & (weekly_data["Date"].dt.date <= prev_week_end)
#     ]["Points"].sum()

#     if prev_week_points > 0:
#         pct_change_points = ((current_week_points - prev_week_points) / prev_week_points) * 100
#     else:
#         pct_change_points = 0 # Avoid division by zero

#     points_kpi_color = "#00FF00" if pct_change_points >= 0 else "#FF4136"
#     points_kpi_arrow = "🔼" if pct_change_points >= 0 else "🔽"

#     st.markdown(
#         f"""
#         <div style='background-color:#333333;padding:15px;border-radius:8px;text-align:center;margin-top:10px;'>
#             <span style='color:#FFFFFF;font-size:22px;'>Week-to-Date Points Change:</span>
#             <span style='color:{points_kpi_color};font-size:26px;font-weight:bold;'>
#                 {pct_change_points:.1f}% {points_kpi_arrow}
#             </span>
#         </div>
#         """,
#         unsafe_allow_html=True
#     )

#     group_cum_points = weekly_data.groupby("Week")["Points"].sum().cumsum().reset_index()
#     fig_group_cum_points = px.line(group_cum_points, x="Week", y="Points", title="Group Cumulative Points Over Time", markers=True, template="plotly_dark")
#     st.plotly_chart(fig_group_cum_points, use_container_width=True)


# with tabs[1]:  # Overview tab
#     st.header("Competition Overview")
#     st.markdown(
#         """
#         ### **Bourbon Chasers - The Descent into Madness**
#         Welcome to the Inferno! Over the next **8 weeks**, you will battle for supremacy using **Heart Rate (HR) Zones** to earn points. 
#         This scoring method ensures that all accepted activities contribute fairly to the competition.

#         #### **Scoring System**
#         Points are awarded based on HR Zones as follows:

#         - **Zone 1** → x1 points  
#         - **Zone 2** → x2 points  
#         - **Zone 3** → x3 points  
#         - **Zone 4** → x4 points  
#         - **Zone 5** → x5 points  

#         #### **Accepted Activities**
#         You can earn points from the following activities:
#         - 🏃 **Running**
#         - 🚴 **Biking**
#         - 🎒 **Rucking**
#         - 🏊 **Swimming**
#         - 🚣 **Rowing**
#         - 🏋️ **Lifting**
#         - 🏃‍♂️ **Elliptical**

#         The battle is fierce, and only the strongest will rise. Stay disciplined and push your limits.  
#         **The descent into madness has begun! 🔥**
#         """
#     )

# with tabs[2]:  # Individual Analysis Tab
#     st.header("Individual Performance Breakdown")
#     participant_selected = st.selectbox(
#         "Select Participant", sorted(weekly_data["Participant"].unique())
#     )
#     individual_data = weekly_data[weekly_data["Participant"] == participant_selected]
#     participant_total_time = individual_data["Total Duration"].sum()
#     group_avg_total_time = weekly_data.groupby("Participant")["Total Duration"].sum().mean()
#     percent_of_group_avg = (participant_total_time / group_avg_total_time) * 100
#     kpi_color = "#00FF00" if percent_of_group_avg >= 100 else "#FF4136"
#     performance_arrow = "🔼" if percent_of_group_avg >= 100 else "🔽"
#     st.markdown(
#         f"""
#         <div style='background-color:#333333;padding:15px;border-radius:8px;text-align:center;margin-top:10px;'>
#             <span style='color:#FFFFFF;font-size:22px;'>Your Total Training Time vs. Group Average:</span><br>
#             <span style='color:{kpi_color};font-size:28px;font-weight:bold;'>
#                 {percent_of_group_avg:.1f}% {performance_arrow}
#             </span>
#         </div>
#         """,
#         unsafe_allow_html=True
#     )
#     zone_columns = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"]
#     participant_zones = individual_data[zone_columns].sum()
#     group_avg_zones = weekly_data.groupby("Participant")[zone_columns].sum().mean()
#     zone_comparison_df = pd.DataFrame({
#         "Zone": zone_columns,
#         participant_selected: participant_zones.values,
#         "Group Average": group_avg_zones.values
#     })
#     fig_zone_comparison = px.bar(
#         zone_comparison_df.melt(id_vars=["Zone"], var_name="Type", value_name="Minutes"),
#         x="Zone",
#         y="Minutes",
#         color="Type",
#         barmode="group",
#         template="plotly_dark",
#         title=f"{participant_selected}'s Time per Zone vs. Group Average"
#     )
#     st.plotly_chart(fig_zone_comparison, use_container_width=True)

#     st.subheader("Activity Breakdown")
#     col1, col2 = st.columns(2)

#     with col1:
#         activity_counts = individual_data['Workout Type'].value_counts().reset_index()
#         activity_counts.columns = ['Workout Type', 'Count']
#         fig_act_count = px.pie(activity_counts, names='Workout Type', values='Count', title='Activity Count by Type', template="plotly_dark")
#         fig_act_count.update_traces(textposition='inside', textinfo='percent+label')
#         st.plotly_chart(fig_act_count, use_container_width=True)

#     with col2:
#         activity_duration = individual_data.groupby('Workout Type')['Total Duration'].sum().reset_index()
#         fig_act_dur = px.pie(activity_duration, names='Workout Type', values='Total Duration', title='Total Duration by Activity Type (minutes)', template="plotly_dark")
#         fig_act_dur.update_traces(textposition='inside', textinfo='percent+label')
#         st.plotly_chart(fig_act_dur, use_container_width=True)

