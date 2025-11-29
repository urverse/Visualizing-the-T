import pandas as pd
import streamlit as st
from pathlib import Path

# Constants for Capacity (approximate per train)
CAPACITY_MAP = {
    'Red': 1300,
    'Orange': 1000,
    'Blue': 900,
    'Green': 300, # Per 2-car train approx
    'Green-B': 300,
    'Green-C': 300,
    'Green-D': 300,
    'Green-E': 300,
    'Mattapan': 100 # Trolley
}

@st.cache_data
def load_all_data():
    """Load all necessary datasets."""
    data_path = Path("data/processed")
    
    try:
        rss_results = pd.read_csv(data_path / "rss_final_results.csv")
        station_scores = pd.read_csv(data_path / "station_rss_scores.csv")
        ridership = pd.read_csv(data_path / "ridership_sample.csv")
        travel_times = pd.read_csv(data_path / "travel_times_sample.csv")
        survey = pd.read_csv(data_path / "passenger_survey_sample.csv")
        
        # Load weights if needed, or just return them
        weights = pd.read_csv(data_path / "rss_weights.csv")
        
        # New Data Sources
        try:
            speed_restrictions = pd.read_csv(data_path / "speed_restrictions_sample.csv")
        except:
            speed_restrictions = None
            
        try:
            confidence_intervals = pd.read_csv(data_path / "bootstrap_confidence_intervals.csv")
        except:
            confidence_intervals = None
            
        try:
            regression_results = pd.read_csv(data_path / "regression_model_results.csv")
        except:
            regression_results = None
            
        try:
            learned_weights = pd.read_csv(data_path / "learned_weights.csv")
        except:
            learned_weights = None
        
        return {
            "rss_results": rss_results,
            "station_scores": station_scores,
            "ridership": ridership,
            "travel_times": travel_times,
            "survey": survey,
            "weights": weights,
            "speed_restrictions": speed_restrictions,
            "confidence_intervals": confidence_intervals,
            "regression_results": regression_results,
            "learned_weights": learned_weights
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

@st.cache_data
def get_station_mapping(travel_times_df):
    """Create a mapping from stop_id to stop_name using travel_times data."""
    # unique pairs of from_stop_id and from_stop_name
    mapping = travel_times_df[['from_stop_id', 'from_stop_name', 'from_parent_station']].drop_duplicates().dropna()
    
    # Ensure ID is string for consistent mapping
    mapping['from_stop_id'] = mapping['from_stop_id'].astype(str)
    
    # Convert to dict
    id_to_name = dict(zip(mapping['from_stop_id'], mapping['from_stop_name']))
    id_to_parent = dict(zip(mapping['from_stop_id'], mapping['from_parent_station']))
    return id_to_name, id_to_parent

def calculate_cts(station_scores, ridership, id_to_name):
    """
    Calculate Commute Time Stress (CTS) Index.
    CTS = (peak_hour_ridership / capacity) * variability
    """
    # 1. Prepare Ridership: Filter for Peak Hours (AM/PM) and aggregate by stop
    # We use 'average_flow' as a proxy for ridership load
    
    # Filter for AM Peak (or make it selectable, for now assume max of AM/PM)
    peak_ridership = ridership[ridership['time_period_name'].isin(['AM_PEAK', 'PM_PEAK'])].copy()
    
    # We need to map ridership stops to station scores stops.
    # station_scores has 'from_stop_id'. Ridership has 'stop_name' or 'parent_station'.
    # We'll map station_scores 'from_stop_id' to name first.
    
    scores_df = station_scores.copy()
    scores_df['from_stop_id'] = scores_df['from_stop_id'].astype(str)
    scores_df['station_name'] = scores_df['from_stop_id'].map(id_to_name)
    
    # If mapping failed for some, drop them or keep raw ID
    scores_df = scores_df.dropna(subset=['station_name'])
    
    # Group ridership by stop_name and route
    # Taking the mean of average_flow during peak hours for each station/route
    ridership_agg = peak_ridership.groupby(['route_id', 'stop_name'])['average_flow'].mean().reset_index()
    
    # Merge
    merged = pd.merge(
        scores_df, 
        ridership_agg, 
        left_on=['route_id', 'station_name'], 
        right_on=['route_id', 'stop_name'], 
        how='inner'
    )
    
    # Add Capacity
    merged['capacity'] = merged['route_id'].map(CAPACITY_MAP).fillna(1000)
    
    # Calculate CTS
    # CTS = (Flow / Capacity) * Volatility
    # We ensure volatility is positive-ish for magnitude
    min_vol = merged['travel_time_volatility'].min()
    if min_vol < 0:
        merged['variability_positive'] = merged['travel_time_volatility'] + abs(min_vol) + 1
    else:
        merged['variability_positive'] = merged['travel_time_volatility'] + 1
        
    merged['load_factor'] = merged['average_flow'] / merged['capacity']
    merged['CTS'] = merged['load_factor'] * merged['variability_positive']
    
    return merged

def get_od_data(travel_times_df, route_id=None):
    """
    Extract Origin-Destination flows from travel times.
    In real world, we'd use ODX data, but here we count trips or use a proxy.
    Since travel_times has individual trips (maybe sample), we can count them.
    """
    df = travel_times_df.copy()
    if route_id:
        df = df[df['route_id'] == route_id]
        
    # Aggregate counts by OD pair
    od_counts = df.groupby(['from_parent_station', 'to_parent_station']).size().reset_index(name='trip_count')
    
    # Filter for meaningful flows (e.g. > threshold)
    od_counts = od_counts[od_counts['trip_count'] > 0].sort_values('trip_count', ascending=False)
    
    return od_counts

def infer_path_order(travel_times_df, route_id):
    """
    Attempt to infer station order from travel times.
    This is tricky without a sequence field. 
    We can look at 'from' and 'to' and chain them.
    """
    df = travel_times_df[travel_times_df['route_id'] == route_id].copy()
    
    # Get all unique connections
    connections = df[['from_parent_station', 'to_parent_station']].drop_duplicates()
    
    return connections
