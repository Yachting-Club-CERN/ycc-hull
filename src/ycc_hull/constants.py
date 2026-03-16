"""Application constants."""

from pathlib import Path

_CONFIG_DIRECTORY = Path("conf")


def find_config_file() -> Path:
    """Find and return the active config file path."""
    active_dev_files = [
        f.name
        for f in _CONFIG_DIRECTORY.iterdir()
        if f.name.startswith("config-dev") and f.name.endswith("-active.json")
    ]

    active_dev_file_count = len(active_dev_files)

    if active_dev_file_count > 1:
        msg = (
            f"Multiple active development configuration files found: {active_dev_files}"
        )
        raise AssertionError(msg)

    if active_dev_file_count == 1:
        config_file = _CONFIG_DIRECTORY / active_dev_files[0]
        # Using print as logging is not configured yet at this point
        print("!!!")  # noqa: T201
        print(f"!!! Using development configuration file: {config_file}")  # noqa: T201
        print("!!!")  # noqa: T201
        return config_file

    config_file = _CONFIG_DIRECTORY / "config.json"
    if not config_file.exists():
        msg = f"Missing configuration file: {config_file}"
        raise AssertionError(msg)
    return config_file


CONFIG_FILE: Path = find_config_file()

LOGGING_CONFIG_FILE = _CONFIG_DIRECTORY / "logging.conf"

TIME_ZONE_ID = "Europe/Zurich"
