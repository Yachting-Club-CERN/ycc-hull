import json
from datetime import date
from os import path
from typing import List, Set, Type

from faker import Faker

from ycc_hull.auth.password_hashing import hash_ycc_password
from ycc_hull.db.models import Member, ModelBase, User

MEMBER_COUNT = 300
MEMBERS_JSON_FILE = "Members.json"
USERS_JSON_FILE = "Users.json"

faker: Faker = Faker()
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

    raise Exception(
        f"Could not generate username for {first_name} {last_name} - try again or improve the code"
    )


def generate_members(count: int) -> List[Member]:
    return [generate_member(i + 1) for i in range(0, count)]


def generate_member(id: int) -> Member:
    # Make sure to eventually use all membership types
    if id < 5:
        membership_type = "H"
    elif id < 10:
        membership_type = "AJ"
    elif id < 15:
        membership_type = "FM"
    elif id < 20:
        membership_type = "T"
    elif id < 25:
        membership_type = "SV"
    else:
        membership_type = "AS"

    last_name = faker.unique.last_name()
    first_name = faker.first_name()

    return Member(
        id=id,
        name=last_name,
        firstname=first_name,
        # birthday = Column(DATE)
        # nationality = Column(VARCHAR2(3))
        membership=membership_type,
        # temp_memb = Column(NUMBER(1, 0))
        # lang1 = Column(VARCHAR2(3))
        # lang2 = Column(VARCHAR2(3))
        category="C" if faker.pybool() else "E",  # *C*ERN or *E*xternal
        # work_address1 = Column(VARCHAR2(50))
        # work_address2 = Column(VARCHAR2(50))
        # work_towncode = Column(VARCHAR2(7))
        # work_town = Column(VARCHAR2(25))
        # work_state = Column(VARCHAR2(5))
        # work_phone = Column(VARCHAR2(25))
        e_mail=f"{first_name}.{last_name}@mailinator.com",
        home_addr="~~~Ignored~~~",
        # home_towncode = Column(VARCHAR2(7))
        # home_town = Column(VARCHAR2(25))
        # home_state = Column(VARCHAR2(5))
        # home_phone = Column(VARCHAR2(25))
        # mail_preference = Column(VARCHAR2(1))
        # favourite_mailing_post = Column(VARCHAR2(1))
        member_entrance=faker.pyint(min_value=1990, max_value=2022),
        # cell_phone = Column(VARCHAR2(25))
        # gender = Column(CHAR(1))
        # valid_until_date = Column(DATE)
        # last_updated_date = Column(DATE)
        # valid_from_date = Column(DATE)
    )


def generate_users(members: List[Member]) -> List[User]:
    return [generate_user(member) for member in members]


def generate_user(member: Member) -> User:
    username = fake_username(member.firstname, member.name)
    return User(
        member_id=member.id,
        logon_id=username,
        session_id=None,
        session_date=None,
        logon_pass2=hash_ycc_password(username),
        pass_reset_key=None,
        pass_reset_exp=None,
        last_changed=faker.date_between(
            start_date=date(2021, 1, 1), end_date=date(2022, 5, 1)
        ),
    )


def to_oracle_data_json(obj):
    if isinstance(obj, date):
        return obj.strftime("%d-%b-%Y").upper()

    raise TypeError(f"Cannot serialize type: {type(obj)}")


def read_json_file(file: str, cls: Type[ModelBase]) -> List[ModelBase]:
    print(f"== Reading from {file} ...")
    with open(file, "r") as fp:
        return [cls(**entry) for entry in json.load(fp)]


def write_json_file(file: str, entries: List[ModelBase]) -> None:
    print(f"Writing {file} ...")
    with open(file, "w") as fp:
        json.dump(
            [entry.dict() for entry in entries],
            fp,
            default=to_oracle_data_json,
            indent=2,
        )


def generate():
    if path.exists(MEMBERS_JSON_FILE):
        members = read_json_file(MEMBERS_JSON_FILE, Member)
    else:
        print("== Generating members...")
        members = generate_members(MEMBER_COUNT)
        write_json_file(MEMBERS_JSON_FILE, members)

    if path.exists(USERS_JSON_FILE):
        print("== Skipping users")
    else:
        print("== Generating users...")
        write_json_file(USERS_JSON_FILE, generate_users(members))


if __name__ == "__main__":
    generate()
