"Email support."

from email.message import EmailMessage
from email.utils import formataddr
from typing import Iterable, Union, overload

from pydantic import BaseModel

from ycc_hull.config import CONFIG
from ycc_hull.controllers.notifications.email_content_utils import (
    SHIFT_REPLACEMENT_REMINDER,
    YCC_APP_SIGNATURE,
    wrap_email_html,
)
from ycc_hull.models.dtos import MemberPublicInfoDto


class EmailMessageBuilder:
    """Type-safe builder for email.message.EmailMessage."""

    def __init__(
        self,
    ):
        self._from: str | None = None
        self._to: list[str] = []
        self._cc: list[str] = []
        self._reply_to: str | None = None
        self._subject: str | None = None
        self._content: str | None = None

    def _extract_address(self, *args: str | MemberPublicInfoDto) -> str:
        if len(args) == 1 and isinstance(args[0], MemberPublicInfoDto):
            return formataddr((args[0].full_name, args[0].email))
        elif len(args) == 2 and all(isinstance(arg, str) for arg in args):
            return formataddr((args[0], args[1]))
        else:
            raise TypeError(
                f"Expected (name, email) or (MemberPublicInfoDto,), got {args}"
            )

    def _add_recipients(
        self,
        target_list: list,
        *args: str | MemberPublicInfoDto | Iterable[MemberPublicInfoDto] | None,
    ) -> None:
        if len(args) == 1 and args[0] is None:
            return

        if (
            len(args) == 1
            and isinstance(args[0], Iterable)
            and not isinstance(args[0], (str, bytes, BaseModel))
        ):
            target_list.extend(self._extract_address(member) for member in args[0])
        else:
            target_list.append(self._extract_address(*args))

    @overload
    def from_(self, name: str, email: str) -> "EmailMessageBuilder": ...

    @overload
    def from_(self, member: MemberPublicInfoDto) -> "EmailMessageBuilder": ...

    def from_(self, *args: str | MemberPublicInfoDto) -> "EmailMessageBuilder":
        self._from = self._extract_address(*args)
        return self

    @overload
    def to(self, name: str, email: str) -> "EmailMessageBuilder": ...

    @overload
    def to(self, member: MemberPublicInfoDto) -> "EmailMessageBuilder": ...

    def to(
        self, *args: str | MemberPublicInfoDto | Iterable[MemberPublicInfoDto] | None
    ) -> "EmailMessageBuilder":
        self._add_recipients(self._to, *args)
        return self

    @overload
    def cc(self, name: str, email: str) -> "EmailMessageBuilder": ...
    @overload
    def cc(self, member: MemberPublicInfoDto | None) -> "EmailMessageBuilder": ...
    @overload
    def cc(self, members: Iterable[MemberPublicInfoDto]) -> "EmailMessageBuilder": ...

    def cc(
        self, *args: str | MemberPublicInfoDto | Iterable[MemberPublicInfoDto] | None
    ) -> "EmailMessageBuilder":
        self._add_recipients(self._cc, *args)
        return self

    @overload
    def reply_to(self, name: str, email: str) -> "EmailMessageBuilder": ...

    @overload
    def reply_to(self, member: MemberPublicInfoDto) -> "EmailMessageBuilder": ...

    def reply_to(self, *args: str | MemberPublicInfoDto) -> "EmailMessageBuilder":
        self._reply_to = self._extract_address(*args)
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
                raise RuntimeError(
                    "Sender is not set and email configuration is not specified"
                )
            self.from_(CONFIG.ycc_app.name, CONFIG.email.from_email)
        if not self._to:
            raise RuntimeError("Recipient is not set")
        if not self._subject:
            raise RuntimeError("Subject is not set")
        if not self._content:
            raise RuntimeError("Content is not set")

        message = EmailMessage()
        message["From"] = self._from
        message["To"] = ", ".join(self._to)

        if self._cc:
            # Remove from CC what is in TO
            self._cc = [cc for cc in self._cc if cc not in self._to]
            message["Cc"] = ", ".join(self._cc)
        if self._reply_to:
            message["Reply-To"] = self._reply_to

        message["Subject"] = self._subject

        message.set_content(
            wrap_email_html(
                f"""
{self._content}

{SHIFT_REPLACEMENT_REMINDER}
{YCC_APP_SIGNATURE}
"""
            ),
            subtype="html",
        )

        return message
