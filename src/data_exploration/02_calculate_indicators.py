"""
RSS Indicator Engineering
DS5110 Team Project - Week 2

Calculates operational performance indicators from consolidated MBTA data:
- Travel time reliability metrics
- Speed restriction impacts
- Ridership exposure weights

Author: Eric
Date: November 2024
"""

import pandas as pd
import numpy as np
from pathlib import Path
import yaml
from datetime import datetime

# Set up paths (adjusted for src/etl/ location)
PROJECT_ROOT = Path(__file__).parent.parent.parent  # Go up to project root
DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "data" / "indicators"
OUTPUT_DIR.mkdir(exist_ok=True)

print("="*70)
print("RSS INDICATOR ENGINEERING")
print("="*70)

# ============================================================================
# 1. LOAD CONSOLIDATED DATA
# ============================================================================

print("\n[1] Loading consolidated datasets...")

# Travel times (this is your large dataset - we'll process it carefully)
travel_times = pd.read_parquet(DATA_DIR / "travel_times_2024_consolidated.parquet")
print(f"  ✓ Travel times: {len(travel_times):,} records")

# Speed restrictions
restrictions = pd.read_parquet(DATA_DIR / "speed_restrictions_2024.parquet")
print(f"  ✓ Speed restrictions: {len(restrictions):,} records")

# Ridership
ridership = pd.read_parquet(DATA_DIR / "ridership_fall2024.parquet")
print(f"  ✓ Ridership: {len(ridership):,} records")

# ============================================================================
# 2. TRAVEL TIME RELIABILITY INDICATORS
# ============================================================================

print("\n[2] Computing travel time reliability indicators...")

# Group by route and direction for comprehensive metrics
travel_reliability = travel_times.groupby(
    ['route_id', 'direction_id', 'from_stop_id', 'to_stop_id']
).agg({
    'travel_time_sec': [
        'count',  # number of observations
        'median',  # typical travel time
        'mean',    # average travel time
        'std',     # volatility
        ('p10', lambda x: x.quantile(0.10)),  # best case
        ('p90', lambda x: x.quantile(0.90)),  # worst case (reliability)
    ]
}).reset_index()

# Flatten column names
travel_reliability.columns = [
    'route_id', 'direction_id', 'from_stop_id', 'to_stop_id',
    'n_observations', 'median_travel_time', 'mean_travel_time', 
    'std_travel_time', 'p10_travel_time', 'p90_travel_time'
]

# Calculate derived reliability metrics
travel_reliability['travel_time_volatility'] = (
    travel_reliability['std_travel_time'] / travel_reliability['median_travel_time']
)

# Buffer time index (extra time needed for reliable trips)
travel_reliability['buffer_time_index'] = (
    (travel_reliability['p90_travel_time'] - travel_reliability['median_travel_time']) 
    / travel_reliability['median_travel_time']
)

# Planning time index (ratio of worst case to best case)
travel_reliability['planning_time_index'] = (
    travel_reliability['p90_travel_time'] / travel_reliability['p10_travel_time']
)

print(f"  ✓ Calculated reliability metrics for {len(travel_reliability):,} route segments")

# ============================================================================
# 3. ON-TIME PERFORMANCE INDICATORS
# ============================================================================

print("\n[3] Computing on-time performance indicators...")

# Define on-time threshold (within 5 minutes of scheduled time would be ideal,
# but we'll use percentile-based approach given our data structure)
# A trip is "reliable" if it's within the 75th percentile of travel times

segment_benchmarks = travel_times.groupby(
    ['route_id', 'direction_id', 'from_stop_id', 'to_stop_id']
)['travel_time_sec'].quantile(0.75).reset_index()
segment_benchmarks.columns = ['route_id', 'direction_id', 'from_stop_id', 'to_stop_id', 'benchmark_time']

# Merge benchmark back to calculate on-time performance
travel_times_with_benchmark = travel_times.merge(
    segment_benchmarks,
    on=['route_id', 'direction_id', 'from_stop_id', 'to_stop_id'],
    how='left'
)

travel_times_with_benchmark['is_on_time'] = (
    travel_times_with_benchmark['travel_time_sec'] <= 
    travel_times_with_benchmark['benchmark_time']
)

