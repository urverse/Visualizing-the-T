"""
Process MBTA 2024 Passenger Survey
Filters to Heavy Rail only and saves as Parquet
"""

import pandas as pd
import os
from datetime import datetime

def main():
    print("=" * 60)
    print("📋 Passenger Survey Processing")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Paths - adjust the input filename to match your actual file
    input_file = "data/raw/passenger_survey_2024.csv"  # ← CHANGE THIS to your actual filename
    output_path = "data/processed/passenger_survey_2024.parquet"
    sample_path = "data/processed/passenger_survey_sample.csv"
    
    HEAVY_RAIL_ROUTES = ['Red', 'Orange', 'Blue']
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"❌ ERROR: File not found: {input_file}")
        print(f"\n   Looking for files in data/raw/:")
        import glob
        raw_files = glob.glob("data/raw/*.csv")
        for f in raw_files:
            print(f"   - {os.path.basename(f)}")
        return
    
    # Read
    print(f"\n📂 Reading: {input_file}")
    size_mb = os.path.getsize(input_file) / (1024 * 1024)
    print(f"   File size: {size_mb:.1f} MB")
    
    df = pd.read_csv(input_file, low_memory=False)
    print(f"   ✅ Loaded: {len(df):,} rows, {len(df.columns)} columns")
    
    # Show what routes are in the data
    if 'route_or_line' in df.columns:
        route_col = 'route_or_line'
    elif 'route_id' in df.columns:
        route_col = 'route_id'
    else:
        print("\n⚠️  Warning: No route column found")
        print("   Available columns:", df.columns.tolist()[:20])
        route_col = None
    
    if route_col:
        print(f"\n📊 Routes in survey data:")
        print(df[route_col].value_counts().head(10).to_string())
        
        # Filter to heavy rail
        print(f"\n🚇 Filtering to Heavy Rail ({', '.join(HEAVY_RAIL_ROUTES)})...")
        # Try to match - survey might have "Red Line" while we filter for "Red"
        df_heavy = df[df[route_col].str.contains('|'.join(HEAVY_RAIL_ROUTES), case=False, na=False)].copy()
        
        filtered_out = len(df) - len(df_heavy)
        print(f"   ✅ Heavy rail rows: {len(df_heavy):,}")
        print(f"   📉 Filtered out: {filtered_out:,} ({filtered_out/len(df)*100:.1f}%)")
    else:
        # If no route column found, keep all data
        print("\n⚠️  No route filtering applied - keeping all data")
        df_heavy = df.copy()
    
    # Show key columns
    print(f"\n📋 Key columns in dataset:")
    for col in df_heavy.columns[:15]:
        print(f"   - {col}")
    if len(df_heavy.columns) > 15:
        print(f"   ... and {len(df_heavy.columns) - 15} more")
    
    # Save
    print(f"\n💾 Saving processed data...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_heavy.to_parquet(output_path, engine='pyarrow', compression='snappy', index=False)
    
    output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"   ✅ Saved: {output_path} ({output_size_mb:.1f} MB)")
    
    # Sample
    print(f"\n📦 Creating sample...")
    sample_size = min(200, len(df_heavy))
    sample = df_heavy.sample(n=sample_size, random_state=42)
    sample.to_csv(sample_path, index=False)
    print(f"   ✅ Sample: {len(sample)} rows")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 PROCESSING COMPLETE!")
    print("=" * 60)
    print(f"✅ Input: {input_file}")
    print(f"✅ Output: {output_path}")
    print(f"✅ Rows: {len(df_heavy):,}")
    print(f"✅ Sample: {sample_path}")
    print(f"🕐 Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()