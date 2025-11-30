import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
from src.dashboard_utils import load_all_data, calculate_cts, get_station_mapping, get_od_data, infer_path_order

st.set_page_config(page_title="Route Deep Dive", page_icon="📈", layout="wide")

st.title("📈 Route Deep Dive")

data = load_all_data()

if data is None:
    st.stop()

# Filter by Route
routes = sorted(data['rss_results']['route_id'].unique())
selected_route = st.selectbox("Select Route", routes, index=0)

# Get data for selected route
station_scores = data['station_scores'][data['station_scores']['route_id'] == selected_route]
ridership = data['ridership'][data['ridership']['route_id'] == selected_route]
travel_times = data['travel_times'][data['travel_times']['route_id'] == selected_route]

# Create mappings
id_to_name, id_to_parent = get_station_mapping(data['travel_times']) # Global mapping to ensure coverage

# Calculate CTS
cts_df = calculate_cts(station_scores, data['ridership'], id_to_name)
route_cts = cts_df[cts_df['route_id'] == selected_route]

# === VISUALIZATIONS ===

# === Ridership Overview ===
st.markdown("### 👥 Station Ridership Volume")
st.write("Average daily ridership by station.")

if not ridership.empty:
    ridership_chart = alt.Chart(ridership).mark_bar().encode(
        x=alt.X('stop_name', sort='-y', title='Station'),
        y=alt.Y('average_flow', title='Average Daily Ridership'),
        tooltip=['stop_name', 'average_flow']
    ).properties(
        title=f'Ridership Volume ({selected_route} Line)',
        height=300
    ).interactive()
    
    st.altair_chart(ridership_chart, use_container_width=True)
else:
    st.info("Ridership data not available.")

st.divider()

st.markdown("### Commute Time Stress (CTS) Index")
st.markdown(r"$$CTS = \left(\frac{\text{Peak Ridership}}{\text{Capacity}}\right) \times \text{Variability}$$")
st.info("This index identifies stations where high crowd density coincides with unreliable service.")

if not route_cts.empty:
    # Sort by CTS
    route_cts = route_cts.sort_values('CTS', ascending=False)
    
    # Chart
    cts_chart = alt.Chart(route_cts).mark_bar().encode(
        x=alt.X('station_name', sort='-y', title='Station'),
        y=alt.Y('CTS', title='Stress Index'),
        color=alt.Color('CTS', scale=alt.Scale(scheme='reds')),
        tooltip=['station_name', 'CTS', 'average_flow', 'travel_time_volatility', 'load_factor']
    ).properties(
        title=f'Commute Time Stress by Station ({selected_route} Line)',
        height=400
    ).interactive()
    
    st.altair_chart(cts_chart, use_container_width=True)
    
    st.markdown("#### High Stress Stations")
    st.dataframe(route_cts[['station_name', 'CTS', 'average_flow', 'travel_time_volatility', 'load_factor']].head())

else:
    st.warning("Not enough data to calculate CTS for this route.")

st.divider()

# === Stability Analysis ===
st.markdown("### 🏘️ Regional Stability Analysis")
st.write("Identifying the most and least stable commute regions (stations) based on travel time volatility.")

if not route_cts.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("✅ Most Stable Stations (Low Volatility)")
        stable = route_cts.sort_values('travel_time_volatility', ascending=True).head(5)
        st.dataframe(stable[['station_name', 'travel_time_volatility', 'CTS']].reset_index(drop=True))
        
    with col2:
        st.error("⚠️ Least Stable Stations (High Volatility)")
        unstable = route_cts.sort_values('travel_time_volatility', ascending=False).head(5)
        st.dataframe(unstable[['station_name', 'travel_time_volatility', 'CTS']].reset_index(drop=True))
else:
    st.info("No volatility data available.")

st.divider()

# === Flow Map / Pressure ===
st.markdown("### 🌊 Route Pressure Map (Morning Peak)")
st.write("Visualizing passenger load relative to capacity.")

if not route_cts.empty:
    # We use Load Factor for pressure
    pressure_data = route_cts.sort_values('load_factor', ascending=False)
    
    pressure_chart = alt.Chart(pressure_data).mark_point(filled=True, size=100).encode(
        x=alt.X('station_name', sort='-y', title='Station'),
        y=alt.Y('load_factor', title='Load Factor (Flow/Capacity)'),
        color=alt.Color('load_factor', scale=alt.Scale(scheme='yelloworangered'), title='Pressure'),
        tooltip=['station_name', 'load_factor', 'average_flow', 'capacity']
    ).properties(
        title=f'Station Load Factors ({selected_route} Line)',
        height=350
    ).interactive()
    
    # Add a line for capacity limit (1.0)
    rule = alt.Chart(pd.DataFrame({'y': [1.0]})).mark_rule(color='red', strokeDash=[5, 5]).encode(y='y')
    
    st.altair_chart(pressure_chart + rule, use_container_width=True)
    st.caption("Stations above the red line (1.0) are operating above estimated capacity during peak hours.")

st.divider()

# === Sankey Diagram ===
st.markdown("### 🔀 Origin-Destination Flow (Sankey Diagram)")
st.write("Visualizing the flow of trips between stations.")

od_data = get_od_data(travel_times, selected_route)

