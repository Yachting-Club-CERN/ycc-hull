"""
Test data generator. Some data can be directly used as it was exported, some needs tailoring, some have to be generated.
"""
import copy
import json
from datetime import date, datetime, timedelta
from os import path
from typing import Any, Iterator, List, NamedTuple, Optional, Sequence, Set, Type

from faker import Faker

from legacy_password_hashing.password_hashing import (
    hash_ycc_password,
    verify_ycc_password,
)
from ycc_hull.db.entities import (
    BaseEntity,
    BoatEntity,
    EntranceFeeRecordEntity,
    FeeRecordEntity,
    MemberEntity,
    UserEntity,
)

SCRIPT_DIR = path.dirname(path.realpath(__file__))

CURRENT_YEAR = date.today().year
MEMBER_COUNT = 300
BOATS_JSON_FILE = f"{SCRIPT_DIR}/generated/Boats.json"
BOATS_EXPORTED_JSON_FILE = f"{SCRIPT_DIR}/exported/BOATS_DATA_TABLE.json-formatted"
ENTRANCE_FEE_RECORDS_JSON_FILE = f"{SCRIPT_DIR}/generated/EntranceFeeRecords.json"
FEE_RECORDS_JSON_FILE = f"{SCRIPT_DIR}/generated/FeeRecords.json"
MEMBERS_JSON_FILE = f"{SCRIPT_DIR}/generated/Members.json"
USERS_JSON_FILE = f"{SCRIPT_DIR}/generated/Users.json"

MemberInfo = NamedTuple(
    "MemberInfo",
    [
        ("member", MemberEntity),
        ("user", UserEntity),
        ("entrance_fee_record", Optional[EntranceFeeRecordEntity]),
        ("fee_records", List[FeeRecordEntity]),
    ],
)

faker: Faker = Faker()
Faker.seed(2021)

assigned_usernames: Set[str] = set()


def fake_username(first_name: str, last_name: str) -> str:
    if not first_name:
        raise ValueError(f"Invalid first name: f{first_name}")
    if not last_name:
        raise ValueError(f"Invalid last name: f{last_name}")

    username: str = f"{first_name[0]}{last_name[0:7]}".upper()

    if username in assigned_usernames:
        username = _fake_username_collision(first_name, last_name)

    assigned_usernames.add(username)
    return username


def _fake_username_collision(first_name: str, last_name: str) -> str:
    for i in range(1, 10):
        username: str = f"{first_name[0]}{last_name[0:6]}{str(i)}".upper()

        if username not in assigned_usernames:
            return username

    raise AssertionError(
        f"Could not generate username for {first_name} {last_name} - try again or improve the code"
    )


def generate_member_infos(count: int) -> List[MemberInfo]:
    return [generate_member_info(i + 1) for i in range(0, count)]


def generate_member_info(member_id: int) -> MemberInfo:
    member = generate_member(member_id)
    return MemberInfo(
        member=member,
        user=generate_user(member),
        entrance_fee_record=generate_member_entrance_fee_record(member),
        fee_records=generate_member_fee_records(member),
    )


def generate_member(member_id: int) -> MemberEntity:
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
        # birthday = Column(DATE)
        # nationality = Column(VARCHAR2(3))
        membership=membership_type,
        # temp_memb = Column(NUMBER(1, 0))
        # lang1 = Column(VARCHAR2(3))
        # lang2 = Column(VARCHAR2(3))
        category=generate_member_category(),
        # work_address1 = Column(VARCHAR2(50))
        # work_address2 = Column(VARCHAR2(50))
        # work_towncode = Column(VARCHAR2(7))
        # work_town = Column(VARCHAR2(25))
        # work_state = Column(VARCHAR2(5))
        work_phone=generate_phone_number(member_id, 10),
        e_mail=f"{first_name}.{last_name}@mailinator.com",
        home_addr="~~~Ignored~~~",
        # home_towncode = Column(VARCHAR2(7))
        # home_town = Column(VARCHAR2(25))
        # home_state = Column(VARCHAR2(5))
        home_phone=generate_phone_number(member_id, 10),
        # mail_preference = Column(VARCHAR2(1))
        # favourite_mailing_post = Column(VARCHAR2(1))
        member_entrance=generate_member_entrance(membership_type),
        cell_phone=generate_phone_number(member_id, 90),
        # gender = Column(CHAR(1))
        # valid_until_date = Column(DATE)
        # last_updated_date = Column(DATE)
        # valid_from_date = Column(DATE)
    )


def generate_phone_number(member_id: int, truth_probability: int) -> Optional[str]:
    return (
        fake_phone_number()
        if member_id == 2 or faker.pybool(truth_probability=truth_probability)
        else None
    )


def fake_phone_number() -> str:
    country_code = "+41" if faker.pybool(truth_probability=75) else "+33"
    number = faker.random_number(digits=7)
    return f"{country_code}00{number:07}"


def generate_member_category() -> str:
    if faker.pybool(truth_probability=50):
        # *C*ERN
        return "C"
    if faker.pybool(truth_probability=45):
        # *E*xternal
        return "E"
    # *R*elative
    return "R"


def generate_member_entrance(membership_type: str) -> int:
    if membership_type == "H":
        return faker.pyint(min_value=1990, max_value=CURRENT_YEAR - 10)
    if faker.pybool(truth_probability=80):
        return faker.pyint(min_value=1990, max_value=CURRENT_YEAR - 1)
    return CURRENT_YEAR


