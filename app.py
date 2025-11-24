import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="MBTA Rider Satisfaction Score Dashboard",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🚇 MBTA Rider Satisfaction Score (RSS) Dashboard")
st.markdown("""
This dashboard visualizes the Rider Satisfaction Score for Boston's MBTA rapid transit system.
The RSS combines multiple indicators including travel time reliability, speed restrictions, and ridership exposure.
""")

# Sidebar for navigation and filters
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Select a view:",
    ["Overview", "Travel Time Reliability", "Speed Restrictions", "Ridership Analysis"]
)

# Data loading function with caching
@st.cache_data
def load_data():
    """Load all indicator datasets from parquet files"""
    indicators_dir = Path("data/indicators")
    
    try:
        travel_times = pd.read_parquet(indicators_dir / "travel_reliability_indicators.parquet")
        speed_restrictions = pd.read_parquet(indicators_dir / "restriction_indicators.parquet")
        ridership = pd.read_parquet(indicators_dir / "ridership_weights.parquet")
        
        return travel_times, speed_restrictions, ridership
    except FileNotFoundError as e:
        st.error(f"Data files not found. Please ensure indicator datasets are in 'data/indicators/' directory.")
        st.error(f"Error: {e}")
        st.info("Expected files: travel_reliability_indicators.parquet, restriction_indicators.parquet, ridership_weights.parquet")
        return None, None, None

# Load data
travel_times, speed_restrictions, ridership = load_data()

# Check if data loaded successfully
if travel_times is None:
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")

# Route filter
available_routes = sorted(travel_times['route_id'].unique()) if 'route_id' in travel_times.columns else []
selected_routes = st.sidebar.multiselect(
    "Select Routes:",
    options=available_routes,
    default=available_routes
)

# Filter data based on selections
if selected_routes:
    travel_times_filtered = travel_times[travel_times['route_id'].isin(selected_routes)]
    # Restrictions are by 'line', not 'route_id'
    speed_restrictions_filtered = speed_restrictions  # No filtering for now
    ridership_filtered = ridership[ridership['route_id'].isin(selected_routes)] if 'route_id' in ridership.columns else ridership
else:
    travel_times_filtered = travel_times
    speed_restrictions_filtered = speed_restrictions
    ridership_filtered = ridership

# === OVERVIEW PAGE ===
if page == "Overview":
    st.header("📊 System Overview")
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_median_tt = travel_times_filtered['median_travel_time'].mean()
        st.metric("Avg Median Travel Time", f"{avg_median_tt:.1f} sec")
    
    with col2:
        avg_otp = travel_times_filtered['on_time_performance'].mean() * 100 if 'on_time_performance' in travel_times_filtered.columns else 0
        st.metric("On-Time Performance", f"{avg_otp:.1f}%")
    
    with col3:
        total_restrictions = speed_restrictions_filtered['n_restrictions'].sum() if 'n_restrictions' in speed_restrictions_filtered.columns else len(speed_restrictions_filtered)
        st.metric("Total Speed Restrictions", f"{total_restrictions:.0f}")
    
    with col4:
        total_ridership = ridership_filtered['avg_daily_ridership'].sum() if 'avg_daily_ridership' in ridership_filtered.columns else 0
        st.metric("Total Daily Ridership", f"{total_ridership:,.0f}")
    
    st.divider()
    
    # Summary statistics by route
    st.subheader("Performance by Route")
    
    if not travel_times_filtered.empty:
        route_summary = travel_times_filtered.groupby('route_id').agg({
            'median_travel_time': 'mean',
            'travel_time_volatility': 'mean',
            'buffer_time_index': 'mean',
            'on_time_performance': 'mean'
        }).reset_index()
        
        route_summary.columns = ['Route', 'Avg Median Travel Time (sec)', 
                                 'Avg Volatility', 'Avg Buffer Time Index', 
                                 'Avg On-Time Performance']
        
        st.dataframe(route_summary.style.format({
            'Avg Median Travel Time (sec)': '{:.1f}',
            'Avg Volatility': '{:.3f}',
            'Avg Buffer Time Index': '{:.2f}',
            'Avg On-Time Performance': '{:.2%}'
        }), use_container_width=True)

# === TRAVEL TIME RELIABILITY PAGE ===
elif page == "Travel Time Reliability":
    st.header("⏱️ Travel Time Reliability")
    
    st.markdown("""
    Travel time reliability indicators measure how consistent journey times are across the system.
    Higher volatility and buffer time indices indicate less reliable service.
    """)
    
    # Time series chart for median travel times
    st.subheader("Median Travel Time Trends")
    
    # Note: Your data is aggregated by segment, not by date
    # We'll show distribution by route instead
    
    chart = alt.Chart(travel_times_filtered).mark_boxplot().encode(
        x=alt.X('route_id:N', title='Route'),
        y=alt.Y('median_travel_time:Q', title='Median Travel Time (seconds)'),
        color=alt.Color('route_id:N', title='Route'),
        tooltip=['route_id:N', 'median_travel_time:Q', 'on_time_performance:Q']
    ).properties(
        width=800,
        height=400
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)
    
    # Volatility comparison
    st.subheader("Travel Time Volatility by Route")
    
    volatility_chart = alt.Chart(travel_times_filtered).mark_boxplot().encode(
        x=alt.X('route_id:N', title='Route'),
        y=alt.Y('travel_time_volatility:Q', title='Volatility'),
        color=alt.Color('route_id:N', title='Route')
    ).properties(
        width=600,
        height=400
    )
    
    st.altair_chart(volatility_chart, use_container_width=True)
    
    # Detailed data table
    with st.expander("View Detailed Travel Time Data"):
        st.dataframe(travel_times_filtered, use_container_width=True)