# Calculate on-time performance by segment
otp_by_segment = travel_times_with_benchmark.groupby(
    ['route_id', 'direction_id', 'from_stop_id', 'to_stop_id']
).agg({
    'is_on_time': 'mean'  # percentage of on-time trips
}).reset_index()
otp_by_segment.columns = ['route_id', 'direction_id', 'from_stop_id', 'to_stop_id', 'on_time_performance']

print(f"  ✓ Calculated OTP for {len(otp_by_segment):,} route segments")

# ============================================================================
# 4. SPEED RESTRICTION INDICATORS
# ============================================================================

print("\n[4] Computing speed restriction indicators...")

# Clean and prepare the speed restrictions data
# Convert date columns to datetime
restrictions['Date_Restriction_Reported'] = pd.to_datetime(restrictions['Date_Restriction_Reported'])
restrictions['Calendar_Date'] = pd.to_datetime(restrictions['Calendar_Date'])

# Handle Date_Restriction_Cleared (it's a string, may contain 'NA' or actual dates)
restrictions['Date_Restriction_Cleared'] = pd.to_datetime(
    restrictions['Date_Restriction_Cleared'], 
    errors='coerce'  # Convert invalid dates to NaT
)

# Convert speed from string to numeric (may contain 'NA' or numeric values)
restrictions['Restriction_Speed_MPH'] = pd.to_numeric(
    restrictions['Restriction_Speed_MPH'], 
    errors='coerce'
)

# Calculate duration: use days active or calculate from dates
# The data has 'Restriction_Days_Active_On_Calendar_Day' which is useful
restrictions['duration_days'] = restrictions['Restriction_Days_Active_On_Calendar_Day']

# For restrictions without cleared date (still active), calculate from reported date to calendar date
mask_active = restrictions['Date_Restriction_Cleared'].isna()
restrictions.loc[mask_active, 'duration_days'] = (
    restrictions.loc[mask_active, 'Calendar_Date'] - 
    restrictions.loc[mask_active, 'Date_Restriction_Reported']
).dt.total_seconds() / 86400

# Aggregate by line
restriction_metrics = restrictions.groupby('Line').agg({
    'ID': 'nunique',  # count unique restriction IDs
    'duration_days': ['mean', 'sum'],  # average and total duration
    'Restriction_Speed_MPH': ['mean', 'min'],  # severity metrics
    'Restriction_Distance_Miles': ['sum', 'mean'],  # track miles affected
    'Line_Restricted_Track_Pct': 'mean',  # average % of line restricted
}).reset_index()

restriction_metrics.columns = [
    'line', 'n_restrictions', 'avg_duration_days', 'total_restriction_days',
    'avg_speed_mph', 'min_speed_mph', 'total_miles_restricted', 
    'avg_miles_per_restriction', 'avg_pct_line_restricted'
]

# Calculate severity index (lower speed = higher severity)
# Normal track speed is ~40-55 MPH for MBTA heavy rail
# Handle NaN values in speed
restriction_metrics['severity_index'] = 1 - (
    restriction_metrics['avg_speed_mph'].fillna(0) / 50
).clip(0, 1)  # Keep between 0 and 1

print(f"  ✓ Calculated restriction metrics for {len(restriction_metrics)} lines")

# ============================================================================
# 5. RIDERSHIP EXPOSURE WEIGHTS
# ============================================================================

print("\n[5] Computing ridership exposure weights...")

# Calculate total ridership by line and time period
ridership_weights = ridership.groupby(['route_id', 'time_period_name']).agg({
    'total_ons': 'sum',
    'total_offs': 'sum',
    'number_service_days': 'first'
}).reset_index()

# Average daily ridership
ridership_weights['avg_daily_ridership'] = (
    (ridership_weights['total_ons'] + ridership_weights['total_offs']) / 2
) / ridership_weights['number_service_days']

# Calculate exposure weights (proportion of total ridership)
total_system_ridership = ridership_weights['avg_daily_ridership'].sum()
ridership_weights['exposure_weight'] = (
    ridership_weights['avg_daily_ridership'] / total_system_ridership
)

