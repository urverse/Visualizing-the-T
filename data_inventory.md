# Data Inventory

## 1. MBTA 2024 System-Wide Passenger Survey

- **Link**: https://mbta-massdot.opendata.arcgis.com/datasets/MassDOT::mbta-2024-system-wide-passenger-survey/about
- **Format**: CSV
- **Last Updated**: May 8, 2025
- **Downloaded**: Yes
- **Location**: /data/raw/SystemWidePassengerSurvey.csv

### Key Fields

| Field             | Type    | Description                | Example Values                                        | Use in RSS              |
| ----------------- | ------- | -------------------------- | ----------------------------------------------------- | ----------------------- |
| aggregation_level | String  | Reporting granularity      | "Rapid Transit Line", "Systemwide", "Reporting Group" | Determines join level   |
| route_or_line     | String  | MBTA route/line identifier | "Red Line", "Orange Line", "SL1/SL2/SL3"              | **Primary join key**    |
| reporting_group   | String  | Geographic station cluster | Numerically sequenced or terminal groups              | Secondary grouping      |
| measure_group     | String  | Survey metric category     | "Race and Ethnicity", "Income"                        | **Equity analysis**     |
| measure           | String  | Specific metric            | "Race", "Income (Top V)", "Minority"                  | **Equity slicing**      |
| category          | String  | Response category          | Varies by measure                                     | Response grouping       |
| weighted_percent  | Numeric | Proportion of riders       | 0.0 - 100.0                                           | **Satisfaction metric** |

### Notes

- **aggregation_level** determines the granularity of reporting (system-wide → line-level → station group)
- **route_or_line** includes special rapid transit lines: SL1/SL2/SL3 (Orange Line area), SL4/SL5 (Bus)
- **reporting_group** provides geographic clustering for proximate stations
- **measure_group** and **measure** work together for equity analysis slicing
- **weighted_percent** is the key metric for survey responses - represents proportion of riders in each category

### Data Quality Observations

- [ ] Check if weighted_percent sums to 100% within each measure_group
- [ ] Verify route_or_line values match standard MBTA naming conventions
- [ ] Confirm aggregation_level hierarchy is consistent across records

## 2. Rapid Transit Travel Times (2024)

- **Link**: https://mbta-massdot.opendata.arcgis.com/datasets/0b4dc16b8b984836962229865d5b573b/about
- **Format**: CSV
- **Last Updated**: January 8, 2025
- **Downloaded**: Yes
- **Location**: /data/raw/RapidTransitTravelTimes.csv

### Key Fields

| Field                            | Type   | Description                               | Example Values                                  | Use in RSS                   |
| -------------------------------- | ------ | ----------------------------------------- | ----------------------------------------------- | ---------------------------- |
| service_date                     | Date   | Date of travel time measurement           | 2024-10-15                                      | **Join key** to restrictions |
| route_id                         | String | MBTA route identifier                     | "Red", "Orange", "Blue"                         | **Primary join key**         |
| stop_id                          | String | Stop/station identifier                   | "70061", "70036"                                | **Join key** to ridership    |
| direction_id                     | Int    | Direction of travel (0 or 1)              | 0, 1                                            | Directional analysis         |
| direction                        | String | Direction description                     | "Southbound", "Inbound"                         | Human-readable direction     |
| from_parent_station              | String | Origin station name/ID                    | "Park Street", "Harvard"                        | OD pair origin               |
| from_stop_id                     | String | Specific origin stop ID                   | "70075-1"                                       | Detailed stop level          |
| to_parent_station                | String | Destination station name/ID               | "Downtown Crossing"                             | OD pair destination          |
| to_stop_id                       | String | Specific destination stop ID              | "70076-2"                                       | Detailed stop level          |
| travel_time_sec                  | Float  | Actual travel time in seconds             | 180.5, 245.3                                    | Raw performance data         |
| benchmark_travel_time_sec        | Float  | Scheduled/benchmark travel time           | "Blue-Bowdoin": 90 sec, "Red-Alewife": 23.5 min | **Baseline comparison**      |
| travel_time_departure_vs_arrival | String | Travel time calculation method            | "DEPARTS_AT vs ARRIVES_AT"                      | Methodology note             |
| threshold_flag_15                | Binary | Flag if >15% over benchmark               | 0, 1                                            | **Reliability indicator**    |
| threshold_flag_25                | Binary | Flag if >25% over benchmark               | 0, 1                                            | **Reliability indicator**    |
| threshold_flag_50                | Binary | Flag if >50% over benchmark               | 0, 1                                            | **Service disruption flag**  |
| threshold_id                     | String | Threshold category identifier             | "BLUE-2024-01-01"                               | Threshold versioning         |
| hy_avg_annual_baseline           | Float  | Historical average baseline               | Varies by route/segment                         | Long-term comparison         |
| hy_avg_service_sec               | Float  | Historical service time average           | Varies                                          | **Performance trend**        |
| travel_time_sec                  | Float  | Current measured travel time (duplicate?) | Same as above                                   | Actual vs baseline           |

