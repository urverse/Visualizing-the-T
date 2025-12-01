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
    st.markdown("### 📈 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Median Travel Time
        if not data['travel_times'].empty:
            median_tt = data['travel_times']['travel_time_sec'].median()
            st.metric(
                "Avg Median Travel Time", 
                f"{median_tt:.1f} sec",
                help="Median travel time across all routes and segments"
            )
        else:
            st.metric("Avg Median Travel Time", "N/A")
            
    with col2:
        # On-Time Performance (Estimated)
        if not data['travel_times'].empty:
            median_tt = data['travel_times']['travel_time_sec'].median()
            threshold = median_tt * 1.25
            otp = (data['travel_times']['travel_time_sec'] < threshold).mean()
            st.metric(
                "On-Time Performance (Est.)", 
                f"{otp:.1%}",
                help="Percentage of trips within 125% of median travel time"
            )
        else:
            st.metric("On-Time Performance", "N/A")
            
    with col3:
        # Speed Restrictions
        if data['speed_restrictions'] is not None:
            n_restr = len(data['speed_restrictions'])
            st.metric(
                "Total Speed Restrictions", 
                f"{n_restr}",
                help="Active speed restrictions tracked across the system"
            )
        else:
            st.metric("Total Speed Restrictions", "N/A")
            
    with col4:
        # Ridership
        if not data['rss_results'].empty:
            total_ridership = data['rss_results']['avg_daily_ridership'].sum()
            st.metric(
                "Total Daily Ridership", 
                f"{total_ridership:,.0f}",
                help="Combined average daily ridership across all analyzed routes"
            )
        else:
            st.metric("Total Daily Ridership", "N/A")
    
    st.markdown("---")

# Highlight key finding upfront
st.success("""
✅ **Key Finding**: Orange Line achieves the highest RSS (100.0) while serving 61% low-income and 66% minority riders. 
This proves our methodology is **equity-neutral** and does not discriminate against disadvantaged communities.
""")

st.markdown("---")

st.markdown("""
### Project Overview

This interactive dashboard visualizes the **Rider Satisfaction Score (RSS)** for the Massachusetts Bay Transportation Authority (MBTA) rapid transit system. 

The RSS is a composite metric designed to reflect the true commuter experience by integrating:

- **Travel Time Reliability**: Variability in trip duration
- **Speed Restrictions**: Slow zones and track conditions  
- **Ridership Exposure**: How many people are affected by these issues

Unlike traditional metrics that focus solely on operational efficiency, RSS captures what riders actually experience daily.

---

### Key Features

**📊 RSS Dashboard**: Compare performance across different lines (Red, Orange, Blue) with 95% confidence intervals

**🔍 Route Deep Dive**: Explore station-level metrics, including the **Commute Time Stress (CTS)** index

**⚖️ Equity Analysis**: Understand how service quality correlates with demographic factors like income and race

**📈 Hypothesis Testing**: Statistical validation including ANOVA (p=0.018) and regression modeling (R²=1.0)

---

### Methodology

Our approach combines heavy rail data (AVL) with demographic data to pinpoint where infrastructure investments would yield the highest return in terms of rider satisfaction and equity.

**RSS Components (Literature-Based Weights):**
- Travel Time Volatility: 25%
- Buffer Time Index: 25%
- On-Time Performance: 25%
- Median Travel Time: 15%
- Speed Restrictions: 10%

**Scale**: 60-100 (interpretable like grades)

---

### Quick Results

| Route | RSS Score | Key Characteristic |
|-------|-----------|-------------------|
| 🟠 Orange | 100.0 | Best overall performance, most consistent |
| 🔴 Red | 68.0 | 113 active restrictions, lowest OTP |
| 🔵 Blue | 60.0 | Highest volatility, needs improvement |

---

*Navigate using the sidebar to explore different sections. Start with **RSS Dashboard** for route comparisons.*
""")

# Bottom navigation helper
st.markdown("---")
st.info("💡 **Getting Started**: Select **RSS Dashboard** from the sidebar to see detailed route comparisons →")

# Footer
st.markdown("---")
st.caption("📊 Data: MBTA Open Data Portal (2024) | 🔗 [GitHub Repository](https://github.com/urverse/Visualizing-the-T) | 👥 Team: Eric (Data Engineering), Louis (Feature Engineering & App), Dhanrithii (Analytics)")
