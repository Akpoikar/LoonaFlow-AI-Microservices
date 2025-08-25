import pandas as pd
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

class CSVReader:
    def __init__(self, data_directory: str = "app/data"):
        self.data_directory = Path(data_directory)
        self.campaigns_directory = self.data_directory
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.campaigns_directory.mkdir(parents=True, exist_ok=True)
    
    def get_campaign_folders(self) -> List[str]:
        """Get list of all campaign folders"""
        campaign_folders = [f.name for f in self.campaigns_directory.iterdir() if f.is_dir()]
        return campaign_folders
    
    def get_csv_files_for_campaign(self, campaign_id: str) -> List[str]:
        """Get list of all CSV files in a specific campaign folder"""
        campaign_path = self.campaigns_directory / campaign_id
        if not campaign_path.exists():
            return []
        
        csv_files = list(campaign_path.glob("*.csv"))
        return [f.name for f in csv_files]
    
    def get_all_csv_files(self) -> Dict[str, List[str]]:
        """Get all CSV files organized by campaign"""
        campaigns = self.get_campaign_folders()
        result = {}
        
        for campaign_id in campaigns:
            result[campaign_id] = self.get_csv_files_for_campaign(campaign_id)
        
        return result
    
    def read_leads_from_campaign_csv(self, campaign_id: str, filename: str) -> pd.DataFrame:
        """
        Read leads from a CSV file in a specific campaign folder
        Expected columns: name, email_1
        """
        file_path = self.campaigns_directory / campaign_id / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        try:
            df = pd.read_csv(file_path)
            
            # Validate required columns
            required_columns = ['name', 'email_1']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Clean the data - remove rows with missing name or email_1
            # df = df.dropna(subset=['name', 'email_1'])
            
            # Remove rows where email_1 is empty string or doesn't contain '@'
            # df = df[df['email_1'].astype(str).str.strip() != '']  # Remove empty strings
            # df = df[df['email_1'].astype(str).str.contains('@', na=False)]  # Basic email validation
            
            return df
            
        except Exception as e:
            raise Exception(f"Error reading CSV file {filename} in campaign {campaign_id}: {str(e)}")
    
    def get_lead_count_for_campaign(self, campaign_id: str, filename: str) -> int:
        """Get the number of leads in a CSV file for a specific campaign"""
        try:
            df = self.read_leads_from_campaign_csv(campaign_id, filename)
            return len(df)
        except Exception:
            return 0
    
    def validate_campaign_csv_structure(self, campaign_id: str, filename: str) -> Dict[str, Any]:
        """Validate CSV structure for a specific campaign and return statistics"""
        try:
            df = self.read_leads_from_campaign_csv(campaign_id, filename)
            
            return {
                "valid": True,
                "campaign_id": campaign_id,
                "filename": filename,
                "total_rows": len(df),
                "valid_emails": len(df[df['email_1'].astype(str).str.contains('@', na=False)]),
                "columns": list(df.columns),
                "sample_data": df.head(3).to_dict('records')
            }
        except Exception as e:
            return {
                "valid": False,
                "campaign_id": campaign_id,
                "filename": filename,
                "error": str(e)
            }
    
    def create_campaign_folder(self, campaign_id: str) -> str:
        """Create a campaign folder and return the path"""
        campaign_path = self.campaigns_directory / campaign_id
        campaign_path.mkdir(parents=True, exist_ok=True)
        return str(campaign_path)
    
    def get_campaign_folder_path(self, campaign_id: str) -> str:
        """Get the path to a campaign folder"""
        return str(self.campaigns_directory / campaign_id)