### Notes

- **OD Pairs**: from_parent_station + to_parent_station define origin-destination segments
- **Threshold flags**: Key reliability indicators - flag when travel time exceeds benchmark by 15%/25%/50%
- **Benchmark**: Pre-defined expected travel times per route segment
- **Historical averages** (hy*avg*\*): Enable trend analysis and anomaly detection
- **Stop vs Parent Station**: parent_station is the station name; stop_id includes platform/direction detail

### Data Quality Observations

- [ ] Check for null values in travel_time_sec (incomplete measurements)
- [ ] Verify threshold flags align with calculated travel_time_sec vs benchmark ratios
- [ ] Confirm date range coverage matches project timeline (Fall 2024)
- [ ] Validate route_id values match standard MBTA naming (Red, Orange, Blue, Green-B/C/D/E)

### Join Strategy

- **To Survey**: route_id (may need fuzzy matching on station names)
- **To Ridership**: route_id + stop_id/parent_station
- **To Restrictions**: service_date + route_id + segment overlap (from/to stops)

### Data Processing/Consolidation

- **Status**: Consolidated ✅
- **Original**: 12 monthly CSVs (~5 GB)
- **Processed**: `data/processed/travel_times_2024_consolidated.parquet`
- **Scope**: Heavy Rail only (Red, Orange, Blue lines)
- **Date Range**: Jan 1 - Dec 31, 2024
- **Rows**: ~XX million (check output from script)
- **Processing**: `src/etl/consolidate_travel_times.py`
- **Completed**: 2024-11-12

## 3. Fall 2024 Rail Ridership by SDP Time Period

- **Link**: https://mbta-massdot.opendata.arcgis.com/datasets/MassDOT::fall-2024-mbta-rail-ridership-by-sdp-time-period-route-line-and-stop/about
- **Format**: CSV
- **Last Updated**: April 7, 2025
- **Location**: /raw/data/RailRidership.csv

### Key Fields

