import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
from src.dashboard_utils import load_all_data, calculate_cts, get_station_mapping, get_od_data, infer_path_order

st.set_page_config(page_title="Route Deep Dive", page_icon="📈", layout="wide")

st.title("📈 Route Deep Dive")

# Add context at the top
st.info("""
🔍 **Station-Level Analysis**: Explore detailed metrics for individual stations including ridership volume, 
commute stress, and speed restrictions. Use this to identify specific problem areas within each line.
""")

data = load_all_data()

if data is None:
    st.error("Failed to load data.")
    st.stop()

st.markdown("---")

# Filter by Route
routes = sorted(data['rss_results']['route_id'].unique())
selected_route = st.selectbox("Select Route", routes, index=0, help="Choose a route to analyze station-level performance")

# Get data for selected route
station_scores = data['station_scores'][data['station_scores']['route_id'] == selected_route]
ridership = data['ridership'][data['ridership']['route_id'] == selected_route]
travel_times = data['travel_times'][data['travel_times']['route_id'] == selected_route]

# Create mappings
id_to_name, id_to_parent = get_station_mapping(data['travel_times'])

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
        color=alt.value('#003da5' if selected_route == 'Blue' else '#ed8b00' if selected_route == 'Orange' else '#da291c'),
        tooltip=['stop_name', 'average_flow']
    ).properties(
        title=f'Ridership Volume ({selected_route} Line)',
        height=300
    ).interactive()
    
    st.altair_chart(ridership_chart, use_container_width=True)
    
    # Add summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Busiest Station", ridership.loc[ridership['average_flow'].idxmax(), 'stop_name'])
    with col2:
        st.metric("Total Daily Riders", f"{ridership['average_flow'].sum():,.0f}")
    with col3:
        st.metric("Average per Station", f"{ridership['average_flow'].mean():,.0f}")
else:
    st.info("Ridership data not available for this route.")

st.divider()

# === CTS Index ===
st.markdown("### 🚨 Commute Time Stress (CTS) Index")

# Add explanation
with st.expander("ℹ️ What is the CTS Index?"):
    st.markdown(r"""
    The **Commute Time Stress (CTS) Index** identifies stations where high crowd density coincides with unreliable service.
    
    **Formula:**
    $$CTS = \left(\frac{\text{Peak Ridership}}{\text{Capacity}}\right) \times \text{Variability}$$
    
    **Interpretation:**
    - Higher values = More stress for commuters
    - Combines crowding (load factor) with unpredictability (volatility)
    - Stations above 1.0 are operating over capacity during peak hours
    """)

if not route_cts.empty:
    # Sort by CTS
    route_cts = route_cts.sort_values('CTS', ascending=False)
    
    # Chart
    cts_chart = alt.Chart(route_cts).mark_bar().encode(
        x=alt.X('station_name', sort='-y', title='Station'),
        y=alt.Y('CTS', title='Stress Index'),
        color=alt.Color('CTS', scale=alt.Scale(scheme='reds'), legend=None),
        tooltip=[
            alt.Tooltip('station_name', title='Station'),
            alt.Tooltip('CTS', title='Stress Index', format='.2f'),
            alt.Tooltip('average_flow', title='Avg Daily Flow', format=','),
            alt.Tooltip('travel_time_volatility', title='Volatility', format='.2f'),
            alt.Tooltip('load_factor', title='Load Factor', format='.2f')
        ]
    ).properties(
        title=f'Commute Time Stress by Station ({selected_route} Line)',
        height=400
    ).interactive()
    
    st.altair_chart(cts_chart, use_container_width=True)
    
    st.markdown("#### High Stress Stations")
    st.dataframe(
        route_cts[['station_name', 'CTS', 'average_flow', 'travel_time_volatility', 'load_factor']]
        .head(10)
        .style.background_gradient(subset=['CTS'], cmap='Reds'),
        use_container_width=True
    )
    st.caption("Stations shown above require immediate attention due to high crowding and unreliable service.")

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
        st.dataframe(
            stable[['station_name', 'travel_time_volatility', 'CTS']]
            .reset_index(drop=True)
            .style.format({'travel_time_volatility': '{:.3f}', 'CTS': '{:.2f}'}),
            use_container_width=True
        )
        st.caption("Consistent travel times → Reliable for commuters")
        
    with col2:
        st.error("⚠️ Least Stable Stations (High Volatility)")
        unstable = route_cts.sort_values('travel_time_volatility', ascending=False).head(5)
        st.dataframe(
            unstable[['station_name', 'travel_time_volatility', 'CTS']]
            .reset_index(drop=True)
            .style.format({'travel_time_volatility': '{:.3f}', 'CTS': '{:.2f}'}),
            use_container_width=True
        )
        st.caption("Unpredictable travel times → Frustrating for commuters")
