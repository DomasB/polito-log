from abc import ABC, abstractmethod
from typing import Optional
import logging
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

logger = logging.getLogger(__name__)


class EmailSender(ABC):
    """Abstract base class for email sending implementations."""

    @abstractmethod
    async def send_magic_link(
        self,
        to_email: str,
        magic_link: str,
        username: Optional[str] = None
    ) -> bool:
        """
        Send a magic link authentication email.

        Args:
            to_email: Recipient email address
            magic_link: The full magic link URL
            username: Optional username for personalization

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        pass


class ConsoleEmailSender(EmailSender):
    """
    Development email sender that prints to console.
    Use this for development and testing.
    """

    async def send_magic_link(
        self,
        to_email: str,
        magic_link: str,
        username: Optional[str] = None
    ) -> bool:
        """Print magic link to console for development."""
        print("\n" + "=" * 80)
        print("MAGIC LINK EMAIL (Development Mode)")
        print("=" * 80)
        print(f"To: {to_email}")
        if username:
            print(f"Username: {username}")
        print(f"\nMagic Link: {magic_link}")
        print("\nClick the link above to log in.")
        print("=" * 80 + "\n")
        return True


class BrevoEmailSender(EmailSender):
    """
    Production email sender using Brevo (formerly Sendinblue) Transactional API.
    Use this for production environments.

    Requires BREVO_API_KEY to be set in environment variables.
    """

    def __init__(
        self,
        api_key: str,
        sender_email: str,
        sender_name: str = "Polito-Log"
    ):
        """
        Initialize Brevo email sender.

        Args:
            api_key: Brevo API key (should be stored in Railway secrets)
            sender_email: Sender email address
            sender_name: Sender name for the email
        """
        self.sender_email = sender_email
        self.sender_name = sender_name

        # Configure Brevo API client
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = api_key
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

    async def send_magic_link(
        self,
        to_email: str,
        magic_link: str,
        username: Optional[str] = None
    ) -> bool:
        """
        Send a magic link authentication email via Brevo.

        Args:
            to_email: Recipient email address
            magic_link: The full magic link URL
            username: Optional username for personalization

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Prepare email content
            greeting = f"Hello {username}," if username else "Hello,"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .button {{
                        display: inline-block;
                        padding: 12px 24px;
                        background-color: #4CAF50;
                        color: white !important;
                        text-decoration: none;
                        border-radius: 4px;
                        margin: 20px 0;
                    }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Login to Polito-Log</h2>
                    <p>{greeting}</p>
                    <p>Click the button below to securely log in to your Polito-Log account:</p>
                    <a href="{magic_link}" class="button">Log In</a>
                    <p>Or copy and paste this link into your browser:</p>
                    <p><a href="{magic_link}">{magic_link}</a></p>
                    <p>This link will expire in 15 minutes for security reasons.</p>
                    <div class="footer">
                        <p>If you didn't request this login link, you can safely ignore this email.</p>
                        <p>&copy; Polito-Log - Tracking Political Accountability</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_content = f"""
            {greeting}

            Click the link below to securely log in to your Polito-Log account:

            {magic_link}

            This link will expire in 15 minutes for security reasons.

            If you didn't request this login link, you can safely ignore this email.

            © Polito-Log - Tracking Political Accountability
            """

            # Create email object
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email}],
                sender={"email": self.sender_email, "name": self.sender_name},
                subject="Your Polito-Log Login Link",
                html_content=html_content,
                text_content=text_content,
            )

            # Send the email
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            logger.info(f"Magic link email sent successfully to {to_email}. Message ID: {api_response.message_id}")
            return True

        except ApiException as e:
            logger.error(f"Brevo API error sending email to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {e}")
            return False


def get_email_sender() -> EmailSender:
    """
    Factory function to get the appropriate email sender based on environment.

    Returns:
        EmailSender: ConsoleEmailSender for development, BrevoEmailSender for production

    Usage:
        from app.core.email import get_email_sender

        email_sender = get_email_sender()
        await email_sender.send_magic_link(to_email="user@example.com", magic_link="https://...")
    """
    from app.config import settings

    # Use Brevo in production if API key is configured
    if settings.ENVIRONMENT == "production" and settings.BREVO_API_KEY:
        logger.info("Using BrevoEmailSender for production email delivery")
        return BrevoEmailSender(
            api_key=settings.BREVO_API_KEY,
            sender_email=settings.BREVO_SENDER_EMAIL,
            sender_name=settings.BREVO_SENDER_NAME
        )

    # Use console sender for development or when Brevo is not configured
    logger.info("Using ConsoleEmailSender for development email delivery")
    return ConsoleEmailSender()


# Future implementations can include:
# - SMTPEmailSender for traditional SMTP
# - SendGridEmailSender for SendGrid API
# - SESEmailSender for AWS SES
# etc.
