"""
Email Service for Payment Notifications
Handles purchase receipts, license delivery, and customer communication
"""
import os
import httpx
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional emails via Resend"""

    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "sales@ayrto.dev")

        if not self.api_key:
            self._load_from_credentials()

        self.base_url = "https://api.resend.com"

    def _load_from_credentials(self):
        """Load credentials from .ai-credentials file"""
        creds_path = os.path.expanduser("~/.ai-credentials/api-keys.env")
        if os.path.exists(creds_path):
            try:
                with open(creds_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key == "RESEND_API_KEY":
                                self.api_key = value.replace(" ", "")  # Remove any spaces
            except Exception as e:
                logger.error(f"Error loading email credentials: {e}")

    @property
    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return bool(self.api_key and self.api_key.startswith('re_'))

    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an email via Resend API"""
        if not self.is_configured:
            logger.warning("Email service not configured - skipping email")
            return {"success": False, "error": "Email not configured"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": self.from_email,
                        "to": [to],
                        "subject": subject,
                        "html": html,
                        "text": text or ""
                    }
                )

                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": response.text}

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {"success": False, "error": str(e)}

    async def send_purchase_receipt(
        self,
        customer_email: str,
        customer_name: str,
        product_name: str,
        amount_cents: int,
        license_key: str,
        download_url: str,
        order_id: str
    ) -> Dict[str, Any]:
        """Send purchase receipt with license key and download link"""

        amount_formatted = f"${amount_cents / 100:.2f}"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #e0e0e0; padding: 40px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #111118; border-radius: 12px; padding: 40px; border: 1px solid #222; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #00f3ff; margin: 0; font-size: 28px; }}
        .receipt-box {{ background: #0a0a0f; border: 1px solid #333; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .license-key {{ font-family: monospace; font-size: 24px; color: #00f3ff; background: #0a0a0f; padding: 15px; text-align: center; border-radius: 6px; letter-spacing: 2px; border: 1px solid #00f3ff33; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #00f3ff, #7000ff); color: #000; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 10px 0; }}
        .amount {{ font-size: 32px; color: #00ff88; font-weight: bold; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #333; font-size: 12px; color: #666; text-align: center; }}
        .row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #222; }}
        .label {{ color: #888; }}
        .value {{ color: #fff; font-weight: 500; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Purchase Confirmed!</h1>
            <p style="color: #888;">Thank you for your purchase</p>
        </div>

        <div class="receipt-box">
            <div class="row">
                <span class="label">Product</span>
                <span class="value">{product_name}</span>
            </div>
            <div class="row">
                <span class="label">Amount</span>
                <span class="value amount">{amount_formatted}</span>
            </div>
            <div class="row">
                <span class="label">Order ID</span>
                <span class="value" style="font-family: monospace; font-size: 12px;">{order_id}</span>
            </div>
        </div>

        <h3 style="color: #00f3ff;">Your License Key</h3>
        <div class="license-key">{license_key}</div>
        <p style="color: #888; font-size: 12px; text-align: center;">Save this key - you'll need it to activate the software</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{download_url}" class="button">⬇️ Download Your Product</a>
        </div>

        <div class="footer">
            <p>Questions? Reply to this email or contact support@ayrto.dev</p>
            <p>© 2026 Ayrto Engineering. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        text = f"""
Purchase Confirmed!

Thank you for purchasing {product_name}!

Amount: {amount_formatted}
Order ID: {order_id}

YOUR LICENSE KEY:
{license_key}

Download your product: {download_url}

Questions? Reply to this email or contact support@ayrto.dev
"""

        return await self.send_email(
            to=customer_email,
            subject=f"🎉 Your {product_name} License Key",
            html=html,
            text=text
        )

    async def send_download_reminder(
        self,
        customer_email: str,
        product_name: str,
        download_url: str,
        expires_in_hours: int = 24
    ) -> Dict[str, Any]:
        """Send reminder that download link is expiring"""

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #e0e0e0; padding: 40px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #111118; border-radius: 12px; padding: 40px; border: 1px solid #222; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #00f3ff, #7000ff); color: #000; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; }}
        .warning {{ background: #ff003c22; border: 1px solid #ff003c; border-radius: 8px; padding: 15px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏰ Download Reminder</h1>
        </div>

        <div class="warning">
            <p>Your download link for <strong>{product_name}</strong> expires in <strong>{expires_in_hours} hours</strong>!</p>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{download_url}" class="button">⬇️ Download Now</a>
        </div>
    </div>
</body>
</html>
"""

        return await self.send_email(
            to=customer_email,
            subject=f"⏰ Your {product_name} download link expires soon",
            html=html
        )


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service singleton"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