else:
    st.info("No volatility data available for this route.")

st.divider()

# === Flow Map / Pressure ===
st.markdown("### 🌊 Route Pressure Map (Morning Peak)")
st.write("Visualizing passenger load relative to capacity.")

if not route_cts.empty:
    pressure_data = route_cts.sort_values('load_factor', ascending=False)
    
    pressure_chart = alt.Chart(pressure_data).mark_point(filled=True, size=100).encode(
        x=alt.X('station_name', sort='-y', title='Station'),
        y=alt.Y('load_factor', title='Load Factor (Flow/Capacity)', scale=alt.Scale(domain=[0, max(1.5, pressure_data['load_factor'].max())])),
        color=alt.Color('load_factor', scale=alt.Scale(scheme='yelloworangered'), legend=None),
        tooltip=[
            alt.Tooltip('station_name', title='Station'),
            alt.Tooltip('load_factor', title='Load Factor', format='.2f'),
            alt.Tooltip('average_flow', title='Daily Flow', format=','),
            alt.Tooltip('capacity', title='Capacity', format=',')
        ]
    ).properties(
        title=f'Station Load Factors ({selected_route} Line)',
        height=350
    ).interactive()
    
    # Add a line for capacity limit (1.0)
    rule = alt.Chart(pd.DataFrame({'y': [1.0]})).mark_rule(color='red', strokeDash=[5, 5], strokeWidth=2).encode(y='y')
    
    st.altair_chart(pressure_chart + rule, use_container_width=True)
    st.caption("⚠️ **Red dashed line = Capacity limit (1.0)**. Stations above this line are overcrowded during peak hours.")
    
    # Show overcrowded stations
    overcrowded = pressure_data[pressure_data['load_factor'] > 1.0]
    if not overcrowded.empty:
        st.warning(f"**{len(overcrowded)} stations operating over capacity**: {', '.join(overcrowded['station_name'].head(5).tolist())}")

st.divider()

# TEMPORARY DEBUG - Remove after fixing
with st.expander("🔧 Debug: Check OD Data"):
    try:
        od_data = get_od_data(travel_times, selected_route)
        st.write(f"OD Data type: {type(od_data)}")
        st.write(f"OD Data shape: {od_data.shape if hasattr(od_data, 'shape') else 'N/A'}")
        st.write(f"OD Data empty: {od_data.empty if hasattr(od_data, 'empty') else 'N/A'}")
        if od_data is not None and hasattr(od_data, 'head'):
            st.write("First 5 rows:")
            st.dataframe(od_data.head())
    except Exception as e:
        st.error(f"Error getting OD data: {str(e)}")

# === Sankey Diagram ===
st.markdown("### 🔀 Origin-Destination Flow (Sankey Diagram)")
st.write("Visualizing the flow of trips between stations.")

