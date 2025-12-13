import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from fastapi import HTTPException, status
import datetime

class EmailService:
    async def send_email(self, to_email: str, subject: str, html_body: str):
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            message = MIMEMultipart()
            message["From"] = f"SoulSpace <{self.email_user}>"
            message["To"] = to_email
            message["Subject"] = subject
            message.attach(MIMEText(html_body, "html"))
            import re
            if not to_email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", to_email):
                print(f"[WARNING] Invalid recipient email: '{to_email}' - skipping send.")
                return
            try:
                with smtplib.SMTP(self.email_host, self.email_port) as server:
                    server.starttls()
                    server.login(self.email_user, self.email_password)
                    server.send_message(message)
            except Exception as e:
                import traceback
                print(f"[WARNING] Send email failed: {e} ({type(e).__name__})")
                traceback.print_exc()
    async def send_appointment_accepted_email(
        self, user_email: str, expert_name: str, appointment_date: str,
        start_time: str, end_time: str, clinic_name: str, clinic_address: str
    ):
        subject = "Your appointment has been confirmed!"
        html_body = f"""
        <div style='font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;'>
            <h2 style='color: #27ae60;'>Congratulations! Your appointment is confirmed</h2>
            <p>Expert <strong>{expert_name}</strong> has accepted your consultation appointment:</p>
            <div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;'>
                <p><strong>Date:</strong> {appointment_date}</p>
                <p><strong>Time:</strong> {start_time} - {end_time}</p>
                <p><strong>Clinic:</strong> {clinic_name}</p>
                <p><strong>Address:</strong> {clinic_address}</p>
            </div>
            <p>Please arrive on time and prepare yourself for a comfortable session!</p>
            <p>Best regards,<br><strong>SoulSpace Team</strong></p>
        </div>
        """
        await self.send_email(user_email, subject, html_body)

    async def send_appointment_declined_email(
        self, user_email: str, expert_name: str, appointment_date: str, start_time: str, reason: str = None
    ):
        subject = "Sorry – Your appointment was declined"
        reason_text = f"<p><strong>Reason:</strong> {reason or 'No specific reason provided'}</p>" if reason else ""
        html_body = f"""
        <div style='font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;'>
            <h2 style='color: #e74c3c;'>Appointment Declined</h2>
            <p>Expert <strong>{expert_name}</strong> could not accept your appointment:</p>
            <div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;'>
                <p><strong>Scheduled date:</strong> {appointment_date}</p>
                <p><strong>Scheduled time:</strong> {start_time}</p>
                {reason_text}
            </div>
            <p>You may choose another time slot or expert.</p>
            <p>Sorry for the inconvenience.<br><strong>SoulSpace Team</strong></p>
        </div>
        """
        await self.send_email(user_email, subject, html_body)
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
        admin_email = settings.EMAIL_USER  # Or set a fixed admin email
        message = MIMEMultipart()
        message["From"] = f"SoulSpace <{self.email_user}>"
        message["To"] = admin_email
        message["Subject"] = f"🔔 New Expert Registration: {expert_name}"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style='font-family: Arial, sans-serif; padding: 20px;'>
            <h2>New Expert Registration</h2>
            <p>A new expert has submitted their profile for review:</p>
            <ul>
                <li><strong>Name:</strong> {expert_name}</li>
                <li><strong>Email:</strong> {expert_email}</li>
            </ul>
            <p>Please review and approve/reject in the admin panel.</p>
            <p style='color: #888; font-size: 12px;'>&copy; {datetime.datetime.now().year} SoulSpace</p>
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
        <body style='font-family: Arial, sans-serif; padding: 20px;'>
            <h2>Congratulations, {expert_name}!</h2>
            <p>Your expert application has been <strong style='color: green;'>approved</strong>.</p>
            <p>You can now log in to the SoulSpace platform and start providing consultations.</p>
            <p>Thank you for joining our community!</p>
            <p style='color: #888; font-size: 12px;'>&copy; {datetime.datetime.now().year} SoulSpace</p>
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
        <body style='font-family: Arial, sans-serif; padding: 20px;'>
            <h2>Dear {expert_name},</h2>
            <p>We regret to inform you that your expert application has been <strong style='color: red;'>rejected</strong>.</p>
            {reason_text}
            <p>You can resubmit your application after addressing the issues mentioned.</p>
            <p>If you have questions, please contact our support team.</p>
            <p style='color: #888; font-size: 12px;'>&copy; {datetime.datetime.now().year} SoulSpace</p>
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
    
    async def send_payment_notification_to_expert(
        self,
        expert_email: str,
        expert_name: str,
        user_name: str,
        appointment_date: str,
        start_time: str,
        clinic_name: str,
        clinic_address: str,
        amount: str,
        method: str
    ):
        subject = "New appointment – Action required"
        html_body = f"""
        <div style='font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;'>
            <h2 style='color: #2c3e50;'>Hello Dr. {expert_name},</h2>
            <p>You have received a <strong>new appointment</strong> from a client:</p>
            <div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;'>
                <p><strong>Client name:</strong> {user_name}</p>
                <p><strong>Date:</strong> {appointment_date}</p>
                <p><strong>Time:</strong> {start_time}</p>
                <p><strong>Clinic:</strong> {clinic_name}</p>
                <p><strong>Address:</strong> {clinic_address}</p>
                <p><strong>Payment method:</strong> <span style='color: {'#27ae60' if 'online' in method else '#e67e22'}'><strong>{method}</strong></span></p>
                <p><strong>Amount:</strong> <strong style='font-size: 18px; color: #27ae60;'>{amount}</strong></p>
            </div>
            <p>Please log in to SoulSpace to <strong>accept</strong> or <strong>decline</strong> this appointment within 24 hours.</p>
            <div style='text-align: center; margin: 30px 0;'>
                <a href='https://soulspace.com/expert/dashboard' 
                   style='background: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;'>
                    VIEW APPOINTMENT
                </a>
            </div>
            <p>Best regards,<br><strong>SoulSpace Team</strong></p>
        </div>
        """
        await self.send_email(expert_email, subject, html_body)

    async def send_refund_email(self, user_email: str, amount: int, appointment_date: str, start_time: str):
        subject = "Refund Processed for Your Cancelled Appointment"
        html_body = f"""
        <div style='font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;'>
            <h2 style='color: #27ae60;'>Refund Processed</h2>
            <p>We have processed a refund for your cancelled appointment:</p>
            <div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;'>
                <p><strong>Amount Refunded:</strong> {amount}</p>
                <p><strong>Appointment Date:</strong> {appointment_date}</p>
                <p><strong>Start Time:</strong> {start_time}</p>
            </div>
            <p>The refund will be credited to your account within 3-5 business days.</p>
            <p>Best regards,<br><strong>SoulSpace Team</strong></p>
        </div>
        """
        await self.send_email(user_email, subject, html_body)
        
    async def send_appointment_cancelled_by_expert_email(
        self, user_email: str, expert_name: str, appointment_date: str, start_time: str, reason: str
    ):
        subject = "Your appointment has been cancelled by the expert"
        html_body = f"""
        <div style='font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;'>
            <h2 style='color: #e74c3c;'>Appointment Cancelled</h2>
            <p>Expert <strong>{expert_name}</strong> has cancelled your appointment:</p>
            <div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;'>
                <p><strong>Date:</strong> {appointment_date}</p>
                <p><strong>Time:</strong> {start_time}</p>
                <p><strong>Reason:</strong> {reason}</p>
            </div>
            <p>We apologize for the inconvenience. You may book another appointment.</p>
            <p>Best regards,<br><strong>SoulSpace Team</strong></p>
        </div>
        """
        await self.send_email(user_email, subject, html_body)

    async def send_test_update_notification(self, user_email: str, test_title: str):
        subject = f"Update regarding your incomplete test: {test_title}"
        html_body = f"""
        <div style='font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;'>
            <h2 style='color: #e67e22;'>Test Content Updated</h2>
            <p>Hello,</p>
            <p>We are writing to inform you that the test <strong>"{test_title}"</strong> which you were in the process of taking has been updated by our administrators.</p>
            <div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;'>
                <p>Because the structure of the test has changed, your previous <strong>in-progress</strong> draft is no longer valid and has been reset.</p>
            </div>
            <p>Please visit the application to start the test again with the updated questions.</p>
            <p>Best regards,<br><strong>SoulSpace Team</strong></p>
        </div>
        """
        await self.send_email(user_email, subject, html_body)