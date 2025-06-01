import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from app.core.models import NewsletterSubscription

class EmailService:
    """Service for handling email operations."""
    
    @classmethod
    def _get_smtp_config(cls):
        """Get SMTP configuration from app config."""
        return {
            'server': current_app.config.get('SMTP_SERVER'),
            'port': current_app.config.get('SMTP_PORT', 587),
            'username': current_app.config.get('SMTP_USERNAME'),
            'password': current_app.config.get('SMTP_PASSWORD'),
            'use_tls': current_app.config.get('SMTP_USE_TLS', True)
        }
    
    @classmethod
    def send_email(cls, to_email, subject, body, html_body=None):
        """
        Send an email to a single recipient.
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Plain text body
            html_body (str): Optional HTML body
            
        Returns:
            dict: Result with success status and message
        """
        try:
            smtp_config = cls._get_smtp_config()
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_config['username']
            msg['To'] = to_email
            
            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                if smtp_config['use_tls']:
                    server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)
            
            return {
                'success': True,
                'message': f'Email sent successfully to {to_email}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to send email: {str(e)}'
            }
    
    @classmethod
    def send_newsletter(cls, subject, content):
        """
        Send newsletter to all subscribers.
        
        Args:
            subject (str): Newsletter subject
            content (str): Newsletter content (can include HTML)
            
        Returns:
            dict: Result with success status and count of emails sent
        """
        try:
            # Get all newsletter subscribers
            subscribers = NewsletterSubscription.get_all()
            
            if not subscribers:
                return {
                    'success': True,
                    'sent_count': 0,
                    'message': 'No subscribers found'
                }
            
            sent_count = 0
            failed_count = 0
            
            smtp_config = cls._get_smtp_config()
            
            # Create HTML template for newsletter
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
                    .header {{ background-color: #3498db; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; line-height: 1.6; }}
                    .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>ZapRead Newsletter</h1>
                </div>
                <div class="content">
                    {content}
                </div>
                <div class="footer">
                    <p>This email was sent to you because you subscribed to ZapRead newsletters.</p>
                    <p>If you no longer wish to receive these emails, please contact us.</p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            plain_body = f"ZapRead Newsletter\n\n{content}\n\nThis email was sent to you because you subscribed to ZapRead newsletters."
            
            # Send emails in batches to avoid overwhelming SMTP server
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                if smtp_config['use_tls']:
                    server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                
                for subscriber in subscribers:
                    try:
                        email = subscriber.get('email')
                        if not email:
                            continue
                        
                        # Create message for this subscriber
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = subject
                        msg['From'] = smtp_config['username']
                        msg['To'] = email
                        
                        # Add both plain text and HTML versions
                        text_part = MIMEText(plain_body, 'plain')
                        html_part = MIMEText(html_body, 'html')
                        
                        msg.attach(text_part)
                        msg.attach(html_part)
                        
                        # Send the email
                        server.send_message(msg)
                        sent_count += 1
                        
                    except Exception as e:
                        print(f"Failed to send newsletter to {email}: {str(e)}")
                        failed_count += 1
                        continue
            
            return {
                'success': True,
                'sent_count': sent_count,
                'failed_count': failed_count,
                'message': f'Newsletter sent to {sent_count} subscribers'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Newsletter sending failed: {str(e)}'
            }
    
    @classmethod
    def send_verification_email(cls, to_email, verification_link):
        """
        Send email verification link to user.
        
        Args:
            to_email (str): User's email address
            verification_link (str): Verification URL
            
        Returns:
            dict: Result with success status
        """
        subject = "Verify your ZapRead account"
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
                .header {{ background-color: #3498db; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; line-height: 1.6; }}
                .button {{ background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Welcome to ZapRead!</h1>
            </div>
            <div class="content">
                <p>Thank you for registering with ZapRead. Please click the button below to verify your email address:</p>
                <p style="text-align: center;">
                    <a href="{verification_link}" class="button">Verify Email Address</a>
                </p>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p>{verification_link}</p>
                <p>This link will expire in 24 hours.</p>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""
        Welcome to ZapRead!
        
        Thank you for registering with ZapRead. Please click the link below to verify your email address:
        
        {verification_link}
        
        This link will expire in 24 hours.
        """
        
        return cls.send_email(to_email, subject, plain_body, html_body) 