"""
Test data generator component for licence infos.
"""

import copy
import json

from test_data.generator_config import LICENCE_INFOS_EXPORTED_JSON_FILE
from ycc_hull.db.entities import LicenceInfoEntity


def generate_licence_infos() -> list[LicenceInfoEntity]:
    with open(LICENCE_INFOS_EXPORTED_JSON_FILE, "r", encoding="utf-8") as file:
        return [
            _create_licence_info(boat)
            for boat in json.load(file)["results"][0]["items"]
        ]


def _create_licence_info(exported_licence_info: dict) -> LicenceInfoEntity:
    licence_info = copy.copy(exported_licence_info)

    for key in [
        "ncourse",
        "nkey",
        "coursefee",
        "course_name",
        "course_active",
        "course_level",
    ]:
        if licence_info[key] == "":
            licence_info[key] = None

    return LicenceInfoEntity(**licence_info)
