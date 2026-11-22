import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode, urlsplit, urlunsplit

from pydantic import SecretStr


class VerificationDeliveryError(Exception):
    """The verification email could not be delivered to the SMTP server."""


class SmtpVerificationSender:
    def __init__(
        self, *, host: str, port: int, sender: str, verification_page: str,
        username: str | None = None, password: SecretStr | None = None,
        tls_context: ssl.SSLContext | None = None, starttls: bool = False,
    ):
        page = urlsplit(verification_page)
        if page.scheme != "https" or not page.hostname or page.username or page.fragment:
            raise ValueError("Use an HTTPS verification page without credentials or a fragment")
        if (username is None) != (password is None):
            raise ValueError("Configure both SMTP username and password")
        self._host = host
        self._port = port
        self._sender = sender
        self._page = page
        self._username = username
        self._password = password
        self._tls_context = tls_context
        self._starttls = starttls

    async def send(self, recipient: str, token: SecretStr) -> None:
        link = urlunsplit(self._page._replace(
            fragment=urlencode({"token": token.get_secret_value()})
        ))
        message = EmailMessage()
        message["Subject"] = "Verifica tu correo en GlucoVida"
        message["From"] = self._sender
        message["To"] = recipient
        message.set_content(f"Abre este enlace para verificar tu correo de GlucoVida:\n\n{link}\n")
        try:
            await asyncio.to_thread(self._send, message)
        except (OSError, smtplib.SMTPException):
            raise VerificationDeliveryError("Could not send verification email") from None

    def _send(self, message: EmailMessage) -> None:
        context = self._tls_context or ssl.create_default_context()
        if self._starttls:
            with smtplib.SMTP(self._host, self._port, timeout=10) as client:
                client.starttls(context=context)
                self._deliver(client, message)
        else:
            with smtplib.SMTP_SSL(self._host, self._port, timeout=10, context=context) as client:
                self._deliver(client, message)

    def _deliver(self, client: smtplib.SMTP, message: EmailMessage) -> None:
        if self._username is not None and self._password is not None:
            client.login(self._username, self._password.get_secret_value())
        client.send_message(message)
