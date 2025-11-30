import streamlit as st
import pandas as pd
from PIL import Image
from src.dashboard_utils import load_all_data

st.set_page_config(
    page_title="MBTA Rider Satisfaction Score",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚇 Visualizing the T: MBTA Rider Satisfaction Score")

# Load Data for System Overview
data = load_all_data()

if data:
    st.markdown("### 📊 System Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Median Travel Time
        if not data['travel_times'].empty:
            median_tt = data['travel_times']['travel_time_sec'].median()
            st.metric("Avg Median Travel Time", f"{median_tt:.1f} sec")
        else:
            st.metric("Avg Median Travel Time", "N/A")
            
    with col2:
        # On-Time Performance (Estimated)
        # We define "On-Time" as trips within 1.25x of the median travel time as a proxy
        if not data['travel_times'].empty:
            median_tt = data['travel_times']['travel_time_sec'].median()
            threshold = median_tt * 1.25
            otp = (data['travel_times']['travel_time_sec'] < threshold).mean()
            st.metric("On-Time Performance (Est.)", f"{otp:.1%}")
        else:
            st.metric("On-Time Performance", "N/A")
            
    with col3:
        # Speed Restrictions
        if data['speed_restrictions'] is not None:
            n_restr = len(data['speed_restrictions'])
            st.metric("Total Speed Restrictions", f"{n_restr}")
        else:
            st.metric("Total Speed Restrictions", "N/A")
            
    with col4:
        # Ridership
        # Sum of avg_daily_ridership from rss_results (which sums to ~732k)
        if not data['rss_results'].empty:
            total_ridership = data['rss_results']['avg_daily_ridership'].sum()
            st.metric("Total Daily Ridership", f"{total_ridership:,.0f}")
        else:
            st.metric("Total Daily Ridership", "N/A")
    
    st.markdown("---")

st.markdown("""
### Project Overview

This interactive dashboard visualizes the **Rider Satisfaction Score (RSS)** for the Massachusetts Bay Transportation Authority (MBTA) rapid transit system. 

The RSS is a composite metric designed to reflect the true commuter experience by integrating:
- **Travel Time Reliability**: Variability in trip duration.
- **Speed Restrictions**: Slow zones and track conditions.
- **Ridership Exposure**: How many people are affected by these issues.

### Key Features
- **RSS Dashboard**: Compare performance across different lines (Red, Orange, Blue).
- **Route Deep Dive**: Explore station-level metrics, including the **Commute Time Stress (CTS)** index.
- **Equity Analysis**: Understand how service quality correlates with demographic factors like income and race.
- **Hypothesis Testing**: Statistical validation of our findings.

### Methodology
Our approach combines heavy rail data (AVL) with demographic data to pinpoint where infrastructure investments would yield the highest return in terms of rider satisfaction and equity.

---
*Navigate using the sidebar to explore different sections.*
""")

# Load and show some high-level stats if possible, or an image
st.info("Select a page from the sidebar to begin.")
