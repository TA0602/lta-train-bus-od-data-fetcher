# LTA Train Historical Data Setup Guide

This guide explains how to fetch **all available historical** Singapore LTA train Origin-Destination (OD) data using GitHub Actions.

## What's Included

- **fetch_lta_data.py** - Python script to fetch all historical data from LTA API and save as Excel
- **requirements.txt** - Python dependencies
- **.github/workflows/fetch-lta-data.yml** - GitHub Actions workflow (manual trigger)

## Setup Steps

### 1. Add Your LTA API Key as a Secret

1. Go to your GitHub repository: https://github.com/TA0602/Hi
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `LTA_API_KEY`
5. Value: `vj6hIAi/T6uoy3zDpCGw1Q==`
6. Click **Add secret**

### 2. Enable Workflows

1. Go to **Actions** tab
2. Click **I understand my workflows, go ahead and enable them**

### 3. Trigger the Workflow

The workflow runs **manually on-demand** (not automatically):

1. Go to **Actions** tab
2. Select **"Fetch LTA Train Historical Data"** workflow
3. Click **Run workflow** (blue button)
4. Click **Run workflow** again to confirm
5. Wait for it to complete (may take a few minutes depending on data size)
6. The historical data file will be saved and committed to the repo

**Time to complete:** Depends on data size (typically 2-10 minutes)

## How It Works

1. GitHub Actions runs the Python script on its servers (which have network access)
2. The script fetches **all available historical data** from the LTA API using pagination
3. Data is converted to Excel format (removes duplicates automatically)
4. The Excel file is automatically committed and pushed to your repository
5. You can download the complete historical dataset from the repo

## File Location

After the workflow runs, you'll find the data file at:
```
lta_train_od_historical.xlsx
```

This file contains all available OD records from the LTA API (can be thousands of records).

## Manual Usage

You can also run the script locally on any machine with network access:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the script to fetch all historical data
python3 fetch_lta_data.py "vj6hIAi/T6uoy3zDpCGw1Q==" "lta_train_od_historical.xlsx"
```

This will fetch all available data from the LTA API and save it to the Excel file.

## Customization

### Change Output Filename
Edit `.github/workflows/fetch-lta-data.yml`:
- Line 30: Change `"lta_train_od_historical.xlsx"` to your preferred filename

### Automate Regular Fetches
If you want the workflow to run periodically (e.g., weekly to get updates), edit `.github/workflows/fetch-lta-data.yml` and add:
```yaml
on:
  schedule:
    - cron: '0 2 * * 0'  # Every Sunday at 2 AM UTC
  workflow_dispatch:
```

## Troubleshooting

**Workflow fails to run:**
- Check that the `LTA_API_KEY` secret is correctly set in GitHub Settings
- Go to **Actions** tab to see error messages

**Data file not generated:**
- Check the workflow run logs for error details
- Verify the API key is valid

**Network errors:**
- The API endpoint may be temporarily unavailable
- The workflow will retry on the next scheduled run
