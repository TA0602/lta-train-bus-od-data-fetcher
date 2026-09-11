#!/usr/bin/env python3
"""
LTA OD Train Historical Data Fetcher
Fetches all available Origin-Destination train data from Singapore LTA API and saves to CSV
"""

import requests
import csv
import sys
import json

def fetch_and_save_to_csv(api_key, output_file="lta_train_od_historical.csv"):
    """
    Fetch all available train OD historical data from LTA API and save to CSV

    Args:
        api_key: LTA API key (AccountKey)
        output_file: Output CSV filename
    """
    try:
        print("Fetching historical data from LTA API...")

        headers = {
            "AccountKey": api_key,
            "accept": "application/json"
        }

        base_url = "https://datamall2.mytransport.sg/ltaodataservice/PV/ODTrain"
        all_records = []

        # Fetch with pagination (LTA API uses $skip parameter)
        skip = 0
        page_size = 500
        max_records = 50000
        consecutive_empty = 0

        while len(all_records) < max_records:
            url = f"{base_url}?$skip={skip}"
            print(f"  Fetching records {skip}-{skip + page_size}...")

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            records = data.get("value", []) if isinstance(data, dict) else data

            if not records:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    print(f"  Reached end of dataset")
                    break
            else:
                consecutive_empty = 0
                all_records.extend(records)
                print(f"    Retrieved {len(records)} records (total: {len(all_records)})")

            skip += page_size

            if skip > 100000:
                print("  Reached safety limit, stopping fetch")
                break

        if not all_records:
            print("✗ No data received from API")
            return False

        # Remove duplicates
        seen = set()
        unique_records = []
        for record in all_records:
            record_str = json.dumps(record, sort_keys=True)
            if record_str not in seen:
                seen.add(record_str)
                unique_records.append(record)

        # Get all keys from records
        all_keys = set()
        for record in unique_records:
            all_keys.update(record.keys())
        fieldnames = sorted(list(all_keys))

        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_records)

        print(f"\n✓ Successfully saved {len(unique_records)} historical records to {output_file}")
        print(f"  Columns: {', '.join(fieldnames)}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ Network error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    api_key = "***REMOVED***"
    output_file = "lta_train_od_historical.csv"

    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    success = fetch_and_save_to_csv(api_key, output_file)
    sys.exit(0 if success else 1)