| Field               | Type    | Description                                                                        | Example Values                                      | Use in RSS                   |
| ------------------- | ------- | ---------------------------------------------------------------------------------- | --------------------------------------------------- | ---------------------------- |
| mode                | String  | Mode of transportation                                                             | "Heavy Rail"                                        | Filter to rapid transit      |
| season              | String  | Season and year for ridership data                                                 | "Fall 2024"                                         | Temporal context             |
| route_id            | String  | Route identifier                                                                   | "Red", "Orange", "Blue"                             | **Primary join key**         |
| route_name          | String  | Full route description                                                             | "Red Line", "Green Line"                            | Human-readable route         |
| direction_id        | String  | Direction of travel                                                                | "NB", "SB", "EB", "WB"                              | Directional splits           |
| day_type_id         | String  | Day type identifier                                                                | "day_type_0", "day_type_1"                          | Weekday/weekend code         |
| day_type_name       | String  | Day type description                                                               | "Weekday", "Saturday", "Sunday" (holidays excluded) | Service pattern grouping     |
| time_period_id      | String  | Time period shorthand per SDP                                                      | "time_period_03"                                    | **Join key** to travel times |
| time_period_name    | String  | Aggregated time period description                                                 | "AM_PEAK", "PM_PEAK", "MIDDAY"                      | **Join key** to survey       |
| stop_name           | String  | GTFS-compatible stop name                                                          | "Wollaston", "Park Street"                          | Human-readable location      |
| parent-station      | String  | GTFS-compatible parent station ID                                                  | "place-wlsta", "place-pktrm"                        | **Join key** to travel times |
| total_ons           | Integer | Total passenger boardings (summed across aggregation)                              | 1491                                                | **Primary exposure weight**  |
| total_offs          | Integer | Total passenger alightings (summed across aggregation)                             | 7990                                                | Secondary weight             |
| number_service_days | Integer | Number of non-holiday service days in season by day type                           | 19, 65                                              | Normalization factor         |
| average_ons         | Integer | Average boardings per typical service day = total_ons/number_service_days          | 435                                                 | **Daily exposure metric**    |
| average_offs        | Integer | Average alightings per typical service day = total_offs/number_service_days        | 65                                                  | Daily alighting metric       |
| average_flow        | Integer | Average passengers traveling through station (between stations within time period) | 21                                                  | Through-traffic estimate     |

### Notes

- **Exposure Weighting**: `total_ons` and `average_ons` are your primary weights for RSS aggregation
- **Granularity**: Data aggregated by route, direction, day_type, time_period, and station
- **Time Periods**: `time_period_name` should align with survey and travel time datasets (AM_PEAK, PM_PEAK, etc.)
- **Station IDs**: `parent-station` uses GTFS format (e.g., "place-xxxxx") - may need mapping to other datasets
- **Day Types**: Holidays excluded from all day_type categories
- **Calculation**: average*\* fields = total*\* / number_service_days

### Data Quality Observations

- [ ] Verify time_period_name values match survey and travel times datasets exactly
- [ ] Check for stations with zero/low ridership (data quality or genuine low usage?)
- [ ] Confirm route_id naming convention matches other datasets
- [ ] Validate parent-station IDs can join to stop_id/parent_station in travel times

### Join Strategy

- **To Travel Times**: route_id + parent-station (to from_parent_station/to_parent_station) + time_period_name
- **To Survey**: route_id + time_period_name (station matching may need fuzzy logic)
- **To Restrictions**: route_id + parent-station

### RSS Usage

We use Fall 2024 ridership distributions to weight all 2024 time periods.
This assumes relative station usage patterns remain stable across seasons,
which is supported by MBTA historical data showing consistent commuter
patterns outside of major service disruptions.

**Primary Role**: Exposure weighting

- Weight station/line/time-period RSS scores by `average_ons` or `total_ons`
- Higher ridership stations/periods influence aggregate RSS more
- Formula: `Weighted_RSS = Σ(RSS_i × average_ons_i) / Σ(average_ons_i)`

## 4. Rapid Transit Speed Restrictions by Day

- **Link**: https://mbta-massdot.opendata.arcgis.com/datasets/d73ed67e4cc84a84b818ea2c5caef696/about
- **Format**: CSV
- **Last Updated**: October 7, 2025
- **Location**: /raw/data/SpeedRestrictions.csv

### Key Fields