if not od_data.empty:
    # Filter top N flows for readability
    top_n = st.slider("Number of Top Flows to Display", 5, 50, 15)
    top_od = od_data.head(top_n)
    
    # Create nodes
    all_nodes = list(set(top_od['from_parent_station'].tolist() + top_od['to_parent_station'].tolist()))
    node_map = {node: i for i, node in enumerate(all_nodes)}
    
    # Map back to names if possible
    # We need a reverse mapping from parent_station ID to name if possible, 
    # but 'from_parent_station' are usually IDs like 'place-north'.
    # id_to_name maps stop_id to name. id_to_parent maps stop_id to parent.
    # We need parent_id to name.
    # Let's try to infer parent name from stop name mapping
    
    # Create parent_id to name mapping
    parent_map_df = data['travel_times'][['from_parent_station', 'from_stop_name']].drop_duplicates()
    # Taking the first name found for each parent
    parent_to_name = parent_map_df.groupby('from_parent_station')['from_stop_name'].first().to_dict()
    
    node_labels = [parent_to_name.get(n, n) for n in all_nodes]
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = node_labels,
          color = "blue"
        ),
        link = dict(
          source = [node_map[src] for src in top_od['from_parent_station']],
          target = [node_map[tgt] for tgt in top_od['to_parent_station']],
          value = top_od['trip_count']
        ))])
    
    fig.update_layout(title_text=f"Top {top_n} OD Flows ({selected_route} Line)", font_size=10)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No OD data available for this route.")

st.divider()

# === Busiest Trip Path ===
st.markdown("### 🚦 Busiest Trip Path Simulation")

# Use OD data to find the single busiest O-D pair
if not od_data.empty:
    busiest_trip = od_data.iloc[0]
    origin = busiest_trip['from_parent_station']
    dest = busiest_trip['to_parent_station']
    origin_name = parent_to_name.get(origin, origin)
    dest_name = parent_to_name.get(dest, dest)
    
    st.metric("Busiest OD Pair", f"{origin_name} ➝ {dest_name}", f"{busiest_trip['trip_count']} trips")
    
    st.write("Simulating high-flow path...")
    
    # Simple path simulation (just direct for now, or use inferred connections if we had graph)
    # Since we don't have a full graph engine, we will visualize the flow volume at the top stations
    # as a proxy for the path.
    
    # Filter flow data for top stations
    if not route_cts.empty:
        top_flow_stations = route_cts.sort_values('average_flow', ascending=False).head(5)
        st.write("**High Volume Stations (Potential Bottlenecks along the path):**")
        
        # Display as a horizontal timeline-like view
        st.dataframe(top_flow_stations[['station_name', 'average_flow', 'load_factor']].reset_index(drop=True))
        
else:
    st.info("Insufficient data for simulation.")

# === Speed Restrictions ===
st.divider()
st.markdown("### 🐢 Speed Restrictions Analysis")
st.write("Current speed restrictions impacting travel times on this line.")

speed_restrictions = data.get('speed_restrictions')

if speed_restrictions is not None:
    # Filter for selected route
    # selected_route is like "Red", "Orange", "Blue"
    # speed_restrictions['Line'] is like "Red Line - Braintree", "Orange Line"
    
    route_restrictions = speed_restrictions[speed_restrictions['Line'].str.contains(selected_route, case=False, na=False)].copy()
    
    if not route_restrictions.empty:
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Active Restrictions", len(route_restrictions))
        with col2:
            try:
                avg_speed = route_restrictions['Restriction_Speed_MPH'].astype(str).str.extract(r'(\d+)').astype(float).mean().iloc[0]
                st.metric("Avg Restriction Speed", f"{avg_speed:.0f} mph")
            except:
                st.metric("Avg Restriction Speed", "N/A")
        with col3:
            total_dist = route_restrictions['Restriction_Distance_Miles'].sum()
            st.metric("Total Restricted Miles", f"{total_dist:.2f} miles")
            
        # Map/Scatter of Restrictions
        # Parse speed to number for plotting
        try:
            route_restrictions['Speed_Num'] = route_restrictions['Restriction_Speed_MPH'].astype(str).str.extract(r'(\d+)').astype(float)
            
            chart = alt.Chart(route_restrictions).mark_bar().encode(
                x=alt.X('Restriction_Distance_Feet', title='Restriction Length (ft)'),
                y=alt.Y('Location_Description', sort='-x', title='Location'),
                color=alt.Color('Speed_Num', scale=alt.Scale(scheme='orangered'), title='Speed Limit (mph)'),
                tooltip=['Location_Description', 'Restriction_Speed_MPH', 'Restriction_Distance_Feet', 'Restriction_Reason', 'Date_Restriction_Reported']
            ).properties(
                title=f'Active Speed Restrictions on {selected_route} Line',
                height=max(300, len(route_restrictions) * 20)
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not plot speed restrictions: {e}")
        
        with st.expander("View Detailed Restriction Data"):
            st.dataframe(route_restrictions[['Location_Description', 'Restriction_Speed_MPH', 'Restriction_Distance_Feet', 'Restriction_Reason', 'Date_Restriction_Reported']])
            
    else:
        st.success(f"No active speed restrictions found for {selected_route} Line in the dataset.")
else:
    st.info("Speed restriction data not available.")

