"""Test data generator component for members & fees."""

from collections.abc import Iterator
from datetime import date, datetime, timedelta
from typing import NamedTuple

from faker import Faker

from legacy_password_hashing.password_hashing import (
    hash_ycc_password,
    verify_ycc_password,
)
from test_data.generator_config import CURRENT_YEAR
from test_data.utils.licences import generate_licences
from ycc_hull.db.entities import (
    EntranceFeeRecordEntity,
    FeeRecordEntity,
    LicenceEntity,
    MemberEntity,
    UserEntity,
)


class MemberInfo(NamedTuple):
    """A member with associated user and other entities."""

    member: MemberEntity
    user: UserEntity
    entrance_fee_record: EntranceFeeRecordEntity | None
    fee_records: list[FeeRecordEntity]
    licences: list[LicenceEntity]


_assigned_usernames: set[str] = set()


def _fake_username(first_name: str, last_name: str) -> str:
    if not first_name:
        msg = f"Invalid first name: {first_name}"
        raise ValueError(msg)
    if not last_name:
        msg = f"Invalid last name: {last_name}"
        raise ValueError(msg)

    username: str = f"{first_name[0]}{last_name[0:7]}".upper()

    if username in _assigned_usernames:
        username = _fake_username_collision(first_name, last_name)

    _assigned_usernames.add(username)
    return username


def _fake_username_collision(first_name: str, last_name: str) -> str:
    for i in range(1, 10):
        username: str = f"{first_name[0]}{last_name[0:6]}{i!s}".upper()

        if username not in _assigned_usernames:
            return username

    msg = (
        f"Could not generate username for {first_name} {last_name} - try again or "
        "improve the code"
    )
    raise AssertionError(msg)


def generate_member_infos(
    faker: Faker, licences_to_ids: dict[str, int], count: int
) -> list[MemberInfo]:
    """Generate member info with associated entities."""
    return [_generate_member_info(faker, licences_to_ids, i + 1) for i in range(count)]


def _generate_member_info(
    faker: Faker, licences_to_ids: dict[str, int], member_id: int
) -> MemberInfo:
    member = _generate_member(faker, member_id)
    return MemberInfo(
        member=member,
        user=_generate_user(faker, member),
        entrance_fee_record=_generate_member_entrance_fee_record(faker, member),
        fee_records=_generate_member_fee_records(faker, member),
        licences=generate_licences(faker, licences_to_ids, member),
    )


def _generate_member(faker: Faker, member_id: int) -> MemberEntity:
    # Make sure to eventually use all membership types
    if member_id <= 5:
        membership_type = "H"
    elif member_id <= 10:
        membership_type = "AJ"
    elif member_id <= 15:
        membership_type = "FM"
    elif member_id <= 20:
        membership_type = "T"
    elif member_id <= 25:
        membership_type = "SV"
    else:
        membership_type = "AS"

    last_name = faker.unique.last_name()
    first_name = faker.first_name()

    return MemberEntity(
        id=member_id,
        name=last_name,
        firstname=first_name,
        # birthday = Column(DATE)  # noqa: ERA001
        # nationality = Column(VARCHAR2(3))  # noqa: ERA001
        membership=membership_type,
        # temp_memb = Column(NUMBER(1, 0))  # noqa: ERA001
        # lang1 = Column(VARCHAR2(3))  # noqa: ERA001
        # lang2 = Column(VARCHAR2(3))  # noqa: ERA001
        category=_generate_member_category(faker),
        # work_address1 = Column(VARCHAR2(50))  # noqa: ERA001
        # work_address2 = Column(VARCHAR2(50))  # noqa: ERA001
        # work_towncode = Column(VARCHAR2(7))  # noqa: ERA001
        # work_town = Column(VARCHAR2(25))  # noqa: ERA001
        # work_state = Column(VARCHAR2(5))  # noqa: ERA001
        work_phone=_generate_phone_number(faker, member_id, 10),
        e_mail=f"{first_name.lower()}.{last_name.lower()}@mailinator.com",
        home_addr="~~~Ignored~~~",
        # home_towncode = Column(VARCHAR2(7))  # noqa: ERA001
        # home_town = Column(VARCHAR2(25))  # noqa: ERA001
        # home_state = Column(VARCHAR2(5))  # noqa: ERA001
        home_phone=_generate_phone_number(faker, member_id, 10),
        # mail_preference = Column(VARCHAR2(1))  # noqa: ERA001
        # favourite_mailing_post = Column(VARCHAR2(1))  # noqa: ERA001
        member_entrance=str(_generate_member_entrance(faker, membership_type)),
        cell_phone=_generate_phone_number(faker, member_id, 90),
        # gender = Column(CHAR(1))  # noqa: ERA001
        # valid_until_date = Column(DATE)  # noqa: ERA001
        # last_updated_date = Column(DATE)  # noqa: ERA001
        # valid_from_date = Column(DATE)  # noqa: ERA001
    )


def _generate_phone_number(
    faker: Faker, member_id: int, truth_probability: int
) -> str | None:
    return (
        _fake_phone_number(faker)
        if member_id == 2 or faker.pybool(truth_probability=truth_probability)
        else None
    )


def _fake_phone_number(faker: Faker) -> str:
    country_code = "+41" if faker.pybool(truth_probability=75) else "+33"
    number = faker.random_number(digits=7)
    return f"{country_code}00{number:07}"


