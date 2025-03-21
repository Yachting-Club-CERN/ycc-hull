"""
Test data generator component for licences.
"""

from faker import Faker

from test_data.generator_config import CURRENT_YEAR
from ycc_hull.db.entities import LicenceEntity, MemberEntity

_LICENCES_LEVEL1 = ["CC", "D", "Y"]
_LICENCES_LEVEL2 = ["C", "EC", "ED", "GS", "SU", "J", "J7"]
_LICENCES_LEVEL3 = ["D3"]
_LICENCES_OTHER = ["M"]


def generate_licences(
    faker: Faker, licences_to_ids: dict[str, int], member: MemberEntity
) -> list[LicenceEntity]:
    return [
        _create_licence(faker, member, licences_to_ids[licence])
        for licence in sorted(_generate_licence_list(faker, member))
    ]


def _create_licence(
    faker: Faker, member: MemberEntity, licence_id: int
) -> LicenceEntity:
    return LicenceEntity(
        member_id=member.id,
        licence_id=licence_id,
        lyear=-1,  # Ignored for now
        test_id=None,  # Ignored for now
        lcomments=None,  # Ignored for now
        status=1 if faker.pybool(truth_probability=95) else 0,  # Rudimentary
    )


def _generate_licence_list(faker: Faker, member: MemberEntity) -> set[str]:
    member_entrance = int(member.member_entrance)

    if member_entrance >= CURRENT_YEAR or faker.pybool(truth_probability=10):
        return set()

    licences: set[str] = set()
    if member_entrance < CURRENT_YEAR - 5 and faker.pybool(truth_probability=10):
        return set(
            _LICENCES_LEVEL1 + _LICENCES_LEVEL2 + _LICENCES_LEVEL3 + _LICENCES_OTHER
        )

    _maybe_add_level1(faker, licences)
    _maybe_add_level2_keelboat(faker, licences)
    _maybe_add_level2_29er_cat(faker, licences)
    _maybe_add_j_j7_d3(faker, licences)

    if faker.pybool(truth_probability=20):
        licences.add("M")

    return licences


def _maybe_add_level1(faker: Faker, licences: set[str]) -> None:
    if faker.pybool(truth_probability=40):
        licences.add("Y")
    if faker.pybool(truth_probability=40):
        licences.add("D")
    if faker.pybool(truth_probability=20):
        licences.add("CC")


def _maybe_add_level2_keelboat(faker: Faker, licences: set[str]) -> None:
    if "Y" not in licences or len(licences) < 2:
        return

    if faker.pybool(truth_probability=20):
        licences.add("SU")
        if faker.pybool(truth_probability=70):
            licences.add("GS")
    elif faker.pybool(truth_probability=15):
        licences.add("GS")


def _maybe_add_level2_29er_cat(faker: Faker, licences: set[str]) -> None:
    if "D" not in licences:
        return

    if faker.pybool(truth_probability=20):
        licences.add("C")
        if faker.pybool(truth_probability=90):
            licences.add("EC")

    if faker.pybool(truth_probability=20):
        licences.add("ED")


def _maybe_add_j_j7_d3(faker: Faker, licences: set[str]) -> None:
    if "SU" in licences:
        if faker.pybool(truth_probability=90):
            licences.add("J")
        if faker.pybool(truth_probability=90):
            licences.add("J7")

    if "GS" in licences and faker.pybool(truth_probability=50):
        licences.add("D3")
