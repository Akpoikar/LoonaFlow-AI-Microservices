# LeadFlow Scrapper Microservice

A FastAPI-based microservice for scraping business leads and sending emails.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file with the following variables:
```
PORT=3002
HOST=localhost
DEBUG=True
```

## Running the Service

To run the service:

```bash
uvicorn app.main:app --host localhost --port 3002 --reload
```

## API Endpoints

### 1. Scrape Leads
`POST /api/scrape`

Request body:
```json
{
    "campaign": {
        "id": "string",
        "businessType": "string",
        "location": "string",
        "maximumResults": 0
    },
    "user": {
        "id": "string",
        "subscription": {}
    }
}
```

### 2. Send Emails
`POST /api/send`

Request body:
```json
{
    "campaign": {
        "id": "string",
        "emailTemplate": {}
    },
    "user": {
        "id": "string",
        "subscription": {}
    }
}
```

## API Documentation

Once the service is running, you can access:
- Swagger UI: http://localhost:3002/docs
- ReDoc: http://localhost:3002/redoc
