# --- START OF FILE app.py ---

import streamlit as st
import pandas as pd
import base64
import plotly.express as px
from datetime import datetime, timedelta # Ensure timedelta is imported
import openpyxl
import requests
from io import BytesIO

# --- Page Config (Keep at the top) ---
st.set_page_config(
    page_title="🔥 Bourbon Chasers Strava Inferno 🔥",
    layout="wide"
)

# --- Utility Functions ---
def get_base64_image(image_path):
    """Encodes a local image file in base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"Sidebar image file not found: {image_path}. Placeholder will be used.")
        return ""
    except Exception as e:
        st.error(f"Error reading sidebar image file {image_path}: {e}")
        return ""

def get_base64_image_from_url(image_url):
    """Fetches an image from a URL and encodes it in base64."""
    try:
        response = requests.get(image_url, timeout=10) # Added timeout
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
        else:
            print(f"Error loading image from URL {image_url}: HTTP {response.status_code}")
            return ""
    except requests.exceptions.Timeout:
        print(f"Timeout error fetching image from URL {image_url}")
        return ""
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching image from URL {image_url}: {e}")
        return ""
    except Exception as e:
        print(f"Unexpected error fetching image from URL {image_url}: {e}")
        return ""

# --- Data Loading Function ---
# @st.cache_data(ttl=300) # Consider re-enabling later for performance (cache for 5 minutes)
def load_weekly_data(url):
    """Loads the weekly scoreboard Excel file from a URL."""
    print(f"Attempting to load data from: {url}")
    try:
        response = requests.get(url, timeout=20) # Added timeout
        response.raise_for_status()
        df = pd.read_excel(BytesIO(response.content), engine="openpyxl")
        print(f"Data loaded successfully. Shape: {df.shape}")
        print(f"Initial columns: {df.columns.tolist()}")
        return df
    except requests.exceptions.Timeout:
        st.error(f"Timeout error fetching data file from {url}. Please try again later.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching data file from {url}: {e}")
        return None
    except Exception as e:
        st.error(f"Failed to load or parse Excel file from {url}. Error: {e}")
        return None

# --- Data Preprocessing Function ---
def preprocess_data(df):
    """Cleans, processes, and prepares the weekly data DataFrame."""
    if df is None or df.empty:
        st.error("Cannot preprocess data: Input DataFrame is None or empty.")
        # Return an empty DataFrame with expected columns to prevent downstream errors
        expected_cols = ["Date", "Participant", "Workout Type", "Total Duration", "Total Distance",
                         "Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Points", "Week"]
        return pd.DataFrame(columns=expected_cols)

    print("Starting Data Preprocessing...")
    processed_df = df.copy() # Work on a copy

    # === Date Handling ===
    if "Date" in processed_df.columns:
        print("Processing 'Date' column...")
        processed_df["Date"] = pd.to_datetime(processed_df["Date"], errors='coerce')
        initial_rows = len(processed_df)
        processed_df.dropna(subset=["Date"], inplace=True)
        rows_dropped = initial_rows - len(processed_df)
        if rows_dropped > 0:
            print(f"Dropped {rows_dropped} rows due to invalid dates.")
        # Sort by Date (most recent first) right after cleaning
        processed_df = processed_df.sort_values(by="Date", ascending=False)
        print("'Date' column processed and sorted.")
    else:
        print("Warning: 'Date' column not found.")
        # Consider adding a placeholder or stopping if Date is crucial for your logic

    # === Zone Handling ===
    zone_cols = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"]
    print("Processing Zone columns...")
    for col in zone_cols:
        if col not in processed_df.columns:
            processed_df[col] = 0 # Add missing zone columns if necessary
            print(f"Warning: Column '{col}' missing, added with zeros.")
        else:
            # Convert to numeric, coerce errors to NaN, then fill NaN with 0
            processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce').fillna(0)
    print("Zone columns processed.")

    # === Points Calculation ===
    print("Calculating 'Points' column...")
    # Calculate directly on the DataFrame (adds/updates 'Points' column at the end)
    try:
        processed_df["Points"] = (
            processed_df["Zone 1"] * 1 + processed_df["Zone 2"] * 2 +
            processed_df["Zone 3"] * 3 + processed_df["Zone 4"] * 4 +
            processed_df["Zone 5"] * 5
        )
        print("'Points' column calculated.")
    except Exception as e:
        print(f"ERROR calculating 'Points' column: {e}. 'Points' column may be incorrect or missing.")
        processed_df["Points"] = 0 # Set to 0 as a fallback if calculation fails

    print(f"Columns AFTER Points calculation: {processed_df.columns.tolist()}") # DEBUG

    # === Other Numeric Columns ===
    numeric_cols = ["Total Distance", "Total Duration", "Week"]
    print("Processing other numeric columns...")
    for col in numeric_cols:
         if col in processed_df.columns:
              # Convert to numeric, coerce errors to NaN (will be handled later if needed, e.g., fillna(0) before sum)
              processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
         else:
              print(f"Warning: Numeric column '{col}' not found.")
    print("Other numeric columns processed.")

    # === ** COLUMN REORDERING LOGIC ** ===
    # This section ensures 'Points' is positioned correctly after 'Zone 5' if both exist.
    print("Attempting final column reordering...")
    current_cols = processed_df.columns.tolist()
    # Define the ideal start of the order
    ideal_start_order = [
        "Date", "Participant", "Workout Type", "Total Duration", "Total Distance",
        "Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Points", "Week"
    ]
    # Create the final list: start with ideal columns found, then add the rest
    final_ordered_cols = [col for col in ideal_start_order if col in current_cols]
    remaining_cols = [col for col in current_cols if col not in final_ordered_cols]
    final_ordered_cols.extend(remaining_cols) # Add any other columns to the end

    try:
        processed_df = processed_df[final_ordered_cols] # Reindex DataFrame with the new order
        print(f"Columns successfully reordered: {processed_df.columns.tolist()}")
    except KeyError as e:
        print(f"KeyError during column reordering: {e}. This likely means a column in 'final_ordered_cols' doesn't exist in the DataFrame. Keeping previous order.")
        # If reordering fails, keep the order from before this step
    except Exception as e:
        print(f"ERROR during column reordering: {e}. Keeping previous order.")
        # If reordering fails for other reasons, keep the order
    # === ** END OF COLUMN REORDERING LOGIC ** ===


    print("Data preprocessing complete.")
    return processed_df

# --- Competition Date & Week Calculation ---
def get_current_competition_week(start_date_dt, total_weeks=8):
    """
    Calculates the current competition week number (1-total_weeks).
    Handles competition starting on Sunday, Mar 10, 2025.
    Week 1: Sun, Mar 10 -> Sun, Mar 17
    Week 2: Mon, Mar 18 -> Sun, Mar 24
    ... subsequent weeks run Monday-Sunday.
    """
    today = datetime.today().date()

    # Ensure start_date is a date object
    if isinstance(start_date_dt, datetime):
        start_date = start_date_dt.date()
    else:
        start_date = start_date_dt # Assume it's already a date object

    # If today is before the official start date, default to showing Week 1
    if today < start_date:
        # print("DEBUG: Today is before start date.") # Optional debug print
        return 1

    # Define the specific end date for Week 1 based on the known schedule
    # This handles the irregular start week.
    try:
        # Explicitly define the end date of the first week - WITH CORRECTED YEAR
        end_of_week_1 = datetime(2025, 3, 17).date()
    except ValueError:
        # Fallback if date is invalid (shouldn't happen for fixed date)
        st.error("Error defining end_of_week_1. Please check the date.")
        return 1 # Default to week 1 on error

    if today <= end_of_week_1:
        # If today is within Week 1 (inclusive of the end date)
        # print(f"DEBUG: Today ({today}) <= end_of_week_1 ({end_of_week_1}). Returning Week 1.") # Optional debug print
        return 1
    else:
        # If today is after Week 1 ended
        # Calculate the start of Week 2 (the Monday after end_of_week_1)
        start_of_week_2 = end_of_week_1 + timedelta(days=1) # Should be Mon, Mar 18, 2025

        # Calculate how many full days have passed since the start of Week 2
        days_since_start_of_week_2 = (today - start_of_week_2).days

        # Calculate the week number:
        # // 7 gives the number of *full* weeks completed since Week 2 started.
        # Add 2 (1 for Week 1 which already passed + 1 because //7 is 0-indexed)
        current_week_number = (days_since_start_of_week_2 // 7) + 2

        # print(f"DEBUG: Today={today}, EndW1={end_of_week_1}, StartW2={start_of_week_2}, DaysSinceW2={days_since_start_of_week_2}, CalcWeek={current_week_number}") # Optional debug print

        # Clamp the week number between 1 and the total duration
        final_week = min(max(current_week_number, 1), total_weeks)
        # print(f"DEBUG: Clamped Week: {final_week}") # Optional debug print
        return final_week

competition_start_datetime = datetime(2025, 3, 10)
competition_total_weeks = 8

# Calculate current week based on explicit date ranges
today_date = datetime.today().date()

# Define date ranges for each week
week_dates = [
    (datetime(2025, 3, 10).date(), datetime(2025, 3, 17).date()),  # Week 1
    (datetime(2025, 3, 18).date(), datetime(2025, 3, 24).date()),  # Week 2
    (datetime(2025, 3, 25).date(), datetime(2025, 3, 31).date()),  # Week 3
    (datetime(2025, 4, 1).date(), datetime(2025, 4, 7).date()),    # Week 4
    (datetime(2025, 4, 8).date(), datetime(2025, 4, 14).date()),   # Week 5
    (datetime(2025, 4, 15).date(), datetime(2025, 4, 21).date()),  # Week 6
    (datetime(2025, 4, 22).date(), datetime(2025, 4, 28).date()),  # Week 7
    (datetime(2025, 4, 29).date(), datetime(2025, 5, 5).date()),   # Week 8
]

# Find which week contains today's date
current_week = 1  # Default to Week 1 if before competition start
for week_num, (start_date, end_date) in enumerate(week_dates, 1):
    if start_date <= today_date <= end_date:
        current_week = week_num
        break
# If today is after the last week, use the last week
if today_date > week_dates[-1][1]:
    current_week = len(week_dates)

print(f"Current Competition Week Calculated by Date Check: {current_week}")

# Check if today is Monday - if so, increment the week
today = datetime.today()
is_monday = today.weekday() == 0  # Monday is 0 in Python's weekday() function
default_display_week = min(current_week + 1 if is_monday else current_week, competition_total_weeks)
print(f"Current Competition Week: {current_week}, Is Monday: {is_monday}, Default Display Week: {default_display_week}")

# --- Load and Preprocess Data ---
DATA_URL = "https://github.com/Steven-Carter-Data/50k-Strava-Tracker/blob/main/TieDye_Weekly_Scoreboard.xlsx?raw=true"
raw_weekly_data = load_weekly_data(DATA_URL)
weekly_data = preprocess_data(raw_weekly_data) # weekly_data is now the cleaned DataFrame

# --- Styling ---
# Background Image
IMAGE_URL = "https://raw.githubusercontent.com/Steven-Carter-Data/50k-Strava-Tracker/main/bg_smolder.png"
base64_image = get_base64_image_from_url(IMAGE_URL)
if base64_image:
    st.markdown(f"""<style>.stApp {{ background: url('data:image/png;base64,{base64_image}') no-repeat center center fixed !important; background-size: cover !important; background-position: center !important; }}</style>""", unsafe_allow_html=True)
else:
    st.warning("Background image failed to load. Using default background.")

# Custom Fonts and Element Styles
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&display=swap');

    /* Global Font and Color */
    .stApp, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp .stMarkdown, .stApp .stDataFrame > div, .stApp .stMetric, .stApp .stTabs,
    .stApp .stButton>button, .stApp .stSelectbox>div {{
        font-family: 'UnifrakturCook', serif !important;
        color: #D4AF37 !important; /* Gold */
    }}

    /* Headings */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'UnifrakturCook', serif !important;
        color: #D4AF37 !important;
    }}

    /* Plotly Chart Titles (Attempt) */
    .plotly .gtitle {{
        font-family: 'UnifrakturCook', serif !important;
        fill: #D4AF37 !important; /* SVG uses fill */
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px; white-space: pre-wrap;
        background-color: rgba(51, 51, 51, 0.7); /* Semi-transparent dark gray */
        border-radius: 4px 4px 0px 0px; gap: 1px; padding: 10px;
        color: #D4AF37 !important; /* Ensure tab text is gold */
        font-family: 'UnifrakturCook', serif !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: rgba(212, 175, 55, 0.8); /* Semi-transparent gold */
        color: #000000 !important; /* Black text for selected tab */
    }}

    /* Dataframe */
    .stDataFrame {{
        background-color: rgba(51, 51, 51, 0.7); /* Semi-transparent background */
    }}
    /* Dataframe Header */
    .stDataFrame thead th {{
        background-color: rgba(212, 175, 55, 0.8); /* Gold header */
        color: #000000 !important; /* Black header text */
        font-family: 'UnifrakturCook', serif !important;
    }}
     /* Dataframe Body Text */
    .stDataFrame tbody td {{
        color: #D4AF37 !important; /* Gold text in cells */
         font-family: 'UnifrakturCook', serif !important;
    }}
     /* Dataframe Alternating Rows */
    .stDataFrame tbody tr:nth-child(even) {{
        background-color: rgba(70, 70, 70, 0.7); /* Slightly different shade for even rows */
    }}
     /* Dataframe Hover */
    .stDataFrame tbody tr:hover {{
        background-color: rgba(212, 175, 55, 0.3); /* Highlight on hover */
    }}

    /* Style selectbox dropdown options (difficult, might not work consistently) */
     /* div[data-baseweb="select"] > div {{ background-color: #333; color: #D4AF37; }} */
     /* div[data-baseweb="popover"] ul li {{ color: #D4AF37 !important; background-color: #222 !important; }} */
     /* div[data-baseweb="popover"] ul li:hover {{ background-color: #555 !important; }} */

     /* Style KPI divs */
    .kpi-div {{
        background-color: rgba(51, 51, 51, 0.7);
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
    }}
    .kpi-div span {{ /* General text inside KPI */
        font-family: 'UnifrakturCook', serif !important;
    }}
    .kpi-title {{
        color: #FFFFFF !important; /* White title */
        font-size: 20px;
    }}
    .kpi-value {{
         /* Color set dynamically */
        font-size: 26px;
        font-weight: bold;
    }}
    .kpi-context {{
        color: #AAAAAA !important; /* Gray context text */
        font-size: 14px;
        font-family: sans-serif !important; /* Use sans-serif for context for readability */
    }}

    </style>""", unsafe_allow_html=True)

