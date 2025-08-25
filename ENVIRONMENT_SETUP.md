# Environment Setup

## Required Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Outscraper API Configuration
OUTSCRAPER_API_KEY=your_outscraper_api_key_here
```

## How to Get Your Outscraper API Key

1. Sign up at [Outscraper](https://outscraper.com/)
2. Go to your dashboard
3. Navigate to API Keys section
4. Generate a new API key
5. Copy the API key to your `.env` file

## API Endpoints

### Locations API
- `GET /api/locations` - Get locations for Italy (default)
- `GET /api/locations/{country}` - Get locations for a specific country

### Example Usage
```bash
# Get locations for Italy
curl http://localhost:3002/api/locations

# Get locations for Germany
curl http://localhost:3002/api/locations/DE

# Get locations for France
curl http://localhost:3002/api/locations/FR
```

## Response Format

The API returns locations in the format:
```json
{
  "status": "success",
  "message": "Successfully retrieved 20 locations for IT",
  "data": {
    "country": "IT",
    "locations": [
      "IT>Abruzzi",
      "IT>Basilicata",
      "IT>Calabria",
      "IT>Campania",
      "IT>Emilia-Romagna",
      "IT>Friuli-Venezia Giulia",
      "IT>Lazio",
      "IT>Liguria",
      "IT>Lombardia",
      "IT>Marche",
      "IT>Molise",
      "IT>Piemonte",
      "IT>Puglia",
      "IT>Sardegna",
      "IT>Sicilia",
      "IT>Toscana",
      "IT>Trentino-Alto Adige",
      "IT>Umbria",
      "IT>Valle D'Aosta",
      "IT>Veneto"
    ],
    "total_count": 20,
    "raw_response": { ... }
  }
}
```


