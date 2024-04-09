"""
Application constants.
"""

import os

CONFIG_FILE = (
    "conf/config-dev.json"
    if os.path.exists("conf/config-dev.json")
    else "conf/config.json"
)

LOGGING_CONFIG_FILE = "conf/logging.conf"

TIME_ZONE_ID = "Europe/Zurich"
