"""
Handwritten models containing only the relevant tables and using Oracle dialect types.

Note: SQLAlchemy requires all tables with PK, but sometimes they are not in the database. These are marked with comments.
"""
from typing import Any, Dict

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.oracle import BLOB, DATE, NUMBER, VARCHAR2
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()
metadata = Base.metadata


class ModelBase:
    def dict(self) -> Dict[str, Any]:
        return {k: v for k, v in sorted(self.__dict__.items()) if not k.startswith("_")}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self.dict()}"


class Boat(Base, ModelBase):
    __tablename__ = "boats"

    boat_id = Column(NUMBER(3, 0), nullable=False, primary_key=True)
    name = Column(VARCHAR2(20), nullable=False, unique=True)
    type = Column(VARCHAR2(20), nullable=False)
    ycc_num = Column(NUMBER(3, 0), nullable=False, unique=True)
    license = Column(VARCHAR2(5), nullable=False)
    class_ = Column("class", VARCHAR2(5), nullable=False)
    table_pos = Column(NUMBER(3, 0), nullable=False, unique=True)
    # Maintainer and maintainer2 are used for sending e-mails to maintainers, e.g., upon Warning/Out of order log entries
    maintainer_id = Column(NUMBER, ForeignKey("members.id"))
    ext_reg_cat = Column(VARCHAR2(2))
    maintainer_id2 = Column(NUMBER, ForeignKey("members.id"))
    registration_pdf = Column(BLOB)

    # TODO This should be many to many when away from Perl
    maintainer1 = relationship(
        "Member",
        back_populates="maintained_boats1",
        foreign_keys=maintainer_id,
        lazy="joined",
    )
    maintainer2 = relationship(
        "Member",
        back_populates="maintained_boats2",
        foreign_keys=maintainer_id2,
        lazy="joined",
    )

    def json_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "number": self.ycc_num,
            "license": self.license,
            "class": self.class_,
            "tablePosition": self.table_pos,
            "maintainer1": self.maintainer1.json_dict() if self.maintainer1 else None,
            "maintainer2": self.maintainer2.json_dict() if self.maintainer2 else None,
        }


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
    gender = Column(VARCHAR2(2))
    valid_until_date = Column(DATE)
    last_updated_date = Column(DATE)
    valid_from_date = Column(DATE)
    interest_in_fibreglass = Column(NUMBER(1, 0))
    interest_in_woodwork = Column(NUMBER(1, 0))
    interest_in_ropework = Column(NUMBER(1, 0))
    interest_in_paintwork = Column(NUMBER(1, 0))
    interest_in_motors = Column(NUMBER(1, 0))
    interest_in_organising_social = Column(NUMBER(1, 0))
    interest_in_organising_regattas = Column(NUMBER(1, 0))
    interest_in_teaching_dinghies = Column(NUMBER(1, 0))
    interest_in_teaching_cats = Column(NUMBER(1, 0))
    interest_in_teaching_keelboats = Column(NUMBER(1, 0))
    interest_in_teaching_motorboats = Column(NUMBER(1, 0))
    interest_in_surveillance = Column(NUMBER(1, 0))
    interest_in_towing_on_land = Column(NUMBER(1, 0))
    special_talents = Column(VARCHAR2(1000))

    user = relationship("User", back_populates="member", uselist=False)
    # TODO This should be many to many when away from Perl
    maintained_boats1 = relationship(
        "Boat", back_populates="maintainer1", foreign_keys="Boat.maintainer_id"
    )
    maintained_boats2 = relationship(
        "Boat", back_populates="maintainer2", foreign_keys="Boat.maintainer_id2"
    )

    def json_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.user.logon_id,
            "firstName": self.firstname,
            "lastName": self.name,
            "membershipType": self.membership,
        }


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
            "descriptionEn": self.e_desc,
            "descriptionFr": self.f_desc,
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
