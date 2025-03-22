# type: ignore
"""
Entities generated by sqlacodegen.
"""

import datetime
from typing import List, Optional

from sqlalchemy import (
    CHAR,
    VARCHAR,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    LargeBinary,
    PrimaryKeyConstraint,
    Table,
    Text,
    text,
)
from sqlalchemy.dialects.oracle import NUMBER
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


t_audit_log = Table(
    "audit_log",
    Base.metadata,
    Column(
        "id",
        NUMBER(asdecimal=False),
        Identity(
            always=True,
            on_null=False,
            start=1,
            increment=1,
            minvalue=1,
            maxvalue=9999999999999999999999999999,
            cycle=False,
            cache=20,
            order=False,
        ),
        nullable=False,
    ),
    Column("DATE", DateTime, nullable=False, server_default=text("SYSDATE ")),
    Column("application", VARCHAR(200), nullable=False),
    Column("USER", VARCHAR(200), nullable=False),
    Column("description", VARCHAR(200), nullable=False),
    Column("data", Text),
)


class EntranceFeesrecords(Base):
    __tablename__ = "entrance_feesrecords"
    __table_args__ = (
        PrimaryKeyConstraint("member_id", name="entrance_feesrecords_pk"),
        Index("entrance_fee_uq", "member_id", "year_f", unique=True),
    )

    member_id: Mapped[float] = mapped_column(NUMBER(asdecimal=False), primary_key=True)
    year_f: Mapped[Optional[float]] = mapped_column(NUMBER(asdecimal=False))


class Fees(Base):
    __tablename__ = "fees"
    __table_args__ = (
        CheckConstraint("cat_id in ('AS','AJ','FM','H','C','T')", name="check_cat"),
        PrimaryKeyConstraint("cat_id", name="cat_pk"),
    )

    cat_id: Mapped[str] = mapped_column(VARCHAR(2), primary_key=True)
    description: Mapped[str] = mapped_column(VARCHAR(25))
    entrance_fee: Mapped[float] = mapped_column(NUMBER(asdecimal=False))
    annual_fee: Mapped[float] = mapped_column(NUMBER(asdecimal=False))
    lastchange: Mapped[Optional[str]] = mapped_column(VARCHAR(15))


class Feesrecords(Base):
    __tablename__ = "feesrecords"
    __table_args__ = (PrimaryKeyConstraint("paymentid", name="pk_feesrecords"),)

    member_id: Mapped[float] = mapped_column(NUMBER(asdecimal=False))
    year_f: Mapped[float] = mapped_column(NUMBER(4, 0, False))
    fee: Mapped[float] = mapped_column(NUMBER(3, 0, False))
    paymentid: Mapped[float] = mapped_column(NUMBER(asdecimal=False), primary_key=True)
    paid_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    paid_mode: Mapped[Optional[str]] = mapped_column(VARCHAR(4))
    entered_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, server_default=text("sysdate")
    )
    payment_reason: Mapped[Optional[str]] = mapped_column(VARCHAR(50))


class HelperTaskCategories(Base):
    __tablename__ = "helper_task_categories"
    __table_args__ = (PrimaryKeyConstraint("id", name="helper_task_categories_pk"),)

    id: Mapped[float] = mapped_column(
        NUMBER(asdecimal=False),
        Identity(
            on_null=False,
            start=10,
            increment=1,
            minvalue=1,
            maxvalue=9999999999999999999999999999,
            cycle=False,
            cache=20,
            order=False,
        ),
        primary_key=True,
    )
    title: Mapped[str] = mapped_column(VARCHAR(50))
    short_description: Mapped[str] = mapped_column(VARCHAR(200))
    long_description: Mapped[Optional[str]] = mapped_column(Text)

    helper_tasks: Mapped[List["HelperTasks"]] = relationship(
        "HelperTasks", back_populates="category"
    )


t_holidays = Table(
    "holidays",
    Base.metadata,
    Column("day", DateTime, nullable=False),
    Column("label", VARCHAR(20), nullable=False),
    Column("id", NUMBER(asdecimal=False)),
)


class ImportantDates(Base):
    __tablename__ = "important_dates"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="sys_c009098"),
        Index("important_dates_uq", "what", unique=True),
    )

    id: Mapped[float] = mapped_column(NUMBER(asdecimal=False), primary_key=True)
    what: Mapped[str] = mapped_column(VARCHAR(50))
    datetime: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)