# --- Page Titles ---
st.markdown("""<h1 style="text-align: center; font-family: 'UnifrakturCook', serif; font-size: 60px; font-weight: bold; color: #D4AF37; max-width: 90%; margin: auto; word-wrap: break-word;">Welcome to the Inferno</h1>""", unsafe_allow_html=True)
st.markdown('<h3 style="text-align: center; font-family: UnifrakturCook, serif; font-size: 25px; font-weight: bold; color: #D4AF37;">Bourbon Chasers - The descent into madness has begun!</h3>', unsafe_allow_html=True)

# --- Sidebar ---
sidebar = st.sidebar
SIDEBAR_IMAGE_PATH = "sidebar_img.png" # Make sure this file exists in the root directory
base64_sidebar_image = get_base64_image(SIDEBAR_IMAGE_PATH)
if base64_sidebar_image:
    sidebar.markdown(f"""<div style="text-align: center;"><img src='data:image/png;base64,{base64_sidebar_image}' style='max-width: 100%; border-radius: 10px;'></div>""", unsafe_allow_html=True)
else:
    sidebar.markdown("<p style='text-align: center; color: yellow;'>Sidebar image not loaded.</p>", unsafe_allow_html=True)
sidebar.title("Bourbon Chasers")

# --- Sidebar Filters ---
# Ensure weekly_data is valid before creating filters
if weekly_data is not None and not weekly_data.empty:
    # Get participants list safely, handle if column doesn't exist
    if "Participant" in weekly_data.columns:
        participants = sorted(weekly_data["Participant"].dropna().unique())
    else:
        participants = ["N/A - Column Missing"]
        st.sidebar.warning("Participant column missing from data.")

    selected_participant_sb = sidebar.selectbox("Select a Bourbon Chaser", ["All"] + participants, key="sb_participant")

    # --- Week selection (Debugging Default) ---
    print("--- DEBUGGING WEEK SELECTBOX ---") # Marker
    all_weeks_options = [f"Week {i}" for i in range(1, competition_total_weeks + 1)] # Use variable
    all_weeks_options.insert(0, "All Weeks") # Add 'All Weeks' at the beginning
    print(f"DEBUG: current_week variable value = {current_week}") # Check the variable itself
    print(f"DEBUG: all_weeks_options = {all_weeks_options}") # Check the list contents

    # Set default week index carefully using the calculated current_week
    default_week_str = f"Week {default_display_week}"
    print(f"DEBUG: Attempting to find index for default_week_str = '{default_week_str}'")

    print(f"DEBUG: Attempting to find index for default_week_str = '{default_week_str}'")

    default_week_index = 0 # Initialize with a safe default
    try:
        # Find the index of the default week string in the options list
        default_week_index = all_weeks_options.index(default_week_str)
        print(f"DEBUG: Found index = {default_week_index} for '{default_week_str}'")
    except ValueError:
        # If the calculated week isn't found
        print(f"DEBUG: *** ValueError *** - '{default_week_str}' NOT found in options. Defaulting index to 0.")
        default_week_index = 0 # Default to 'All Weeks' (index 0)
    except Exception as e:
        # Catch any other unexpected error during index finding
        print(f"DEBUG: *** Exception *** - Error finding index for '{default_week_str}': {e}. Defaulting index to 0.")
        default_week_index = 0

    print(f"DEBUG: FINAL default_week_index being passed to selectbox = {default_week_index}")
    print("--- END DEBUGGING WEEK SELECTBOX ---") # Marker

    selected_week_str_sb = sidebar.selectbox(
        "Select a Week",
        all_weeks_options,
        index=default_week_index, # Use the calculated index
        key="sb_week"
    )
    # --- End of Week Selection ---

