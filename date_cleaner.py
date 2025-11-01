import os
import pandas as pd
from datetime import datetime

# Path to your data directory
DATA_DIR = "data"

def is_iso_datetime(value: str) -> bool:
    """Check if a cell looks like an ISO datetime string."""
    if not isinstance(value, str):
        return False
    try:
        # Try parsing ISO timestamp
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False

def fix_date_format(date_value):
    """Convert ISO or datetime-like values to DD-MM-YYYY format."""
    if pd.isna(date_value):
        return date_value  # leave empty cells unchanged
    if isinstance(date_value, str):
        if is_iso_datetime(date_value):
            try:
                dt = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
                return dt.strftime("%d-%m-%Y")
            except Exception:
                pass
        # Already formatted correctly (DD-MM-YYYY)
        try:
            datetime.strptime(date_value, "%d-%m-%Y")
            return date_value
        except ValueError:
            pass
    # Try general conversion for pandas Timestamps or other date objects
    try:
        dt = pd.to_datetime(date_value)
        return dt.strftime("%d-%m-%Y")
    except Exception:
        return date_value  # leave anything unparseable unchanged

def clean_csv_dates():
    """Scan all CSV files in /data and fix date columns."""
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".csv"):
            filepath = os.path.join(DATA_DIR, filename)
            print(f"🧾 Checking {filename}...")

            try:
                df = pd.read_csv(filepath)

                if "date" not in df.columns:
                    print("   ⚠️ No 'date' column found — skipped.")
                    continue

                original_dates = df["date"].copy()
                df["date"] = df["date"].apply(fix_date_format)

                if not df["date"].equals(original_dates):
                    backup_path = filepath.replace(".csv", "_backup.csv")
                    df.to_csv(filepath, index=False, encoding="utf-8")
                    print(f"   ✅ Fixed and saved → {filename}")
                    print(f"   💾 Backup created at → {backup_path}")
                else:
                    print("   ✔️ Already correctly formatted.")

            except Exception as e:
                print(f"   ❌ Error processing {filename}: {e}")

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    clean_csv_dates()
