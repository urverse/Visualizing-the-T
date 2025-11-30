import streamlit as st
import pandas as pd
import altair as alt
from src.dashboard_utils import load_all_data

st.set_page_config(page_title="RSS Dashboard", page_icon="📊", layout="wide")

st.title("📊 RSS Dashboard: System Overview")

data = load_all_data()

if data is None:
    st.error("Failed to load data.")
    st.stop()

rss_results = data['rss_results']
confidence_intervals = data.get('confidence_intervals')
learned_weights = data.get('learned_weights')
regression_results = data.get('regression_results')

st.markdown("### Route Comparison")
st.write("Comparing Rider Satisfaction Scores across major lines.")

# Metrics Row
col1, col2, col3 = st.columns(3)
with col1:
    best_route = rss_results.loc[rss_results['RSS_literature_scaled'].idxmax()]
    st.metric("Best Performing Line", best_route['route_id'], f"{best_route['RSS_literature_scaled']:.1f}")
with col2:
    worst_route = rss_results.loc[rss_results['RSS_literature_scaled'].idxmin()]
    st.metric("Worst Performing Line", worst_route['route_id'], f"{worst_route['RSS_literature_scaled']:.1f}")
with col3:
    avg_score = rss_results['RSS_literature_scaled'].mean()
    st.metric("System Average RSS", f"{avg_score:.1f}")


# Bar Chart with Confidence Intervals
if confidence_intervals is not None:
    # Rename columns to match expected format if needed
    if 'Route' in confidence_intervals.columns:
        confidence_intervals = confidence_intervals.rename(columns={'Route': 'route_id', 'CI_Lower': 'ci_lower', 'CI_Upper': 'ci_upper'})
    
    # Merge rss_results with confidence_intervals
    chart_data = pd.merge(rss_results, confidence_intervals, on='route_id', how='left')
    
    # Base bar chart
    bars = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('route_id', axis=alt.Axis(title='Route')),
        y=alt.Y('RSS_literature_scaled', axis=alt.Axis(title='RSS Score (Scaled)')),
        color=alt.Color('route_id', scale=alt.Scale(domain=['Red', 'Orange', 'Blue', 'Green-B', 'Green-C', 'Green-D', 'Green-E'], range=['#da291c', '#ed8b00', '#003da5', '#00843D', '#00843D', '#00843D', '#00843D'])),
        tooltip=['route_id', 'RSS_literature_scaled', 'ci_lower', 'ci_upper']
    )
    
    # Error bars
    error_bars = alt.Chart(chart_data).mark_errorbar().encode(
        x='route_id',
        y=alt.Y('ci_lower', title='RSS Score (Scaled)'),
        y2='ci_upper'
    )
    
    final_chart = (bars + error_bars).properties(
        title='Rider Satisfaction Score by Line (with 95% Confidence Intervals)'
    ).interactive()
    
    st.altair_chart(final_chart, use_container_width=True)
else:
    # Fallback if no CI data
    chart = alt.Chart(rss_results).mark_bar().encode(
        x=alt.X('route_id', axis=alt.Axis(title='Route')),
        y=alt.Y('RSS_literature_scaled', axis=alt.Axis(title='RSS Score (Scaled)')),
        color=alt.Color('route_id', scale=alt.Scale(domain=['Red', 'Orange', 'Blue'], range=['#da291c', '#ed8b00', '#003da5'])),
        tooltip=['route_id', 'RSS_literature_scaled', 'median_travel_time', 'on_time_performance']
    ).properties(
        title='Rider Satisfaction Score by Line'
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)

# Detailed Table
st.markdown("### Detailed Metrics")
st.dataframe(rss_results[['route_id', 'median_travel_time', 'on_time_performance', 'n_restrictions', 'RSS_literature_scaled']].style.format({
    'median_travel_time': '{:.2f}',
    'on_time_performance': '{:.2%}',
    'RSS_literature_scaled': '{:.1f}'
}))

st.markdown("""
**Note:** The RSS is calculated based on literature-derived weights for travel time, volatility, and buffer time.
""")

# Model Insights Section
if learned_weights is not None or regression_results is not None:
    st.markdown("---")
    st.markdown("### 🧠 Model Insights & Validation")
    st.info("These insights are derived from a machine learning model trained to predict RSS scores.")
    
    c1, c2 = st.columns(2)
    
    with c1:
        if learned_weights is not None:
            st.markdown("#### Feature Importance (Learned Weights)")
            # No melt needed as it's already Feature, Weight columns
            weights_df = learned_weights.copy()
            
            weight_chart = alt.Chart(weights_df).mark_bar().encode(
                x=alt.X('Weight', title='Weight Coefficient'),
                y=alt.Y('Feature', sort='-x', title='Feature'),
                color=alt.condition(
                    alt.datum.Weight > 0,
                    alt.value('steelblue'),
                    alt.value('orange')
                ),
                tooltip=['Feature', 'Weight']
            ).properties(height=300)
            st.altair_chart(weight_chart, use_container_width=True)
            st.caption("Positive weights increase RSS (better), negative weights decrease RSS (worse).")

    with c2:
        if regression_results is not None:
            st.markdown("#### Regression Model Performance")
            st.dataframe(regression_results)
            st.caption("Performance metrics for the RSS prediction model (R² close to 1 indicates high accuracy).")

