from abc import ABC, abstractmethod
from typing import Optional


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


# Future implementations can include:
# - SMTPEmailSender for traditional SMTP
# - SendGridEmailSender for SendGrid API
# - SESEmailSender for AWS SES
# etc.
