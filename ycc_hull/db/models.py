"""
Handwritten models containing only the relevant tables and using Oracle dialect types.

Note: SQLAlchemy requires all tables with PK, but sometimes they are not in the database. These are marked with comments.
"""
from typing import Any, Dict

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.oracle import CHAR, DATE, NUMBER, VARCHAR2
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()
metadata = Base.metadata


class ModelBase:
    def dict(self) -> Dict[str, Any]:
        return {k: v for k, v in sorted(self.__dict__.items()) if not k.startswith("_")}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self.dict()}"


class Holiday(Base, ModelBase):
    __tablename__ = "holidays"

    day = Column(
        DATE,
        nullable=False,
        # Code only primary key, not in DB
        primary_key=True,
    )
    label = Column(VARCHAR2(20), nullable=False)

    def json_dict(self) -> dict:
        return {
            "date": self.day.date().isoformat(),  # Oracle DATE = datetime, but here not needed
            "label": self.label,
        }


class Member(Base, ModelBase):
    __tablename__ = "members"

    id = Column(NUMBER, nullable=False, primary_key=True)
    name = Column(VARCHAR2(25), nullable=False)
    firstname = Column(VARCHAR2(25), nullable=False)
    birthday = Column(DATE)
    nationality = Column(VARCHAR2(3))
    membership = Column(VARCHAR2(2), nullable=False)
    temp_memb = Column(NUMBER(1, 0))
    lang1 = Column(VARCHAR2(3))
    lang2 = Column(VARCHAR2(3))
    category = Column(VARCHAR2(1))
    work_address1 = Column(VARCHAR2(50))
    work_address2 = Column(VARCHAR2(50))
    work_towncode = Column(VARCHAR2(7))
    work_town = Column(VARCHAR2(25))
    work_state = Column(VARCHAR2(5))
    work_phone = Column(VARCHAR2(25))
    e_mail = Column(VARCHAR2(50))
    home_addr = Column(VARCHAR2(50), nullable=False)
    home_towncode = Column(VARCHAR2(7))
    home_town = Column(VARCHAR2(25))
    home_state = Column(VARCHAR2(5))
    home_phone = Column(VARCHAR2(25))
    mail_preference = Column(VARCHAR2(1))
    favourite_mailing_post = Column(VARCHAR2(1))
    member_entrance = Column(VARCHAR2(4), nullable=False)
    cell_phone = Column(VARCHAR2(25))
    gender = Column(CHAR(1))
    valid_until_date = Column(DATE)
    last_updated_date = Column(DATE)
    valid_from_date = Column(DATE)

    def json_dict(self) -> dict:
        return {
            "id": self.id,
            "first_name": self.firstname,
            "last_name": self.name,
            "membership_type": self.membership,
        }

    user = relationship("User", back_populates="member", uselist=False)


class MembershipType(Base, ModelBase):
    __tablename__ = "membership"

    mb_id = Column(
        NUMBER(2, 0),
        nullable=False,
        # Code only primary key, not in DB
        primary_key=True,
    )
    mb_name = Column(
        VARCHAR2(2),
        nullable=False,
        # Code only unique key, not in DB
        unique=True,
    )
    e_desc = Column(VARCHAR2(20), nullable=False)
    f_desc = Column(VARCHAR2(20), nullable=False)
    comments = Column(VARCHAR2(100))

    def json_dict(self) -> dict:
        return {
            "id": self.mb_id,
            "name": self.mb_name,
            "description_en": self.e_desc,
            "description_fr": self.f_desc,
            "comments": self.comments,
        }


class User(Base, ModelBase):
    __tablename__ = "web_logon"

    member_id = Column(
        NUMBER, ForeignKey("members.id"), nullable=False, primary_key=True
    )
    logon_id = Column(VARCHAR2(25), nullable=False, unique=True)
    session_id = Column(NUMBER)
    session_date = Column(DATE)
    logon_pass2 = Column(VARCHAR2(128))
    pass_reset_key = Column(VARCHAR2(128))
    pass_reset_exp = Column(DATE)
    last_changed = Column(DATE)

    member = relationship("Member", back_populates="user")

    def json_dict(self) -> dict:
        return {
            "id": self.member_id,
            "username": self.logon_id,
            # Ignore sensitive info
        }
