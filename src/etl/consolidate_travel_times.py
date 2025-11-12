"""
Consolidate monthly travel times CSV files - MEMORY EFFICIENT + ROBUST
Handles mixed data types properly.
"""

import pandas as pd
import glob
import os
from datetime import datetime

def main():
    print("=" * 60)
    print("📦 Travel Times Consolidation (Memory Efficient)")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Paths
    raw_data_path = "data/raw/travel_times/"
    output_path = "data/processed/travel_times_2024_consolidated.parquet"
    sample_path = "data/processed/travel_times_sample.csv"
    
    # Heavy rail routes only
    HEAVY_RAIL_ROUTES = ['Red', 'Orange', 'Blue']
    
    # Find all files
    print(f"\n📂 Looking for files in: {raw_data_path}")
    csv_files = sorted(glob.glob(f"{raw_data_path}*_HRTravelTimes.csv"))
    
    if len(csv_files) == 0:
        print(f"❌ ERROR: No files found")
        return
    
    print(f"\n✅ Found {len(csv_files)} files")
    
    # Process files one at a time
    print("\n📥 Processing files (one at a time to save memory)...")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    first_file = True
    total_rows = 0
    
    for i, file in enumerate(csv_files, 1):
        month = os.path.basename(file).split('_')[0]
        size_mb = os.path.getsize(file) / (1024 * 1024)
        
        print(f"\n[{i}/{len(csv_files)}] Processing {month} ({size_mb:.1f} MB)...")
        
        # Read file - treat everything as string first to avoid mixed type issues
        print(f"   Reading...", end=' ')
        df = pd.read_csv(file, low_memory=False, dtype=str)  # Read as strings
        print(f"✅ {len(df):,} rows")
        
        # Filter to heavy rail immediately
        print(f"   Filtering to heavy rail...", end=' ')
        df_heavy = df[df['route_id'].isin(HEAVY_RAIL_ROUTES)].copy()
        del df  # Free memory
        print(f"✅ {len(df_heavy):,} rows kept")
        
        total_rows += len(df_heavy)
        
        # Save as CSV first (easier to append)
        temp_csv = f"data/processed/temp_{month}.csv"
        print(f"   Saving temp file...")
        df_heavy.to_csv(temp_csv, index=False)
        
        del df_heavy  # Free memory
        print(f"   ✅ Done with {month}")
    
    # Now combine all temp CSV files into one Parquet
    print(f"\n🔗 Combining all files into Parquet...")
    temp_files = sorted(glob.glob("data/processed/temp_*.csv"))
    
    combined_chunks = []
    for temp_file in temp_files:
        print(f"   Reading {os.path.basename(temp_file)}...")
        chunk = pd.read_csv(temp_file, low_memory=False)
        combined_chunks.append(chunk)
    
    print(f"   Concatenating...")
    final_df = pd.concat(combined_chunks, ignore_index=True)
    
    # Clean up temp files
    print(f"   Cleaning up temp files...")
    for temp_file in temp_files:
        os.remove(temp_file)
    
    print(f"\n✅ Total rows: {len(final_df):,}")
    print(f"✅ Columns: {len(final_df.columns)}")
    
    # Show routes
    print("\n📊 Routes in final dataset:")
    print(final_df['route_id'].value_counts().to_string())
    
    # Date range
    if 'service_date' in final_df.columns:
        final_df['service_date'] = pd.to_datetime(final_df['service_date'])
        print(f"\n📅 Date range: {final_df['service_date'].min()} to {final_df['service_date'].max()}")
    
    # Save final parquet
    print(f"\n💾 Saving final Parquet file...")
    final_df.to_parquet(output_path, engine='pyarrow', compression='snappy', index=False)
    
    output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"   ✅ Saved: {output_size_mb:.1f} MB")
    
    # Create sample
    print(f"\n📦 Creating sample file...")
    sample_df = final_df.sample(n=min(1000, len(final_df)), random_state=42)
    sample_df.to_csv(sample_path, index=False)
    
    sample_size_kb = os.path.getsize(sample_path) / 1024
    print(f"   ✅ Sample: {len(sample_df)} rows, {sample_size_kb:.1f} KB")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 CONSOLIDATION COMPLETE!")
    print("=" * 60)
    print(f"✅ Input: {len(csv_files)} monthly CSV files")
    print(f"✅ Output: {output_path}")
    print(f"✅ Total rows: {len(final_df):,}")
    print(f"✅ Routes: {', '.join(HEAVY_RAIL_ROUTES)}")
    print(f"✅ Sample: {sample_path}")
    print(f"🕐 Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()