print(f"  ✓ Calculated exposure weights for {len(ridership_weights)} line-period combinations")
print(f"  ✓ Total system daily ridership: {total_system_ridership:,.0f}")

# ============================================================================
# 6. COMBINE AND SAVE INDICATORS
# ============================================================================

print("\n[6] Combining indicators and saving outputs...")

# Merge travel reliability with OTP
combined_travel_indicators = travel_reliability.merge(
    otp_by_segment,
    on=['route_id', 'direction_id', 'from_stop_id', 'to_stop_id'],
    how='left'
)

# Save individual indicator datasets
combined_travel_indicators.to_parquet(
    OUTPUT_DIR / "travel_reliability_indicators.parquet",
    index=False
)
print(f"  ✓ Saved travel reliability indicators")

restriction_metrics.to_parquet(
    OUTPUT_DIR / "restriction_indicators.parquet",
    index=False
)
print(f"  ✓ Saved restriction indicators")

ridership_weights.to_parquet(
    OUTPUT_DIR / "ridership_weights.parquet",
    index=False
)
print(f"  ✓ Saved ridership weights")

# ============================================================================
# 7. CREATE SUMMARY STATISTICS
# ============================================================================

print("\n[7] Generating summary statistics...")

summary_stats = {
    'generation_date': datetime.now().isoformat(),
    'travel_reliability': {
        'n_segments': len(combined_travel_indicators),
        'median_buffer_index': float(combined_travel_indicators['buffer_time_index'].median()),
        'mean_otp': float(combined_travel_indicators['on_time_performance'].mean()),
        'median_volatility': float(combined_travel_indicators['travel_time_volatility'].median()),
    },
    'restrictions': {
        'n_lines': len(restriction_metrics),
        'total_restrictions': int(restriction_metrics['n_restrictions'].sum()),
        'avg_severity': float(restriction_metrics['severity_index'].mean()),
        'total_miles_restricted': float(restriction_metrics['total_miles_restricted'].sum()),
        'avg_pct_line_restricted': float(restriction_metrics['avg_pct_line_restricted'].mean()),
    },
    'ridership': {
        'total_daily_riders': float(total_system_ridership),
        'n_line_periods': len(ridership_weights),
    }
}

# Save summary
with open(OUTPUT_DIR / "indicator_summary.yml", 'w') as f:
    yaml.dump(summary_stats, f, default_flow_style=False, sort_keys=False)

print(f"  ✓ Saved summary statistics")

# ============================================================================
# 8. DISPLAY SUMMARY
# ============================================================================

print("\n" + "="*70)
print("INDICATOR GENERATION COMPLETE")
print("="*70)
print("\nSummary Statistics:")
print(f"\nTravel Reliability:")
print(f"  • Segments analyzed: {summary_stats['travel_reliability']['n_segments']:,}")
print(f"  • Median buffer time index: {summary_stats['travel_reliability']['median_buffer_index']:.3f}")
print(f"  • Mean on-time performance: {summary_stats['travel_reliability']['mean_otp']:.1%}")
print(f"  • Median volatility: {summary_stats['travel_reliability']['median_volatility']:.3f}")

print(f"\nSpeed Restrictions:")
print(f"  • Lines analyzed: {summary_stats['restrictions']['n_lines']}")
print(f"  • Total restrictions: {summary_stats['restrictions']['total_restrictions']}")
print(f"  • Average severity index: {summary_stats['restrictions']['avg_severity']:.3f}")
print(f"  • Total track miles restricted: {summary_stats['restrictions']['total_miles_restricted']:.1f}")
print(f"  • Avg % of line restricted: {summary_stats['restrictions']['avg_pct_line_restricted']:.1%}")

print(f"\nRidership Exposure:")
print(f"  • Total daily riders: {summary_stats['ridership']['total_daily_riders']:,.0f}")
print(f"  • Line-period combinations: {summary_stats['ridership']['n_line_periods']}")

print("\n" + "="*70)
print("\nNext Steps:")
print("  1. Review indicator distributions in data/indicators/")
print("  2. Create weights.yml for RSS calculation")
print("  3. Normalize indicators using z-scores or min-max scaling")
print("  4. Compute prototype RSS for pilot lines")
print("="*70)