class ImportantValues(Base):
    __tablename__ = "important_values"
    __table_args__ = (PrimaryKeyConstraint("id", name="sys_c009055"),)

    id: Mapped[float] = mapped_column(NUMBER(10, 0, False), primary_key=True)
    what: Mapped[str] = mapped_column(VARCHAR(50))
    val: Mapped[str] = mapped_column(VARCHAR(50))
    last_modified: Mapped[datetime.datetime] = mapped_column(DateTime)


class Infolicences(Base):
    __tablename__ = "infolicences"
    __table_args__ = (
        PrimaryKeyConstraint("infoid", name="licinfo_pk"),
        Index("infolicences_uk1", "nlicence", unique=True),
    )

    infoid: Mapped[float] = mapped_column(NUMBER(asdecimal=False), primary_key=True)
    nlicence: Mapped[str] = mapped_column(VARCHAR(2))
    description: Mapped[str] = mapped_column(VARCHAR(50))
    ncourse: Mapped[Optional[str]] = mapped_column(VARCHAR(2))
    nkey: Mapped[Optional[str]] = mapped_column(VARCHAR(2))
    coursefee: Mapped[Optional[float]] = mapped_column(NUMBER(4, 0, False))
    course_name: Mapped[Optional[str]] = mapped_column(VARCHAR(30))
    course_active: Mapped[Optional[str]] = mapped_column(CHAR(1))
    course_level: Mapped[Optional[float]] = mapped_column(NUMBER(1, 0, False))
    has_test: Mapped[Optional[float]] = mapped_column(
        NUMBER(1, 0, False), server_default=text("0\n   ")
    )

    helper_tasks: Mapped[List["HelperTasks"]] = relationship(
        "HelperTasks", back_populates="captain_required_licence_info"
    )
    licences: Mapped[List["Licences"]] = relationship(
        "Licences", back_populates="licence"
    )


