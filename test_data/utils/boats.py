"""
Test data generator component for boats.
"""
import copy
import json
from test_data.generator_config import BOATS_EXPORTED_JSON_FILE
from ycc_hull.db.entities import BoatEntity


def generate_boats() -> list[BoatEntity]:
    # Remove maintainers from the exported file
    with open(BOATS_EXPORTED_JSON_FILE, "r", encoding="utf-8") as file:
        return [_create_boat(boat) for boat in json.load(file)["results"][0]["items"]]


def _create_boat(exported_boat: dict) -> BoatEntity:
    boat = copy.copy(exported_boat)
    boat["class_"] = boat["class"]
    del boat["class"]
    boat["maintainer_id"] = None
    boat["maintainer_id2"] = None
    return BoatEntity(**boat)
