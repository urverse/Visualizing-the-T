import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
import numpy as np

# Page configuration
st.set_page_config(
    page_title="MBTA Rider Satisfaction Score Dashboard",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for MBTA branding
st.markdown("""
<style>
    .mbta-header {
        background: linear-gradient(135deg, #003DA5 0%, #DA291C 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #003DA5;
    }
    .info-box {
        background: #e7f3ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #003DA5;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for navigation
st.sidebar.image("https://cdn.mbta.com/sites/default/files/styles/media_thumbnail/public/2022-04/MBTA-logo-t-digital.png", width=100)
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page:",
    ["🏠 Home", "📊 RSS Dashboard", "🔍 Route Deep Dive", 
     "⚖️ Equity Analysis", "🔬 Hypothesis Testing", "ℹ️ About"]
)

# Data loading function with caching
@st.cache_data
def load_data():
    """Load all datasets"""
    indicators_dir = Path("data/indicators")
    processed_dir = Path("data/processed")
    
    try:
        # Original indicators
        travel_times = pd.read_parquet(indicators_dir / "travel_reliability_indicators.parquet")
        speed_restrictions = pd.read_parquet(indicators_dir / "restriction_indicators.parquet")
        ridership = pd.read_parquet(indicators_dir / "ridership_weights.parquet")
        
        # New analytics files
        rss_results = pd.read_csv(processed_dir / "rss_final_results.csv")
        station_rss = pd.read_csv(processed_dir / "station_rss_scores.csv")
        bootstrap_ci = pd.read_csv(processed_dir / "bootstrap_confidence_intervals.csv")
        model_results = pd.read_csv(processed_dir / "regression_model_results.csv")
        learned_weights = pd.read_csv(processed_dir / "learned_weights.csv")
        survey = pd.read_csv(processed_dir / "passenger_survey_sample.csv")
        
        return {
            'travel_times': travel_times,
            'speed_restrictions': speed_restrictions,
            'ridership': ridership,
            'rss_results': rss_results,
            'station_rss': station_rss,
            'bootstrap_ci': bootstrap_ci,
            'model_results': model_results,
            'learned_weights': learned_weights,
            'survey': survey
        }
    except FileNotFoundError as e:
        st.error(f"Data files not found: {e}")
        return None

# Load data
data = load_data()

if data is None:
    st.stop()

# Extract datasets
travel_times = data['travel_times']
speed_restrictions = data['speed_restrictions']
ridership = data['ridership']
rss_results = data['rss_results']
station_rss = data['station_rss']
bootstrap_ci = data['bootstrap_ci']

# MBTA color scheme
MBTA_COLORS = {'Blue': '#003DA5', 'Orange': '#ED8B00', 'Red': '#DA291C'}

# ============================================================================
# HOME PAGE
# ============================================================================
if page == "🏠 Home":
    st.markdown('<div class="mbta-header"><h1>🚇 Visualizing the T</h1><h3>A Data-Driven Analysis of MBTA Rider Satisfaction</h3></div>', unsafe_allow_html=True)
    
    # Project overview
    st.markdown("""
    ## Project Overview
    
    This dashboard presents a comprehensive analysis of Boston's MBTA rapid transit system through 
    the lens of a **Rider Satisfaction Score (RSS)** - a composite metric that quantifies service 
    quality across multiple dimensions.
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Routes Analyzed", "3", help="Blue, Orange, and Red Lines")
    with col2:
        st.metric("Stations Evaluated", f"{len(station_rss):,}", help="Station-level performance metrics")
    with col3:
        st.metric("Travel Segments", f"{len(travel_times):,}", help="Individual route segments analyzed")
    with col4:
        st.metric("Daily Ridership", f"{ridership['avg_daily_ridership'].sum():,.0f}", help="Average daily passengers")
    
    st.divider()
    
    # Key findings
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🎯 Key Findings")
        
        st.markdown("""
        **RSS Scores (60-100 Scale):**
        - 🟠 **Orange Line: 100.0** - Best overall performance
        - 🔴 **Red Line: 68.0** - Moderate performance
        - 🔵 **Blue Line: 60.0** - Needs improvement
        
        **Statistical Analysis:**
        - ✅ Significant differences in travel time volatility (p=0.018)
        - ❌ No significant difference in on-time performance (p=0.229)
        
        **Equity Assessment:**
        - ✅ **No discrimination detected** - Orange Line serves highest proportion of low-income (61%) 
          and minority (66%) riders while maintaining best RSS score
        
        **Performance Drivers:**
        - Most important: Travel time volatility and buffer time
        - Predictive model R² = 1.0 (perfect fit on training data)
        """)
    
    with col2:
        st.markdown("### 📊 Quick Stats")
        
        # Mini RSS chart
        rss_chart_data = rss_results[['route_id', 'RSS_literature_scaled']].sort_values('RSS_literature_scaled', ascending=False)
        
        mini_chart = alt.Chart(rss_chart_data).mark_bar().encode(
            y=alt.Y('route_id:N', title=None, sort='-x'),
            x=alt.X('RSS_literature_scaled:Q', title='RSS Score', scale=alt.Scale(domain=[0, 105])),
            color=alt.Color('route_id:N', 
                           scale=alt.Scale(domain=list(MBTA_COLORS.keys()), 
                                         range=list(MBTA_COLORS.values())),
                           legend=None),
            tooltip=['route_id:N', alt.Tooltip('RSS_literature_scaled:Q', format='.1f')]
        ).properties(height=150)
        
        st.altair_chart(mini_chart, use_container_width=True)
        
        st.info("💡 RSS scores are **relative** - they compare performance across the three heavy rail lines.")
    
    st.divider()
    
    # What is RSS section
    st.markdown("### 🤔 What is the Rider Satisfaction Score?")
    
    st.markdown("""
    The RSS is a composite metric (60-100 scale) that combines five key performance indicators:
    
    | Indicator | Weight | Description |
    |-----------|--------|-------------|
    | On-Time Performance | 25% | Percentage of trips meeting schedule |
    | Travel Time Volatility | 25% | Consistency of journey times |
    | Buffer Time Index | 25% | Extra time needed for reliable planning |
    | Median Travel Time | 15% | Absolute journey duration |
    | Speed Restrictions | 10% | Impact of slow zones |
    
    *Weights based on transit research literature prioritizing reliability over speed.*
    """)
    
    st.divider()
    
    # Navigation guide
    st.markdown("### 🧭 Navigation Guide")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📊 RSS Dashboard**  
        Interactive comparison of route performance with detailed metrics and visualizations.
        
        **🔍 Route Deep Dive**  
        Station-level analysis, bootstrap confidence intervals, and performance distributions.
        """)
    
    with col2:
        st.markdown("""
        **⚖️ Equity Analysis**  
        Correlation between RSS scores and socioeconomic demographics.
        
        **🔬 Hypothesis Testing**  
        Statistical validation of performance differences across routes.
        """)
    
    with col3:
        st.markdown("""
        **ℹ️ About**  
        Methodology, data sources, and team information.
        """)

# ============================================================================
# RSS DASHBOARD
# ============================================================================
elif page == "📊 RSS Dashboard":
    st.markdown('<div class="mbta-header"><h1>📊 RSS Dashboard</h1><p>Interactive Route Performance Comparison</p></div>', unsafe_allow_html=True)
    
    # Filters
    st.sidebar.header("Filters")
    available_routes = sorted(travel_times['route_id'].unique())
    selected_routes = st.sidebar.multiselect(
        "Select Routes:",
        options=available_routes,
        default=available_routes
    )
    
    if not selected_routes:
        st.warning("Please select at least one route.")
        st.stop()
    
    # Filter data
    travel_times_filtered = travel_times[travel_times['route_id'].isin(selected_routes)]
    rss_filtered = rss_results[rss_results['route_id'].isin(selected_routes)]
    
    # Main RSS comparison
    st.subheader("🎯 Rider Satisfaction Score by Route")
    
    col1, col2, col3 = st.columns(3)
    
    for idx, row in rss_filtered.sort_values('RSS_literature_scaled', ascending=False).iterrows():
        with [col1, col2, col3][idx % 3]:
            st.markdown(f"### {row['route_id']} Line")
            st.metric("RSS Score", f"{row['RSS_literature_scaled']:.1f}/100")
            st.metric("On-Time Performance", f"{row['on_time_performance']:.1%}")
            st.metric("Volatility", f"{row['travel_time_volatility']:.2f}")
            st.metric("Buffer Time Index", f"{row['buffer_time_index']:.2f}")
    
    st.divider()
    
    # RSS Bar Chart
    rss_chart_data = rss_filtered[['route_id', 'RSS_literature_scaled']].sort_values('RSS_literature_scaled', ascending=False)
    
    chart = alt.Chart(rss_chart_data).mark_bar(size=80).encode(
        x=alt.X('route_id:N', 
                title='Route', 
                sort=alt.EncodingSortField(field='RSS_literature_scaled', order='descending')),
        y=alt.Y('RSS_literature_scaled:Q', 
                title='RSS Score (60-100)', 
                scale=alt.Scale(domain=[0, 105])),
        color=alt.Color('route_id:N', 
                       scale=alt.Scale(domain=list(MBTA_COLORS.keys()), 
                                     range=list(MBTA_COLORS.values())),
                       legend=None),
        tooltip=[
            alt.Tooltip('route_id:N', title='Route'),
            alt.Tooltip('RSS_literature_scaled:Q', format='.1f', title='RSS Score')
        ]
    ).properties(height=400)
    
    text = chart.mark_text(
        align='center',
        baseline='bottom',
        dy=-5,
        fontSize=14,
        fontWeight='bold'
    ).encode(
        text=alt.Text('RSS_literature_scaled:Q', format='.1f')
    )
    
    st.altair_chart((chart + text), use_container_width=True)
    
    st.info("💡 **Note:** RSS uses a 60-100 scale (like letter grades). Scores are relative - they compare performance across the selected routes.")
    
    st.divider()
    
    # Component breakdown heatmap
    st.subheader("📈 Component Score Breakdown")
    
    components = ['median_travel_time', 'travel_time_volatility', 
                  'buffer_time_index', 'on_time_performance', 'total_miles_restricted']
    
    component_data = []
    for _, row in rss_filtered.iterrows():
        for comp in components:
            component_data.append({
                'Route': row['route_id'],
                'Component': comp.replace('_', ' ').title(),
                'Value': row[comp]
            })
    
    component_df = pd.DataFrame(component_data)
    
    heatmap = alt.Chart(component_df).mark_rect().encode(
        x=alt.X('Route:N', title='Route'),
        y=alt.Y('Component:N', title='Performance Indicator'),
        color=alt.Color('Value:Q', scale=alt.Scale(scheme='redyellowgreen'), title='Z-Score'),
        tooltip=['Route:N', 'Component:N', alt.Tooltip('Value:Q', format='.3f', title='Normalized Value')]
    ).properties(height=300)
    
    st.altair_chart(heatmap, use_container_width=True)
    
    st.divider()
    
    # Performance metrics table
    st.subheader("📋 Detailed Performance Metrics")
    
    performance_table = travel_times_filtered.groupby('route_id').agg({
        'median_travel_time': 'mean',
        'travel_time_volatility': 'mean',
        'buffer_time_index': 'mean',
        'planning_time_index': 'mean',
        'on_time_performance': 'mean',
        'n_observations': 'sum'
    }).reset_index()
    
    performance_table.columns = ['Route', 'Avg Travel Time (sec)', 'Volatility', 
                                  'Buffer Time Index', 'Planning Time Index', 
                                  'On-Time Performance', 'Observations']
    
    st.dataframe(performance_table.style.format({
        'Avg Travel Time (sec)': '{:.1f}',
        'Volatility': '{:.3f}',
        'Buffer Time Index': '{:.2f}',
        'Planning Time Index': '{:.2f}',
        'On-Time Performance': '{:.2%}',
        'Observations': '{:,.0f}'
    }), use_container_width=True)

# ============================================================================
# ROUTE DEEP DIVE
# ============================================================================
elif page == "🔍 Route Deep Dive":
    st.markdown('<div class="mbta-header"><h1>🔍 Route Deep Dive</h1><p>Station-Level Analysis & Performance Distribution</p></div>', unsafe_allow_html=True)
    
    # Route selector
    selected_route = st.sidebar.selectbox(
        "Select Route for Deep Dive:",
        options=sorted(travel_times['route_id'].unique())
    )
    
    station_rss_route = station_rss[station_rss['route_id'] == selected_route]
    travel_times_route = travel_times[travel_times['route_id'] == selected_route]
    
    # Route overview
    st.subheader(f"{selected_route} Line Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    route_rss = rss_results[rss_results['route_id'] == selected_route].iloc[0]
    
    with col1:
        st.metric("RSS Score", f"{route_rss['RSS_literature_scaled']:.1f}/100")
    with col2:
        st.metric("Stations", f"{len(station_rss_route)}")
    with col3:
        st.metric("Avg OTP", f"{route_rss['on_time_performance']:.1%}")
    with col4:
        st.metric("Volatility", f"{route_rss['travel_time_volatility']:.2f}")
    
    st.divider()
    
    # Station-level analysis
    st.subheader("🚉 Station-Level RSS Scores")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribution histogram
        hist = alt.Chart(station_rss_route).mark_bar().encode(
            x=alt.X('station_rss_scaled:Q', bin=alt.Bin(step=5), title='Station RSS Score'),
            y=alt.Y('count():Q', title='Number of Stations'),
            color=alt.value(MBTA_COLORS[selected_route]),
            tooltip=['count():Q']
        ).properties(height=300, title='Score Distribution')
        
        st.altair_chart(hist, use_container_width=True)
    
    with col2:
        # Box plot
        box = alt.Chart(station_rss_route).mark_boxplot().encode(
            y=alt.Y('station_rss_scaled:Q', title='Station RSS Score'),
            color=alt.value(MBTA_COLORS[selected_route])
        ).properties(height=300, title='Score Statistics')
        
        st.altair_chart(box, use_container_width=True)
    
    st.divider()
    
    # Top and bottom performers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 Stations")
        best = station_rss_route.nlargest(10, 'station_rss_scaled')[['from_stop_id', 'station_rss_scaled']]
        best.columns = ['Station', 'RSS Score']
        st.dataframe(best.style.format({'RSS Score': '{:.1f}'}), use_container_width=True)
    
    with col2:
        st.subheader("⚠️ Bottom 10 Stations")
        worst = station_rss_route.nsmallest(10, 'station_rss_scaled')[['from_stop_id', 'station_rss_scaled']]
        worst.columns = ['Station', 'RSS Score']
        st.dataframe(worst.style.format({'RSS Score': '{:.1f}'}), use_container_width=True)
    
    st.divider()
    
    # Bootstrap confidence intervals
    st.subheader("📊 Bootstrap Confidence Intervals (95%)")
    
    st.markdown("""
    Confidence intervals show the uncertainty in RSS estimates based on 1000 bootstrap resamples.
    Narrower intervals indicate more consistent performance across stations.
    """)
    
    # Show all routes for comparison
    ci_chart = alt.Chart(bootstrap_ci).mark_bar().encode(
        x=alt.X('Route:N', title='Route'),
        y=alt.Y('Mean_RSS:Q', title='Mean RSS Score'),
        color=alt.Color('Route:N',
                       scale=alt.Scale(domain=list(MBTA_COLORS.keys()),
                                     range=list(MBTA_COLORS.values())),
                       legend=None),
        tooltip=['Route:N', alt.Tooltip('Mean_RSS:Q', format='.2f'), 
                alt.Tooltip('CI_Lower:Q', format='.2f', title='Lower CI'), 
                alt.Tooltip('CI_Upper:Q', format='.2f', title='Upper CI'),
                alt.Tooltip('CI_Width:Q', format='.2f', title='CI Width')]
    ).properties(height=400)
    
    ci_error = alt.Chart(bootstrap_ci).mark_errorbar(size=10).encode(
        x=alt.X('Route:N'),
        y=alt.Y('CI_Lower:Q', title=''),
        y2=alt.Y2('CI_Upper:Q'),
        color=alt.Color('Route:N',
                       scale=alt.Scale(domain=list(MBTA_COLORS.keys()),
                                     range=list(MBTA_COLORS.values())),
                       legend=None)
    )
    
    st.altair_chart((ci_chart + ci_error), use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    for idx, row in bootstrap_ci.iterrows():
        with [col1, col2, col3][idx]:
            st.metric(
                f"{row['Route']} Line",
                f"{row['Mean_RSS']:.2f}",
                delta=f"±{row['CI_Width']/2:.2f}",
                delta_color="off"
            )
    
    st.divider()
    
    # Travel time reliability
    st.subheader("⏱️ Travel Time Reliability")
    
    col1, col2 = st.columns(2)
    
    with col1:
        travel_hist = alt.Chart(travel_times_route).mark_bar().encode(
            x=alt.X('median_travel_time:Q', bin=alt.Bin(maxbins=20), title='Median Travel Time (sec)'),
            y=alt.Y('count():Q', title='Frequency'),
            color=alt.value(MBTA_COLORS[selected_route])
        ).properties(height=300, title='Travel Time Distribution')
        
        st.altair_chart(travel_hist, use_container_width=True)
    
    with col2:
        volatility_hist = alt.Chart(travel_times_route).mark_bar().encode(
            x=alt.X('travel_time_volatility:Q', bin=alt.Bin(maxbins=20), title='Volatility'),
            y=alt.Y('count():Q', title='Frequency'),
            color=alt.value(MBTA_COLORS[selected_route])
        ).properties(height=300, title='Volatility Distribution')
        
        st.altair_chart(volatility_hist, use_container_width=True)

# ============================================================================
# EQUITY ANALYSIS
# ============================================================================
elif page == "⚖️ Equity Analysis":
    st.markdown('<div class="mbta-header"><h1>⚖️ Equity Analysis</h1><p>RSS Performance vs Demographics</p></div>', unsafe_allow_html=True)
    
    st.markdown("""
    This analysis examines whether RSS scores correlate with income and race/ethnicity demographics
    to identify potential service equity issues.
    """)
    
    # Equity summary data
    equity_data = pd.DataFrame({
        'Route': ['Orange', 'Red', 'Blue'],
        'RSS_Score': [100.0, 68.0, 60.0],
        'Low_Income_Pct': [61.3, 23.0, 6.8],
        'Minority_Pct': [65.7, 45.3, 35.0]
    })
    
    st.divider()
    
    # Key findings callout
    st.success("""
    ### ✅ KEY FINDING: NO DISCRIMINATION DETECTED
    
    The Orange Line, which serves the **highest proportion** of low-income (61%) and minority (66%) riders, 
    has the **BEST RSS score (100.0)**.
    
    This demonstrates **equitable service distribution** across socioeconomic groups.
    """)
    
    st.divider()
    
    # Correlation analysis
    st.subheader("📊 RSS vs Demographics Correlation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### RSS vs Low-Income Ridership")
        
        income_chart = alt.Chart(equity_data).mark_circle(size=200).encode(
            x=alt.X('Low_Income_Pct:Q', title='Low-Income Ridership (%)', scale=alt.Scale(domain=[0, 70])),
            y=alt.Y('RSS_Score:Q', title='RSS Score', scale=alt.Scale(domain=[50, 110])),
            color=alt.Color('Route:N',
                           scale=alt.Scale(domain=list(MBTA_COLORS.keys()),
                                         range=list(MBTA_COLORS.values())),
                           legend=None),
            tooltip=['Route:N', 'RSS_Score:Q', 'Low_Income_Pct:Q']
        ).properties(height=400)
        
        # Add trend line
        income_line = income_chart.transform_regression(
            'Low_Income_Pct', 'RSS_Score'
        ).mark_line(color='gray', strokeDash=[5, 5])
        
        st.altair_chart((income_chart + income_line), use_container_width=True)
        
        st.metric("Spearman Correlation", "r = +1.0", help="Perfect positive correlation")
        st.caption("Higher low-income ridership → Higher RSS ✅")
    
    with col2:
        st.markdown("#### RSS vs Minority Ridership")
        
        minority_chart = alt.Chart(equity_data).mark_circle(size=200).encode(
            x=alt.X('Minority_Pct:Q', title='Minority Ridership (%)', scale=alt.Scale(domain=[30, 70])),
            y=alt.Y('RSS_Score:Q', title='RSS Score', scale=alt.Scale(domain=[50, 110])),
            color=alt.Color('Route:N',
                           scale=alt.Scale(domain=list(MBTA_COLORS.keys()),
                                         range=list(MBTA_COLORS.values())),
                           legend=None),
            tooltip=['Route:N', 'RSS_Score:Q', 'Minority_Pct:Q']
        ).properties(height=400)
        
        # Add trend line
        minority_line = minority_chart.transform_regression(
            'Minority_Pct', 'RSS_Score'
        ).mark_line(color='gray', strokeDash=[5, 5])
        
        st.altair_chart((minority_chart + minority_line), use_container_width=True)
        
        st.metric("Spearman Correlation", "r = +1.0", help="Perfect positive correlation")
        st.caption("Higher minority ridership → Higher RSS ✅")
    
    st.divider()
    
    # Detailed breakdown
    st.subheader("📋 Demographic Breakdown by Route")
    
    st.dataframe(equity_data.style.format({
        'RSS_Score': '{:.1f}',
        'Low_Income_Pct': '{:.1f}%',
        'Minority_Pct': '{:.1f}%'
    }).background_gradient(subset=['RSS_Score'], cmap='RdYlGn', vmin=60, vmax=100), 
    use_container_width=True)
    
    st.divider()
    
    # Interpretation
    st.subheader("🎯 Interpretation")
    
    st.markdown("""
    **Positive Correlations (r = +1.0):**
    - Routes serving more low-income riders have HIGHER RSS scores
    - Routes serving more minority riders have HIGHER RSS scores
    
    **What This Means:**
    - ✅ No evidence of discriminatory service allocation
    - ✅ Disadvantaged communities receive comparable or better service
    - ✅ Orange Line (serving most disadvantaged riders) has best performance
    
    **Important Caveats:**
    - Small sample size (n=3 routes) limits statistical power
    - Correlation does not imply causation
    - Other factors may influence both demographics and service quality
    - This analysis uses aggregated route-level data
    """)

# ============================================================================
# HYPOTHESIS TESTING
# ============================================================================
elif page == "🔬 Hypothesis Testing":
    st.markdown('<div class="mbta-header"><h1>🔬 Hypothesis Testing</h1><p>Statistical Validation of Performance Differences</p></div>', unsafe_allow_html=True)
    
    st.markdown("""
    Statistical tests to determine if observed performance differences across routes are 
    statistically significant or could occur by chance.
    """)
    
    st.divider()
    
    # Test 1: Volatility
    st.subheader("Test 1: Travel Time Volatility Comparison")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Null Hypothesis (H₀):** Mean volatility is equal across all routes  
        **Alternative Hypothesis (H₁):** At least one route has different volatility
        
        **Statistical Test:** One-way ANOVA  
        **Significance Level:** α = 0.05
        """)
        
        volatility_by_route = travel_times.groupby('route_id')['travel_time_volatility'].agg(['mean', 'std', 'count']).reset_index()
        volatility_by_route.columns = ['Route', 'Mean', 'Std Dev', 'N']
        
        st.dataframe(volatility_by_route.style.format({
            'Mean': '{:.3f}',
            'Std Dev': '{:.3f}',
            'N': '{:.0f}'
        }), use_container_width=True)
    
    with col2:
        st.markdown("### Result")
        st.error("**Reject H₀**")
        st.metric("p-value", "0.018", delta="< 0.05", delta_color="inverse")
        
        st.markdown("""
        **Conclusion:**  
        Routes have significantly different volatility levels.
        
        - Blue: Highest (2.76)
        - Red: Lowest (0.57)
        """)
    
    # Visualization
    vol_chart = alt.Chart(travel_times).transform_density(
        'travel_time_volatility',
        as_=['travel_time_volatility', 'density'],
        groupby=['route_id']
    ).mark_area(opacity=0.5).encode(
        x=alt.X('travel_time_volatility:Q', title='Volatility'),
        y=alt.Y('density:Q', title='Density'),
        color=alt.Color('route_id:N',
                       scale=alt.Scale(domain=list(MBTA_COLORS.keys()),
                                     range=list(MBTA_COLORS.values())),
                       title='Route')
    ).properties(height=300)
    
    st.altair_chart(vol_chart, use_container_width=True)
    
    st.divider()
    
    # Test 2: On-Time Performance
    st.subheader("Test 2: On-Time Performance Comparison")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Null Hypothesis (H₀):** Mean OTP is equal across all routes  
        **Alternative Hypothesis (H₁):** At least one route has different OTP
        
        **Statistical Test:** One-way ANOVA  
        **Significance Level:** α = 0.05
        """)
        
        otp_by_route = travel_times.groupby('route_id')['on_time_performance'].agg(['mean', 'std', 'count']).reset_index()
        otp_by_route.columns = ['Route', 'Mean', 'Std Dev', 'N']
        
        st.dataframe(otp_by_route.style.format({
            'Mean': '{:.3f}',
            'Std Dev': '{:.3f}',
            'N': '{:.0f}'
        }), use_container_width=True)
    
    with col2:
        st.markdown("### Result")
        st.success("**Fail to Reject H₀**")
        st.metric("p-value", "0.229", delta="> 0.05", delta_color="normal")
        
        st.markdown("""
        **Conclusion:**  
        No significant difference in OTP across routes.
        
        All routes perform similarly (~75% OTP).
        """)
    
    # Visualization
    otp_chart = alt.Chart(travel_times).transform_density(
        'on_time_performance',
        as_=['on_time_performance', 'density'],
        groupby=['route_id']
    ).mark_area(opacity=0.5).encode(
        x=alt.X('on_time_performance:Q', title='On-Time Performance'),
        y=alt.Y('density:Q', title='Density'),
        color=alt.Color('route_id:N',
                       scale=alt.Scale(domain=list(MBTA_COLORS.keys()),
                                     range=list(MBTA_COLORS.values())),
                       title='Route')
    ).properties(height=300)
    
    st.altair_chart(otp_chart, use_container_width=True)
    
    st.divider()
    
    # Summary
    st.subheader("📋 Testing Summary")
    
    summary_data = pd.DataFrame({
        'Test': ['Travel Time Volatility', 'On-Time Performance'],
        'Statistical Test': ['One-way ANOVA', 'One-way ANOVA'],
        'p-value': [0.018, 0.229],
        'Result': ['Significant ✓', 'Not Significant ✗'],
        'Interpretation': [
            'Routes differ significantly in consistency',
            'Routes perform similarly in meeting schedules'
        ]
    })
    
    st.dataframe(summary_data, use_container_width=True)
    
    st.info("""
    **Key Takeaway:** While routes have different reliability (volatility), they maintain similar 
    on-time performance. This suggests that all lines face similar challenges in meeting schedules, 
    but some handle variability better than others.
    """)

# ============================================================================
# ABOUT PAGE
# ============================================================================
elif page == "ℹ️ About":
    st.markdown('<div class="mbta-header"><h1>ℹ️ About This Project</h1><p>Methodology, Data Sources, and Team</p></div>', unsafe_allow_html=True)
    
    # Methodology
    st.header("📐 Methodology")
    
    st.markdown("""
    ### Rider Satisfaction Score (RSS) Calculation
    
    The RSS is a composite metric that combines five performance indicators:
    
    1. **Data Collection:** Aggregate MBTA operational data by route segment
    2. **Normalization:** Convert indicators to z-scores for comparability
    3. **Weighting:** Apply literature-based weights prioritizing reliability
    4. **Scaling:** Transform to 60-100 scale (like letter grades)
    
    **Formula:**
    ```
    RSS = 0.25×OTP - 0.25×Volatility - 0.25×BufferTime - 0.15×TravelTime - 0.10×Restrictions
    RSS_scaled = 60 + 40 × (RSS - min) / (max - min)
    ```
    
    **Weight Justification:**
    - Literature shows riders value **reliability** over absolute speed
    - On-time performance, volatility, and buffer time each get 25%
    - Travel time (15%) and restrictions (10%) have lower weights
    """)
    
    st.divider()
    
    # Data sources
    st.header("📊 Data Sources")
    
    st.markdown("""
    ### MBTA Open Data Portal
    
    All data sourced from the MBTA's public data portal (November 2024):
    
    | Dataset | Records | Time Period | Description |
    |---------|---------|-------------|-------------|
    | Travel Times | 1,850+ segments | Fall 2024 | Segment-level travel time measurements |
    | Speed Restrictions | 100+ restrictions | 2024 | Active slow zones and severity |
    | Ridership | 36K+ trips | Fall 2024 | Passenger counts by route and time period |
    | Passenger Survey | 10K+ responses | 2024 | Demographics and satisfaction |
    
    **Scope:**
    - Heavy rail lines only (Blue, Orange, Red)
    - Green Line excluded due to light rail complexity
    - Focus on rapid transit operations
    """)
    
    st.divider()
    
    # Technical stack
    st.header("⚙️ Technical Stack")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Data Processing:**
        - Python 3.12
        - PySpark for big data handling
        - Pandas for analysis
        - PyArrow for efficient storage
        
        **Statistical Analysis:**
        - SciPy for hypothesis testing
        - Scikit-learn for regression
        - Bootstrap resampling (1000 iterations)
        """)
    
    with col2:
        st.markdown("""
        **Visualization:**
        - Streamlit for dashboard
        - Altair for interactive charts
        - Matplotlib/Seaborn for exploratory analysis
        
        **Deployment:**
        - GitHub for version control
        - Render for cloud hosting
        - Continuous deployment pipeline
        """)
    
    st.divider()
    
    # Team
    st.header("👥 Team")
    
    st.markdown("""
    ### DS5110 Fall 2024 - Final Project
    
    **Team Members:**
    - **Eric Fu** - Project lead, data engineering, deployment
    - **Dhanrithii Deepa** - Statistical analysis, equity research  
    - **Yuchen Cai** - Indicator engineering, methodology
    
    **Project Timeline:**
    - Week 1 (Nov 10-17): Data consolidation and preparation
    - Week 2 (Nov 18-24): RSS calculation and validation
    - Week 3 (Nov 25-Dec 1): Advanced analytics and dashboard
    
    **Advisor:** Professor [Name]  
    **Institution:** Northeastern University
    """)
    
    st.divider()
    
    # Links
    st.header("🔗 Links & Resources")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Project Resources:**
        - [GitHub Repository](https://github.com/urverse/Visualizing-the-T)
        - [MBTA Open Data](https://www.mbta.com/developers/mbta-performance)
        """)
    
    with col2:
        st.markdown("""
        **Documentation:**
        - Project Proposal
        - Final Report
        - Code Documentation
        """)
    
    with col3:
        st.markdown("""
        **Contact:**
        - [Email Team](mailto:your-email@northeastern.edu)
        - Report Issues on GitHub
        """)
    
    st.divider()
    
    # Acknowledgments
    st.header("🙏 Acknowledgments")
    
    st.markdown("""
    Special thanks to:
    - MBTA for providing comprehensive open data
    - DS5110 teaching staff for guidance
    - Transit research community for methodology references
    - Fellow students for feedback and suggestions
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p><strong>Visualizing the T: MBTA Rider Satisfaction Analysis</strong></p>
    <p>DS5110 Fall 2024 | Eric Fu, Dhanrithii Deepa, Yuchen Cai</p>
    <p>Data Source: MBTA Open Data Portal | Last Updated: November 2024</p>
</div>
""", unsafe_allow_html=True)