else:
    sidebar.markdown("_(Data not loaded or is empty, filters unavailable)_")
    # Set defaults if data loading failed
    selected_participant_sb = "All"
    selected_week_str_sb = "All Weeks" # Keep default as All Weeks if data fails
    # Add a debug print here too, in case the data load is the issue
    print("DEBUG: weekly_data is None or empty, filters unavailable.")


# --- Main App Tabs ---
tabs = st.tabs(["Leaderboards", "Overview", "Individual Analysis"])

# ===========================
# ======= LEADERBOARDS TAB =======
# ===========================
with tabs[0]:
    st.header("Leaderboards & Group Trends")

    # Check again if data is available AFTER preprocessing
    if weekly_data is not None and not weekly_data.empty:

        # --- Weekly Activity Data Table ---
        st.subheader("Weekly Activity Data Log")
        st.markdown("Detailed log of all recorded activities. Use sidebar filters to narrow down by participant and/or week.")
        filtered_display_data = weekly_data.copy() # Start with the clean, preprocessed data

        # Apply filters (check column existence before filtering)
        # Week Filter
        if selected_week_str_sb != "All Weeks":
            if "Week" in filtered_display_data.columns:
                try:
                    selected_week_num = int(selected_week_str_sb.replace("Week ", ""))
                    # Ensure 'Week' column is numeric before comparison
                    filtered_display_data['Week'] = pd.to_numeric(filtered_display_data['Week'], errors='coerce')
                    # Filter, keeping rows where Week matches or is NaN (if conversion failed)
                    filtered_display_data = filtered_display_data[filtered_display_data["Week"] == selected_week_num]
                except ValueError:
                    st.warning(f"Invalid week selection format: {selected_week_str_sb}")
                except Exception as e:
                    st.warning(f"Error applying week filter: {e}")
            else:
                st.warning("Cannot filter by week: 'Week' column not found.")

        # Participant Filter
        if selected_participant_sb != "All":
            if "Participant" in filtered_display_data.columns:
                 # Filter out potential NaN participants before comparison
                 filtered_display_data = filtered_display_data[filtered_display_data["Participant"].notna()]
                 filtered_display_data = filtered_display_data[filtered_display_data["Participant"] == selected_participant_sb]
            else:
                 st.warning("Cannot filter by participant: 'Participant' column not found.")

        # Format Date for display just before showing table
        display_df_log = filtered_display_data.copy() # Use a final copy for display
        if "Date" in display_df_log.columns:
             # Assume Date is already datetime from preprocessing
             try:
                 display_df_log["Date"] = display_df_log["Date"].dt.strftime("%B %d, %Y")
             except AttributeError:
                  st.warning("Could not format 'Date' column for display (might not be datetime).")
             except Exception as e:
                  st.warning(f"Error formatting date column: {e}")

        # Select only the columns that survived preprocessing and reordering
        display_cols_log = [col for col in weekly_data.columns if col in display_df_log.columns]
        st.dataframe(display_df_log[display_cols_log], use_container_width=True, hide_index=True)


        # --- Competition Leaderboard ---
        def calculate_leaderboard(data, total_weeks):
            """Calculates the main competition leaderboard."""
            required_cols = ["Participant", "Points", "Week"]
            if data is None or data.empty or not all(c in data.columns for c in required_cols):
                 st.warning(f"Leaderboard calculation skipped: Missing required columns {required_cols}")
                 return pd.DataFrame(columns=["Rank", "Participant", "Points", "Points Behind"])

            # Ensure Points is numeric before grouping
            data['Points'] = pd.to_numeric(data['Points'], errors='coerce').fillna(0)
            leaderboard = data.groupby("Participant")["Points"].sum().reset_index().sort_values(by="Points", ascending=False)

            if not leaderboard.empty:
                max_points = leaderboard["Points"].iloc[0]
                leaderboard["Points Behind"] = max_points - leaderboard["Points"]
            else:
                leaderboard["Points Behind"] = 0 # Handle empty leaderboard case

            leaderboard.reset_index(drop=True, inplace=True)
            leaderboard.insert(0, 'Rank', leaderboard.index + 1)

            # Move 'Points Behind' column
            if "Points Behind" in leaderboard.columns:
                try:
                    points_idx = leaderboard.columns.get_loc("Points")
                    points_behind_col = leaderboard.pop("Points Behind")
                    leaderboard.insert(points_idx + 1, "Points Behind", points_behind_col)
                except Exception as e:
                     print(f"Error moving 'Points Behind' column: {e}") # Log error, continue

            # Add weekly totals
            data['Week'] = pd.to_numeric(data['Week'], errors='coerce') # Ensure Week is numeric
            for week_num in range(1, total_weeks + 1):
                # Ensure points are numeric before summing for the week
                week_data = data[data["Week"] == week_num].copy()
                week_data['Points'] = pd.to_numeric(week_data['Points'], errors='coerce').fillna(0)
                week_points = week_data.groupby("Participant")["Points"].sum()
                leaderboard[f"Week {week_num} Totals"] = leaderboard["Participant"].map(week_points).fillna(0).astype(int)

            return leaderboard

        # competition_total_weeks is defined earlier
        leaderboard_df = calculate_leaderboard(weekly_data.copy(), competition_total_weeks) # Use a copy of the cleaned data
        st.subheader("Strava Competition Leaderboard")
        st.markdown("Overall ranking based on **cumulative points** earned from HR Zones across all activities and weeks. Also shows points behind the leader and a breakdown of points earned each week.")
        st.dataframe(leaderboard_df, use_container_width=True, hide_index=True)


        # --- Biggest Mover Highlight ---
        st.subheader(f"🔥 Biggest Points Mover - Week {current_week}")
        st.caption(f"Highlights the participant who earned the most points specifically in Week {current_week}.")
        if current_week > 0 and not leaderboard_df.empty:
            current_week_col = f"Week {current_week} Totals"
            if current_week_col in leaderboard_df.columns:
                # Ensure the column is numeric before finding max
                leaderboard_df[current_week_col] = pd.to_numeric(leaderboard_df[current_week_col], errors='coerce').fillna(0)
                if leaderboard_df[current_week_col].sum() > 0 : # Check if anyone scored points this week
                    try:
                        biggest_mover = leaderboard_df.loc[leaderboard_df[current_week_col].idxmax()]
                        st.success(f"**{biggest_mover['Participant']}** with **{biggest_mover[current_week_col]:.0f} points** earned this week!")
                    except ValueError:
                        st.info(f"No participants found for Week {current_week} to determine biggest mover.") # Handle case where idxmax returns empty
                    except Exception as e:
                        st.warning(f"Error finding biggest mover: {e}")
                else:
                    st.info(f"No points recorded yet for Week {current_week}.")
            else:
                 st.info(f"Weekly totals column '{current_week_col}' not found in leaderboard.")
        else:
             st.info("Leaderboard data is empty or competition is in Week 1 (no previous week for comparison yet).")


        # --- Top Runners Visualization ---
        st.subheader("Top Runners by Distance and Duration")
        st.markdown("Compares participants based on their **total accumulated running distance** and **total running duration** throughout the competition. Average pace for runs is shown on the distance bars.")
        required_run_cols = ["Total Distance", "Workout Type", "Total Duration", "Participant"]
        if all(col in weekly_data.columns for col in required_run_cols):
            run_data = weekly_data[weekly_data["Workout Type"].str.contains("Run", case=False, na=False)].copy()
            # Ensure required columns are numeric BEFORE filtering/grouping
            run_data["Total Distance"] = pd.to_numeric(run_data["Total Distance"], errors='coerce').fillna(0)
            run_data["Total Duration"] = pd.to_numeric(run_data["Total Duration"], errors='coerce').fillna(0)

            if not run_data.empty:
                try:
                    distance_data = run_data.groupby("Participant")["Total Distance"].sum().reset_index()
                    duration_data = run_data.groupby("Participant")["Total Duration"].sum().reset_index()
                    combined_data = pd.merge(distance_data, duration_data, on="Participant", how="left") # Keep all participants with distance

                    # Calculate Pace safely
                    combined_data["Pace (min/mile)"] = combined_data.apply(
                        lambda row: row["Total Duration"] / row["Total Distance"] if row["Total Distance"] > 0 else 0, axis=1
                    )
                    combined_data["Formatted Pace"] = combined_data["Pace (min/mile)"].apply(
                        lambda x: f"{int(x)}:{int((x % 1) * 60):02d} min/mi" if x > 0 else "N/A"
                    )

                    combined_data = combined_data.sort_values(by="Total Distance", ascending=True) # Ascending for horizontal bar chart

                    # Prepare data for Plotly (melt)
                    melted_data = combined_data.melt(
                        id_vars=["Participant", "Formatted Pace"],
                        value_vars=["Total Distance", "Total Duration"],
                        var_name="Metric", value_name="Value"
                    )
                    # Create display columns
                    melted_data['Display Value'] = melted_data.apply(lambda row: row['Value'] / 60 if row['Metric'] == 'Total Duration' else row['Value'], axis=1)
                    melted_data['Metric Label'] = melted_data['Metric'].replace({"Total Distance": "Distance (miles)", "Total Duration": "Duration (hours)"})

                    # Create the bar chart
                    fig_runners = px.bar(
                        melted_data, x="Display Value", y="Participant", color="Metric Label", orientation="h",
                        color_discrete_map={"Distance (miles)": "#E25822", "Duration (hours)": "#FFD700"}, template="plotly_dark",
                        hover_name="Participant",
                        hover_data={ 'Participant': False, 'Metric Label': False, 'Display Value': ':.2f', 'Formatted Pace': (melted_data['Metric Label'] == 'Distance (miles)') }
                    )
                    # Add text labels
                    text_labels = melted_data.apply(lambda row: row['Formatted Pace'] if row['Metric Label'] == 'Distance (miles)' else f"{row['Display Value']:.1f} hrs", axis=1)
                    fig_runners.update_traces(text=text_labels, textposition='auto', selector=dict(type='bar'))
                    # Update layout
                    fig_runners.update_layout(
                        title=dict(text="Total Running Distance & Duration by Bourbon Chaser", x=0.01, xanchor="left", font=dict(size=20, family='UnifrakturCook, serif', color='#D4AF37')),
                        xaxis_title="Value (Miles or Hours)", yaxis_title="Participant", legend_title_text="Metric", barmode='group', yaxis={'categoryorder':'total ascending'}
                    )
                    st.plotly_chart(fig_runners, use_container_width=True)
                except Exception as e:
                    st.error(f"An error occurred while creating the runners chart: {e}")
            else:
                st.info("No 'Run' activities found in the data to display the runners chart.")
        else:
            st.warning(f"Cannot create runners chart: Missing one or more required columns ({required_run_cols})")


        # --- Group Weekly Running Distance Progress & KPI ---
        st.subheader("Group Weekly Running Distance Progress")
        st.markdown("Tracks the **total distance run by the entire group** each week and compares Week-to-Date (WtD) progress against the previous week.")
        required_group_run_cols = ["Week", "Total Distance", "Workout Type", "Date"] # Date needed for KPI
        if all(col in weekly_data.columns for col in required_group_run_cols):
             running_data_group = weekly_data[weekly_data["Workout Type"].str.contains("Run", case=False, na=False)].copy()
             # Ensure data types are correct before proceeding
             running_data_group['Week'] = pd.to_numeric(running_data_group['Week'], errors='coerce')
             running_data_group['Total Distance'] = pd.to_numeric(running_data_group['Total Distance'], errors='coerce').fillna(0)
             running_data_group['Date'] = pd.to_datetime(running_data_group['Date'], errors='coerce')
             running_data_group.dropna(subset=['Week', 'Date'], inplace=True) # Drop rows where Week or Date is invalid

             if not running_data_group.empty:
                 # --- Weekly Line Chart ---
                 try:
                     weekly_distance = running_data_group.groupby("Week")["Total Distance"].sum().reset_index().sort_values("Week")
                     fig_weekly_miles = px.line( weekly_distance, x="Week", y="Total Distance", markers=True, labels={"Total Distance": "Total Distance (Miles)", "Week": "Competition Week"}, template="plotly_dark")
                     fig_weekly_miles.update_layout( title=dict(text="Total Group Miles Run by Week", x=0.01, xanchor='left', font=dict(family='UnifrakturCook, serif', color='#D4AF37')), yaxis_title="Total Distance (Miles)")
                     fig_weekly_miles.update_traces(line=dict(color='#E25822'))
                     st.plotly_chart(fig_weekly_miles, use_container_width=True)
                 except Exception as e:
                     st.error(f"Error creating weekly distance chart: {e}")

                 # --- Week-to-Date Running Distance KPI ---
                 try:
                     today_date = datetime.today().date(); start_date_dt = competition_start_datetime.date()
                     if today_date >= start_date_dt:
                         # Calculate current competition week number based on Mon-Sun cycle
                         current_week_num_for_calc = get_current_competition_week(start_date_dt, competition_total_weeks)
                         # Calculate date ranges relative to Mon-Sun weeks
                         start_weekday = start_date_dt.weekday() # Mon=0, Sun=6
                         monday_of_start_week = start_date_dt - timedelta(days=start_weekday)
                         # Monday of the current week
                         today_weekday = today_date.weekday()
                         monday_of_current_week = today_date - timedelta(days=today_weekday)
                         # Calculate start/end dates for current and previous WtD periods
                         days_into_current_week = (today_date - monday_of_current_week).days
                         current_period_end_dt = today_date
                         current_week_start_dt = monday_of_current_week
                         prev_week_monday = monday_of_current_week - timedelta(weeks=1)
                         prev_period_end_dt = prev_week_monday + timedelta(days=days_into_current_week)
                         prev_week_start_dt = prev_week_monday # The start of the previous week is its Monday

                         # Sum distances within ranges
                         current_week_distance = running_data_group[ (running_data_group["Date"].dt.date >= current_week_start_dt) & (running_data_group["Date"].dt.date <= current_period_end_dt) ]["Total Distance"].sum()
                         prev_week_distance = running_data_group[ (running_data_group["Date"].dt.date >= prev_week_start_dt) & (running_data_group["Date"].dt.date <= prev_period_end_dt) ]["Total Distance"].sum()
                         # Calculate percentage change safely
                         if prev_week_distance > 0: pct_change_distance = ((current_week_distance - prev_week_distance) / prev_week_distance) * 100
                         elif current_week_distance > 0: pct_change_distance = 100.0 # Indicate increase from zero
                         else: pct_change_distance = 0.0 # No change if both zero
                         # Determine color and arrow
                         kpi_color = "#00FF00" if pct_change_distance >= 0 else "#FF4136"; kpi_arrow = "🔼" if pct_change_distance >= 0 else "🔽"
                         # Display KPI using styled div
                         st.markdown( f"""<div class='kpi-div'>
                                          <span class='kpi-title'>WtD Running Distance vs Prev. Week:</span><br>
                                          <span class='kpi-value' style='color:{kpi_color};'>{pct_change_distance:.1f}% {kpi_arrow}</span><br>
                                          <span class='kpi-context'>(Current: {current_week_distance:.1f} mi | Previous: {prev_week_distance:.1f} mi)</span>
                                         </div>""", unsafe_allow_html=True)
                     else:
                          st.info("Week-to-Date comparison starts after the competition begin date.")
                 except Exception as e:
                      st.error(f"Error calculating WtD running distance KPI: {e}")

             else:
                 st.info("No valid 'Run' activities found for group distance analysis.")
        else:
             st.warning(f"Cannot display group running trends: Missing one or more required columns ({required_group_run_cols})")


        # --- Group Activity Level Progress (WtD Count) ---
        st.subheader("Group Activity Count Progress (Week-to-Date)")
        st.markdown("Compares the **total number of activities** (all types) logged by the group **so far this week** against the count from the **same period last week**.")
        if "Date" in weekly_data.columns:
             weekly_data_kpi_act = weekly_data.copy()
             weekly_data_kpi_act["Date"] = pd.to_datetime(weekly_data_kpi_act["Date"], errors='coerce')
             weekly_data_kpi_act.dropna(subset=["Date"], inplace=True) # Need valid dates

             if not weekly_data_kpi_act.empty:
                 try:
                     today_date = datetime.today().date(); start_date_dt = competition_start_datetime.date()
                     if today_date >= start_date_dt:
                         # Use same date range logic as Running Distance KPI (Mon-Sun weeks)
                         start_weekday = start_date_dt.weekday()
                         monday_of_start_week = start_date_dt - timedelta(days=start_weekday)
                         today_weekday = today_date.weekday()
                         monday_of_current_week = today_date - timedelta(days=today_weekday)
                         days_into_current_week = (today_date - monday_of_current_week).days
                         current_period_end_dt = today_date
                         current_week_start_dt = monday_of_current_week
                         prev_week_monday = monday_of_current_week - timedelta(weeks=1)
                         prev_period_end_dt = prev_week_monday + timedelta(days=days_into_current_week)
                         prev_week_start_dt = prev_week_monday

                         # Count activities within ranges
                         current_week_activity_count = weekly_data_kpi_act[ (weekly_data_kpi_act["Date"].dt.date >= current_week_start_dt) & (weekly_data_kpi_act["Date"].dt.date <= current_period_end_dt) ].shape[0]
                         prev_week_activity_count = weekly_data_kpi_act[ (weekly_data_kpi_act["Date"].dt.date >= prev_week_start_dt) & (weekly_data_kpi_act["Date"].dt.date <= prev_period_end_dt) ].shape[0]
                         # Calculate percentage change safely
                         if prev_week_activity_count > 0: pct_change_activity = ((current_week_activity_count - prev_week_activity_count) / prev_week_activity_count) * 100
                         elif current_week_activity_count > 0: pct_change_activity = 100.0
                         else: pct_change_activity = 0.0
                         # Determine color and arrow
                         activity_color = "#00FF00" if pct_change_activity >= 0 else "#FF4136"; activity_arrow = "🔼" if pct_change_activity >= 0 else "🔽"
                         # Display KPI
                         st.markdown(f"""<div class='kpi-div'>
                                           <span class='kpi-title'>WtD Activity Count vs Prev. Week:</span><br>
                                           <span class='kpi-value' style='color:{activity_color};'>{pct_change_activity:.1f}% {activity_arrow}</span><br>
                                           <span class='kpi-context'>(Current: {current_week_activity_count} | Previous: {prev_week_activity_count})</span>
                                          </div>""", unsafe_allow_html=True)
                     else:
                          st.info("Week-to-Date comparison starts after the competition begin date.")
                 except Exception as e:
                     st.error(f"Error calculating WtD activity count KPI: {e}")
             else:
                 st.info("No valid activity data available for WtD Activity Count KPI.")
        else:
             st.warning("Cannot calculate WtD Activity Count KPI: Missing 'Date' column.")


        # --- Group Points Progress (WtD Points) ---
        st.subheader("Group Points Progress (Week-to-Date)")
        st.markdown("Compares the **total points earned** by the group **so far this week** against the points earned during the **same period last week**.")
        required_cols_pts_kpi = ["Date", "Points"]
        if all(c in weekly_data.columns for c in required_cols_pts_kpi):
              weekly_data_kpi_pts = weekly_data.copy()
              weekly_data_kpi_pts["Date"] = pd.to_datetime(weekly_data_kpi_pts["Date"], errors='coerce')
              weekly_data_kpi_pts["Points"] = pd.to_numeric(weekly_data_kpi_pts["Points"], errors='coerce') # Ensure points is numeric
              weekly_data_kpi_pts.dropna(subset=required_cols_pts_kpi, inplace=True) # Need valid date and points

              if not weekly_data_kpi_pts.empty:
                  try:
                      today_date = datetime.today().date(); start_date_dt = competition_start_datetime.date()
                      if today_date >= start_date_dt:
                         # Use same date range logic as Running Distance KPI (Mon-Sun weeks)
                         start_weekday = start_date_dt.weekday()
                         monday_of_start_week = start_date_dt - timedelta(days=start_weekday)
                         today_weekday = today_date.weekday()
                         monday_of_current_week = today_date - timedelta(days=today_weekday)
                         days_into_current_week = (today_date - monday_of_current_week).days
                         current_period_end_dt = today_date
                         current_week_start_dt = monday_of_current_week
                         prev_week_monday = monday_of_current_week - timedelta(weeks=1)
                         prev_period_end_dt = prev_week_monday + timedelta(days=days_into_current_week)
                         prev_week_start_dt = prev_week_monday

                         # Sum points within ranges
                         current_week_points = weekly_data_kpi_pts[ (weekly_data_kpi_pts["Date"].dt.date >= current_week_start_dt) & (weekly_data_kpi_pts["Date"].dt.date <= current_period_end_dt) ]["Points"].sum()
                         prev_week_points = weekly_data_kpi_pts[ (weekly_data_kpi_pts["Date"].dt.date >= prev_week_start_dt) & (weekly_data_kpi_pts["Date"].dt.date <= prev_period_end_dt) ]["Points"].sum()
                         # Calculate percentage change
                         if prev_week_points > 0: pct_change_points = ((current_week_points - prev_week_points) / prev_week_points) * 100
                         elif current_week_points > 0: pct_change_points = 100.0
                         else: pct_change_points = 0.0
                         # Determine color and arrow
                         points_kpi_color = "#00FF00" if pct_change_points >= 0 else "#FF4136"; points_kpi_arrow = "🔼" if pct_change_points >= 0 else "🔽"
                         # Display KPI
                         st.markdown(f"""<div class='kpi-div'>
                                           <span class='kpi-title'>WtD Points Earned vs Prev. Week:</span><br>
                                           <span class='kpi-value' style='color:{points_kpi_color};'>{pct_change_points:.1f}% {points_kpi_arrow}</span><br>
                                           <span class='kpi-context'>(Current: {current_week_points:.0f} | Previous: {prev_week_points:.0f})</span>
                                          </div>""", unsafe_allow_html=True)
                      else:
                         st.info("Week-to-Date comparison starts after the competition begin date.")
                  except Exception as e:
                     st.error(f"Error calculating WtD points KPI: {e}")

              else:
                 st.info("No valid data available for WtD Points KPI after cleaning.")
        else:
             st.warning(f"Cannot calculate WtD Points KPI: Missing one or more required columns ({required_cols_pts_kpi})")

    else: # weekly_data is None or empty
        st.warning("No weekly data available to display Leaderboards and Trends.")


