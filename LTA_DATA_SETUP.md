# LTA Train Data Setup Guide

This guide explains how to automatically fetch Singapore LTA train Origin-Destination (OD) data using GitHub Actions.

## What's Included

- **fetch_lta_data.py** - Python script to fetch data from LTA API and save as Excel
- **requirements.txt** - Python dependencies
- **.github/workflows/fetch-lta-data.yml** - GitHub Actions workflow that runs automatically

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

**Option A: Automatic (Recommended)**
- The workflow runs automatically every day at 2 AM UTC (10 AM Singapore time)
- The fetched data is saved as `lta_train_od_data.xlsx`

**Option B: Manual**
1. Go to **Actions** tab
2. Select **Fetch LTA Train Data** workflow
3. Click **Run workflow** → **Run workflow**

## How It Works

1. GitHub Actions runs the Python script on its servers (which have network access)
2. The script fetches real-time data from the LTA API
3. Data is converted to Excel format
4. The Excel file is automatically committed and pushed to your repository
5. You can download the file from the repo whenever you need it

## File Location

After the workflow runs, you'll find the data file at:
```
lta_train_od_data.xlsx
```

## Manual Usage

You can also run the script locally on any machine with network access:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the script
python3 fetch_lta_data.py "vj6hIAi/T6uoy3zDpCGw1Q==" "train_data.xlsx"
```

## Customization

### Change Schedule
Edit `.github/workflows/fetch-lta-data.yml`:
- Line 7: Change the cron schedule (currently `0 2 * * *` = daily at 2 AM UTC)
- Example: `0 0 * * 0` = weekly on Sunday at midnight

### Change Output Filename
Edit `.github/workflows/fetch-lta-data.yml`:
- Line 34: Change `"lta_train_od_data.xlsx"` to your preferred filename

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