class InterestLevels(Base):
    __tablename__ = "interest_levels"
    __table_args__ = (PrimaryKeyConstraint("interest_level", name="sys_c009100"),)

    interest_level: Mapped[float] = mapped_column(NUMBER(1, 0, False), primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(VARCHAR(100))


class Members(Base):
    __tablename__ = "members"
    __table_args__ = (PrimaryKeyConstraint("id", name="members_pk"),)

    id: Mapped[float] = mapped_column(NUMBER(asdecimal=False), primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(25))
    firstname: Mapped[str] = mapped_column(VARCHAR(25))
    membership: Mapped[str] = mapped_column(VARCHAR(2))
    home_addr: Mapped[str] = mapped_column(VARCHAR(50))
    member_entrance: Mapped[str] = mapped_column(VARCHAR(4))
    birthday: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    nationality: Mapped[Optional[str]] = mapped_column(VARCHAR(3))
    temp_memb: Mapped[Optional[float]] = mapped_column(NUMBER(1, 0, False))
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
    home_towncode: Mapped[Optional[str]] = mapped_column(VARCHAR(7))
    home_town: Mapped[Optional[str]] = mapped_column(VARCHAR(25))
    home_state: Mapped[Optional[str]] = mapped_column(VARCHAR(5))
    home_phone: Mapped[Optional[str]] = mapped_column(VARCHAR(25))
    mail_preference: Mapped[Optional[str]] = mapped_column(VARCHAR(1))
    favourite_mailing_post: Mapped[Optional[str]] = mapped_column(VARCHAR(1))
    cell_phone: Mapped[Optional[str]] = mapped_column(VARCHAR(25))
    gender: Mapped[Optional[str]] = mapped_column(VARCHAR(2))
    valid_until_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    last_updated_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    valid_from_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    interest_in_fibreglass: Mapped[Optional[float]] = mapped_column(NUMBER(1, 0, False))
    interest_in_woodwork: Mapped[Optional[float]] = mapped_column(NUMBER(1, 0, False))
    interest_in_ropework: Mapped[Optional[float]] = mapped_column(NUMBER(1, 0, False))
    interest_in_paintwork: Mapped[Optional[float]] = mapped_column(NUMBER(1, 0, False))
    interest_in_motors: Mapped[Optional[float]] = mapped_column(NUMBER(1, 0, False))
    interest_in_organising_social: Mapped[Optional[float]] = mapped_column(
        NUMBER(1, 0, False)
    )
    interest_in_organising_regattas: Mapped[Optional[float]] = mapped_column(
        NUMBER(1, 0, False)
    )
    interest_in_teaching_dinghies: Mapped[Optional[float]] = mapped_column(
        NUMBER(1, 0, False)
    )
    interest_in_teaching_cats: Mapped[Optional[float]] = mapped_column(
        NUMBER(1, 0, False)
    )
    interest_in_teaching_keelboats: Mapped[Optional[float]] = mapped_column(
        NUMBER(1, 0, False)
    )
    interest_in_teaching_motorboats: Mapped[Optional[float]] = mapped_column(
        NUMBER(1, 0, False)
    )
    interest_in_surveillance: Mapped[Optional[float]] = mapped_column(
        NUMBER(1, 0, False)
    )
    interest_in_towing_on_land: Mapped[Optional[float]] = mapped_column(
        NUMBER(1, 0, False)
    )
    special_talents: Mapped[Optional[str]] = mapped_column(VARCHAR(1000))

    boats: Mapped[List["Boats"]] = relationship("Boats", back_populates="members")
    committee: Mapped[List["Committee"]] = relationship(
        "Committee", back_populates="member"
    )
    helper_tasks: Mapped[List["HelperTasks"]] = relationship(
        "HelperTasks", foreign_keys="[HelperTasks.captain_id]", back_populates="captain"
    )
    helper_tasks_: Mapped[List["HelperTasks"]] = relationship(
        "HelperTasks", foreign_keys="[HelperTasks.contact_id]", back_populates="contact"
    )
    helper_tasks1: Mapped[List["HelperTasks"]] = relationship(
        "HelperTasks",
        foreign_keys="[HelperTasks.marked_as_done_by_id]",
        back_populates="marked_as_done_by",
    )
    helper_tasks2: Mapped[List["HelperTasks"]] = relationship(
        "HelperTasks",
        foreign_keys="[HelperTasks.validated_by_id]",
        back_populates="validated_by",
    )
    licences: Mapped[List["Licences"]] = relationship(
        "Licences", back_populates="member"
    )
    boat_maintainer: Mapped[List["BoatMaintainer"]] = relationship(
        "BoatMaintainer", back_populates="member"
    )
    helper_task_helpers: Mapped[List["HelperTaskHelpers"]] = relationship(
        "HelperTaskHelpers", back_populates="member"
    )


t_membership = Table(
    "membership",
    Base.metadata,
    Column("mb_id", NUMBER(2, 0, False), nullable=False),
    Column("mb_name", VARCHAR(2), nullable=False),
    Column("e_desc", VARCHAR(20), nullable=False),
    Column("f_desc", VARCHAR(20), nullable=False),
    Column("comments", VARCHAR(200)),
)


class Boats(Base):
    __tablename__ = "boats"
    __table_args__ = (
        ForeignKeyConstraint(["maintainer_id2"], ["members.id"], name="sys_c009128"),
        PrimaryKeyConstraint("boat_id", name="sys_c009093"),
        Index("sys_c009094", "name", unique=True),
        Index("sys_c009095", "ycc_num", unique=True),
        Index("sys_c009096", "table_pos", unique=True),
    )

    boat_id: Mapped[float] = mapped_column(NUMBER(3, 0, False), primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(20))
    type: Mapped[str] = mapped_column(VARCHAR(20))
    license: Mapped[str] = mapped_column(VARCHAR(5))
    class_: Mapped[str] = mapped_column("class", VARCHAR(5))
    ycc_num: Mapped[Optional[float]] = mapped_column(NUMBER(3, 0, False))
    table_pos: Mapped[Optional[float]] = mapped_column(NUMBER(5, 0, False))
    maintainer_id: Mapped[Optional[float]] = mapped_column(NUMBER(asdecimal=False))
    ext_reg_cat: Mapped[Optional[str]] = mapped_column(VARCHAR(2))
    maintainer_id2: Mapped[Optional[float]] = mapped_column(NUMBER(asdecimal=False))
    registration_pdf: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    capacity: Mapped[Optional[int]] = mapped_column(Integer)

    members: Mapped[Optional["Members"]] = relationship(
        "Members", back_populates="boats"
    )
    boat_maintainer: Mapped[List["BoatMaintainer"]] = relationship(
        "BoatMaintainer", back_populates="boat"
    )
    reservations: Mapped[List["Reservations"]] = relationship(
        "Reservations", back_populates="boat"
    )


class Committee(Base):
    __tablename__ = "committee"
    __table_args__ = (
        ForeignKeyConstraint(["member_id"], ["members.id"], name="committee_member_fk"),
        PrimaryKeyConstraint("member_id", "cyear", name="committee_pk"),
        Index("sys_c009108", "commid", unique=True),
    )

    member_id: Mapped[float] = mapped_column(NUMBER(asdecimal=False), primary_key=True)
    cyear: Mapped[float] = mapped_column(NUMBER(4, 0, False), primary_key=True)
    commid: Mapped[float] = mapped_column(NUMBER(10, 0, False))
    lcomments: Mapped[Optional[str]] = mapped_column(VARCHAR(100))
    photo: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    position: Mapped[Optional[float]] = mapped_column(NUMBER(asdecimal=False))
    roles: Mapped[Optional[str]] = mapped_column(VARCHAR(500))

    member: Mapped["Members"] = relationship("Members", back_populates="committee")


class HelperTasks(Base):
    __tablename__ = "helper_tasks"
    __table_args__ = (
        CheckConstraint(
            " (                0 <= helper_min_count )\n            AND ( helper_min_count <= helper_max_count ) ",
            name="helper_tasks_check_helper_min_max_count",
        ),
        CheckConstraint(
            " (                0 <= helper_min_count )\n            AND ( helper_min_count <= helper_max_count ) ",
            name="helper_tasks_check_helper_min_max_count",
        ),
        CheckConstraint(
            " ( captain_id IS     NULL AND captain_signed_up_at IS     NULL )\n             OR ( captain_id IS NOT NULL AND captain_signed_up_at IS NOT NULL ) ",
            name="helper_tasks_check_captain_fields",
        ),
        CheckConstraint(
            " ( captain_id IS     NULL AND captain_signed_up_at IS     NULL )\n             OR ( captain_id IS NOT NULL AND captain_signed_up_at IS NOT NULL ) ",
            name="helper_tasks_check_captain_fields",
        ),
        CheckConstraint(
            " ( starts_at IS NOT NULL AND ends_at IS NOT NULL AND deadline IS     NULL and starts_at < ends_at )\n             OR ( starts_at IS     NULL AND ends_at IS     NULL AND deadline IS NOT NULL                         ) ",
            name="helper_tasks_check_timing",
        ),
        CheckConstraint(
            " ( starts_at IS NOT NULL AND ends_at IS NOT NULL AND deadline IS     NULL and starts_at < ends_at )\n             OR ( starts_at IS     NULL AND ends_at IS     NULL AND deadline IS NOT NULL                         ) ",
            name="helper_tasks_check_timing",
        ),
        CheckConstraint(
            " ( starts_at IS NOT NULL AND ends_at IS NOT NULL AND deadline IS     NULL and starts_at < ends_at )\n             OR ( starts_at IS     NULL AND ends_at IS     NULL AND deadline IS NOT NULL                         ) ",
            name="helper_tasks_check_timing",
        ),
        CheckConstraint(
            " (marked_as_done_at IS     NULL AND marked_as_done_by_id IS     NULL)\n             OR (marked_as_done_at IS NOT NULL AND marked_as_done_by_id IS NOT NULL) ",
            name="helper_tasks_check_marked_as_done_fields",
        ),
        CheckConstraint(
            " (marked_as_done_at IS     NULL AND marked_as_done_by_id IS     NULL)\n             OR (marked_as_done_at IS NOT NULL AND marked_as_done_by_id IS NOT NULL) ",
            name="helper_tasks_check_marked_as_done_fields",
        ),
        CheckConstraint(
            " (validated_at IS     NULL AND validated_by_id IS     NULL)\n             OR (validated_at IS NOT NULL AND validated_by_id IS NOT NULL) ",
            name="helper_tasks_check_validated_fields",
        ),
        CheckConstraint(
            " (validated_at IS     NULL AND validated_by_id IS     NULL)\n             OR (validated_at IS NOT NULL AND validated_by_id IS NOT NULL) ",
            name="helper_tasks_check_validated_fields",
        ),
        ForeignKeyConstraint(
            ["captain_id"], ["members.id"], name="helper_tasks_captain_fk"
        ),
        ForeignKeyConstraint(
            ["captain_required_licence_info_id"],
            ["infolicences.infoid"],
            name="helper_tasks_captain_required_licence_info_fk",
        ),
        ForeignKeyConstraint(
            ["category_id"],
            ["helper_task_categories.id"],
            name="helper_tasks_category_fk",
        ),
        ForeignKeyConstraint(
            ["contact_id"], ["members.id"], name="helper_tasks_contact_fk"
        ),
        ForeignKeyConstraint(
            ["marked_as_done_by_id"],
            ["members.id"],
            name="helper_tasks_marked_as_done_by_fk",
        ),
        ForeignKeyConstraint(
            ["validated_by_id"], ["members.id"], name="helper_tasks_validated_by_fk"
        ),
        PrimaryKeyConstraint("id", name="helper_tasks_pk"),
    )

    id: Mapped[float] = mapped_column(
        NUMBER(asdecimal=False),
        Identity(
            on_null=False,
            start=3000,
            increment=1,
            minvalue=1,
            maxvalue=9999999999999999999999999999,
            cycle=False,
            cache=20,
            order=False,
        ),
        primary_key=True,
    )
    category_id: Mapped[float] = mapped_column(NUMBER(asdecimal=False))
    title: Mapped[str] = mapped_column(VARCHAR(50))
    short_description: Mapped[str] = mapped_column(VARCHAR(200))
    contact_id: Mapped[float] = mapped_column(NUMBER(asdecimal=False))
    urgent: Mapped[float] = mapped_column(NUMBER(1, 0, False))
    helper_min_count: Mapped[float] = mapped_column(NUMBER(asdecimal=False))
    helper_max_count: Mapped[float] = mapped_column(NUMBER(asdecimal=False))
    published: Mapped[float] = mapped_column(NUMBER(1, 0, False))
    long_description: Mapped[Optional[str]] = mapped_column(Text)
    starts_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    ends_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    deadline: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    captain_required_licence_info_id: Mapped[Optional[float]] = mapped_column(
        NUMBER(asdecimal=False)
    )
    captain_id: Mapped[Optional[float]] = mapped_column(NUMBER(asdecimal=False))
    captain_signed_up_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    marked_as_done_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    marked_as_done_by_id: Mapped[Optional[float]] = mapped_column(
        NUMBER(asdecimal=False)
    )
    marked_as_done_comment: Mapped[Optional[str]] = mapped_column(Text)
    validated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    validated_by_id: Mapped[Optional[float]] = mapped_column(NUMBER(asdecimal=False))
    validation_comment: Mapped[Optional[str]] = mapped_column(Text)

    captain: Mapped[Optional["Members"]] = relationship(
        "Members", foreign_keys=[captain_id], back_populates="helper_tasks"
    )
    captain_required_licence_info: Mapped[Optional["Infolicences"]] = relationship(
        "Infolicences", back_populates="helper_tasks"
    )
    category: Mapped["HelperTaskCategories"] = relationship(
        "HelperTaskCategories", back_populates="helper_tasks"
    )
    contact: Mapped["Members"] = relationship(
        "Members", foreign_keys=[contact_id], back_populates="helper_tasks_"
    )
    marked_as_done_by: Mapped[Optional["Members"]] = relationship(
        "Members", foreign_keys=[marked_as_done_by_id], back_populates="helper_tasks1"
    )
    validated_by: Mapped[Optional["Members"]] = relationship(
        "Members", foreign_keys=[validated_by_id], back_populates="helper_tasks2"
    )
    helper_task_helpers: Mapped[List["HelperTaskHelpers"]] = relationship(
        "HelperTaskHelpers", back_populates="task"
    )


class HelpersAppPermissions(Members):
    __tablename__ = "helpers_app_permissions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["member_id"], ["members.id"], name="helpers_app_permissions_member_fk"
        ),
        PrimaryKeyConstraint("member_id", name="helpers_app_permissions_pk"),
    )

    member_id: Mapped[float] = mapped_column(NUMBER(asdecimal=False), primary_key=True)
    permission: Mapped[str] = mapped_column(Enum("ADMIN", "EDITOR"))


