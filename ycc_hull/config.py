"""
Application configuration.
"""
import json
import os

from ycc_hull.models.config import Config

_CONFIG_FILE = "config.json"
CONFIG: Config


if os.path.isfile(_CONFIG_FILE):
    with open(_CONFIG_FILE, "r", encoding="utf-8") as file:
        _config_data = json.load(file)
        CONFIG = Config(**_config_data)
else:
    raise AssertionError(f"Missing configuration file: {_CONFIG_FILE}")
