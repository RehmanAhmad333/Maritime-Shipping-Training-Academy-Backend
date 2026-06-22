import logging
import sendgrid
from sendgrid.helpers.mail import Mail
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_email_sync(to_email: str, subject: str, content: str) -> dict:
    """
    Send email synchronously using SendGrid.
    """
    try:
        if not to_email:
            return {"error": "Recipient email is required."}
        
        if not settings.SENDGRID_API_KEY:
            logger.error("SENDGRID_API_KEY not configured")
            return {"error": "SendGrid API key is missing."}
        
        if not settings.SENDGRID_FROM_EMAIL:
            logger.error("SENDGRID_FROM_EMAIL not configured")
            return {"error": "Sender email is missing."}
        
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        
        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            plain_text_content=content
        )
        
        response = sg.send(message)
        
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"Email sent to {to_email}")
            return {"status": response.status_code, "message": "Email sent successfully."}
        else:
            logger.warning(f"Email returned status {response.status_code}")
            return {"error": f"SendGrid returned status {response.status_code}"}
    
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return {"error": str(e)}

def send_email_background(to_email: str, subject: str, content: str):
    """
    Background task wrapper for sending emails.
    """
    return send_email_sync(to_email, subject, content)