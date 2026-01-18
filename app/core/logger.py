import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def set_logging_level(level: str):
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    LOGGER.setLevel(numeric_level)
    LOGGER.info(f"Log level set to {level.upper()}")


def set_log(message: str):
    LOGGER.info(f"{message}")