def generate_user(member: MemberEntity) -> UserEntity:
    username = fake_username(member.firstname, member.name)
    password_hash = hash_ycc_password(username)

    if not verify_ycc_password(username, password_hash):
        raise AssertionError(f"Password hash verification failed for {username}")

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


def generate_member_entrance_fee_record(
    member: MemberEntity,
) -> Optional[EntranceFeeRecordEntity]:
    financial_year: Optional[int] = (
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


def generate_member_fee_records(member: MemberEntity) -> List[FeeRecordEntity]:
    fee_records: List[FeeRecordEntity] = []
    if member.id == 2:
        # Fixed honorary member without any payments
        return fee_records

    # This test data generator really tries to simulate the existing database, e.g., missing payment records from the database
    for year in range(int(member.member_entrance), CURRENT_YEAR + 1):
        if faker.pybool(truth_probability=95):
            fee_records.append(create_fee_record(member, year, 350))

        if faker.pybool(truth_probability=10):
            fee_records.append(create_fee_record(member, year, 170))
        elif faker.pybool(truth_probability=5):
            fee_records.append(create_fee_record(member, year, 90))

    return fee_records


def create_fee_record(
    member: MemberEntity, financial_year: int, fee: int
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
        paid_mode=generate_paid_mode(),
        fee=fee,
        entered_date=entered_date,
    )


def generate_paid_mode() -> Optional[str]:
    if faker.pybool(truth_probability=80):
        return "UBS"
    if faker.pybool(truth_probability=50):
        return "XXX"

    return None


def generate_boats() -> List[BoatEntity]:
    # Remove maintainers from the exported file
    with open(BOATS_EXPORTED_JSON_FILE, "r", encoding="utf-8") as file:
        return [generate_boat(boat) for boat in json.load(file)["results"][0]["items"]]


def generate_boat(exported_boat: dict) -> BoatEntity:
    boat = copy.copy(exported_boat)
    boat["class_"] = boat["class"]
    del boat["class"]
    boat["maintainer_id"] = None
    boat["maintainer_id2"] = None
    return BoatEntity(**boat)


def to_json_dict(obj: Any) -> dict:
    # This will cause the importer to handle certain types as objects, not strings
    if isinstance(obj, datetime):
        return {"@type": "datetime", "@value": obj.isoformat()}
    if isinstance(obj, date):
        return {"@type": "date", "@value": obj.isoformat()}

    raise TypeError(f"Cannot serialize type: {type(obj)}")


def read_json_file(file_path: str, cls: Type[BaseEntity]) -> Sequence[BaseEntity]:
    print(f"== Reading from {file_path} ...")
    with open(file_path, "r", encoding="utf-8") as file:
        return [cls(**entry) for entry in json.load(file)]


def write_json_file(file_path: str, entries: Sequence[BaseEntity]) -> None:
    print(f"Writing {file_path} ...")
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            [entry.dict() for entry in entries],
            file,
            default=to_json_dict,
            indent=2,
        )


def regenerate() -> None:
    generate(True)


def get_member_info_by_id(member_id: int, member_infos: List[MemberInfo]) -> MemberInfo:
    return next(
        filter(lambda member_info: member_info.member.id == member_id, member_infos)
    )


def get_members_with_payment_current_year(
    member_infos: List[MemberInfo],
) -> Iterator[MemberInfo]:
    return filter(_paid_fee_current_year, member_infos)


def get_members_without_payment_current_year(
    member_infos: List[MemberInfo],
) -> Iterator[MemberInfo]:
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


def generate(force_regenerate: bool = False) -> None:
    if path.exists(MEMBERS_JSON_FILE) and not force_regenerate:
        print("== Skipping members")
    else:
        print(
            "== Generating members (and users, entrance fee records and fee records)..."
        )
        member_infos = generate_member_infos(MEMBER_COUNT)
        members = [member_info.member for member_info in member_infos]
        users = [member_info.user for member_info in member_infos]
        entrance_fee_records = [
            member_info.entrance_fee_record
            for member_info in member_infos
            if member_info.entrance_fee_record
        ]
        fee_records = [
            fee_record
            for member_info in member_infos
            for fee_record in member_info.fee_records
        ]

        write_json_file(MEMBERS_JSON_FILE, members)
        write_json_file(USERS_JSON_FILE, users)
        write_json_file(ENTRANCE_FEE_RECORDS_JSON_FILE, entrance_fee_records)
        write_json_file(FEE_RECORDS_JSON_FILE, fee_records)

        print(
            "Member with id=2 (honorary, no fee paid): "
            + get_member_info_by_id(2, member_infos).user.logon_id
        )

        print(
            "Active with payment: "
            + next(
                get_members_with_payment_current_year(member_infos[100:])
            ).user.logon_id
        )
        print(
            "Inactive member: "
            + next(
                get_members_without_payment_current_year(member_infos[100:])
            ).user.logon_id
        )

    if path.exists(BOATS_JSON_FILE) and not force_regenerate:
        print("== Skipping boats")
    else:
        print("== Generating boats...")
        write_json_file(BOATS_JSON_FILE, generate_boats())


if __name__ == "__main__":
    generate(True)
