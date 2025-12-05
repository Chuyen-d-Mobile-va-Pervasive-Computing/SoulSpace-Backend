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

    async def notify_admin_new_expert(self, expert_email: str, expert_name: str):
        """Notify admin when new expert submits profile."""
        admin_email = settings.EMAIL_USER  # Hoặc email admin cố định
        
        message = MIMEMultipart()
        message["From"] = f"SoulSpace <{self.email_user}>"
        message["To"] = admin_email
        message["Subject"] = f"🔔 New Expert Registration: {expert_name}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>New Expert Registration</h2>
            <p>A new expert has submitted their profile for review:</p>
            <ul>
                <li><strong>Name:</strong> {expert_name}</li>
                <li><strong>Email:</strong> {expert_email}</li>
            </ul>
            <p>Please review and approve/reject in the admin panel.</p>
            <p style="color: #888; font-size: 12px;">© {datetime.datetime.now().year} SoulSpace</p>
        </body>
        </html>
        """
        message.attach(MIMEText(html_body, "html"))
        
        try:
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(message)
        except Exception as e:
            # Log but don't fail the request
            print(f"Failed to send admin notification: {e}")

    async def notify_expert_approved(self, expert_email: str, expert_name: str):
        """Notify expert when their application is approved."""
        message = MIMEMultipart()
        message["From"] = f"SoulSpace <{self.email_user}>"
        message["To"] = expert_email
        message["Subject"] = "✅ Your Expert Application Has Been Approved!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Congratulations, {expert_name}!</h2>
            <p>Your expert application has been <strong style="color: green;">approved</strong>.</p>
            <p>You can now log in to the SoulSpace platform and start providing consultations.</p>
            <p>Thank you for joining our community!</p>
            <p style="color: #888; font-size: 12px;">© {datetime.datetime.now().year} SoulSpace</p>
        </body>
        </html>
        """
        message.attach(MIMEText(html_body, "html"))
        
        try:
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(message)
        except Exception as e:
            print(f"Failed to send approval notification: {e}")

    async def notify_expert_rejected(self, expert_email: str, expert_name: str, reason: str = None):
        """Notify expert when their application is rejected."""
        message = MIMEMultipart()
        message["From"] = f"SoulSpace <{self.email_user}>"
        message["To"] = expert_email
        message["Subject"] = "❌ Your Expert Application Status"
        
        reason_text = f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Dear {expert_name},</h2>
            <p>We regret to inform you that your expert application has been <strong style="color: red;">rejected</strong>.</p>
            {reason_text}
            <p>You can resubmit your application after addressing the issues mentioned.</p>
            <p>If you have questions, please contact our support team.</p>
            <p style="color: #888; font-size: 12px;">© {datetime.datetime.now().year} SoulSpace</p>
        </body>
        </html>
        """
        message.attach(MIMEText(html_body, "html"))
        
        try:
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(message)
        except Exception as e:
            print(f"Failed to send rejection notification: {e}")

