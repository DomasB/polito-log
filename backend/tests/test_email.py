import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from brevo.core.api_error import ApiError

from app.core.email import BrevoEmailSender


def make_sender(send: AsyncMock) -> BrevoEmailSender:
    client = MagicMock()
    client.transactional_emails.send_transac_email = send
    with patch("brevo.AsyncBrevo", return_value=client) as brevo_cls:
        sender = BrevoEmailSender(api_key="key", sender_email="from@example.com", sender_name="Sender")
    brevo_cls.assert_called_once_with(api_key="key")
    return sender


def test_brevo_sends_magic_link():
    send = AsyncMock(return_value=MagicMock(message_id="<msg-1>"))
    sender = make_sender(send)

    sent = asyncio.run(sender.send_magic_link("to@example.com", "https://x/verify?t=abc", "alice"))

    assert sent is True
    kwargs = send.await_args.kwargs
    assert [item.email for item in kwargs["to"]] == ["to@example.com"]
    assert kwargs["sender"].email == "from@example.com"
    assert kwargs["sender"].name == "Sender"
    assert kwargs["subject"] == "Your Polito-Log Login Link"
    assert "https://x/verify?t=abc" in kwargs["html_content"]
    assert "https://x/verify?t=abc" in kwargs["text_content"]
    assert "Hello alice," in kwargs["text_content"]


def test_brevo_api_error_returns_false():
    send = AsyncMock(side_effect=ApiError(status_code=401, body="unauthorized"))
    sender = make_sender(send)

    assert asyncio.run(sender.send_magic_link("to@example.com", "https://x")) is False
