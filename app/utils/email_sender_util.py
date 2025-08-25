import smtplib
import asyncio
import random
from email.message import EmailMessage
from typing import Dict, Any, Tuple
from ..config.email_config import EmailConfig, EmailTemplate

class EmailSenderUtil:
    def __init__(self, email_config: EmailConfig):
        self.email_config = email_config
    
    def send_single_email(self, to_email: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Send a single email and return the result
        """
        msg = EmailMessage()
        msg['From'] = self.email_config.email_address
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.set_content(body)
        
        try:
            with smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(self.email_config.email_address, self.email_config.email_password)
                smtp.send_message(msg)
                return {
                    "status": "success",
                    "email": to_email,
                    "message": f"✅ Sent to {to_email}"
                }
        except Exception as e:
            return {
                "status": "failed",
                "email": to_email,
                "error": str(e),
                "message": f"❌ Failed to send to {to_email}: {e}"
            }
    
    async def send_bulk_emails(self, leads_data: list,
                        custom_template: Dict[str, Any] = None, 
                        delay_range: Tuple[int, int] = (2, 5),
                        campaign_id: str = None) -> Dict[str, Any]:
        """
        Send bulk emails to leads from CSV data
        
        Args:
            leads_data: List of dictionaries with 'name' and 'email_1' keys
            custom_template: Template data for custom emails
            delay_range: Tuple of (min_delay, max_delay) in seconds
            campaign_id: Campaign ID for tracking pixel
        """
        results = {
            "total_sent": 0,
            "total_failed": 0,
            "successful_emails": [],
            "failed_emails": [],
            "details": []
        }
        
        for lead in leads_data:
            business_name = lead['name']
            email = lead['email_1']
            
            # Get email template with tracking pixel
            subject, body = EmailTemplate.get_custom_template(business_name, custom_template, campaign_id)

            # Send email
            result = self.send_single_email(email, subject, body)
            results["details"].append(result)
            
            if result["status"] == "success":
                results["total_sent"] += 1
                results["successful_emails"].append(email)
            else:
                results["total_failed"] += 1
                results["failed_emails"].append(email)
            
            # Random delay between emails (non-blocking)
            if len(leads_data) > 1:  # Don't delay after the last email
                delay = random.uniform(delay_range[0], delay_range[1])
                await asyncio.sleep(delay)
        
        return results
