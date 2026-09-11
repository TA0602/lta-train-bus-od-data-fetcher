#!/usr/bin/env python3
"""
LTA OD Train Data Fetcher
Fetches Origin-Destination train data from Singapore LTA API and saves to Excel
"""

import requests
import pandas as pd
import sys
from datetime import datetime

def fetch_and_convert_to_excel(api_key, output_file="train_data.xlsx"):
    """
    Fetch train OD data from LTA API and save to Excel

    Args:
        api_key: LTA API key (AccountKey)
        output_file: Output Excel filename
    """
    try:
        print("Fetching data from LTA API...")

        headers = {
            "AccountKey": api_key,
            "accept": "application/json"
        }

        url = "https://datamall2.mytransport.sg/ltaodataservice/PV/ODTrain"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Extract the value array from the response
        records = data.get("value", []) if isinstance(data, dict) else data

        if not records:
            print("No data received from API")
            return False

        # Convert to DataFrame
        df = pd.json_normalize(records)

        # Save to Excel
        df.to_excel(output_file, index=False)

        print(f"✓ Successfully saved {len(df)} records to {output_file}")
        print(f"  Columns: {', '.join(df.columns.tolist())}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ Network error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    api_key = "***REMOVED***"
    output_file = "train_data.xlsx"

    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    success = fetch_and_convert_to_excel(api_key, output_file)
    sys.exit(0 if success else 1)
