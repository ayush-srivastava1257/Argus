import os
import pandas as pd
from pathlib import Path

def create_sample_dataset(source_dir: Path, target_dir: Path, rows: int = 50000):
    print(f"Creating sample dataset in {target_dir}...")
    if not target_dir.exists():
        target_dir.mkdir(parents=True)
        
    for root, dirs, files in os.walk(source_dir):
        # Create corresponding directories in target
        rel_path = Path(root).relative_to(source_dir)
        target_root = target_dir / rel_path
        if not target_root.exists():
            target_root.mkdir(parents=True)
            
        for file in files:
            if file.endswith('.csv'):
                source_file = Path(root) / file
                target_file = target_root / file
                
                print(f"Sampling {source_file.name}...")
                try:
                    # Read only the first N rows to save memory
                    df = pd.read_csv(source_file, nrows=rows, low_memory=False)
                    df.to_csv(target_file, index=False)
                    print(f"  -> Saved {len(df)} rows to {target_file}")
                except Exception as e:
                    print(f"  -> Failed to sample {source_file.name}: {e}")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    source = base_dir / "data"
    target = base_dir / "data_sample"
    create_sample_dataset(source, target)
    print("Done!")
