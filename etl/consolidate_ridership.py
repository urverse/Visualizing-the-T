"""
Process Fall 2024 Rail Ridership by SDP
Filters to Heavy Rail only and saves as Parquet
"""

import pandas as pd
import os
from datetime import datetime

def main():
    print("=" * 60)
    print("👥 Ridership Data Processing")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Paths - adjust filename to match your actual file
    input_file = "data/raw/ridership_fall_2024.csv"  # ← CHANGE THIS to your actual filename
    output_path = "data/processed/ridership_fall2024.parquet"
    sample_path = "data/processed/ridership_sample.csv"
    
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
    
    # Filter by mode if available
    if 'mode' in df.columns:
        print(f"\n📊 Modes in data:")
        print(df['mode'].value_counts().to_string())
        
        print(f"\n🚇 Filtering to Heavy Rail mode...")
        df = df[df['mode'] == 'Heavy Rail'].copy()
        print(f"   ✅ Heavy Rail rows: {len(df):,}")
    
    # Filter by route
    if 'route_id' in df.columns:
        route_col = 'route_id'
    elif 'route_name' in df.columns:
        route_col = 'route_name'
    else:
        print("\n   Available columns:", df.columns.tolist()[:20])
        route_col = None
    
    if route_col:
        print(f"\n📊 Routes in data:")
        print(df[route_col].value_counts().to_string())
        
        print(f"\n🚇 Filtering to Heavy Rail routes ({', '.join(HEAVY_RAIL_ROUTES)})...")
        df_heavy = df[df[route_col].isin(HEAVY_RAIL_ROUTES)].copy()
        
        print(f"   ✅ Final rows: {len(df_heavy):,}")
        
        print(f"\n📊 Final distribution by route:")
        print(df_heavy[route_col].value_counts().to_string())
    else:
        df_heavy = df.copy()
    
    # Show key columns
    print(f"\n📋 Key columns:")
    for col in df_heavy.columns:
        print(f"   - {col}")
    
    # Check for ridership metrics
    ridership_cols = [c for c in df_heavy.columns if 'ons' in c.lower() or 'offs' in c.lower() or 'boardings' in c.lower()]
    if ridership_cols:
        print(f"\n📊 Ridership metrics found:")
        for col in ridership_cols:
            print(f"   - {col}: {df_heavy[col].sum():,.0f} total")
    
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