def _generate_member_category(faker: Faker) -> str:
    if faker.pybool(truth_probability=50):
        # *C*ERN
        return "C"
    if faker.pybool(truth_probability=45):
        # *E*xternal
        return "E"
    # *R*elative
    return "R"


def _generate_member_entrance(faker: Faker, membership_type: str) -> int:
    if membership_type == "H":
        return faker.pyint(min_value=1990, max_value=CURRENT_YEAR - 10)
    if faker.pybool(truth_probability=80):
        return faker.pyint(min_value=1990, max_value=CURRENT_YEAR - 1)
    return CURRENT_YEAR


def _generate_user(faker: Faker, member: MemberEntity) -> UserEntity:
    username = _fake_username(member.firstname, member.name)
    password_hash = hash_ycc_password(username)

    if not verify_ycc_password(username, password_hash):
        msg = f"Password hash verification failed for {username}"
        raise AssertionError(msg)

    return UserEntity(
        member_id=member.id,
        logon_id=username,
        session_id=None,
        session_date=None,
        logon_pass2=password_hash,
        pass_reset_key=None,
        pass_reset_exp=None,
        last_changed=faker.date_time_between(
            start_date=date(CURRENT_YEAR - 2, 1, 1), end_date=date(CURRENT_YEAR, 4, 1)
        ),
    )


def _generate_member_entrance_fee_record(
    faker: Faker,
    member: MemberEntity,
) -> EntranceFeeRecordEntity | None:
    financial_year: int | None = (
        int(member.member_entrance) if faker.pybool(truth_probability=90) else None
    )
    return (
        EntranceFeeRecordEntity(
            member_id=member.id,
            year_f=financial_year,
        )
        if faker.pybool(truth_probability=90)
        else None
    )


def _generate_member_fee_records(
    faker: Faker, member: MemberEntity
) -> list[FeeRecordEntity]:
    fee_records: list[FeeRecordEntity] = []
    if member.id == 2:
        # Fixed honorary member without any payments
        return fee_records

    # This test data generator really tries to simulate the existing database,
    # e.g., missing payment records
    for year in range(int(member.member_entrance), CURRENT_YEAR + 1):
        if faker.pybool(truth_probability=95):
            fee_records.append(_create_fee_record(faker, member, year, 350))

        if faker.pybool(truth_probability=10):
            fee_records.append(_create_fee_record(faker, member, year, 170))
        elif faker.pybool(truth_probability=5):
            fee_records.append(_create_fee_record(faker, member, year, 90))

    return fee_records


def _create_fee_record(
    faker: Faker, member: MemberEntity, financial_year: int, fee: int
) -> FeeRecordEntity:
    paid_date: date = faker.date_between(
        start_date=date(financial_year - 1, 11, 1), end_date=date(financial_year, 4, 1)
    )
    entered_date: datetime = faker.date_time_between(
        start_date=paid_date, end_date=paid_date + timedelta(days=10)
    )

    return FeeRecordEntity(
        member_id=member.id,
        year_f=financial_year,
        paid_date=paid_date,
        paid_mode=_generate_paid_mode(faker),
        fee=fee,
        entered_date=entered_date,
        payment_reason=None,
    )


def _generate_paid_mode(faker: Faker) -> str | None:
    if faker.pybool(truth_probability=80):
        return "UBS"
    if faker.pybool(truth_probability=50):
        return "XXX"

    return None


def get_member_info_by_id(member_id: int, member_infos: list[MemberInfo]) -> MemberInfo:
    """Find a member info by member ID."""
    return next(
        filter(lambda member_info: member_info.member.id == member_id, member_infos)
    )


def get_members_with_payment_current_year(
    member_infos: list[MemberInfo],
) -> Iterator[MemberInfo]:
    """Filter members who paid fees this year."""
    return filter(_paid_fee_current_year, member_infos)


def get_members_without_payment_current_year(
    member_infos: list[MemberInfo],
) -> Iterator[MemberInfo]:
    """Filter members who did not pay fees this year."""
    return filter(
        _did_not_pay_fee_current_year,
        member_infos,
    )


def _paid_fee_current_year(member_info: MemberInfo) -> bool:
    search = filter(
        lambda fee_record: fee_record.year_f == CURRENT_YEAR,
        member_info.fee_records,
    )
    return any(search)


def _did_not_pay_fee_current_year(member_info: MemberInfo) -> bool:
    return not _paid_fee_current_year(member_info)


def get_members_with_licence(
    member_infos: list[MemberInfo], licence_info_id: int
) -> Iterator[MemberInfo]:
    """Filter members who have a specific licence."""
    return filter(
        lambda member_info: _has_licence(member_info, licence_info_id), member_infos
    )


def get_members_without_licence(
    member_infos: list[MemberInfo], licence_info_id: int
) -> Iterator[MemberInfo]:
    """Filter members who lack a specific licence."""
    return filter(
        lambda member_info: _lacks_licence(member_info, licence_info_id), member_infos
    )


def _has_licence(member_info: MemberInfo, licence_info_id: int) -> bool:
    search = filter(
        lambda licence: licence.licence_id == licence_info_id,
        member_info.licences,
    )
    return any(search)


def _lacks_licence(member_info: MemberInfo, licence_info_id: int) -> bool:
    return not _has_licence(member_info, licence_info_id)
