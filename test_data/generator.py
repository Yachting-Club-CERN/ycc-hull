"""
Test data generator. Some data can be directly used as it was exported, some needs tailoring, some have to be generated.
"""

import json
from collections.abc import Sequence
from datetime import date, datetime
from os import path
from typing import Any

from faker import Faker

from test_data.generator_config import (BOATS_JSON_FILE,
                                        ENTRANCE_FEE_RECORDS_JSON_FILE,
                                        FEE_RECORDS_JSON_FILE,
                                        HELPER_TASK_CATEGORIES_JSON_FILE,
                                        HELPER_TASK_HELPERS_JSON_FILE,
                                        HELPER_TASKS_JSON_FILE,
                                        HELPERS_APP_PERMISSIONS_JSON_FILE,
                                        HOLIDAYS_EXPORTED_JSON_FILE,
                                        HOLIDAYS_JSON_FILE,
                                        LICENCE_INFOS_JSON_FILE,
                                        LICENCES_JSON_FILE, MEMBER_COUNT,
                                        MEMBERS_JSON_FILE, USERS_JSON_FILE)
from test_data.utils.boats import generate_boats
from test_data.utils.helpers import (generate_helper_task_categories,
                                     generate_helper_task_helpers,
                                     generate_helper_tasks,
                                     generate_helpers_app_permissions)
from test_data.utils.holidays import generate_holidays
from test_data.utils.licence_infos import generate_licence_infos
from test_data.utils.members import (generate_member_infos,
                                     get_member_info_by_id,
                                     get_members_with_licence,
                                     get_members_with_payment_current_year,
                                     get_members_without_licence,
                                     get_members_without_payment_current_year)
from ycc_hull.db.entities import BaseEntity

faker: Faker = Faker()
Faker.seed(2021)


def to_json_dict(obj: Any) -> dict:
    # This will cause the importer to handle certain types as objects, not strings
    if isinstance(obj, datetime):
        return {"@type": "datetime", "value": obj.isoformat()}
    if isinstance(obj, date):
        return {"@type": "date", "value": obj.isoformat()}

    raise TypeError(f"Cannot serialize type: {type(obj)}")


def read_json_file(file_path: str, cls: type[BaseEntity]) -> Sequence[BaseEntity]:
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


def generate(force_regenerate: bool = False) -> None:
    if path.exists(HOLIDAYS_EXPORTED_JSON_FILE) and not force_regenerate:
        print("== Skipping holidays")
    else:
        print("== Generating holidays...")
        write_json_file(HOLIDAYS_JSON_FILE, generate_holidays())

    licence_infos = generate_licence_infos()
    licences_to_ids = {info.nlicence: info.infoid for info in licence_infos}

    if path.exists(LICENCE_INFOS_JSON_FILE) and not force_regenerate:
        print("== Skipping licence infos")
    else:
        print("== Generating licence infos...")
        write_json_file(LICENCE_INFOS_JSON_FILE, licence_infos)

    if path.exists(MEMBERS_JSON_FILE) and not force_regenerate:
        print("== Skipping members")
    else:
        print(
            "== Generating members (and users, entrance fee records, fee records and licences)..."
        )
        member_infos = generate_member_infos(faker, licences_to_ids, MEMBER_COUNT)
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
        licences = [
            licence for member_info in member_infos for licence in member_info.licences
        ]

        write_json_file(MEMBERS_JSON_FILE, members)
        write_json_file(USERS_JSON_FILE, users)
        write_json_file(ENTRANCE_FEE_RECORDS_JSON_FILE, entrance_fee_records)
        write_json_file(FEE_RECORDS_JSON_FILE, fee_records)
        write_json_file(LICENCES_JSON_FILE, licences)

        print(
            "Member with id=1 (honorary, Helpers App admin): "
            + get_member_info_by_id(1, member_infos).user.logon_id
        )
        print(
            "Member with id=2 (honorary, no fee paid, Helpers App editor): "
            + get_member_info_by_id(2, member_infos).user.logon_id
        )
        print(
            "Member with id=3 (honorary, Helpers App editor): "
            + get_member_info_by_id(3, member_infos).user.logon_id
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
        print(
            "Has M key: "
            + next(get_members_with_licence(member_infos[100:], 9)).user.logon_id
        )
        print(
            "Lacks M key: "
            + next(get_members_without_licence(member_infos[100:], 9)).user.logon_id
        )

    if path.exists(BOATS_JSON_FILE) and not force_regenerate:
        print("== Skipping boats")
    else:
        print("== Generating boats...")
        write_json_file(BOATS_JSON_FILE, generate_boats())

    if path.exists(HELPER_TASKS_JSON_FILE) and not force_regenerate:
        print("== Skipping helper data")
    else:
        print("== Generating helpers data (categories, tasks, helpers)...")
        write_json_file(
            HELPERS_APP_PERMISSIONS_JSON_FILE, generate_helpers_app_permissions()
        )
        write_json_file(
            HELPER_TASK_CATEGORIES_JSON_FILE, generate_helper_task_categories()
        )
        write_json_file(HELPER_TASKS_JSON_FILE, generate_helper_tasks())
        write_json_file(HELPER_TASK_HELPERS_JSON_FILE, generate_helper_task_helpers())


def regenerate() -> None:
    generate(True)


if __name__ == "__main__":
    regenerate()
