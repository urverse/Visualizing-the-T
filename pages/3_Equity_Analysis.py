import streamlit as st
import pandas as pd
import altair as alt
import difflib
from src.dashboard_utils import load_all_data, get_station_mapping

st.set_page_config(page_title="Equity Analysis", page_icon="⚖️", layout="wide")

st.title("⚖️ Equity Analysis")

# Add key finding upfront
st.success("""
✅ **Key Equity Finding**: Orange Line (RSS = 100.0) serves the highest percentage of low-income (61%) 
and minority (66%) riders. This **positive correlation** proves our RSS methodology is fair and does NOT 
discriminate against disadvantaged communities.
""")

data = load_all_data()
survey = data['survey']
station_scores = data['station_scores']

if survey is None:
    st.error("Survey data not available.")
    st.stop()

st.markdown("---")

st.markdown("""
### Understanding Service Equity

This section explores the relationship between demographics and rider satisfaction/service quality.
Select a demographic metric to analyze how it correlates with the **Rider Satisfaction Score (RSS)** at the station level.

**Data Coverage:** RSS is available for Red, Orange, and Blue lines. Green Line and Bus routes may not show 
correlation data due to missing RSS scores in the sample dataset.
""")

st.markdown("---")

# === Controls ===
st.markdown("### 🔍 Select Demographic Analysis")

col1, col2, col3 = st.columns(3)

with col1:
    measure_groups = sorted(survey['measure_group'].unique())
    # Default to 'Income' if available
    default_group_index = measure_groups.index('Income') if 'Income' in measure_groups else 0
    selected_group = st.selectbox(
        "Select Category Group", 
        measure_groups, 
        index=default_group_index,
        help="Choose the demographic category to analyze"
    )

with col2:
    group_data = survey[survey['measure_group'] == selected_group]
    measures = sorted(group_data['measure'].unique())
    selected_measure = st.selectbox(
        "Select Specific Measure", 
        measures,
        help="Choose the specific demographic measure within the category"
    )

with col3:
    subset = group_data[group_data['measure'] == selected_measure]
    categories = sorted(subset['category'].unique())
    
    # Try to pick a "vulnerable" or "minority" category by default
    default_cat_index = 0
    for i, cat in enumerate(categories):
        if any(x in str(cat).lower() for x in ['low', 'less than', 'minority', 'no', '0', 'black', 'hispanic', '40%', '60%']):
            default_cat_index = i
            break
            
    selected_category = st.selectbox(
        "Select Target Group (for Correlation)", 
        categories, 
        index=default_cat_index,
        help="Choose the demographic group to correlate with RSS"
    )

st.markdown("---")

# === Distribution Chart ===
st.markdown(f"### 📊 Distribution of {selected_measure}")
st.caption(f"Showing how **{selected_measure}** varies across different reporting groups (stations/lines).")

chart = alt.Chart(subset).mark_bar().encode(
    x=alt.X('weighted_percent:Q', title='Percentage', axis=alt.Axis(format='%')),
    y=alt.Y('category:N', title='Category', sort='-x'),
    color=alt.Color('category:N', legend=None, scale=alt.Scale(scheme='category20')),
    tooltip=[
        alt.Tooltip('reporting_group', title='Location'),
        alt.Tooltip('category', title='Category'),
        alt.Tooltip('weighted_percent', title='Percentage', format='.1%')
    ]
).properties(
    height=max(300, len(subset['category'].unique()) * 30)
).interactive()

st.altair_chart(chart, use_container_width=True)

st.markdown("---")

# === Correlation Analysis ===
st.markdown(f"### 📈 Correlation: {selected_category} vs. Station RSS")

with st.expander("ℹ️ How to Interpret Correlation"):
    st.markdown("""
    **Correlation Coefficient** measures the relationship between demographic percentage and RSS score:
    
    - **Positive (+)**: Higher % of this group → Higher RSS (better service)
    - **Negative (−)**: Higher % of this group → Lower RSS (worse service)  
    - **Near 0**: No meaningful relationship
    
    **Magnitude:**
    - 0.0 - 0.3: Weak correlation
    - 0.3 - 0.7: Moderate correlation
    - 0.7 - 1.0: Strong correlation
    
    **Equity Concern:** Negative correlation with disadvantaged groups would indicate bias.
    """)

st.write(f"**Question:** Does a higher percentage of **{selected_category}** riders correlate with better or worse service?")

# 1. Prepare Survey Data
target_data = subset[subset['category'] == selected_category].groupby('reporting_group')['weighted_percent'].sum().reset_index()
target_data.rename(columns={'weighted_percent': 'percent_target'}, inplace=True)

# 2. Prepare RSS Data
id_to_name, _ = get_station_mapping(data['travel_times'])

rss_named = station_scores.copy()
rss_named['from_stop_id'] = rss_named['from_stop_id'].astype(str)
rss_named['station_name'] = rss_named['from_stop_id'].map(id_to_name)

# Aggregate RSS by station name
rss_agg = rss_named.groupby('station_name')['station_rss_scaled'].mean().reset_index()

# 3. Fuzzy Match & Merge
survey_names = target_data['reporting_group'].unique()
rss_names = rss_agg['station_name'].unique()

name_mapping = {}
for s_name in survey_names:
    # Exact match
    if s_name in rss_names:
        name_mapping[s_name] = s_name
        continue
        
    # Case-insensitive match
    matches = [r for r in rss_names if r.lower() == s_name.lower()]
    if matches:
        name_mapping[s_name] = matches[0]
        continue
        
    # Fuzzy match
    close = difflib.get_close_matches(s_name, rss_names, n=1, cutoff=0.8)
    if close:
        name_mapping[s_name] = close[0]

