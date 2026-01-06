"""
Email notification utilities using SendGrid
"""
import logging
from typing import Optional
from decimal import Decimal
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize SendGrid client
sendgrid_client = None
if settings.SENDGRID_API_KEY:
    sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send email using SendGrid
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body (optional)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not sendgrid_client:
        logger.warning("SendGrid API key not configured. Email not sent.")
        return False
    
    try:
        message = Mail(
            from_email=Email(settings.FROM_EMAIL),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        if text_content:
            message.add_content(Content("text/plain", text_content))
        
        response = sendgrid_client.send(message)
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"Email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send email. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {str(e)}")
        return False


def send_verification_email(email: str, verification_token: str) -> bool:
    """
    Send email verification link
    """
    verification_url = f"https://your-domain.com/api/auth/verify-email/{verification_token}"
    
    subject = "Verify Your Email - Price Tracker Pro"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; 
                      color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to Price Tracker Pro!</h1>
            <p>Thank you for signing up. Please verify your email address by clicking the button below:</p>
            <a href="{verification_url}" class="button">Verify Email</a>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <div class="footer">
                <p>If you didn't create an account, please ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Welcome to Price Tracker Pro!
    
    Thank you for signing up. Please verify your email address by visiting:
    {verification_url}
    
    This link will expire in 24 hours.
    
    If you didn't create an account, please ignore this email.
    """
    
    return send_email(email, subject, html_content, text_content)


def send_price_alert_email(
    email: str,
    product_name: str,
    old_price: Decimal,
    new_price: Decimal,
    price_difference: Decimal,
    price_difference_percent: Decimal,
    product_url: str
) -> bool:
    """
    Send price drop alert email
    """
    savings = float(price_difference)
    discount = float(price_difference_percent)
    
    subject = f"💰 Price Drop Alert: {product_name} - {discount:.1f}% OFF!"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .alert-box {{ background-color: #d4edda; border: 1px solid #c3e6cb; 
                         border-radius: 5px; padding: 20px; margin: 20px 0; }}
            .price {{ font-size: 24px; font-weight: bold; color: #28a745; }}
            .old-price {{ text-decoration: line-through; color: #666; }}
            .savings {{ font-size: 18px; color: #28a745; font-weight: bold; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; 
                      color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 Price Drop Alert!</h1>
            <div class="alert-box">
                <h2>{product_name}</h2>
                <p class="old-price">Old Price: ₹{old_price:,.2f}</p>
                <p class="price">New Price: ₹{new_price:,.2f}</p>
                <p class="savings">You Save: ₹{savings:,.2f} ({discount:.1f}% OFF)</p>
            </div>
            <a href="{product_url}" class="button">View Product</a>
            <p>Don't miss out on this great deal!</p>
            <div class="footer">
                <p>This is an automated alert from Price Tracker Pro.</p>
                <p>You can manage your alerts in your dashboard.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Price Drop Alert!
    
    {product_name}
    
    Old Price: ₹{old_price:,.2f}
    New Price: ₹{new_price:,.2f}
    You Save: ₹{savings:,.2f} ({discount:.1f}% OFF)
    
    View Product: {product_url}
    
    Don't miss out on this great deal!
    
    This is an automated alert from Price Tracker Pro.
    """
    
    return send_email(email, subject, html_content, text_content)


def send_password_reset_email(email: str, reset_token: str) -> bool:
    """
    Send password reset email
    """
    reset_url = f"https://your-domain.com/reset-password?token={reset_token}"
    
    subject = "Reset Your Password - Price Tracker Pro"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; 
                      color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .warning {{ background-color: #fff3cd; border: 1px solid #ffc107; 
                       border-radius: 5px; padding: 15px; margin: 20px 0; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Password Reset Request</h1>
            <p>You requested to reset your password. Click the button below to create a new password:</p>
            <a href="{reset_url}" class="button">Reset Password</a>
            <p>Or copy and paste this link into your browser:</p>
            <p>{reset_url}</p>
            <div class="warning">
                <p><strong>Important:</strong> This link will expire in 1 hour.</p>
                <p>If you didn't request a password reset, please ignore this email or contact support.</p>
            </div>
            <div class="footer">
                <p>Price Tracker Pro Security Team</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Password Reset Request
    
    You requested to reset your password. Visit this link to create a new password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request a password reset, please ignore this email or contact support.
    """
    
    return send_email(email, subject, html_content, text_content)


def send_welcome_email(email: str, user_name: str) -> bool:
    """
    Send welcome email to new users
    """
    subject = "Welcome to Price Tracker Pro! 🎉"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; 
                      color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to Price Tracker Pro, {user_name}!</h1>
            <p>We're excited to help you save money by tracking product prices.</p>
            <h2>Getting Started:</h2>
            <ol>
                <li>Add products you want to track</li>
                <li>Set your target prices</li>
                <li>Get notified when prices drop!</li>
            </ol>
            <a href="https://your-domain.com/dashboard" class="button">Go to Dashboard</a>
            <p>Happy tracking! 🛒</p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Welcome to Price Tracker Pro, {user_name}!
    
    We're excited to help you save money by tracking product prices.
    
    Getting Started:
    1. Add products you want to track
    2. Set your target prices
    3. Get notified when prices drop!
    
    Visit your dashboard: https://your-domain.com/dashboard
    
    Happy tracking!
    """
    
    return send_email(email, subject, html_content, text_content)


def send_invoice_email(email: str, invoice_data: dict) -> bool:
    """
    Send invoice/receipt email
    """
    subject = f"Invoice #{invoice_data.get('invoice_number', 'N/A')} - Price Tracker Pro"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .invoice-box {{ border: 1px solid #ddd; border-radius: 5px; padding: 20px; margin: 20px 0; }}
            .amount {{ font-size: 24px; font-weight: bold; color: #28a745; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Payment Receipt</h1>
            <div class="invoice-box">
                <p><strong>Invoice #:</strong> {invoice_data.get('invoice_number', 'N/A')}</p>
                <p><strong>Plan:</strong> {invoice_data.get('plan_name', 'N/A')}</p>
                <p><strong>Amount:</strong> <span class="amount">₹{invoice_data.get('amount', 0):,.2f}</span></p>
                <p><strong>Date:</strong> {invoice_data.get('date', 'N/A')}</p>
                <p><strong>Status:</strong> {invoice_data.get('status', 'N/A')}</p>
            </div>
            <p>Thank you for your subscription!</p>
            <p>You can view all your invoices in your dashboard.</p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Payment Receipt
    
    Invoice #: {invoice_data.get('invoice_number', 'N/A')}
    Plan: {invoice_data.get('plan_name', 'N/A')}
    Amount: ₹{invoice_data.get('amount', 0):,.2f}
    Date: {invoice_data.get('date', 'N/A')}
    Status: {invoice_data.get('status', 'N/A')}
    
    Thank you for your subscription!
    """
    
    return send_email(email, subject, html_content, text_content)
