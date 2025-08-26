import os
import pandas as pd
import shutil
from typing import Dict, Any, Optional
from pathlib import Path
from ..config.email_config import EmailConfig
from ..utils.csv_reader import CSVReader
from ..utils.email_sender_util import EmailSenderUtil

class EmailSenderService:
    def __init__(self):
        self.csv_reader = CSVReader()
    
    async def send_emails(self, campaign_id: str, email_template: dict, user_id: str, subscription: dict, email_config: dict = None, current_position: int = 0, emails_per_day: int = 50):
        """
        Send emails to leads from CSV file using the provided template and email configuration with pagination
        """
        try:
            # Validate email config
            if not email_config:
                raise ValueError("Email configuration is required")
            
            # Create email config object - handle both dict and EmailConfig object
            if isinstance(email_config, dict):
                email_config_obj = EmailConfig.from_dict(email_config)
            elif isinstance(email_config, EmailConfig):
                email_config_obj = email_config
            else:
                raise ValueError(f"Invalid email_config type: {type(email_config)}. Expected dict or EmailConfig")
            
            # Get CSV files for this campaign
            csv_files = self.csv_reader.get_csv_files_for_campaign('task_'+campaign_id)
            if not csv_files:
                raise FileNotFoundError(f"No CSV files found for campaign {campaign_id}")
            # Use the first CSV file found (you can modify this logic as needed)
            csv_filename = csv_files[0]
            # Read leads from CSV
            df = self.csv_reader.read_leads_from_campaign_csv('task_'+campaign_id, csv_filename)
            
            # Apply pagination
            total_rows = len(df)
            start_position = current_position
            end_position = min(start_position + emails_per_day, total_rows)
            
            # Get the subset of data for this batch
            df_subset = df.iloc[start_position:end_position]
            leads_data = df_subset.to_dict('records')
            
            # Filter out leads without emails and count skipped ones
            valid_leads_data = []
            emails_skipped = 0
            for lead in leads_data:
                if not lead.get('email_1') or pd.isna(lead.get('email_1')) or str(lead.get('email_1')).strip() == '':
                    emails_skipped += 1
                else:
                    valid_leads_data.append(lead)
            
            # Create email sender utility
            email_sender = EmailSenderUtil(email_config_obj)
           
            # Send bulk emails (now async) - only to valid leads
            results = await email_sender.send_bulk_emails(
                leads_data=valid_leads_data,  # ✅ Only valid leads with emails
                custom_template=email_template,
                delay_range=(30, 60),  # Random delay between 30-60 seconds
                campaign_id=campaign_id
            )
            
            # Clean up the downloaded file and folder after successful email sending
            cleanup_result = self.cleanup_campaign_files(campaign_id)
            
            return {
                "status": "success",
                "message": f"Successfully sent {results['total_sent']} emails, {results['total_failed']} failed",
                "data": {
                    "campaign_id": campaign_id,
                    "csv_file": csv_filename,
                    "total_leads": len(leads_data),
                    "emails_sent": results['total_sent'],
                    "emails_failed": results['total_failed'],
                    "emails_skipped": emails_skipped,
                    "successful_emails": results['successful_emails'],
                    "failed_emails": results['failed_emails'],
                    "details": results['details'],
                    "pagination": {
                        "total_rows": total_rows,
                        "current_position": start_position,
                        "next_position": end_position,
                        "emails_per_day": emails_per_day,
                        "has_more": end_position < total_rows
                    },
                    "cleanup": cleanup_result
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to send emails: {str(e)}",
                "data": {
                    "campaign_id": campaign_id,
                    "error": str(e)
                }
            }
    
    def cleanup_campaign_files(self, campaign_id: str) -> Dict[str, Any]:
        """
        Remove the downloaded file and folder for a campaign after email sending is completed
        
        Args:
            campaign_id: The campaign ID (Outscraper task ID)
            
        Returns:
            Dictionary containing cleanup status and details
        """
        try:
            # Construct the task folder path
            task_folder = Path("app/data") / f"task_{campaign_id}"
            
            if not task_folder.exists():
                return {
                    "status": "skipped",
                    "message": f"Task folder {task_folder} does not exist",
                    "data": {
                        "campaign_id": campaign_id,
                        "folder_path": str(task_folder),
                        "files_removed": 0
                    }
                }
            
            # Count files before removal
            files_count = len(list(task_folder.glob("*")))
            
            # Remove the entire folder and its contents
            shutil.rmtree(task_folder)
            
            return {
                "status": "success",
                "message": f"Successfully cleaned up {files_count} files from task folder",
                "data": {
                    "campaign_id": campaign_id,
                    "folder_path": str(task_folder),
                    "files_removed": files_count
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to cleanup campaign files: {str(e)}",
                "data": {
                    "campaign_id": campaign_id,
                    "error": str(e)
                }
            }
    
    def get_campaign_folders(self) -> list:
        """Get list of available campaign folders"""
        return self.csv_reader.get_campaign_folders()
    
    def get_csv_files_for_campaign(self, campaign_id: str) -> list:
        """Get list of CSV files for a specific campaign"""
        return self.csv_reader.get_csv_files_for_campaign(campaign_id)
    
    def get_all_csv_files(self) -> dict:
        """Get all CSV files organized by campaign"""
        return self.csv_reader.get_all_csv_files()
    
    def validate_campaign_csv_file(self, campaign_id: str, filename: str) -> dict:
        """Validate a CSV file structure for a specific campaign"""
        return self.csv_reader.validate_campaign_csv_structure(campaign_id, filename)
    
    def create_campaign_folder(self, campaign_id: str) -> str:
        """Create a campaign folder"""
        return self.csv_reader.create_campaign_folder(campaign_id)
