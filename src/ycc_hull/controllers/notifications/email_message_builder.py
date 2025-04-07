from email.message import EmailMessage
from email.utils import formataddr
from typing import Iterable

from pydantic import BaseModel

from ycc_hull.config import CONFIG
from ycc_hull.controllers.notifications.format_utils import (
    wrap_email_html,
)
from ycc_hull.models.dtos import MemberPublicInfoDto
from ycc_hull.models.user import User

# Email contact:
#
# - string: "alice@example.com", "Alice <alice@example.com>"
# - MemberPublicInfoDto, User: object with email and full_name
EmailContact = str | MemberPublicInfoDto | User
EmailContacts = EmailContact | Iterable[EmailContact | None]


class EmailMessageBuilder:
    """
    Type-safe builder for email.message.EmailMessage.

    build(...) wraps the main content with the rest of the HTML code and text.
    """

    def __init__(
        self,
    ) -> None:
        self._from: str | None = None
        self._to: set[str] = set()
        self._cc: set[str] = set()
        self._reply_to: str | None = None
        self._subject: str | None = None
        self._content: str | None = None

    def _extract_address(self, recipient: EmailContact) -> str:
        if isinstance(recipient, str):
            return recipient
        elif isinstance(recipient, (MemberPublicInfoDto, User)):
            return formataddr((recipient.full_name, recipient.email))
        else:
            raise TypeError(
                f"Expected string, MemberPublicInfoDto or User, got {recipient}"
            )

    def _add_contacts(
        self, target_set: set[str], contact: EmailContacts | None
    ) -> None:
        if not contact:
            return

        if isinstance(contact, Iterable) and not isinstance(
            contact, (bytes, str, BaseModel)
        ):
            target_set.update(
                self._extract_address(recipient) for recipient in contact if recipient
            )
        else:
            target_set.add(self._extract_address(contact))

    def from_(self, contact: EmailContact) -> "EmailMessageBuilder":
        self._from = self._extract_address(contact)
        return self

    def to(
        self, contacts: EmailContact | EmailContacts | None
    ) -> "EmailMessageBuilder":
        self._add_contacts(self._to, contacts)
        return self

    def cc(
        self, contacts: EmailContact | EmailContacts | None
    ) -> "EmailMessageBuilder":
        self._add_contacts(self._cc, contacts)
        return self

    def reply_to(self, contact: EmailContact) -> "EmailMessageBuilder":
        self._reply_to = self._extract_address(contact)
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
                    "Email configuration is not set, cannot determine default FROM address"
                )
            self.from_(formataddr((CONFIG.ycc_app.name, CONFIG.email.from_email)))
        if not self._to:
            raise RuntimeError("Recipient (TO) is not set")
        if not self._subject:
            raise RuntimeError("Subject is not set")
        if not self._content:
            raise RuntimeError("Content is not set")

        message = EmailMessage()
        message["From"] = self._from
        message["To"] = ", ".join(self._to)

        self._cc.difference_update(self._to)
        if self._cc:
            message["Cc"] = ", ".join(self._cc)
        if self._reply_to:
            message["Reply-To"] = self._reply_to

        message["Subject"] = self._subject

        message.set_content(wrap_email_html(self._content), subtype="html")

        return message