# ===========================
# ======= OVERVIEW TAB =======
# ===========================
with tabs[1]:
    st.header("Competition Overview")
    # Keep your existing markdown description here
    st.markdown("""
        ### **Bourbon Chasers - The Descent into Madness**
        Welcome to the Inferno! Over the next **8 weeks** (starting March 10th, 2025), you will battle for supremacy using **Heart Rate (HR) Zones** from your activities to earn points.
        This scoring method aims to level the playing field across different types of endurance activities.

        #### **Scoring System**
        Points are awarded based on **time spent in each HR Zone** per activity (in minutes):

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
        """) # End of Markdown

# =================================
# ======= INDIVIDUAL ANALYSIS TAB =======
# =================================
with tabs[2]:
    st.header("Individual Performance Breakdown")

    # Check if data and participant column exist
    if weekly_data is not None and not weekly_data.empty and 'Participant' in weekly_data.columns:
        participants_list = sorted(weekly_data["Participant"].dropna().unique())
        if not participants_list:
             st.warning("No participants found in the data.")
        else:
             participant_selected_ind = st.selectbox(
                 "Select Participant to Analyze", participants_list, key="ind_participant_select"
             )

             # Filter data for the selected participant
             individual_data = weekly_data[weekly_data["Participant"] == participant_selected_ind].copy()

             if not individual_data.empty:
                 # --- Individual vs Group Average Time KPI ---
                 st.subheader(f"{participant_selected_ind}'s Training Time vs. Group Average")
                 st.markdown("Compares the **total time (duration) spent on all activities** by the selected participant against the average total time logged by **all participants** in the competition.")
                 req_cols_kpi1 = ["Total Duration", "Participant"]
                 if all(c in individual_data.columns for c in req_cols_kpi1) and all(c in weekly_data.columns for c in req_cols_kpi1):
                     try:
                         # Ensure duration is numeric for both individual and group
                         individual_data['Total Duration'] = pd.to_numeric(individual_data['Total Duration'], errors='coerce').fillna(0)
                         participant_total_time = individual_data["Total Duration"].sum()

                         group_time_data = weekly_data.copy()
                         group_time_data['Total Duration'] = pd.to_numeric(group_time_data['Total Duration'], errors='coerce').fillna(0)
                         # Calculate group average safely
                         group_totals = group_time_data.groupby("Participant")["Total Duration"].sum()
                         group_avg_total_time = group_totals.mean() if not group_totals.empty else 0

                         # Calculate percentage safely
                         if group_avg_total_time > 0: percent_of_group_avg = (participant_total_time / group_avg_total_time) * 100
                         else: percent_of_group_avg = 100.0 if participant_total_time > 0 else 0.0

                         kpi_color_ind = "#00FF00" if percent_of_group_avg >= 100 else "#FFD700"; performance_arrow_ind = "🔼" if percent_of_group_avg >= 100 else "🔽"
                         st.markdown(f"""<div class='kpi-div'>
                                            <span class='kpi-title'>Total Training Time vs. Group Average:</span><br>
                                            <span class='kpi-value' style='color:{kpi_color_ind};'>{percent_of_group_avg:.1f}% {performance_arrow_ind}</span><br>
                                            <span class='kpi-context'>({participant_total_time:.0f} min vs Avg: {group_avg_total_time:.0f} min)</span>
                                           </div>""", unsafe_allow_html=True)
                     except Exception as e:
                         st.error(f"Error calculating time comparison KPI: {e}")
                 else:
                     st.warning(f"Cannot calculate Time KPI: Missing required columns ({req_cols_kpi1})")

                 # --- Individual Zone Distribution vs Group Average ---
                 st.subheader(f"{participant_selected_ind}'s Time in Zone vs. Group Average")
                 st.markdown("Compares the **total minutes spent in each Heart Rate Zone** by the selected participant against the average minutes spent in those zones by **all participants**.")
                 zone_columns = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"]
                 req_cols_zones = zone_columns + ["Participant"]
                 if all(col in individual_data.columns for col in zone_columns) and all(col in weekly_data.columns for col in req_cols_zones):
                     try:
                         # Ensure zones are numeric for individual
                         for z_col in zone_columns: individual_data[z_col] = pd.to_numeric(individual_data[z_col], errors='coerce').fillna(0)
                         participant_zones = individual_data[zone_columns].sum()

                         # Ensure zones are numeric for group calculation
                         group_zone_data = weekly_data.copy()
                         for z_col in zone_columns: group_zone_data[z_col] = pd.to_numeric(group_zone_data[z_col], errors='coerce').fillna(0)
                         # Calculate group average safely
                         group_zone_totals = group_zone_data.groupby("Participant")[zone_columns].sum()
                         group_avg_zones = group_zone_totals.mean() if not group_zone_totals.empty else pd.Series(0, index=zone_columns)

                         zone_comparison_df = pd.DataFrame({ "Zone": zone_columns, f"{participant_selected_ind}": participant_zones.values, "Group Average": group_avg_zones.values }).fillna(0)

                         fig_zone_comparison = px.bar( zone_comparison_df.melt(id_vars=["Zone"], var_name="Type", value_name="Minutes"), x="Zone", y="Minutes", color="Type", barmode="group", template="plotly_dark", color_discrete_map={f"{participant_selected_ind}": "#FFD700", "Group Average": "#AAAAAA"})
                         fig_zone_comparison.update_layout( title=dict(text=f"{participant_selected_ind}'s Time per Zone vs. Group Average", x=0.01, xanchor='left', font=dict(family='UnifrakturCook, serif', color='#D4AF37')), yaxis_title="Total Minutes", xaxis_title="Heart Rate Zone", legend_title_text="")
                         st.plotly_chart(fig_zone_comparison, use_container_width=True)
                     except Exception as e:
                         st.error(f"Error creating zone comparison chart: {e}")
                 else:
                     st.warning(f"Cannot create Zone comparison chart: Missing required columns ({req_cols_zones})")


                 # --- Individual Cumulative Points Trend ---
                 st.subheader(f"{participant_selected_ind}'s Cumulative Points Over Time")
                 st.markdown("Shows the week-by-week **accumulation of points** for the selected participant, illustrating their scoring progression throughout the competition.")
                 req_cols_cumul = ["Week", "Points"]
                 if all(col in individual_data.columns for col in req_cols_cumul):
                    try:
                        # Ensure numeric and handle NaNs
                        individual_data['Week'] = pd.to_numeric(individual_data['Week'], errors='coerce')
                        individual_data['Points'] = pd.to_numeric(individual_data['Points'], errors='coerce').fillna(0)
                        individual_data.dropna(subset=['Week'], inplace=True) # Need valid week number

                        if not individual_data.empty:
                            ind_cum_points = individual_data.sort_values("Week").groupby("Week")["Points"].sum().cumsum().reset_index()
                            fig_ind_cum_points = px.line( ind_cum_points, x="Week", y="Points", markers=True, template="plotly_dark", labels={"Points": "Cumulative Points", "Week": "Competition Week"})
                            fig_ind_cum_points.update_layout( title=dict(text=f"{participant_selected_ind}'s Cumulative Points", x=0.01, xanchor='left', font=dict(family='UnifrakturCook, serif', color='#D4AF37')), yaxis_title="Cumulative Points")
                            fig_ind_cum_points.update_traces(line=dict(color='#FFD700'))
                            st.plotly_chart(fig_ind_cum_points, use_container_width=True)
                        else:
                            st.info(f"No valid weekly point data found for {participant_selected_ind} to plot cumulative trend.")
                    except Exception as e:
                        st.error(f"Error creating cumulative points chart: {e}")
                 else:
                     st.warning(f"Cannot create cumulative points chart: Missing required columns ({req_cols_cumul})")


                 # --- Activity Type Breakdown ---
                 st.subheader(f"{participant_selected_ind}'s Activity Breakdown")
                 st.markdown("Illustrates how the participant's logged activities are distributed by **type**, based on both the **number of sessions** and the **total time spent**.")
                 req_cols_act = ["Workout Type", "Total Duration"]
                 if all(col in individual_data.columns for col in req_cols_act):
                     try:
                         col1, col2 = st.columns(2)
                         # Count Chart
                         with col1:
                             st.markdown("##### By Number of Activities")
                             # Handle potential NaN workout types
                             activity_counts = individual_data['Workout Type'].dropna().value_counts().reset_index()
                             activity_counts.columns = ['Workout Type', 'Count']
                             if not activity_counts.empty:
                                 fig_act_count = px.pie(activity_counts, names='Workout Type', values='Count', template="plotly_dark", hole=0.3)
                                 fig_act_count.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
                                 fig_act_count.update_layout(showlegend=False, title_text='By Count', title_x=0.5, title_font_family='UnifrakturCook, serif', title_font_color='#D4AF37')
                                 st.plotly_chart(fig_act_count, use_container_width=True)
                             else:
                                 st.info("No activities with valid types found.")
                         # Duration Chart
                         with col2:
                             st.markdown("##### By Total Duration")
                             individual_data['Total Duration'] = pd.to_numeric(individual_data['Total Duration'], errors='coerce').fillna(0)
                             # Group by workout type after handling NaNs
                             activity_duration = individual_data.dropna(subset=['Workout Type']).groupby('Workout Type')['Total Duration'].sum().reset_index()
                             # Filter out zero duration activities if needed
                             activity_duration = activity_duration[activity_duration['Total Duration'] > 0]
                             if not activity_duration.empty:
                                 fig_act_dur = px.pie(activity_duration, names='Workout Type', values='Total Duration', template="plotly_dark", hole=0.3)
                                 fig_act_dur.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
                                 fig_act_dur.update_layout(showlegend=False, title_text='By Duration (min)', title_x=0.5, title_font_family='UnifrakturCook, serif', title_font_color='#D4AF37')
                                 st.plotly_chart(fig_act_dur, use_container_width=True)
                             else:
                                  st.info("No activities with valid duration found.")
                     except Exception as e:
                          st.error(f"Error creating activity breakdown charts: {e}")
                 else:
                     st.warning(f"Cannot create activity breakdown: Missing required columns ({req_cols_act})")


                 # --- Consistency Metric ---
                 st.subheader(f"{participant_selected_ind}'s Consistency")
                 st.markdown("Indicates the number of **distinct weeks** the participant has logged at least one activity during the competition period.")
                 if 'Week' in individual_data.columns:
                     try:
                         individual_data['Week'] = pd.to_numeric(individual_data['Week'], errors='coerce')
                         active_weeks = individual_data['Week'].dropna().nunique() # Ensure NaNs are dropped before nunique
                         # total_competition_weeks defined earlier
                         st.metric(label="Active Weeks Logged", value=f"{active_weeks} out of {total_competition_weeks}")
                     except Exception as e:
                         st.error(f"Error calculating consistency metric: {e}")
                 else:
                     st.warning("Cannot calculate consistency: Missing 'Week' column.")
             else: # individual_data is empty
                 st.info(f"No data found for participant: {participant_selected_ind}")

    else: # weekly_data is None, empty, or missing 'Participant' column
         st.warning("Weekly data is unavailable or missing 'Participant' column, cannot display individual analysis.")


# --- Footer ---
st.markdown("---")
st.caption("🔥 Bourbon Chasers Strava Inferno | Data sourced from Strava activities | Dashboard by Steven Carter 🔥")

# --- END OF FILE app.py ---