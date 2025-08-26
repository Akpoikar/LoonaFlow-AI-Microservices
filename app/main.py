from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
from .services.scraper import ScraperService
from .services.email_sender import EmailSenderService
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime

load_dotenv()

# In-memory task storage (in production, use a proper database)
tasks: Dict[str, dict] = {}

app = FastAPI(
    title="LeadFlow Scraper Service",
    description="API service for scraping leads and sending emails",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
scraper_service = ScraperService()
email_sender_service = EmailSenderService()

class User(BaseModel):
    id: str
    subscription: dict

class Campaign(BaseModel):
    id: str
    businessType: Optional[str] = None
    location: Optional[str] = None
    maximumResults: Optional[int] = None
    emailTemplate: Optional[dict] = None
    outscraperTaskId: Optional[str] = None
    emailsPerDay: Optional[int] = 50
    currentPosition: Optional[int] = 0

class ScrapeRequest(BaseModel):
    campaign: Campaign
    user: User

class EmailConfig(BaseModel):
    smtpServer: str
    smtpPort: int
    emailAddress: str
    emailPassword: str

class SendEmailRequest(BaseModel):
    campaign: Campaign
    user: User
    emailConfig: EmailConfig

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

class LocationResponse(BaseModel):
    status: str
    message: str
    data: dict

class ScrapeTaskResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None

class CampaignResponse(BaseModel):
    status: str
    campaigns: list
    count: int

class CSVFilesResponse(BaseModel):
    status: str
    campaign_id: str
    files: list
    count: int

class ValidationResponse(BaseModel):
    status: str
    campaign_id: str
    filename: str
    validation: dict

class FolderResponse(BaseModel):
    status: str
    campaign_id: str
    folder_path: str
    message: str

class AllFilesResponse(BaseModel):
    status: str
    files_by_campaign: dict

class TaskInfoResponse(BaseModel):
    status: str
    message: str
    data: dict

class OutscraperTaskInfo(BaseModel):
    """Detailed response model for Outscraper task information"""
    metadata: dict
    updated: str
    user_id: str
    status: str
    created: str
    queue_task_id: str
    results: list
    id: str

class DownloadResponse(BaseModel):
    status: str
    message: str
    data: dict

async def background_scrape(task_id: str, request: ScrapeRequest):
    try:
        result = scraper_service.scrape(
            business_type=request.campaign.businessType,
            location=request.campaign.location,
            max_results=request.campaign.maximumResults,
            user_id=request.user.id,
            subscription=request.user.subscription
        )
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = result
        tasks[task_id]["completed_at"] = datetime.now().isoformat()
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["completed_at"] = datetime.now().isoformat()

async def background_send_emails(task_id: str, request: SendEmailRequest):
    try:
        # Get task info and download file
        raw_data = scraper_service.get_task_info_raw(request.campaign.outscraperTaskId)
        
        # Check if task is completed and has results
        if raw_data.get("status") != "SUCCESS":
            raise Exception(f"Task {request.campaign.outscraperTaskId} is not completed. Current status: {raw_data.get('status')}")
        
        results = raw_data.get("results", [])
        if not results:
            raise Exception(f"No results found for task {request.campaign.outscraperTaskId}")
        
        # Get the first result's file URL
        file_url = results[0].get("file_url")
        if not file_url:
            raise Exception(f"No file URL found in results for task {request.campaign.outscraperTaskId}")
        
        # Download the file
        download_result = scraper_service.download_task_file(request.campaign.outscraperTaskId, file_url)
        
        if download_result["status"] != "success":
            raise Exception(f"Download failed: {download_result['message']}")
 
        # Step 2: Convert Pydantic EmailConfig to dictionary
        email_config_dict = {
            'smtpServer': request.emailConfig.smtpServer,
            'smtpPort': request.emailConfig.smtpPort,
            'emailAddress': request.emailConfig.emailAddress,
            'emailPassword': request.emailConfig.emailPassword
        }
        
        
        # Step 3: Send emails using the downloaded file (now async) with pagination
        result = await email_sender_service.send_emails(
            campaign_id=request.campaign.outscraperTaskId,
            email_template=request.campaign.emailTemplate,
            user_id=request.user.id,
            subscription=request.user.subscription,
            email_config=email_config_dict,
            current_position=request.campaign.currentPosition,
            emails_per_day=request.campaign.emailsPerDay
        )
        
        # Combine download and email results with detailed information
        combined_result = {
            "download": download_result,
            "email_sending": {
                "status": result["status"],
                "message": result["message"],
                "campaign_id": result["data"]["campaign_id"],
                "csv_file": result["data"]["csv_file"],
                "total_leads": result["data"]["total_leads"],
                "emails_sent": result["data"]["emails_sent"],
                "emails_failed": result["data"]["emails_failed"],
                "emails_skipped": result["data"]["emails_skipped"],
                "successful_emails": result["data"]["successful_emails"],
                "failed_emails": result["data"]["failed_emails"],
                "pagination": result["data"]["pagination"],
                "details": result["data"]["details"]
            },
            "cleanup": result["data"].get("cleanup", {})
        }
        
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = combined_result
        tasks[task_id]["completed_at"] = datetime.now().isoformat()
        
        
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["completed_at"] = datetime.now().isoformat()

@app.post("/api/scrape", response_model=TaskResponse)
async def scrape_leads(request: ScrapeRequest):
    """Scrape leads using Outscraper API and return the Outscraper task ID"""
    try:
        # Directly call the scraper service
        result = scraper_service.scrape(
            business_type=request.campaign.businessType,
            location=request.campaign.location,
            max_results=request.campaign.maximumResults,
            user_id=request.user.id,
            subscription=request.user.subscription
        )
        
        if result["status"] != "success":
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Extract the Outscraper task ID from the result
        outscraper_task_id = result["data"]["task_id"]
        
        return TaskResponse(
            task_id=outscraper_task_id,
            status="success",
            message=f"Scraping task initiated successfully. Outscraper task ID: {outscraper_task_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/send", response_model=TaskResponse)
async def send_emails(request: SendEmailRequest, background_tasks: BackgroundTasks):
    # Use the outscraperTaskId from the campaign as the task ID
    task_id = request.campaign.outscraperTaskId
    
    # Check if outscraperTaskId is provided
    if not task_id:
        raise HTTPException(status_code=400, detail="outscraperTaskId is required in campaign")
    
    tasks[task_id] = {
        "status": "processing",
        "created_at": datetime.now().isoformat()
    }

    background_tasks.add_task(background_send_emails, task_id, request)
    
    return TaskResponse(
        task_id=task_id,
        status="processing",
        message=f"Email sending task started for Outscraper task ID: {task_id}"
    )

@app.get("/api/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
        error=task.get("error"),
        created_at=task["created_at"],
        completed_at=task.get("completed_at")
    )

@app.get("/api/campaigns", response_model=CampaignResponse)
async def get_campaigns():
    """Get list of available campaigns"""
    try:
        campaigns = email_sender_service.get_campaign_folders()
        return CampaignResponse(
            status="success",
            campaigns=campaigns,
            count=len(campaigns)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/campaigns/{campaign_id}/csv-files", response_model=CSVFilesResponse)
async def get_csv_files_for_campaign(campaign_id: str):
    """Get list of CSV files for a specific campaign"""
    try:
        csv_files = email_sender_service.get_csv_files_for_campaign(campaign_id)
        return CSVFilesResponse(
            status="success",
            campaign_id=campaign_id,
            files=csv_files,
            count=len(csv_files)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/campaigns/{campaign_id}/csv-files/{filename}/validate", response_model=ValidationResponse)
async def validate_campaign_csv_file(campaign_id: str, filename: str):
    """Validate a CSV file structure for a specific campaign"""
    try:
        validation_result = email_sender_service.validate_campaign_csv_file(campaign_id, filename)
        return ValidationResponse(
            status="success",
            campaign_id=campaign_id,
            filename=filename,
            validation=validation_result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/campaigns/{campaign_id}/create-folder", response_model=FolderResponse)
async def create_campaign_folder(campaign_id: str):
    """Create a campaign folder for storing CSV files"""
    try:
        folder_path = email_sender_service.create_campaign_folder(campaign_id)
        return FolderResponse(
            status="success",
            campaign_id=campaign_id,
            folder_path=folder_path,
            message="Campaign folder created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/csv-files/all", response_model=AllFilesResponse)
async def get_all_csv_files():
    """Get all CSV files organized by campaign"""
    try:
        all_files = email_sender_service.get_all_csv_files()
        return AllFilesResponse(
            status="success",
            files_by_campaign=all_files
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/locations/{country}", response_model=LocationResponse)
async def get_locations(country: str):
    """Get locations for a specific country from Outscraper API"""
    try:
        result = scraper_service.get_locations(country)
        return LocationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/locations", response_model=LocationResponse)
async def get_locations_default():
    """Get locations for Italy (default) from Outscraper API"""
    try:
        result = scraper_service.get_locations("IT")
        return LocationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scrape/task/{task_id}", response_model=ScrapeTaskResponse)
async def get_scrape_task_status(task_id: str):
    """Get the status and results of a scraping task"""
    try:
        result = scraper_service.get_task_status(task_id)
        return ScrapeTaskResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scrape/task/{task_id}/info", response_model=TaskInfoResponse)
async def get_scrape_task_info(task_id: str):
    """Get complete task information from Outscraper API"""
    try:
        result = scraper_service.get_task_info(task_id)
        return TaskInfoResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/task/{task_id}", response_model=TaskInfoResponse)
async def get_task_info(task_id: str):
    """Get complete task information from Outscraper API (direct endpoint)"""
    try:
        result = scraper_service.get_task_info(task_id)
        return TaskInfoResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/task/{task_id}/raw", response_model=OutscraperTaskInfo)
async def get_task_info_raw(task_id: str):
    """Get raw task information from Outscraper API (matches exact Outscraper response format)"""
    try:
        raw_data = scraper_service.get_task_info_raw(task_id)
        # If status is not present, consider it as in progress
        if "status" not in raw_data:
            raw_data["status"] = "IN_PROGRESS"
        return OutscraperTaskInfo(**raw_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/task/{task_id}/download", response_model=DownloadResponse)
async def download_task_file(task_id: str):
    """Get task info and download the result file to the data folder"""
    try:
        # First, get the task info to extract the file URL
        raw_data = scraper_service.get_task_info_raw(task_id)
        
        # Check if task is completed and has results
        if raw_data.get("status") != "SUCCESS":
            raise HTTPException(
                status_code=400, 
                detail=f"Task {task_id} is not completed. Current status: {raw_data.get('status')}"
            )
        
        results = raw_data.get("results", [])
        if not results:
            raise HTTPException(
                status_code=404, 
                detail=f"No results found for task {task_id}"
            )
        
        # Get the first result's file URL
        file_url = results[0].get("file_url")
        if not file_url:
            raise HTTPException(
                status_code=404, 
                detail=f"No file URL found in results for task {task_id}"
            )
        
        # Download the file
        download_result = scraper_service.download_task_file(task_id, file_url)
        
        if download_result["status"] != "success":
            raise HTTPException(
                status_code=500, 
                detail=download_result["message"]
            )
        
        return DownloadResponse(**download_result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/download/file", response_model=DownloadResponse)
async def download_file_by_url(file_url: str, task_id: Optional[str] = None):
    """Download a file from a specific URL and save it to the data folder"""
    try:
        # Use provided task_id or generate one
        if not task_id:
            task_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Download the file
        download_result = scraper_service.download_task_file(task_id, file_url)
        
        if download_result["status"] != "success":
            raise HTTPException(
                status_code=500, 
                detail=download_result["message"]
            )
        
        return DownloadResponse(**download_result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CleanupResponse(BaseModel):
    status: str
    message: str
    data: dict

@app.delete("/api/campaigns/{campaign_id}/cleanup", response_model=CleanupResponse)
async def cleanup_campaign_files(campaign_id: str):
    """Manually cleanup downloaded files and folder for a specific campaign"""
    try:
        cleanup_result = email_sender_service.cleanup_campaign_files(campaign_id)
        return CleanupResponse(**cleanup_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
