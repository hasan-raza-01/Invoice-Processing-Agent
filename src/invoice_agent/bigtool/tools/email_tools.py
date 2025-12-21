"""Email notification tools"""
from invoice_agent.bigtool.bigtool_picker import BaseTool
from typing import Dict, Any
import random


class MockEmailTool(BaseTool):
    """Mock email service"""
    name = "mock_email"
    capability = "email"
    
    def execute(self, recipient: str, subject: str, body: str, **kwargs) -> Dict[str, Any]:
        """
        Send email (mock)
        
        Args:
            recipient: Email recipient
            subject: Email subject
            body: Email body
            
        Returns:
            Sending status
        """
        message_id = f"MSG-{random.randint(1000, 9999)}"
        
        # Log to console instead of actually sending
        print(f"\n📧 Email Notification:")
        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        print(f"Body: {body[:100]}...")
        print(f"Message ID: {message_id}\n")
        
        return {
            "sent": True,
            "message_id": message_id,
            "recipient": recipient,
            "status": "DELIVERED"
        }
