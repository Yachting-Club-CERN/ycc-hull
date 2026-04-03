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

SURVEILLANCE_TASK_PREFIX = "Surveillance"
SURVEILLANCE_SIGN_UP_LIMIT_MONTH = 5
SURVEILLANCE_SIGN_UP_LIMIT_DAY = 1
SURVEILLANCE_SIGN_UP_LIMIT_STR = "1 May"

# Only these are supported - do not rely on OS specific MIME type databases
ATTACHMENT_ALLOWED_EXTENSIONS_TO_MIME_TYPES: dict[str, str] = {
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
ATTACHMENT_MAX_DESCRIPTION_LENGTH = 200
ATTACHMENT_MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
ATTACHMENT_REF_CLASS_ID = 1968
ATTACHMENT_UPLOAD_BUFFER_CHUNK_SIZE = 64 * 1024
