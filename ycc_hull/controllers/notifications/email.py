"Email support."
from email.message import EmailMessage
from email.utils import formataddr

from ycc_hull.config import CONFIG


class EmailMessageBuilder:
    """Type-safe builder for email.message.EmailMessage."""

    def __init__(
        self,
    ):
        self._from: str | None = None
        self._to: list[str] = []
        self._cc: list[str] = []
        self._bcc: list[str] = []
        self._reply_to: str | None = None
        self._subject: str | None = None
        self._content: str | None = None

    def from_(self, name: str, email: str) -> "EmailMessageBuilder":
        self._from = formataddr((name, email))
        return self

    def to(self, name: str, email: str) -> "EmailMessageBuilder":
        self._to.append(formataddr((name, email)))
        return self

    def cc(self, name: str, email: str) -> "EmailMessageBuilder":
        self._cc.append(formataddr((name, email)))
        return self

    def bcc(self, name: str, email: str) -> "EmailMessageBuilder":
        self._bcc.append(formataddr((name, email)))
        return self

    def reply_to(self, name: str, email: str) -> "EmailMessageBuilder":
        self._reply_to = formataddr((name, email))
        return self

    def subject(self, subject: str) -> "EmailMessageBuilder":
        self._subject = subject
        return self

    def content(self, content: str) -> "EmailMessageBuilder":
        self._content = content
        return self

    def build(self) -> EmailMessage:
        if not self._from:
            if not CONFIG.email:
                raise ValueError(
                    "Sender is not set and email configuration is not specified"
                )
            self.from_(CONFIG.email.from_name, CONFIG.email.from_email)
        if not self._to:
            raise ValueError("Recipient is not set")
        if not self._subject:
            raise ValueError("Subject is not set")
        if not self._content:
            raise ValueError("Content is not set")

        message = EmailMessage()
        message["From"] = self._from
        message["To"] = ", ".join(self._to)

        if self._cc:
            message["Cc"] = ", ".join(self._cc)
        if self._bcc:
            message["Bcc"] = ", ".join(self._bcc)
        if self._reply_to:
            message["Reply-To"] = self._reply_to

        message["Subject"] = self._subject
        message.set_content(
            self._content,
            subtype="html",
        )

        return message
