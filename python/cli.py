#!/usr/bin/env python3

"""
Author: Mike
Version: 0.1
Description: TODO

                           -`
           ...            .o+`
        .+++s+   .h`.    `ooo/
       `+++%++  .h+++   `+oooo:
       +++o+++ .hhs++. `+oooooo:
       +s%%so%.hohhoo'  'oooooo+:
       `+ooohs+h+sh++`/:  ++oooo+:
        hh+o+hoso+h+`/++++.+++++++:
         `+h+++h.+ `/++++++++++++++:
                  `/+++ooooooooooooo/`
                 ./ooosssso++osssssso+`
                .oossssso-````/osssss::`
               -osssssso.      :ssss``to.
              :osssssss/  Mike  osssl   +
             /ossssssss/        +sssslb
           `/ossssso+/:-        -:/+ossss'.-
          `+sso+:-`                 `.-/+oso:
         `++:.                           `-/+/
         .`       github.com/mike325/       `/
"""

# from datetime import datetime
import argparse
import logging
import os

# from typing import Dict
from typing import Optional

from libs.constants import AUTHOR, HEADER, VERSION
from libs.logger import create_logger, str_to_logging

# import subprocess
# import sys
# import re
# import shutil

# from typing import List
# from typing import Sequence
# from typing import TextIO
# from typing import Any
# from typing import Union
# from typing import cast
# from dataclasses import dataclass, field

_log: logging.Logger
# _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTNAME = os.path.basename(__file__)
_log_file: Optional[str] = os.path.splitext(_SCRIPTNAME)[0] + ".log"

# _verbose = False
# _is_windows = os.name == 'nt'
# _home = os.environ['USERPROFILE' if _is_windows else 'HOME']


def _parseArgs():
    """Parse CLI arguments

    Returns
        argparse.ArgumentParser class instance

    """

    class NegateAction(argparse.Action):
        def __call__(self, parser, ns, values, option):
            global _protocol
            if len(option) == 2:
                setattr(ns, self.dest, True)
            else:
                setattr(ns, self.dest, option[2:4] != "no")

    class ChangeLogFile(argparse.Action):
        def __call__(self, parser, ns, values, option):
            if option[2:4] == "no":
                setattr(ns, self.dest, None)
            else:
                pass
                setattr(ns, self.dest, values)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--color",
        "--nocolor",
        "--no-color",
        dest="color",
        action=NegateAction,
        default=True,
        nargs=0,
        help="Disable colored output",
    )

    parser.add_argument(
        "--log",
        "--nolog",
        "--no-log",
        dest="logfile",
        action=ChangeLogFile,
        default=_log_file,
        nargs="?",
        type=str,
        help="Log filename or disable log file",
    )

    parser.add_argument(
        "--version",
        dest="show_version",
        action="store_true",
        help="Print script version and exit",
    )

    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        default=False,
        help="Turn on console debug messages",
    )

    parser.add_argument(
        "--quiet",
        dest="quiet",
        action="store_true",
        default=False,
        help="Turn off all console messages",
    )

    parser.add_argument(
        "-l",
        "--logging",
        dest="stdout_logging",
        default="info",
        type=str,
        help="Console logger verbosity",
    )

    parser.add_argument(
        "-f",
        "--file-logging",
        dest="file_logging",
        default="debug",
        type=str,
        help="File logger verbosity",
    )

    return parser.parse_args()


def main():
    """Main function

    Returns
        exit code, 0 in success any other integer in failure

    """
    global _log

    args = _parseArgs()

    if args.show_version:
        print(f"{HEADER}\nAuthor:   {AUTHOR}\nVersion:  {VERSION}")
        return 0

    stdout_level = args.stdout_logging if not args.verbose else "debug"
    file_level = args.file_logging if not args.verbose else "debug"

    stdout_level = stdout_level if not args.quiet else 0
    file_level = file_level if not args.quiet else 0

    _log = create_logger(
        stdout_level=str_to_logging(stdout_level),
        file_level=str_to_logging(file_level),
        color=args.color,
        filename=args.logfile,
    )

    # _log.debug('This is a DEBUG message')
    # _log.info('This is a INFO message')
    # _log.warning('This is a WARNing message')
    # _log.error('This is a ERROR message')

    errors = 0
    try:
        pass
    except (Exception, KeyboardInterrupt) as e:
        _log.exception(f"Halting due to {str(e.__class__.__name__)} exception")
        errors = 1

    return errors


if __name__ == "__main__":
    exit(main())
