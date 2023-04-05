"""
Test data generator configuration.
"""
from datetime import date
from os import path

_SCRIPT_DIR = path.dirname(path.realpath(__file__))

CURRENT_YEAR = date.today().year
MEMBER_COUNT = 300

BOATS_JSON_FILE = f"{_SCRIPT_DIR}/generated/Boats.json"
BOATS_EXPORTED_JSON_FILE = f"{_SCRIPT_DIR}/exported/BOATS_DATA_TABLE.json-formatted"
ENTRANCE_FEE_RECORDS_JSON_FILE = f"{_SCRIPT_DIR}/generated/EntranceFeeRecords.json"
FEE_RECORDS_JSON_FILE = f"{_SCRIPT_DIR}/generated/FeeRecords.json"
INFOLICENCES_EXPORTED_JSON_FILE = (
    f"{_SCRIPT_DIR}/exported/INFOLICENCES_DATA_TABLE.json-formatted"
)
LICENCES_JSON_FILE = f"{_SCRIPT_DIR}/generated/Licences.json"
MEMBERS_JSON_FILE = f"{_SCRIPT_DIR}/generated/Members.json"
USERS_JSON_FILE = f"{_SCRIPT_DIR}/generated/Users.json"
