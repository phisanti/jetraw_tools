import sys
import logging


def setup_logger(
    name: str = "jetraw_tools", level: int = logging.INFO
) -> logging.Logger:
    """
    Configure and return a logger instance.

    :param name: The name of the logger.
    :type name: str, optional
    :param level: The logging level to set.
    :type level: int, optional
    :return: A configured logger instance.
    :rtype: logging.Logger
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers if they already exist
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# Create a default logger instance for import
logger = setup_logger()