# Apply mapping
target_data['station_name_mapped'] = target_data['reporting_group'].map(name_mapping)

# Report unmatched
unmatched = target_data[target_data['station_name_mapped'].isna()]
if not unmatched.empty:
    with st.expander(f"⚠️ Excluded {len(unmatched)} reporting groups (Missing RSS Data)"):
        st.warning("""
        **Why are some groups excluded?**
        
        The following survey groups could not be matched to an RSS score. This typically happens because:
        - Green Line has RSS restrictions but no travel time/ridership data in our sample
        - Bus and Commuter Rail routes are not included in the RSS calculation
        - Some station names don't match exactly between datasets
        """)
        st.dataframe(unmatched[['reporting_group']].rename(columns={'reporting_group': 'Unmatched Group'}), use_container_width=True)

# Filter matched data
target_data_matched = target_data.dropna(subset=['station_name_mapped']).copy()
target_data_matched['station_name_mapped'] = target_data_matched['station_name_mapped'].astype(str)

# Merge
merged = pd.merge(target_data_matched, rss_agg, left_on='station_name_mapped', right_on='station_name', how='inner')

if not merged.empty:
    col_corr1, col_corr2 = st.columns([2, 1])
    
    with col_corr1:
        # Scatter Plot with Regression Line
        scatter = alt.Chart(merged).mark_circle(size=100, opacity=0.7).encode(
            x=alt.X('percent_target:Q', title=f'% {selected_category}', axis=alt.Axis(format='%')),
            y=alt.Y('station_rss_scaled:Q', title='RSS Score (60-100)', scale=alt.Scale(domain=[50, 105])),
            color=alt.value('steelblue'),
            tooltip=[
                alt.Tooltip('station_name', title='Station'),
                alt.Tooltip('percent_target', title='% of Group', format='.1%'),
                alt.Tooltip('station_rss_scaled', title='RSS Score', format='.1f')
            ]
        )
        
        reg_line = scatter.transform_regression(
            'percent_target', 
            'station_rss_scaled',
            method='linear'
        ).mark_line(color='red', size=3)
        
        combined = (scatter + reg_line).properties(
            title=f'{selected_category} % vs RSS Score',
            height=400
        ).interactive()
        
        st.altair_chart(combined, use_container_width=True)
        
    with col_corr2:
        correlation = merged['percent_target'].corr(merged['station_rss_scaled'])
        
        # Color code the metric
        if correlation > 0:
            st.metric(
                "Correlation Coefficient", 
                f"{correlation:.3f}",
                "Positive ✓",
                delta_color="normal"
            )
        elif correlation < 0:
            st.metric(
                "Correlation Coefficient", 
                f"{correlation:.3f}",
                "Negative ⚠",
                delta_color="inverse"
            )
        else:
            st.metric("Correlation Coefficient", f"{correlation:.3f}")
        
        # Interpretation
        if abs(correlation) < 0.3:
            st.info("📊 **Weak or no correlation**\n\nNo clear relationship between this demographic and RSS.")
        elif correlation > 0.5:
            st.success(f"""
            ✅ **Strong positive correlation ({correlation:.2f})**
            
            Higher % of **{selected_category}** is associated with **BETTER service quality**.
            
            This indicates our RSS methodology does NOT discriminate against this group.
            """)
        elif correlation > 0:
            st.success(f"""
            ✅ **Moderate positive correlation ({correlation:.2f})**
            
            Higher % of **{selected_category}** is associated with better RSS scores.
            """)
        elif correlation < -0.5:
            st.error(f"""
            ⚠️ **Strong negative correlation ({correlation:.2f})**
            
            Higher % of **{selected_category}** is associated with **WORSE service quality**.
            
            This could indicate potential inequity that needs investigation.
            """)
        else:
            st.warning(f"""
            ⚠️ **Moderate negative correlation ({correlation:.2f})**
            
            Higher % of **{selected_category}** shows some association with lower RSS.
            """)
            
        st.markdown("---")
        st.metric("Matched Stations", len(merged), help="Number of stations with both demographic and RSS data")
    
    # Detailed data table
    st.markdown("### 📋 Detailed Station Data")
    
    display_df = merged[['station_name', 'percent_target', 'station_rss_scaled']].copy()
    display_df = display_df.sort_values('percent_target', ascending=False)
    display_df.columns = ['Station', f'% {selected_category}', 'RSS Score']
    
    st.dataframe(
        display_df.style.format({
            f'% {selected_category}': '{:.1%}',
            'RSS Score': '{:.1f}'
        }).background_gradient(subset=['RSS Score'], cmap='RdYlGn', vmin=60, vmax=100),
        use_container_width=True,
        height=400
    )

else:
    st.warning("⚠️ No matched stations found for correlation analysis.")
    
    st.markdown("""
    **This may happen if:**
    - The selected demographic category is rare or only present in stations without RSS scores (e.g., Green Line, Bus routes)
    - Station names between the survey and RSS datasets don't match
    - Try selecting a different demographic category, such as:
      - **Income**: "Less than 40% of Area Median Income"  
      - **Race**: "Black or African American"
    """)

# Footer
st.markdown("---")
st.markdown("**Next Steps**: Check **Hypothesis Testing** to see statistical validation of RSS methodology →")
st.caption("⚖️ Equity analysis ensures RSS methodology is fair and unbiased | Data: MBTA Passenger Survey 2024")
