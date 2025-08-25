import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import urllib.parse
from pathlib import Path

load_dotenv()

class ScraperService:
    def __init__(self):
        self.api_key = os.getenv('OUTSCRAPER_API_KEY')
        self.base_url = "https://api.outscraper.cloud"
        
        if not self.api_key:
            raise ValueError("OUTSCRAPER_API_KEY not found in environment variables")
    
    def get_locations(self, country: str = "IT") -> Dict[str, Any]:
        """
        Get locations from Outscraper API for a specific country
        
        Args:
            country: Country code (e.g., "IT" for Italy)
            
        Returns:
            Dictionary containing status and locations data
        """
        try:
            url = f"{self.base_url}/locations"
            headers = {
                "X-API-KEY": self.api_key
            }
            params = {
                "country": country
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract locations from the response
            locations = self._extract_locations_from_response(data, country)
            
            return {
                "status": "success",
                "message": f"Successfully retrieved {len(locations)} locations for {country}",
                "data": {
                    "country": country,
                    "locations": locations,
                    "total_count": len(locations),
                    "raw_response": data
                }
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"API request failed: {str(e)}",
                "data": {
                    "country": country,
                    "error": str(e)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "data": {
                    "country": country,
                    "error": str(e)
                }
            }
    
    def _extract_locations_from_response(self, data: Dict[str, Any], country: str) -> List[str]:
        """
        Extract locations from the Outscraper API response
        
        Args:
            data: Raw API response data
            country: Country code
            
        Returns:
            List of location strings in format "COUNTRY>REGION"
        """
        locations = []
        
        try:
            items = data.get('items', [])
            
            for item in items:
                region_name = item.get('v', '')
                if region_name:
                    # Format: "COUNTRY>REGION"
                    location_string = f"{country}>{region_name}"
                    locations.append(location_string)
            
            return locations
            
        except Exception as e:
            return []
    
    def scrape(self, business_type: str, location: str, max_results: int, user_id: str, subscription: dict):
        """
        Scrape business data using Outscraper API
        """
        try:
            # First, get locations for the country
            locations_result = self.get_locations(location)
            
            if locations_result["status"] != "success":
                return locations_result
            
            locations = locations_result["data"]["locations"]
            
            # Now make the second API call to scrape business data
            scrape_result = self._scrape_business_data(
                business_type=business_type,
                locations=locations,
                max_results=max_results,
                country=location
            )
            
            return scrape_result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Scraping failed: {str(e)}",
                "data": {
                    "business_type": business_type,
                    "location": location,
                    "error": str(e)
                }
            }
    
    def _scrape_business_data(self, business_type: str, locations: List[str], max_results: int, country: str) -> Dict[str, Any]:
        """
        Make API call to Outscraper tasks endpoint to scrape business data
        
        Args:
            business_type: Type of business to search for
            locations: List of location strings in format "COUNTRY>REGION"
            max_results: Maximum number of results to return
            country: Country code
            
        Returns:
            Dictionary containing scraping task result
        """
        try:
            url = f"{self.base_url}/tasks"
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "service_name": "google_maps_service_v2",
                "queries": [],
                "enrich": False,
                "settings": {
                    "output_extension": "csv",
                    "output_columns": []
                },
                "tags": [],
                "enrichments": ["domains_service"],
                "categories": [business_type] if business_type else [],
                "locations": locations,
                "language": "en",
                "region": country,
                "limit": max_results,
                "organizationsPerQueryLimit": 500,
                "filters": [],
                "exactMatch": False,
                "useZipCodes": True,
                "dropDuplicates": "true",
                "dropEmailDuplicates": False,
                "ignoreWithoutEmails": False,
                "UISettings": {
                    "isCustomQueries": False,
                    "isCustomCategories": False,
                    "isCustomLocations": False
                },
                "enrichLocations": True
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "status": "success",
                "message": f"Successfully initiated scraping task for {business_type} businesses",
                "data": {
                    "business_type": business_type,
                    "locations": locations,
                    "max_results": max_results,
                    "country": country,
                    "task_id": data.get("id"),
                    "raw_response": data
                }
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"API request failed: {str(e)}",
                "data": {
                    "business_type": business_type,
                    "locations": locations,
                    "error": str(e)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "data": {
                    "business_type": business_type,
                    "locations": locations,
                    "error": str(e)
                }
            }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status and results of a scraping task
        
        Args:
            task_id: The task ID returned from the scraping request
            
        Returns:
            Dictionary containing task status and results
        """
        try:
            url = f"{self.base_url}/tasks/{task_id}"
            headers = {
                "X-API-KEY": self.api_key
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "status": "success",
                "message": f"Successfully retrieved task status for {task_id}",
                "data": {
                    "task_id": task_id,
                    "task_status": data.get("status"),
                    "results": data.get("results"),
                    "raw_response": data
                }
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"API request failed: {str(e)}",
                "data": {
                    "task_id": task_id,
                    "error": str(e)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "data": {
                    "task_id": task_id,
                    "error": str(e)
                }
            }
    
    def get_task_info(self, task_id: str) -> Dict[str, Any]:
        """
        Get complete task information from Outscraper API
        
        Args:
            task_id: The task ID returned from the scraping request
            
        Returns:
            Dictionary containing complete task information
        """
        try:
            url = f"{self.base_url}/tasks/{task_id}"
            headers = {
                "X-API-KEY": self.api_key
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "status": "success",
                "message": f"Successfully retrieved task info for {task_id}",
                "data": data  # Return the complete raw response
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "data": {
                    "task_id": task_id,
                    "error": str(e)
                }
            }
    
    def get_task_info_raw(self, task_id: str) -> Dict[str, Any]:
        """
        Get raw task information from Outscraper API without wrapper
        
        Args:
            task_id: The task ID returned from the scraping request
            
        Returns:
            Raw task information from Outscraper API
        """
        try:
            url = f"{self.base_url}/tasks/{task_id}"
            headers = {
                "X-API-KEY": self.api_key
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()  # Return raw response directly
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
    
    def download_task_file(self, task_id: str, file_url: str) -> Dict[str, Any]:
        """
        Download a file from the provided URL and save it to the data folder
        
        Args:
            task_id: The task ID for organizing the file
            file_url: The URL of the file to download
            
        Returns:
            Dictionary containing download status and file path
        """
        try:
            # Create data directory if it doesn't exist
            data_dir = Path("app/data")
            data_dir.mkdir(exist_ok=True)
            
            # Create a subdirectory for the task
            task_dir = data_dir / f"task_{task_id}"
            task_dir.mkdir(exist_ok=True)
            
            # Extract filename from URL
            parsed_url = urllib.parse.urlparse(file_url)
            filename = os.path.basename(parsed_url.path)
            
            # If no filename found, create one based on task_id
            if not filename or '.' not in filename:
                filename = f"task_{task_id}.xlsx"
            
            # Full path for the file
            file_path = task_dir / filename
            
            # Download the file
            response = requests.get(file_url, stream=True)
            response.raise_for_status()
            
            # Save the file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return {
                "status": "success",
                "message": f"Successfully downloaded file for task {task_id}",
                "data": {
                    "task_id": task_id,
                    "file_url": file_url,
                    "local_path": str(file_path),
                    "filename": filename,
                    "file_size": file_path.stat().st_size if file_path.exists() else 0
                }
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Download failed: {str(e)}",
                "data": {
                    "task_id": task_id,
                    "file_url": file_url,
                    "error": str(e)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error during download: {str(e)}",
                "data": {
                    "task_id": task_id,
                    "file_url": file_url,
                    "error": str(e)
                }
            }
