import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from fastapi import HTTPException, status
import datetime

class EmailService:
    def __init__(self):
        """Initialize EmailService with SMTP configuration."""
        self.email_host = settings.EMAIL_HOST
        self.email_port = settings.EMAIL_PORT
        self.email_user = settings.EMAIL_USER
        self.email_password = settings.EMAIL_PASSWORD

    async def send_otp_email(self, to_email: str, otp: str):
        """Send OTP email to the user with professional HTML formatting.

        Args:
            to_email: Recipient email address.
            otp: One-time password to include in the email.

        Raises:
            HTTPException: If email sending fails.
        """
        # Create email message
        message = MIMEMultipart()
        message["From"] = f"SoulSpace <{self.email_user}>"
        message["To"] = to_email
        message["Subject"] = "SoulSpace Password Reset OTP"

        # HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    padding: 20px 0;
                }}
                .header img {{
                    max-width: 150px;
                }}
                .content {{
                    padding: 20px;
                    text-align: center;
                }}
                .otp {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                    background-color: #e8f0fe;
                    padding: 10px 20px;
                    display: inline-block;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #777777;
                    padding: 20px 0;
                }}
                @media (max-width: 600px) {{
                    .container {{
                        margin: 10px;
                        padding: 10px;
                    }}
                    .otp {{
                        font-size: 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="https://via.placeholder.com/150x50?text=SoulSpace+Logo" alt="SoulSpace Logo">
                </div>
                <div class="content">
                    <h2>Password Reset Request</h2>
                    <p>We received a request to reset your SoulSpace account password. Use the OTP below to proceed:</p>
                    <div class="otp">{otp}</div>
                    <p>This OTP is valid for 10 minutes. If you did not request a password reset, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.datetime.now().year} SoulSpace. All rights reserved.</p>
                    <p>Contact us at <a href="mailto:support@soulspace.com">support@soulspace.com</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        message.attach(MIMEText(html_body, "html"))

        try:
            # Connect to SMTP server
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls()  # Enable TLS
                server.login(self.email_user, self.email_password)
                server.send_message(message)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send OTP email: {str(e)}"
            )