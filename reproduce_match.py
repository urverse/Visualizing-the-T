import pandas as pd
from pathlib import Path

def get_station_mapping(travel_times_df):
    mapping = travel_times_df[['from_stop_id', 'from_stop_name', 'from_parent_station']].drop_duplicates().dropna()
    mapping['from_stop_id'] = mapping['from_stop_id'].astype(str)
    id_to_name = dict(zip(mapping['from_stop_id'], mapping['from_stop_name']))
    return id_to_name

try:
    data_path = Path("data/processed")
    station_scores = pd.read_csv(data_path / "station_rss_scores.csv")
    travel_times = pd.read_csv(data_path / "travel_times_sample.csv")
    survey = pd.read_csv(data_path / "passenger_survey_sample.csv")

    print("Data loaded.")
    
    # 1. Survey Names
    survey_names = survey['reporting_group'].unique()
    print(f"Survey unique names: {len(survey_names)}")
    print("Sample Survey Names:", survey_names[:10])

    # 2. RSS Names
    id_to_name = get_station_mapping(travel_times)
    station_scores['from_stop_id'] = station_scores['from_stop_id'].astype(str)
    station_scores['station_name'] = station_scores['from_stop_id'].map(id_to_name)
    
    # Check for unmapped
    unmapped = station_scores[station_scores['station_name'].isna()]
    if not unmapped.empty:
        print(f"Unmapped RSS rows: {len(unmapped)}")
        print("Unmapped IDs:", unmapped['from_stop_id'].head().tolist())
    
    rss_names = station_scores['station_name'].dropna().unique()
    print(f"RSS unique names: {len(rss_names)}")
    print("Sample RSS Names:", rss_names[:10])

    # 3. Intersection
    intersection = set(survey_names).intersection(set(rss_names))
    print(f"Intersection count: {len(intersection)}")
    print("Intersection Sample:", list(intersection)[:10])
    
    # 4. Mismatches
    survey_only = set(survey_names) - set(rss_names)
    print(f"Survey only (Sample): {list(survey_only)[:10]}")

except Exception as e:
    print(f"Error: {e}")
