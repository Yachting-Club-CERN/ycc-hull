"""
Handwritten Database entities containing only the relevant tables.

For mapping use SQLAlchemy types, so we can also use the entities for
testing/local development with SQLite. The generated DDL is not used for Oracle
(that is database-first approach).

For `mapped_column(...)` declarations do not use `nullable`, use `Optional`
instead for nullable fields.

Type mapping from Oracle to SQLAlchemy (so we can use SQLite for testing):

```
BLOB -> BLOB
CHAR -> CHAR
CLOB -> CLOB
NUMBER -> Integer (or Numeric for non-integers)
DATE - > DateTime
VARCHAR2 -> VARCHAR
```

Note 1: SQLAlchemy requires all tables with PK, but sometimes they are not in
the database. These are marked with comments.

Note 2: The existing DB is inconsistent in spelling "licence" vs "license". Try
to always the British spellings in this project ('c' instead of 's').

Note 3: The existing DB is inconsistent in boolean fields. Sometimes they are
NUMBER(1,0) and sometimes VARCHAR2(1). For new tables use NUMBER(1,0).
"""
from datetime import datetime
from typing import Any, Optional

from collections.abc import Sequence
from sqlalchemy import (
    BLOB,
    CHAR,
    CLOB,
    VARCHAR,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ycc_hull.utils import short_type_name


class BaseEntity(DeclarativeBase):
    """
    Base class for DB entities.
    """

    def dict(self) -> dict[str, Any]:
        return {k: v for k, v in sorted(self.__dict__.items()) if not k.startswith("_")}

    def __repr__(self) -> str:
        return f"{short_type_name(self.__class__)}{self.dict()}"


class AuditLogEntryEntity(BaseEntity):
    """
    Represents an audit log entry.
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        # SYSDATE in Oracle, this is for SQLite (for Oracle it's DB first approach)
        server_default=text("(DATETIME('now','localtime'))"),
    )
    application: Mapped[str] = mapped_column(VARCHAR(200))
    principal: Mapped[str] = mapped_column(VARCHAR(200))
    description: Mapped[str] = mapped_column(VARCHAR(200))
    data: Mapped[Optional[str]] = mapped_column(CLOB)


class BoatEntity(BaseEntity):
    """
    Represents a boat.
    """

    __tablename__ = "boats"

    # NUMBER(3, 0) in DB
    boat_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(20), unique=True)
    type: Mapped[str] = mapped_column(VARCHAR(20))
    license: Mapped[str] = mapped_column(VARCHAR(5))
    class_: Mapped[str] = mapped_column("class", VARCHAR(5))
    # NUMBER(5, 0) in DB
    table_pos: Mapped[int] = mapped_column(Integer, unique=True)
    # NUMBER(3, 0) in DB
    ycc_num: Mapped[int] = mapped_column(Integer, unique=True)
    # Maintainer and maintainer2 are used for sending e-mails to maintainers, e.g., upon Warning/Out of order log entries
    maintainer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("members.id")
    )
    ext_reg_cat: Mapped[Optional[str]] = mapped_column(VARCHAR(2))
    maintainer_id2: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("members.id")
    )
    registration_pdf: Mapped[Optional[Any]] = mapped_column(BLOB)

    # This could be many to many when away from Perl (and maybe APEX too)
    maintainer1: Mapped[Optional["MemberEntity"]] = relationship(
        foreign_keys=maintainer_id, back_populates="maintained_boats1"
    )
    maintainer2: Mapped[Optional["MemberEntity"]] = relationship(
        foreign_keys=maintainer_id2,
        back_populates="maintained_boats2",
    )


class EntranceFeeRecordEntity(BaseEntity):
    """
    Represents an entrance fee record paid by a new member.
    """

    __tablename__ = "entrance_feesrecords"
    __table_args__ = (Index("entrance_fee_uq", "member_id", "year_f", unique=True),)

    # Code-only foreign key, not in DB
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("members.id"), primary_key=True
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
    # NUMBER(4, 0) in DB
    year_f: Mapped[Optional[int]] = mapped_column(Integer)


class FeeRecordEntity(BaseEntity):
    """
    Represents a fee record paid by a member (membership fee, course fee, etc.).
    """

    # Note: FEESRECORDS_TRG trigger may fill entered_date and paymentid
    __tablename__ = "feesrecords"

    # Code-only foreign key, not in DB
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("members.id"))
    # NUMBER(4, 0) in DB
    year_f: Mapped[int] = mapped_column(Integer)
    paid_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    paid_mode: Mapped[Optional[str]] = mapped_column(VARCHAR(4))
    # NUMBER(4, 0) in DB
    fee: Mapped[int] = mapped_column(Integer)
    entered_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        # SYSDATE in Oracle, this is for SQLite (for Oracle it's DB first approach)
        server_default=text("(DATETIME('now','localtime'))"),
    )
    # Nullable in DB, but filled by a trigger
    # Code-only primary key, not in DB; autoincrement=True added for SQLite (de-facto unique in Oracle & managed by a trigger)
    paymentid: Mapped[Optional[int]] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )


class HelpersAppPermissionEntity(BaseEntity):
    """
    Represents a Helpers App permission.
    """

    __tablename__ = "helpers_app_permissions"

    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("members.id"), primary_key=True
    )
    permission: Mapped[str] = mapped_column(VARCHAR)


class HelperTaskCategoryEntity(BaseEntity):
    """
    Represents a helper task category.
    """

    __tablename__ = "helper_task_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(VARCHAR(50))
    short_description: Mapped[str] = mapped_column(VARCHAR(200))
    long_description: Mapped[Optional[str]] = mapped_column(CLOB)

    tasks: Mapped[list["HelperTaskEntity"]] = relationship(back_populates="category")


class HelperTaskEntity(BaseEntity):
    """
    Represents a helper task.
    """

    __tablename__ = "helper_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("helper_task_categories.id")
    )
    title: Mapped[str] = mapped_column(VARCHAR(50))
    short_description: Mapped[str] = mapped_column(VARCHAR(200))
    long_description: Mapped[Optional[str]] = mapped_column(CLOB)
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("members.id"))
    # Either start+end is specified or the deadline
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime)
    # NUMBER(1, 0) in DB
    urgent: Mapped[bool] = mapped_column(Integer)
    captain_required_licence_info_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("infolicences.infoid")
    )
    helper_min_count: Mapped[int] = mapped_column(Integer)
    helper_max_count: Mapped[int] = mapped_column(Integer)
    # NUMBER(1, 0) in DB
    published: Mapped[bool] = mapped_column(Integer)
    captain_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("members.id"))
    captain_signed_up_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    category: Mapped["HelperTaskCategoryEntity"] = relationship(
        back_populates="tasks", lazy="joined"
    )
    contact: Mapped["MemberEntity"] = relationship(
        foreign_keys=contact_id, back_populates="helper_tasks_as_contact", lazy="joined"
    )
    captain_required_licence_info: Mapped[Optional["LicenceInfoEntity"]] = relationship(
        lazy="joined"
    )
    captain: Mapped[Optional["MemberEntity"]] = relationship(
        foreign_keys=captain_id,
        back_populates="helper_tasks_as_captain",
        lazy="joined",
    )
    helpers: Mapped[list["HelperTaskHelperEntity"]] = relationship(
        back_populates="helper_task", lazy="joined"
    )


class HelperTaskHelperEntity(BaseEntity):
    """
    Association between helper tasks and helpers.
    """

    __tablename__ = "helper_task_helpers"

    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("helper_tasks.id"), primary_key=True
    )
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("members.id"), primary_key=True
    )
    signed_up_at: Mapped[datetime] = mapped_column(DateTime)

    helper_task: Mapped["HelperTaskEntity"] = relationship(
        back_populates="helpers", lazy="joined"
    )
    member: Mapped["MemberEntity"] = relationship(
        back_populates="helper_tasks_as_helper", lazy="joined"
    )


class HolidayEntity(BaseEntity):
    """
    Represents a holiday. Holidays are usually the CERN holidays and are used for boat booking rules.
    """

    __tablename__ = "holidays"

    day: Mapped[datetime] = mapped_column(DateTime)
    label: Mapped[str] = mapped_column(VARCHAR(20))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)


class LicenceEntity(BaseEntity):
    """
    Represents a licence belonging to a member.
    """

    __tablename__ = "licences"
    __table_args__ = (
        PrimaryKeyConstraint("licence_id", "member_id", name="licence_pk"),
    )

    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("members.id"))
    # NUMBER(2, 0) in DB
    licence_id: Mapped[int] = mapped_column(Integer, ForeignKey("infolicences.infoid"))
    # Year when the licence was issued
    # NUMBER(4, 0) in DB
    lyear: Mapped[int] = mapped_column(Integer)
    # Most often "Registered by Firstname LASTNAME"
    lcomments: Mapped[Optional[str]] = mapped_column(VARCHAR(100))
    # This should be linked to tests when they are supported, see issue #27
    test_id: Mapped[Optional[int]] = mapped_column(Integer)
    # 0 = inactive, 1 = active (NUMBER(4,0) in the DB)
    status: Mapped[Optional[int]] = mapped_column(Integer)

    licence_info: Mapped["LicenceInfoEntity"] = relationship(lazy="joined")
    member: Mapped["MemberEntity"] = relationship(back_populates="licences")


class LicenceInfoEntity(BaseEntity):
    """
    Represents a YCC licence.

    This table is a bit of a mess, but it is used for the boat booking rules, courses, etc.
    """

    __tablename__ = "infolicences"

    # Can be negative
    infoid: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Course identifier, e.g., "GS", sometimes NULL
    ncourse: Mapped[Optional[str]] = mapped_column(VARCHAR(2))
    # This is actually the licence ID, same as BoatEntity.license (note the inconsistency in the spelling).
    # However, boats do not have licence in their table what is here, for example Laser is listed as L here,
    # but for booking a Laser one needs a D licence (at least as of 2023)
    nlicence: Mapped[Optional[str]] = mapped_column(VARCHAR(2))
    # Probably we can ignore this one, often NULLm especially for new entries
    nkey: Mapped[Optional[str]] = mapped_column(VARCHAR(2))
    description: Mapped[str] = mapped_column(VARCHAR(50))
    # NULL, 0, 90, 170, ... (NUMBER(4, 0) in DB)
    coursefee: Mapped[Optional[int]] = mapped_column(Integer)
    # NULL, "Cabin keel-boat", ...
    course_name: Mapped[Optional[str]] = mapped_column(VARCHAR(30))
    # NULL, Y, N
    course_active: Mapped[Optional[str]] = mapped_column(CHAR(1))
    # NULL, 1, 2, 3 (NUMBER(1, 0) in DB)
    course_level: Mapped[Optional[int]] = mapped_column(Integer)


class MemberEntity(BaseEntity):
    """
    Represents a YCC member.
    """

    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(25))
    firstname: Mapped[str] = mapped_column(VARCHAR(25))
    birthday: Mapped[Optional[datetime]] = mapped_column(DateTime)
    nationality: Mapped[Optional[str]] = mapped_column(VARCHAR(3))
    membership: Mapped[str] = mapped_column(VARCHAR(2))
    # NUMBER(1, 0) in DB
    temp_memb: Mapped[Optional[int]] = mapped_column(Integer)
    lang1: Mapped[Optional[str]] = mapped_column(VARCHAR(3))
    lang2: Mapped[Optional[str]] = mapped_column(VARCHAR(3))
    category: Mapped[Optional[str]] = mapped_column(VARCHAR(1))
    work_address1: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    work_address2: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    work_towncode: Mapped[Optional[str]] = mapped_column(VARCHAR(7))
    work_town: Mapped[Optional[str]] = mapped_column(VARCHAR(25))
    work_state: Mapped[Optional[str]] = mapped_column(VARCHAR(5))
    work_phone: Mapped[Optional[str]] = mapped_column(VARCHAR(25))
    e_mail: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    home_addr: Mapped[str] = mapped_column(VARCHAR(50))
    home_towncode: Mapped[Optional[str]] = mapped_column(VARCHAR(7))
    home_town: Mapped[Optional[str]] = mapped_column(VARCHAR(25))
    home_state: Mapped[Optional[str]] = mapped_column(VARCHAR(5))
    home_phone: Mapped[Optional[str]] = mapped_column(VARCHAR(25))
    mail_preference: Mapped[Optional[str]] = mapped_column(VARCHAR(1))
    favourite_mailing_post: Mapped[Optional[str]] = mapped_column(VARCHAR(1))
    # Note: it is VARCHAR2(4 BYTE) in the DB
    member_entrance: Mapped[str] = mapped_column(VARCHAR(4))
    cell_phone: Mapped[Optional[str]] = mapped_column(VARCHAR(25))
    gender: Mapped[Optional[str]] = mapped_column(VARCHAR(2))
    valid_until_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_updated_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    valid_from_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    # interest_in* are NUMBER(1,0) in DB
    interest_in_fibreglass: Mapped[Optional[int]] = mapped_column(Integer)
    interest_in_woodwork: Mapped[Optional[int]] = mapped_column(Integer)
    interest_in_ropework: Mapped[Optional[int]] = mapped_column(Integer)
    interest_in_paintwork: Mapped[Optional[int]] = mapped_column(Integer)
    interest_in_motors: Mapped[Optional[int]] = mapped_column(Integer)
    interest_in_organising_social: Mapped[Optional[int]] = mapped_column(Integer)
    interest_in_organising_regattas: Mapped[Optional[int]] = mapped_column(Integer)
    interest_in_teaching_dinghies: Mapped[Optional[int]] = mapped_column(Integer)
    interest_in_teaching_cats: Mapped[Optional[int]] = mapped_column(Integer)
    interest_in_teaching_keelboats: Mapped[Optional[int]] = mapped_column(Integer)
    interest_in_teaching_motorboats: Mapped[Optional[int]] = mapped_column(Integer)
    interest_in_surveillance: Mapped[Optional[int]] = mapped_column(Integer)
    interest_in_towing_on_land: Mapped[Optional[int]] = mapped_column(Integer)
    special_talents: Mapped[Optional[str]] = mapped_column(VARCHAR(1000))

    # Code-only foreign key, not in DB
    entrance_fee_record: Mapped[Optional["EntranceFeeRecordEntity"]] = relationship()
    # Code-only foreign key, not in DB
    fee_records: Mapped[list["FeeRecordEntity"]] = relationship(
        order_by="FeeRecordEntity.paid_date"
    )
    helper_tasks_as_contact: Mapped[list["HelperTaskEntity"]] = relationship(
        foreign_keys="HelperTaskEntity.contact_id", back_populates="contact"
    )
    helper_tasks_as_captain: Mapped[list["HelperTaskEntity"]] = relationship(
        foreign_keys="HelperTaskEntity.captain_id", back_populates="captain"
    )
    helper_tasks_as_helper: Mapped[list["HelperTaskHelperEntity"]] = relationship(
        back_populates="member"
    )
    licences: Mapped[list["LicenceEntity"]] = relationship()
    # This could be many to many when away from Perl (and maybe APEX too)
    maintained_boats1: Mapped[list["BoatEntity"]] = relationship(
        foreign_keys="BoatEntity.maintainer_id",
        order_by="BoatEntity.name",
        back_populates="maintainer1",
    )
    maintained_boats2: Mapped[list["BoatEntity"]] = relationship(
        foreign_keys="BoatEntity.maintainer_id2",
        order_by="BoatEntity.name",
        back_populates="maintainer2",
    )
    user: Mapped[Optional["UserEntity"]] = relationship(
        back_populates="member", lazy="joined"
    )

    @property
    def all_licence_infos(self) -> Sequence["LicenceInfoEntity"]:
        """
        Returns all licences, including expired ones.
        """
        return [licence.licence_info for licence in self.licences]

    @property
    def active_licence_infos(self) -> Sequence["LicenceInfoEntity"]:
        """
        Returns all active licences.
        """
        return [
            licence.licence_info
            for licence in self.licences
            if licence.status and licence.status > 0
        ]


class MembershipTypeEntity(BaseEntity):
    """
    Represents a YCC membership type.
    """

    __tablename__ = "membership"

    # NUMBER(2, 0) in DB
    mb_id: Mapped[int] = mapped_column(
        Integer,
        # Code-only primary key, not in DB
        primary_key=True,
    )
    mb_name: Mapped[str] = mapped_column(
        VARCHAR(2),
        # Code-only unique key, not in DB
        unique=True,
    )
    e_desc: Mapped[str] = mapped_column(VARCHAR(20))
    f_desc: Mapped[str] = mapped_column(VARCHAR(20))
    comments: Mapped[Optional[str]] = mapped_column(VARCHAR(100))


class UserEntity(BaseEntity):
    """
    Represents a YCC member's login details.
    """

    __tablename__ = "web_logon"

    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("members.id"), primary_key=True
    )
    logon_id: Mapped[str] = mapped_column(VARCHAR(25), unique=True)
    session_id: Mapped[Optional[int]] = mapped_column(Integer)
    session_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    logon_pass2: Mapped[Optional[str]] = mapped_column(VARCHAR(128))
    pass_reset_key: Mapped[Optional[str]] = mapped_column(VARCHAR(128))
    pass_reset_exp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_changed: Mapped[Optional[datetime]] = mapped_column(DateTime)
    rf_uid: Mapped[Optional[str]] = mapped_column(VARCHAR(10))

    member: Mapped["MemberEntity"] = relationship(back_populates="user", lazy="joined")