# === SPEED RESTRICTIONS PAGE ===
elif page == "Speed Restrictions":
    st.header("🚧 Speed Restrictions Impact")
    
    st.markdown("""
    Speed restrictions slow down trains and affect overall system performance.
    This view shows where and when restrictions are most impactful.
    """)
    
    if not speed_restrictions_filtered.empty:
        # Restrictions by line
        st.subheader("Speed Restrictions by Line")
        
        if 'line' in speed_restrictions_filtered.columns:
            
            bar_chart = alt.Chart(speed_restrictions_filtered).mark_bar().encode(
                x=alt.X('line:N', title='Line'),
                y=alt.Y('n_restrictions:Q', title='Number of Restrictions'),
                color=alt.Color('line:N', title='Line'),
                tooltip=['line:N', 'n_restrictions:Q', 'avg_severity_index:Q', 'total_miles_restricted:Q']
            ).properties(
                width=600,
                height=400
            )
            
            st.altair_chart(bar_chart, use_container_width=True)
            
            # Additional metrics
            st.subheader("Restriction Impact Metrics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_severity = speed_restrictions_filtered['severity_index'].mean()
                st.metric("Avg Severity Index", f"{avg_severity:.3f}")
            
            with col2:
                total_miles = speed_restrictions_filtered['total_miles_restricted'].sum()
                st.metric("Total Miles Restricted", f"{total_miles:.1f}")
            
            with col3:
                avg_duration = speed_restrictions_filtered['avg_duration_days'].mean()
                st.metric("Avg Duration (days)", f"{avg_duration:.1f}")
        
        # Detailed restrictions table
        st.subheader("Speed Restriction Details")
        st.dataframe(speed_restrictions_filtered.style.format({
            'avg_severity_index': '{:.3f}',
            'total_miles_restricted': '{:.2f}',
            'avg_duration_days': '{:.1f}',
            'avg_pct_line_restricted': '{:.1%}'
        }), use_container_width=True)
    else:
        st.info("No speed restriction data available for the selected filters.")

# === RIDERSHIP ANALYSIS PAGE ===
elif page == "Ridership Analysis":
    st.header("👥 Ridership Exposure Weights")
    
    st.markdown("""
    Ridership exposure weights help us understand which routes and segments carry the most passengers.
    These weights are used to calculate exposure-weighted RSS scores.
    """)
    
    if not ridership_filtered.empty and 'avg_daily_ridership' in ridership_filtered.columns:
        # Ridership by route
        st.subheader("Average Daily Ridership by Route")
        
        if 'route_id' in ridership_filtered.columns:
            ridership_by_route = ridership_filtered.groupby('route_id')['avg_daily_ridership'].sum().reset_index()
            
            ridership_chart = alt.Chart(ridership_by_route).mark_bar().encode(
                x=alt.X('route_id:N', title='Route', sort='-y'),
                y=alt.Y('avg_daily_ridership:Q', title='Average Daily Ridership'),
                color=alt.Color('route_id:N', title='Route'),
                tooltip=['route_id:N', 'avg_daily_ridership:Q']
            ).properties(
                width=600,
                height=400
            )
            
            st.altair_chart(ridership_chart, use_container_width=True)
        
        # Ridership by time period
        if 'time_period_name' in ridership_filtered.columns:
            st.subheader("Ridership by Time Period")
            
            time_period_chart = alt.Chart(ridership_filtered).mark_bar().encode(
                x=alt.X('time_period_name:N', title='Time Period'),
                y=alt.Y('sum(avg_daily_ridership):Q', title='Total Daily Ridership'),
                color=alt.Color('route_id:N', title='Route'),
                tooltip=['time_period_name:N', 'route_id:N', 'avg_daily_ridership:Q']
            ).properties(
                width=800,
                height=400
            )
            
            st.altair_chart(time_period_chart, use_container_width=True)
        
        # Exposure weights
        st.subheader("Ridership Exposure Weights")
        
        if 'exposure_weight' in ridership_filtered.columns:
            weight_summary = ridership_filtered.groupby('route_id')['exposure_weight'].sum().reset_index()
            weight_summary.columns = ['Route', 'Total Exposure Weight']
            
            st.dataframe(weight_summary.style.format({
                'Total Exposure Weight': '{:.4f}'
            }), use_container_width=True)
        
        # Detailed ridership data
        with st.expander("View Detailed Ridership Data"):
            st.dataframe(ridership_filtered, use_container_width=True)
    else:
        st.info("No ridership data available for the selected filters.")

# Footer
st.divider()
st.markdown("""
**DS5110 Team Project** | Eric Fu, Dhanrithii Deepa, Yuchen Cai  
Data Source: MBTA Open Data Portal | November-December 2024
""")