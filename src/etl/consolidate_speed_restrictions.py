"""
Consolidate Speed Restrictions data (monthly files)
Filters to Heavy Rail only and saves as Parquet
"""

import pandas as pd
import glob
import os
from datetime import datetime

def main():
    print("=" * 60)
    print("🚧 Speed Restrictions Consolidation")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Paths
    raw_data_path = "data/raw/speed_restrictions/"
    output_path = "data/processed/speed_restrictions_2024.parquet"
    sample_path = "data/processed/speed_restrictions_sample.csv"
    
    HEAVY_RAIL_ROUTES = ['Red', 'Orange', 'Blue']
    
    # Find files - adjust pattern to match your actual files
    print(f"\n📂 Looking for files in: {raw_data_path}")
    csv_files = sorted(glob.glob(f"{raw_data_path}*.csv"))
    
    if len(csv_files) == 0:
        print(f"❌ ERROR: No CSV files found")
        print(f"\n   Checking if directory exists...")
        if os.path.exists(raw_data_path):
            print(f"   Directory exists but is empty")
        else:
            print(f"   Directory does not exist")
            print(f"   Looking in data/raw/ instead...")
            csv_files = sorted(glob.glob("data/raw/*restriction*.csv"))
            if csv_files:
                print(f"   Found {len(csv_files)} restriction files in data/raw/")
        return
    
    print(f"\n✅ Found {len(csv_files)} files:")
    for f in csv_files[:5]:  # Show first 5
        print(f"   - {os.path.basename(f)}")
    if len(csv_files) > 5:
        print(f"   ... and {len(csv_files) - 5} more")
    
    # Load all files
    print(f"\n📥 Loading all files...")
    dfs = []
    
    for i, file in enumerate(csv_files, 1):
        filename = os.path.basename(file)
        size_mb = os.path.getsize(file) / (1024 * 1024)
        
        print(f"   [{i}/{len(csv_files)}] {filename} ({size_mb:.1f} MB)...", end=' ')
        
        try:
            df = pd.read_csv(file, low_memory=False)
            
            # Filter to heavy rail immediately if route_id exists
            if 'route_id' in df.columns:
                df = df[df['route_id'].isin(HEAVY_RAIL_ROUTES)].copy()
            
            dfs.append(df)
            print(f"✅ {len(df):,} rows")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    if len(dfs) == 0:
        print("\n❌ No files were successfully loaded")
        return
    
    # Combine
    print(f"\n🔗 Combining {len(dfs)} files...")
    result = pd.concat(dfs, ignore_index=True)
    
    print(f"\n✅ Total rows: {len(result):,}")
    print(f"✅ Columns: {len(result.columns)}")
    
    # Show routes
    if 'route_id' in result.columns:
        print(f"\n📊 Routes in dataset:")
        print(result['route_id'].value_counts().to_string())
    
    # Show date range if available
    date_cols = [c for c in result.columns if 'date' in c.lower()]
    if date_cols:
        print(f"\n📅 Date columns found: {date_cols}")
        for col in date_cols:
            try:
                result[col] = pd.to_datetime(result[col])
                print(f"   {col}: {result[col].min()} to {result[col].max()}")
            except:
                pass
    
    # Show key columns
    print(f"\n📋 Columns in dataset:")
    for col in result.columns:
        print(f"   - {col}")
    
    # Save
    print(f"\n💾 Saving consolidated data...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result.to_parquet(output_path, engine='pyarrow', compression='snappy', index=False)
    
    output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"   ✅ Saved: {output_path} ({output_size_mb:.1f} MB)")
    
    # Sample
    print(f"\n📦 Creating sample...")
    sample_size = min(200, len(result))
    sample = result.sample(n=sample_size, random_state=42)
    sample.to_csv(sample_path, index=False)
    print(f"   ✅ Sample: {len(sample)} rows")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 CONSOLIDATION COMPLETE!")
    print("=" * 60)
    print(f"✅ Input: {len(csv_files)} CSV files")
    print(f"✅ Output: {output_path}")
    print(f"✅ Rows: {len(result):,}")
    print(f"✅ Sample: {sample_path}")
    print(f"🕐 Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()