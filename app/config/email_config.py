import os
from typing import Dict, Any

class EmailConfig:
    def __init__(self, smtp_server: str, smtp_port: int, email_address: str, email_password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_address = email_address
        self.email_password = email_password
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'EmailConfig':
        return cls(
            smtp_server=config_dict['smtpServer'],
            smtp_port=config_dict['smtpPort'],
            email_address=config_dict['emailAddress'],
            email_password=config_dict['emailPassword']
        )

class EmailTemplate:
    @staticmethod
    def get_custom_template(business_name: str, template_data: Dict[str, Any], campaign_id: str = None) -> tuple[str, str]:
        """
        Returns (subject, body) for custom email template with tracking pixel
        """
        subject = template_data.get('subject', '').replace('{name}', business_name)
        body = template_data.get('content', '').replace('{name}', business_name)
        
        # Add tracking pixel if campaign_id is provided
        if campaign_id:
            # tracking_pixel = f'<img src="http://localhost:3001/api/campaigns/{campaign_id}/track" width="1" height="1" style="display:none;" />'
            tracking_pixel=''
            body += f'\n\n{tracking_pixel}'
        
        return subject, body