try:
    od_data = get_od_data(travel_times, selected_route)
    
    if od_data is not None and not od_data.empty and len(od_data) > 0:
        # Filter top N flows for readability
        top_n = st.slider("Number of Top Flows to Display", 5, 50, 15, help="More flows = more complex diagram")
        top_od = od_data.head(top_n)
        
        # Validate we have enough data
        if len(top_od) < 2:
            st.warning("Not enough origin-destination pairs to create a flow diagram.")
        else:
            # Create nodes
            all_nodes = list(set(top_od['from_parent_station'].tolist() + top_od['to_parent_station'].tolist()))
            
            if len(all_nodes) < 2:
                st.warning("Insufficient unique stations for flow visualization.")
            else:
                node_map = {node: i for i, node in enumerate(all_nodes)}
                
                # Create parent_id to name mapping
                parent_map_df = data['travel_times'][['from_parent_station', 'from_stop_name']].drop_duplicates()
                parent_to_name = parent_map_df.groupby('from_parent_station')['from_stop_name'].first().to_dict()
                
                node_labels = [parent_to_name.get(n, n) for n in all_nodes]
                
                # Create Sankey diagram
                try:
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
                          value = top_od['trip_count'].tolist()
                        ))])
                    
                    fig.update_layout(
                        title_text=f"Top {top_n} OD Flows ({selected_route} Line)", 
                        font_size=10, 
                        height=600
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption("**Thicker flows** indicate more trips between station pairs. Identifies key transfer points and travel patterns.")
                    
                except Exception as e:
                    st.error(f"Error creating Sankey diagram: {str(e)}")
                    st.info("Showing OD data in table format instead:")
                    st.dataframe(
                        top_od[['from_parent_station', 'to_parent_station', 'trip_count']]
                        .rename(columns={
                            'from_parent_station': 'Origin',
                            'to_parent_station': 'Destination', 
                            'trip_count': 'Trip Count'
                        })
                        .style.format({'Trip Count': '{:,}'}),
                        use_container_width=True
                    )
    else:
        st.info("No origin-destination flow data available for this route.")
        st.markdown("**Possible reasons:**")
        st.markdown("- Sample data may not include detailed trip-level information")
        st.markdown("- This route may not have sufficient trip records in the dataset")
        
except Exception as e:
    st.warning(f"Could not load OD flow data: {str(e)}")
    st.info("This feature requires detailed trip-level data which may not be available in the current dataset.")

# === Busiest Trip Path ===
st.markdown("### 🚦 Busiest Trip Path")

if not od_data.empty:
    busiest_trip = od_data.iloc[0]
    origin = busiest_trip['from_parent_station']
    dest = busiest_trip['to_parent_station']
    origin_name = parent_to_name.get(origin, origin)
    dest_name = parent_to_name.get(dest, dest)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Busiest Origin-Destination", f"{origin_name} → {dest_name}")
    with col2:
        st.metric("Trip Count", f"{busiest_trip['trip_count']:,}")
    
    # Show high-volume stations
    if not route_cts.empty:
        top_flow_stations = route_cts.sort_values('average_flow', ascending=False).head(5)
        st.markdown("**High Volume Stations (Potential Bottlenecks):**")
        st.dataframe(
            top_flow_stations[['station_name', 'average_flow', 'load_factor']]
            .reset_index(drop=True)
            .style.format({'average_flow': '{:,.0f}', 'load_factor': '{:.2f}'}),
            use_container_width=True
        )
else:
    st.info("Insufficient origin-destination data available.")

st.divider()

# === Speed Restrictions ===
st.markdown("### 🐢 Speed Restrictions Analysis")
st.write("Current speed restrictions impacting travel times on this line.")

speed_restrictions = data.get('speed_restrictions')

if speed_restrictions is not None:
    route_restrictions = speed_restrictions[speed_restrictions['Line'].str.contains(selected_route, case=False, na=False)].copy()
    
    if not route_restrictions.empty:
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Active Restrictions", len(route_restrictions), help="Number of slow zones currently active")
        with col2:
            try:
                avg_speed = route_restrictions['Restriction_Speed_MPH'].astype(str).str.extract(r'(\d+)').astype(float).mean().iloc[0]
                st.metric("Avg Restriction Speed", f"{avg_speed:.0f} mph", help="Average speed limit in slow zones")
            except:
                st.metric("Avg Restriction Speed", "N/A")
        with col3:
            total_dist = route_restrictions['Restriction_Distance_Miles'].sum()
            st.metric("Total Restricted Miles", f"{total_dist:.2f} mi", help="Total track length affected by slow zones")
            
        # Map/Scatter of Restrictions
        try:
            route_restrictions['Speed_Num'] = route_restrictions['Restriction_Speed_MPH'].astype(str).str.extract(r'(\d+)').astype(float)
            
            chart = alt.Chart(route_restrictions).mark_bar().encode(
                x=alt.X('Restriction_Distance_Feet', title='Restriction Length (ft)'),
                y=alt.Y('Location_Description', sort='-x', title='Location'),
                color=alt.Color('Speed_Num', scale=alt.Scale(scheme='orangered'), title='Speed (mph)'),
                tooltip=[
                    alt.Tooltip('Location_Description', title='Location'),
                    alt.Tooltip('Restriction_Speed_MPH', title='Speed Limit'),
                    alt.Tooltip('Restriction_Distance_Feet', title='Length (ft)', format=','),
                    alt.Tooltip('Restriction_Reason', title='Reason'),
                    alt.Tooltip('Date_Restriction_Reported', title='Reported')
                ]
            ).properties(
                title=f'Active Speed Restrictions on {selected_route} Line',
                height=max(300, len(route_restrictions) * 20)
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
            st.caption("**Darker red = Lower speed limits**. Longer bars indicate longer affected track segments.")
        except Exception as e:
            st.warning(f"Could not plot speed restrictions: {e}")
        
        with st.expander("📋 View Detailed Restriction Data"):
            st.dataframe(
                route_restrictions[['Location_Description', 'Restriction_Speed_MPH', 'Restriction_Distance_Feet', 
                                   'Restriction_Reason', 'Date_Restriction_Reported']]
                .style.format({'Restriction_Distance_Feet': '{:,.0f}'}),
                use_container_width=True
            )
            
    else:
        st.success(f"✅ No active speed restrictions found for {selected_route} Line in the dataset!")
else:
    st.info("Speed restriction data not available.")

# Footer
st.markdown("---")
st.markdown("**Next Steps**: Check **Equity Analysis** to see how service quality varies by demographics →")
st.caption(f"📈 {selected_route} Line analysis | Data source: MBTA Open Data Portal")
