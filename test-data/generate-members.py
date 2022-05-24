import json
from typing import Set, List

from faker import Faker

from ycc_hull.db.models import Member

faker: Faker = Faker()
assigned_usernames: Set[str] = set()


def fake_username(first_name: str, last_name: str) -> str:
    if not first_name:
        raise ValueError(f"Invalid first name: f{first_name}")
    if not last_name:
        raise ValueError(f"Invalid last name: f{last_name}")

    username: str = f"{first_name[0]}{last_name[1:8]}".upper()

    if username in assigned_usernames:
        username = _fake_username_collision(first_name, last_name)

    assigned_usernames.add(username)
    return username


def _fake_username_collision(first_name: str, last_name: str) -> str:
    for i in range(1, 10):
        username: str = f"{first_name[0]}{last_name[1:7]}{str(i)}".upper()

        if username not in assigned_usernames:
            return username

    raise Exception(
        f"Could not generate username for {first_name} {last_name} - try again or improve the code")


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

    return Member(
        id=id,
        name=faker.unique.last_name(),
        firstname=faker.first_name(),
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
        # e_mail = Column(VARCHAR2(50))
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


def generate_ycc_logon(members: List[Member]):
    # TODO
    # username = fake_username(first_name, last_name)
    pass


if __name__ == "__main__":
    members = generate_members(300)
    with open('Members.json', 'w') as fp:
        json.dump([member.dict() for member in members], fp, indent=2)
        print('== Generated members')
