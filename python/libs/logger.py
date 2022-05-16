#!/usr/bin/env python3

# import argparse
import logging
import os

# import subprocess
import sys

# import re
# import shutil

# from typing import List
# from typing import Sequence
# from typing import TextIO
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union
from typing import cast

from datetime import datetime

from .constants import HEADER
from .constants import AUTHOR
from .constants import VERSION

# from dataclasses import dataclass, field

ColorFormatter: Any = None
Formatter: Any = None

try:
    from colorlog import ColoredFormatter

    Formatter = ColoredFormatter
    ColorFormatter = ColoredFormatter
except ImportError:

    class PrimitiveFormatter(logging.Formatter):
        """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

        def __init__(self, fmt, log_colors=None):
            super().__init__()
            self.fmt = fmt

            colors = {
                "grey": "\x1b[38;21m",
                "green": "\x1b[32m",
                "magenta": "\x1b[35m",
                "purple": "\x1b[35m",
                "blue": "\x1b[38;5;39m",
                "yellow": "\x1b[38;5;226m",
                "red": "\x1b[38;5;196m",
                "bold_red": "\x1b[31;1m",
                "reset": "\x1b[0m",
            }

            if log_colors is None:
                log_colors = {}

            log_colors["DEBUG"] = log_colors["DEBUG"] if "DEBUG" in log_colors else "magenta"
            log_colors["INFO"] = log_colors["INFO"] if "INFO" in log_colors else "green"
            log_colors["WARNING"] = log_colors["WARNING"] if "WARNING" in log_colors else "yellow"
            log_colors["ERROR"] = log_colors["ERROR"] if "ERROR" in log_colors else "red"
            log_colors["CRITICAL"] = log_colors["CRITICAL"] if "CRITICAL" in log_colors else "bold_red"

            self.FORMATS = {
                logging.DEBUG: colors[log_colors["DEBUG"]] + self.fmt + colors["reset"],
                logging.INFO: colors[log_colors["INFO"]] + self.fmt + colors["reset"],
                logging.WARNING: colors[log_colors["WARNING"]] + self.fmt + colors["reset"],
                logging.ERROR: colors[log_colors["ERROR"]] + self.fmt + colors["reset"],
                logging.CRITICAL: colors[log_colors["CRITICAL"]] + self.fmt + colors["reset"],
            }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    Formatter = PrimitiveFormatter


# _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# _SCRIPTNAME = os.path.basename(__file__)
# _log_file: Optional[str] = os.path.splitext(_SCRIPTNAME)[0] + ".log"
# _is_windows = os.name == 'nt'
# _home = os.environ['USERPROFILE' if _is_windows else 'HOME']

_loggers: Dict[str, logging.Logger] = {}


def _get_stdout_handler(level: int, color: bool = True):
    """Create a new stdout handler

    Args:
        level (int): handler internal logging level
        color (bool): Control if colors should be output to the stdout stream

    Returns:
        logging handler
    """
    # This means both 0 and 100 silence all output
    level = 100 if level == 0 else level
    has_color = ColorFormatter is not None and color
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    logformat = "{color}%(levelname)-8s | %(message)s"
    logformat = logformat.format(
        color="%(log_color)s" if has_color else "",
        # reset='%(reset)s' if has_color else '',
    )
    stdout_format = Formatter(
        logformat,
        log_colors={
            "DEBUG": "purple",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red",
        },
    )
    stdout_handler.setFormatter(stdout_format)
    return stdout_handler


def _get_logfile_handler(level: int, logfile: str = "dummy.log"):
    """Create a new file handler

    Args:
        level (int): handler internal logging level
        logfile (str): filename of the logger

    Returns:
        logging handler
    """
    with open(logfile, "a") as log:
        log.write(HEADER)
        log.write(f"\nDate: {datetime.today()}")
        log.write(f"\nAuthor:   {AUTHOR}")
        log.write(f"\nVersion:   {VERSION}\n")

    file_handler = logging.FileHandler(filename=logfile)
    file_handler.setLevel(level)
    file_format = logging.Formatter("%(levelname)-8s | %(filename)s: [%(funcName)s] - %(message)s")
    file_handler.setFormatter(file_format)
    return file_handler


def str_to_logging(level: Union[int, str]) -> int:
    """Convert logging level string to a logging number

    Args:
        level: integer representation or a valid logging string
                    - debug/verbose
                    - info
                    - warn/warning
                    - error
                    - critical
                All non valid integer or logging strings defaults to 0 logging

    Returns:
        logging level of the given string
    """

    if isinstance(level, int):
        level = abs(level - 100)
    elif isinstance(level, str):
        try:
            level = abs(int(level) - 100)
        except Exception:
            level = cast(str, level).lower()
            if level == "debug" or level == "verbose":
                level = logging.DEBUG
            elif level == "info":
                level = logging.INFO
            elif level == "warn" or level == "warning":
                level = logging.WARN
            elif level == "error":
                level = logging.ERROR
            elif level == "critical":
                level = logging.CRITICAL
            else:
                level = 100

    return level


def create_logger(
    stdout_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    color: bool = True,
    filename: Optional[str] = "dummy.log",
    name: str = "Main",
):
    """Create a new logger object

    Args:
        stdout_level (int): logging level to send to the stdout
        file_level (int): logging level to send to the logfile
        color (bool): turn on/off color output of the stdout handler
        filename (Optional[str]): name of the logfile
        name (str): name of the logger

    Returns:
        logger object
    """

    # stdout_level = str_to_logging(stdout_level)
    # file_level = str_to_logging(file_level)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    has_file_hanlder = file_level > 0 and file_level < 100 and filename is not None
    handlers = logger.handlers

    add_stdout = False
    add_logfile = False

    if len(handlers) == 0 or handlers[0].level != stdout_level:
        add_stdout = True

    if has_file_hanlder and len(handlers) < 2:
        add_logfile = True
    elif has_file_hanlder:
        h_level = handlers[1].level
        h_name = handlers[1].stream.name  # type: ignore
        if h_level != file_level or os.path.basename(h_name) != filename:
            add_logfile = True

    if add_stdout or add_logfile:
        stdout_handler = logger.handlers[0] if not add_stdout else _get_stdout_handler(stdout_level, color)
        file_handler = None
        if add_logfile or has_file_hanlder:
            file_handler = (
                logger.handlers[1]
                if not add_logfile and len(handlers) >= 2
                else _get_logfile_handler(file_level, cast(str, filename))
            )

        other_handlers = []
        if len(logger.handlers) > 2:
            other_handlers = logger.handlers[2::]

        while logger.hasHandlers():
            logger.removeHandler(logger.handlers[0])

        logger.addHandler(stdout_handler)
        if add_logfile or has_file_hanlder:
            logger.addHandler(cast(logging.FileHandler, file_handler))

        for h in other_handlers:
            logger.addHandler(h)

    _loggers[name] = logger
    return logger


def get_logger(name: str):
    """Get an active logger or create a new one

    Args:
        name (str): Name of the logger

    Returns:
        logger object from the list of active logger or a newly created logger with default parameters
    """
    if name in _loggers:
        return _loggers[name]
    return create_logger(
        stdout_level=str_to_logging("INFO"),
        file_level=str_to_logging("DEBUG"),
        color=True,
        filename=None,
        name=name,
    )


if __name__ == "__main__":
    raise Exception("This library should not be run as a standalone script")