class Licences(Base):
    __tablename__ = "licences"
    __table_args__ = (
        ForeignKeyConstraint(
            ["licence_id"], ["infolicences.infoid"], name="licences_licence_id_fk"
        ),
        ForeignKeyConstraint(["member_id"], ["members.id"], name="sys_c009133"),
        PrimaryKeyConstraint("licence_id", "member_id", name="licence_pk"),
    )

    member_id: Mapped[float] = mapped_column(NUMBER(asdecimal=False), primary_key=True)
    licence_id: Mapped[float] = mapped_column(NUMBER(2, 0, False), primary_key=True)
    lyear: Mapped[float] = mapped_column(NUMBER(4, 0, False))
    lcomments: Mapped[Optional[str]] = mapped_column(VARCHAR(100))
    test_id: Mapped[Optional[float]] = mapped_column(NUMBER(asdecimal=False))
    status: Mapped[Optional[float]] = mapped_column(NUMBER(4, 0, False))

    licence: Mapped["Infolicences"] = relationship(
        "Infolicences", back_populates="licences"
    )
    member: Mapped["Members"] = relationship("Members", back_populates="licences")


class WebLogon(Members):
    __tablename__ = "web_logon"
    __table_args__ = (
        ForeignKeyConstraint(["member_id"], ["members.id"], name="sys_c009135"),
        PrimaryKeyConstraint("member_id", name="sys_c009119"),
        Index("sys_c009120", "logon_id", unique=True),
    )

    member_id: Mapped[float] = mapped_column(NUMBER(asdecimal=False), primary_key=True)
    logon_id: Mapped[str] = mapped_column(VARCHAR(25))
    session_id: Mapped[Optional[float]] = mapped_column(NUMBER(asdecimal=False))
    session_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    logon_pass2: Mapped[Optional[str]] = mapped_column(VARCHAR(256))
    pass_reset_key: Mapped[Optional[str]] = mapped_column(VARCHAR(128))
    pass_reset_exp: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    last_changed: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    rf_uid: Mapped[Optional[str]] = mapped_column(VARCHAR(10))


