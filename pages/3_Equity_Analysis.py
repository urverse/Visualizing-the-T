import streamlit as st
import pandas as pd
import altair as alt
import difflib
from src.dashboard_utils import load_all_data, get_station_mapping

st.set_page_config(page_title="Equity Analysis", page_icon="⚖️", layout="wide")

st.title("⚖️ Equity Analysis")

data = load_all_data()
survey = data['survey']
station_scores = data['station_scores']

if survey is None:
    st.stop()

st.markdown("""
This section explores the relationship between demographics and rider satisfaction/service quality.
Select a demographic metric to analyze how it correlates with the **Rider Satisfaction Score (RSS)** at the station level.

**Note:** RSS data is currently available primarily for Red, Orange, and Blue lines. Green Line and Bus routes may not show correlation data due to missing RSS scores.
""")

# === Controls ===
col1, col2, col3 = st.columns(3)

with col1:
    measure_groups = sorted(survey['measure_group'].unique())
    # Default to 'Income' if available
    default_group_index = measure_groups.index('Income') if 'Income' in measure_groups else 0
    selected_group = st.selectbox("1. Select Category Group", measure_groups, index=default_group_index)

with col2:
    group_data = survey[survey['measure_group'] == selected_group]
    measures = sorted(group_data['measure'].unique())
    selected_measure = st.selectbox("2. Select Specific Measure", measures)

with col3:
    subset = group_data[group_data['measure'] == selected_measure]
    categories = sorted(subset['category'].unique())
    # Try to pick a "vulnerable" or "minority" category by default if possible
    default_cat_index = 0
    for i, cat in enumerate(categories):
        if any(x in str(cat).lower() for x in ['low', 'less than', 'minority', 'no', '0', 'black', 'hispanic']):
            default_cat_index = i
            break
            
    selected_category = st.selectbox("3. Select Target Group (for Correlation)", categories, index=default_cat_index)

# === Distribution Chart ===
st.subheader(f"Distribution of {selected_measure}")
st.caption(f"Showing distribution across different reporting groups (stations/lines).")

chart = alt.Chart(subset).mark_bar().encode(
    x=alt.X('weighted_percent', title='Percentage', axis=alt.Axis(format='%')),
    y=alt.Y('category', title='Category'),
    color=alt.Color('category', legend=None),
    tooltip=['reporting_group', 'category', alt.Tooltip('weighted_percent', format='.1%')]
).properties(
    height=300
).interactive()

st.altair_chart(chart, use_container_width=True)

st.divider()

# === Correlation Analysis ===
st.subheader(f"Correlation: {selected_category} vs. Station RSS")
st.write(f"Does a higher percentage of **{selected_category}** riders correlate with better or worse service?")

# 1. Prepare Survey Data: Get % of selected category per reporting group
target_data = subset[subset['category'] == selected_category].groupby('reporting_group')['weighted_percent'].sum().reset_index()
target_data.rename(columns={'weighted_percent': 'percent_target'}, inplace=True)

# 2. Prepare RSS Data
id_to_name, _ = get_station_mapping(data['travel_times'])

rss_named = station_scores.copy()
rss_named['from_stop_id'] = rss_named['from_stop_id'].astype(str)
rss_named['station_name'] = rss_named['from_stop_id'].map(id_to_name)

# Aggregate RSS by station name (taking mean if multiple stops per station name)
rss_agg = rss_named.groupby('station_name')['station_rss_scaled'].mean().reset_index()

# 3. Fuzzy Match & Merge
# Create a mapping from Survey Reporting Group -> RSS Station Name
survey_names = target_data['reporting_group'].unique()
rss_names = rss_agg['station_name'].unique()

name_mapping = {}
for s_name in survey_names:
    # 1. Exact match
    if s_name in rss_names:
        name_mapping[s_name] = s_name
        continue
        
    # 2. Case-insensitive match
    matches = [r for r in rss_names if r.lower() == s_name.lower()]
    if matches:
        name_mapping[s_name] = matches[0]
        continue
        
    # 3. Fuzzy match (useful for small typos or suffix differences)
    # cutoff=0.8 means 80% similarity required
    close = difflib.get_close_matches(s_name, rss_names, n=1, cutoff=0.8)
    if close:
        name_mapping[s_name] = close[0]

# Apply mapping
target_data['station_name_mapped'] = target_data['reporting_group'].map(name_mapping)

# Report unmatched for transparency
unmatched = target_data[target_data['station_name_mapped'].isna()]
if not unmatched.empty:
    with st.expander(f"Excluded {len(unmatched)} reporting groups (Missing RSS Data)"):
        st.write("The following survey groups could not be matched to an RSS score (likely Green Line, Bus, or Commuter Rail):")
        st.dataframe(unmatched['reporting_group'])

# Filter out rows that didn't match BEFORE merging to avoid type mismatch (float NaN vs string)
target_data_matched = target_data.dropna(subset=['station_name_mapped']).copy()

# Ensure the join key is string type
target_data_matched['station_name_mapped'] = target_data_matched['station_name_mapped'].astype(str)

# Merge using mapped name
merged = pd.merge(target_data_matched, rss_agg, left_on='station_name_mapped', right_on='station_name', how='inner')

if not merged.empty:
    col_corr1, col_corr2 = st.columns([2, 1])
    
    with col_corr1:
        # Scatter Plot with Regression Line
        scatter = alt.Chart(merged).mark_circle(size=80).encode(
            x=alt.X('percent_target', title=f'% {selected_category}', axis=alt.Axis(format='%')),
            y=alt.Y('station_rss_scaled', title='RSS Score (60-100)', scale=alt.Scale(domain=[50, 100])),
            tooltip=['station_name', alt.Tooltip('percent_target', format='.1%'), alt.Tooltip('station_rss_scaled', format='.1f')]
        )
        
        reg_line = scatter.transform_regression('percent_target', 'station_rss_scaled').mark_line(color='red')
        
        st.altair_chart((scatter + reg_line).interactive(), use_container_width=True)
        
    with col_corr2:
        correlation = merged['percent_target'].corr(merged['station_rss_scaled'])
        
        st.metric("Correlation Coefficient", f"{correlation:.2f}")
        
        if abs(correlation) < 0.3:
            st.info("Weak or no correlation.")
        elif correlation > 0:
            st.success("Positive correlation: Higher % of this group is associated with BETTER scores.")
        else:
            st.error("Negative correlation: Higher % of this group is associated with WORSE scores.")
            
        st.write(f"**Matched Stations:** {len(merged)}")
        st.dataframe(merged[['station_name', 'percent_target', 'station_rss_scaled']].sort_values('percent_target', ascending=False).style.format({
            'percent_target': '{:.1%}',
            'station_rss_scaled': '{:.1f}'
        }), height=300)

else:
    st.warning("No matched stations found for correlation analysis.")
    st.write("This may happen if the selected demographic category is rare or only present in stations without RSS scores (e.g. Green Line).")


