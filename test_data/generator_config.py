"""
Test data generator configuration.
"""

from datetime import date
from os import path

_SCRIPT_DIR = path.dirname(path.realpath(__file__))

CURRENT_YEAR = date.today().year
MEMBER_COUNT = 300

# Holidays
HOLIDAYS_EXPORTED_JSON_FILE = (
    f"{_SCRIPT_DIR}/exported/HOLIDAYS_DATA_TABLE.json-formatted"
)
HOLIDAYS_JSON_FILE = f"{_SCRIPT_DIR}/generated/Holidays.json"

# Members & Licences
ENTRANCE_FEE_RECORDS_JSON_FILE = f"{_SCRIPT_DIR}/generated/EntranceFeeRecords.json"
FEE_RECORDS_JSON_FILE = f"{_SCRIPT_DIR}/generated/FeeRecords.json"
INFOLICENCES_EXPORTED_JSON_FILE = (
    f"{_SCRIPT_DIR}/exported/INFOLICENCES_DATA_TABLE.json-formatted"
)
LICENCES_JSON_FILE = f"{_SCRIPT_DIR}/generated/Licences.json"
MEMBERS_JSON_FILE = f"{_SCRIPT_DIR}/generated/Members.json"
MEMBERSHIP_EXPORTED_JSON_FILE = (
    f"{_SCRIPT_DIR}/exported/MEMBERSHIP_DATA_TABLE.json-formatted"
)
USERS_JSON_FILE = f"{_SCRIPT_DIR}/generated/Users.json"

# Boats
BOATS_JSON_FILE = f"{_SCRIPT_DIR}/generated/Boats.json"
BOATS_EXPORTED_JSON_FILE = f"{_SCRIPT_DIR}/exported/BOATS_DATA_TABLE.json-formatted"

# Helpers
HELPERS_APP_PERMISSIONS_JSON_FILE = (
    f"{_SCRIPT_DIR}/generated/HelpersAppPermissions.json"
)
HELPER_TASK_CATEGORIES_JSON_FILE = f"{_SCRIPT_DIR}/generated/HelperTaskCategories.json"
HELPER_TASKS_JSON_FILE = f"{_SCRIPT_DIR}/generated/HelperTasks.json"
HELPER_TASK_HELPERS_JSON_FILE = f"{_SCRIPT_DIR}/generated/HelperTaskHelpers.json"
