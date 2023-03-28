"""
Handwritten models containing only the relevant tables and using Oracle dialect types.

Note: SQLAlchemy requires all tables with PK, but sometimes they are not in the database. These are marked with comments.
"""
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import ForeignKey, Index, PrimaryKeyConstraint, text
from sqlalchemy.dialects.oracle import BLOB, DATE, NUMBER, VARCHAR2
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Base class for DB model types.
    """

    def dict(self) -> Dict[str, Any]:
        return {k: v for k, v in sorted(self.__dict__.items()) if not k.startswith("_")}

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}{self.dict()}"


class Boat(Base):
    """
    Represents a boat.
    """

    __tablename__ = "boats"

    boat_id: Mapped[int] = mapped_column(NUMBER(3, 0), nullable=False, primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR2(20), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(VARCHAR2(20), nullable=False)
    ycc_num: Mapped[int] = mapped_column(NUMBER(3, 0), nullable=False, unique=True)
    license: Mapped[str] = mapped_column(VARCHAR2(5), nullable=False)
    class_: Mapped[str] = mapped_column("class", VARCHAR2(5), nullable=False)
    table_pos: Mapped[int] = mapped_column(NUMBER(3, 0), nullable=False, unique=True)
    # Maintainer and maintainer2 are used for sending e-mails to maintainers, e.g., upon Warning/Out of order log entries
    maintainer_id: Mapped[int] = mapped_column(NUMBER, ForeignKey("members.id"))
    ext_reg_cat: Mapped[str] = mapped_column(VARCHAR2(2))
    maintainer_id2: Mapped[int] = mapped_column(NUMBER, ForeignKey("members.id"))
    registration_pdf: Mapped[Any] = mapped_column(BLOB)

    # This could be many to many when away from Perl (and maybe APEX too)
    maintainer1: Mapped["Member"] = relationship(
        back_populates="maintained_boats1", foreign_keys=maintainer_id
    )
    maintainer2: Mapped["Member"] = relationship(
        back_populates="maintained_boats2", foreign_keys=maintainer_id2
    )


class EntranceFeeRecord(Base):
    """
    Represents an entrance fee record paid by a new member.
    """

    __tablename__ = "entrance_feesrecords"
    __table_args__ = (Index("entrance_fee_uq", "member_id", "year_f", unique=True),)

    # Code-only foreign key, not in DB
    member_id: Mapped[int] = mapped_column(
        NUMBER, ForeignKey("members.id"), nullable=False, primary_key=True
    )
    """
    This field is nullable, however, it is only null for some members who joined 2010 or before. (Lajos, 2023-03)

    SELECT
        '' as "-- MEMBERS --",
        m.NAME,
        m.FIRSTNAME,
        m.MEMBER_ENTRANCE,
        '' as "-- ENTRANCE_FEESRECORDS --",
        efr.*
    FROM ENTRANCE_FEESRECORDS efr
    LEFT OUTER JOIN MEMBERS m ON efr.MEMBER_ID = m.ID
    WHERE efr.YEAR_F IS NULL
    ORDER BY m.MEMBER_ENTRANCE DESC, m.NAME ASC;
    """
    year_f: Mapped[int] = mapped_column(NUMBER(4, 0), nullable=True)


class FeeRecord(Base):
    """
    Represents a fee record paid by a member (membership fee, course fee, etc.).
    """

    # Note: FEESRECORDS_TRG trigger may fill entered_date and paymentid
    __tablename__ = "feesrecords"
    __table_args__ = (
        # Code-only primary key, not in DB
        PrimaryKeyConstraint(
            "member_id",
            "year_f",
            "paid_date",
            "paid_mode",
            "fee",
            "entered_date",
            "paymentid",
        ),
    )

    # Code-only foreign key, not in DB
    member_id: Mapped[int] = mapped_column(
        NUMBER, ForeignKey("members.id"), nullable=False
    )
    year_f: Mapped[int] = mapped_column(NUMBER(4, 0), nullable=False)
    paid_date: Mapped[datetime] = mapped_column(DATE)
    paid_mode: Mapped[str] = mapped_column(VARCHAR2(4))
    fee: Mapped[int] = mapped_column(NUMBER(3, 0), nullable=False)
    entered_date: Mapped[datetime] = mapped_column(DATE, server_default=text("sysdate"))
    paymentid: Mapped[int] = mapped_column(NUMBER)


class Holiday(Base):
    """
    Represents a holiday. Holidays are usually the CERN holidays and are used for boat booking rules.
    """

    __tablename__ = "holidays"

    day: Mapped[datetime] = mapped_column(
        DATE,
        nullable=False,
        # Code-only primary key, not in DB
        primary_key=True,
    )
    label: Mapped[str] = mapped_column(VARCHAR2(20), nullable=False)


class Member(Base):
    """
    Represents a YCC member.
    """

    __tablename__ = "members"

    id: Mapped[int] = mapped_column(NUMBER, nullable=False, primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR2(25), nullable=False)
    firstname: Mapped[str] = mapped_column(VARCHAR2(25), nullable=False)
    birthday: Mapped[datetime] = mapped_column(DATE)
    nationality: Mapped[str] = mapped_column(VARCHAR2(3))
    membership: Mapped[str] = mapped_column(VARCHAR2(2), nullable=False)
    temp_memb: Mapped[int] = mapped_column(NUMBER(1, 0))
    lang1: Mapped[str] = mapped_column(VARCHAR2(3))
    lang2: Mapped[str] = mapped_column(VARCHAR2(3))
    category: Mapped[str] = mapped_column(VARCHAR2(1))
    work_address1: Mapped[str] = mapped_column(VARCHAR2(50))
    work_address2: Mapped[str] = mapped_column(VARCHAR2(50))
    work_towncode: Mapped[str] = mapped_column(VARCHAR2(7))
    work_town: Mapped[str] = mapped_column(VARCHAR2(25))
    work_state: Mapped[str] = mapped_column(VARCHAR2(5))
    work_phone: Mapped[str] = mapped_column(VARCHAR2(25))
    e_mail: Mapped[str] = mapped_column(VARCHAR2(50))
    home_addr: Mapped[str] = mapped_column(VARCHAR2(50), nullable=False)
    home_towncode: Mapped[str] = mapped_column(VARCHAR2(7))
    home_town: Mapped[str] = mapped_column(VARCHAR2(25))
    home_state: Mapped[str] = mapped_column(VARCHAR2(5))
    home_phone: Mapped[str] = mapped_column(VARCHAR2(25))
    mail_preference: Mapped[str] = mapped_column(VARCHAR2(1))
    favourite_mailing_post: Mapped[str] = mapped_column(VARCHAR2(1))
    # Note: it is VARCHAR2(4 BYTE) in the DB
    member_entrance: Mapped[str] = mapped_column(VARCHAR2(4), nullable=False)
    cell_phone: Mapped[str] = mapped_column(VARCHAR2(25))
    gender: Mapped[str] = mapped_column(VARCHAR2(2))
    valid_until_date: Mapped[datetime] = mapped_column(DATE)
    last_updated_date: Mapped[datetime] = mapped_column(DATE)
    valid_from_date: Mapped[datetime] = mapped_column(DATE)
    interest_in_fibreglass: Mapped[int] = mapped_column(NUMBER(1, 0))
    interest_in_woodwork: Mapped[int] = mapped_column(NUMBER(1, 0))
    interest_in_ropework: Mapped[int] = mapped_column(NUMBER(1, 0))
    interest_in_paintwork: Mapped[int] = mapped_column(NUMBER(1, 0))
    interest_in_motors: Mapped[int] = mapped_column(NUMBER(1, 0))
    interest_in_organising_social: Mapped[int] = mapped_column(NUMBER(1, 0))
    interest_in_organising_regattas: Mapped[int] = mapped_column(NUMBER(1, 0))
    interest_in_teaching_dinghies: Mapped[int] = mapped_column(NUMBER(1, 0))
    interest_in_teaching_cats: Mapped[int] = mapped_column(NUMBER(1, 0))
    interest_in_teaching_keelboats: Mapped[int] = mapped_column(NUMBER(1, 0))
    interest_in_teaching_motorboats: Mapped[int] = mapped_column(NUMBER(1, 0))
    interest_in_surveillance: Mapped[int] = mapped_column(NUMBER(1, 0))
    interest_in_towing_on_land: Mapped[int] = mapped_column(NUMBER(1, 0))
    special_talents: Mapped[str] = mapped_column(VARCHAR2(1000))

    # Code-only foreign key, not in DB
    entrance_fee_record: Mapped["EntranceFeeRecord"] = relationship()
    # Code-only foreign key, not in DB
    fee_records: Mapped[List["FeeRecord"]] = relationship(
        order_by="FeeRecord.paid_date"
    )
    # This could be many to many when away from Perl (and maybe APEX too)
    maintained_boats1: Mapped[List["Boat"]] = relationship(
        back_populates="maintainer1",
        foreign_keys="Boat.maintainer_id",
        order_by="Boat.name",
    )
    maintained_boats2: Mapped[List["Boat"]] = relationship(
        back_populates="maintainer2",
        foreign_keys="Boat.maintainer_id2",
        order_by="Boat.name",
    )
    user: Mapped["User"] = relationship(back_populates="member", lazy="joined")


class MembershipType(Base):
    """
    Represents a YCC membership type.
    """

    __tablename__ = "membership"

    mb_id: Mapped[int] = mapped_column(
        NUMBER(2, 0),
        nullable=False,
        # Code-only primary key, not in DB
        primary_key=True,
    )
    mb_name: Mapped[str] = mapped_column(
        VARCHAR2(2),
        nullable=False,
        # Code-only unique key, not in DB
        unique=True,
    )
    e_desc: Mapped[str] = mapped_column(VARCHAR2(20), nullable=False)
    f_desc: Mapped[str] = mapped_column(VARCHAR2(20), nullable=False)
    comments: Mapped[str] = mapped_column(VARCHAR2(100))


class User(Base):
    """
    Represents a YCC member's login details.
    """

    __tablename__ = "web_logon"

    member_id: Mapped[int] = mapped_column(
        NUMBER, ForeignKey("members.id"), nullable=False, primary_key=True
    )
    logon_id: Mapped[str] = mapped_column(VARCHAR2(25), nullable=False, unique=True)
    session_id: Mapped[int] = mapped_column(NUMBER)
    session_date: Mapped[datetime] = mapped_column(DATE)
    logon_pass2: Mapped[str] = mapped_column(VARCHAR2(128))
    pass_reset_key: Mapped[str] = mapped_column(VARCHAR2(128))
    pass_reset_exp: Mapped[datetime] = mapped_column(DATE)
    last_changed: Mapped[datetime] = mapped_column(DATE)

    member: Mapped["Member"] = relationship(back_populates="user", lazy="joined")
