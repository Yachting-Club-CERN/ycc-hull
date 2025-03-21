"""
Application constants.
"""

import os

_CONFIG_DIRECTORY = "conf"


def find_config_file() -> str:
    active_dev_files = [
        f
        for f in os.listdir(_CONFIG_DIRECTORY)
        if f.startswith("config-dev") and f.endswith("-active.json")
    ]

    active_dev_file_count = len(active_dev_files)

    if active_dev_file_count > 1:
        raise AssertionError(
            f"Multiple active development configuration files found: {active_dev_files}"
        )
    elif active_dev_file_count == 1:
        config_file = f"{_CONFIG_DIRECTORY}/{active_dev_files[0]}"
        # Using print as logging is not configured yet at this point
        print("!!!")
        print(f"!!! Using development configuration file: {config_file}")
        print("!!!")
        return config_file
    else:
        config_file = f"{_CONFIG_DIRECTORY}/config.json"
        if not os.path.exists(config_file):
            raise AssertionError(f"Missing configuration file: {config_file}")
        return config_file


CONFIG_FILE = find_config_file()

LOGGING_CONFIG_FILE = f"{_CONFIG_DIRECTORY}/logging.json"

TIME_ZONE_ID = "Europe/Zurich"