| Field                     | Type     | Description                                                                      | Example Values                     | Use in RSS                   |
| ------------------------- | -------- | -------------------------------------------------------------------------------- | ---------------------------------- | ---------------------------- |
| route_id                  | String   | Route identifier                                                                 | "Red", "Orange", "Blue", "Green-B" | **Primary join key**         |
| direction                 | String   | Direction of travel                                                              | "Northbound", "Southbound"         | Directional analysis         |
| from_stop_name            | String   | Start station of restricted segment                                              | "Park Street", "Harvard"           | Segment origin               |
| to_stop_name              | String   | End station of restricted segment                                                | "Charles/MGH", "Central"           | Segment destination          |
| speed_mph                 | Integer  | Restricted speed limit in MPH                                                    | 3, 6, 10, 25, 40                   | **Severity indicator**       |
| published_date            | Date     | Date restriction information was published                                       | 2024-10-15                         | Publication timestamp        |
| effective_date            | Date     | Date restriction became active                                                   | 2024-10-20                         | **Join key** to travel times |
| last_updated_date         | Date     | Most recent update to restriction                                                | 2024-11-01                         | Track changes over time      |
| restriction_length_miles  | Float    | Length of restricted track segment                                               | 0.25, 0.5, 1.2                     | **Impact metric**            |
| total_route_miles         | Float    | Total length of route                                                            | 11.5, 15.3                         | Normalization denominator    |
| percent_route_restricted  | Float    | Percentage of route under restriction = (restriction_length / total_route) × 100 | 2.5%, 8.7%                         | **Route-level disruption**   |
| restriction_reason        | String   | Cause of restriction                                                             | "Track condition", "Signal work"   | Root cause analysis          |
| alert_lifecycle_status    | String   | Current status of restriction alert                                              | "Ongoing", "Resolved", "Planned"   | Active vs historical         |
| restrictions_last_updated | DateTime | Timestamp of last data refresh                                                   | 2024-11-12 10:30:00                | Data currency                |

### Additional Detail Fields

| Field                                        | Type    | Description                                         | Use in RSS                |
| -------------------------------------------- | ------- | --------------------------------------------------- | ------------------------- |
| Speed_Restriction_Travel_Time_Seconds_Added  | Integer | Extra travel time added by restriction (calculated) | **Direct delay impact**   |
| Speed_Restriction_Travel_Time_Minutes_Added  | Float   | Extra travel time in minutes                        | Human-readable delay      |
| Calculation notes                            | String  | Methodology for time impact calculation             | Documentation             |
| Assumptions_about_Normal_Operating_Speed_MPH | Integer | Baseline speed without restriction                  | Counterfactual for impact |
| Notes_Assumptions_Travel_Time_Calculations   | String  | Additional calculation context                      | Transparency notes        |

### Notes

- **Speed Restrictions**: Lower speed_mph = more severe disruption (3 MPH = "slow zone", 40 MPH = minor)
- **Segment-Level**: Each row represents one restricted segment on one route
- **Time Impact**: Some records include pre-calculated delay (Speed*Restriction_Travel_Time*\*\_Added)
- **Active vs Historical**: Filter by alert_lifecycle_status = "Ongoing" for current restrictions
- **Route Coverage**: percent_route_restricted aggregates segment impacts to route level

### Data Quality Observations

- [ ] Check date alignment: effective_date should match service_date in travel times
- [ ] Verify all segments have valid from_stop_name → to_stop_name pairs
- [ ] Confirm speed_mph values are reasonable (typically 3-40 MPH range)
- [ ] Check for overlapping restrictions on same segment/date
- [ ] Validate restriction_length_miles against known station spacing

### Join Strategy

- **To Travel Times**:
  - `effective_date = service_date`
  - `route_id = route_id`
  - Segment overlap: `from_stop_name/to_stop_name` ⊆ `from_parent_station/to_parent_station`
- **To Ridership**: route_id (aggregate restrictions to route/day level)
- **To Survey**: route_id (contextual disruption info)

### RSS Usage

**Primary Role**: Explain performance degradation

1. **Disruption Indicator**: Count or % of route under restriction per day
   - `daily_restriction_share = Σ(restriction_length_miles) / total_route_miles`
2. **Severity Weight**: Weight by speed reduction
   - `severity_score = (normal_speed - speed_mph) / normal_speed`
3. **Delay Attribution**: Use Speed*Restriction_Travel_Time*\*\_Added to explain travel time variance
4. **RSS Adjustment**: Penalize segments/routes with active slow zones

---
