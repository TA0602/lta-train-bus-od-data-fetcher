#!/usr/bin/env python3
"""
LTA OD Train Historical Data Fetcher
Fetches all available Origin-Destination train data from Singapore LTA API and saves to Excel
"""

import requests
import pandas as pd
import sys
from datetime import datetime, timedelta

def fetch_and_convert_to_excel(api_key, output_file="lta_train_od_historical.xlsx"):
    """
    Fetch all available train OD historical data from LTA API and save to Excel

    Args:
        api_key: LTA API key (AccountKey)
        output_file: Output Excel filename
    """
    try:
        print("Fetching historical data from LTA API...")

        headers = {
            "AccountKey": api_key,
            "accept": "application/json"
        }

        base_url = "https://datamall2.mytransport.sg/ltaodataservice/PV/ODTrain"
        all_records = []

        # Try to fetch with pagination (LTA API typically uses $skip parameter)
        skip = 0
        page_size = 500
        max_records = 50000  # Limit to avoid overwhelming the API
        consecutive_empty = 0

        while len(all_records) < max_records:
            url = f"{base_url}?$skip={skip}"
            print(f"  Fetching page {skip // page_size + 1} (records {skip}-{skip + page_size})...")

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            records = data.get("value", []) if isinstance(data, dict) else data

            if not records:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    print(f"  No more data available (reached end of dataset)")
                    break
            else:
                consecutive_empty = 0
                all_records.extend(records)
                print(f"    Retrieved {len(records)} records (total: {len(all_records)})")

            skip += page_size

            # Safety check
            if skip > 100000:
                print("  Reached safety limit, stopping fetch")
                break

        if not all_records:
            print("✗ No data received from API")
            return False

        # Convert to DataFrame
        df = pd.json_normalize(all_records)

        # Remove duplicates if any
        df = df.drop_duplicates()

        # Save to Excel
        df.to_excel(output_file, index=False)

        print(f"\n✓ Successfully saved {len(df)} historical records to {output_file}")
        print(f"  Columns: {', '.join(df.columns.tolist())}")
        print(f"  Data spans from {df.iloc[0] if len(df) > 0 else 'N/A'} to {df.iloc[-1] if len(df) > 0 else 'N/A'}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ Network error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    api_key = "***REMOVED***"
    output_file = "lta_train_od_historical.xlsx"

    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    success = fetch_and_convert_to_excel(api_key, output_file)
    sys.exit(0 if success else 1)
