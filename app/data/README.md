# Data Directory Structure

This directory contains CSV files organized by campaign/job IDs.

## Folder Structure

```
app/data/
├── campaigns/
│   ├── campaign_123456/
│   │   ├── leads.csv
│   │   └── backup_leads.csv
│   ├── campaign_789012/
│   │   └── leads.csv
│   └── job_abc123/
│       └── leads.csv
└── README.md
```

## How to Use

1. **Create a Campaign Folder**: Use the API endpoint `/api/campaigns/{campaign_id}/create-folder` to create a new campaign folder
2. **Add CSV Files**: Place your CSV files in the appropriate campaign folder
3. **CSV Format**: Your CSV files must have these columns:
   - `Business Name` - The name of the business
   - `Email` - The email address to send to

## API Endpoints

- `GET /api/campaigns` - List all campaigns
- `GET /api/campaigns/{campaign_id}/csv-files` - List CSV files for a campaign
- `GET /api/campaigns/{campaign_id}/csv-files/{filename}/validate` - Validate a CSV file
- `POST /api/campaigns/{campaign_id}/create-folder` - Create a new campaign folder
- `GET /api/csv-files/all` - Get all CSV files organized by campaign

## Example CSV Format

```csv
Business Name,Email
Escape Room Berlin,contact@escaperoomberlin.de
Mystery Games Hamburg,info@mysterygameshamburg.com
Adventure Quest Munich,hello@adventurequestmunich.de
```

## Notes

- Campaign IDs should be unique identifiers (e.g., campaign_123456, job_abc123)
- The email sender will automatically use the first CSV file found in the campaign folder
- CSV files are validated for required columns and basic email format