class BoatMaintainer(Base):
    __tablename__ = "boat_maintainer"
    __table_args__ = (
        ForeignKeyConstraint(["boat_id"], ["boats.boat_id"], name="sys_c009129"),
        ForeignKeyConstraint(["member_id"], ["members.id"], name="sys_c009130"),
        PrimaryKeyConstraint("id", name="sys_c009083"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    boat_id: Mapped[int] = mapped_column(Integer)
    member_id: Mapped[int] = mapped_column(Integer)
    priority: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[datetime.datetime] = mapped_column(DateTime)
    last_update: Mapped[datetime.datetime] = mapped_column(DateTime)
    end_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    comments: Mapped[Optional[str]] = mapped_column(VARCHAR(255))

    boat: Mapped["Boats"] = relationship("Boats", back_populates="boat_maintainer")
    member: Mapped["Members"] = relationship(
        "Members", back_populates="boat_maintainer"
    )


class HelperTaskHelpers(Base):
    __tablename__ = "helper_task_helpers"
    __table_args__ = (
        ForeignKeyConstraint(
            ["member_id"], ["members.id"], name="helper_task_helpers_member_fk"
        ),
        ForeignKeyConstraint(
            ["task_id"], ["helper_tasks.id"], name="helper_task_helpers_task_fk"
        ),
        PrimaryKeyConstraint("task_id", "member_id", name="helper_task_helpers_pk"),
    )

    task_id: Mapped[float] = mapped_column(NUMBER(asdecimal=False), primary_key=True)
    member_id: Mapped[float] = mapped_column(NUMBER(asdecimal=False), primary_key=True)
    signed_up_at: Mapped[datetime.datetime] = mapped_column(DateTime)

    member: Mapped["Members"] = relationship(
        "Members", back_populates="helper_task_helpers"
    )
    task: Mapped["HelperTasks"] = relationship(
        "HelperTasks", back_populates="helper_task_helpers"
    )


class Reservations(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        ForeignKeyConstraint(["boat_id"], ["boats.boat_id"], name="sys_c009134"),
        PrimaryKeyConstraint("res_id", name="sys_c009116"),
    )

    res_id: Mapped[float] = mapped_column(NUMBER(asdecimal=False), primary_key=True)
    boat_id: Mapped[float] = mapped_column(NUMBER(3, 0, False))
    owner_id: Mapped[float] = mapped_column(NUMBER(asdecimal=False))
    label: Mapped[str] = mapped_column(VARCHAR(25))
    day: Mapped[datetime.datetime] = mapped_column(DateTime)
    period: Mapped[float] = mapped_column(NUMBER(1, 0, False))
    modified: Mapped[datetime.datetime] = mapped_column(DateTime)
    locked: Mapped[Optional[float]] = mapped_column(NUMBER(1, 0, False))
    deleted: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    category: Mapped[Optional[str]] = mapped_column(VARCHAR(20))

    boat: Mapped["Boats"] = relationship("Boats", back_populates="reservations")
