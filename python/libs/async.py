#!/usr/bin/env python3

# from datetime import datetime
# import argparse
import logging

# import os
# import subprocess
# import sys
# import re
# import shutil
# import datetime
import asyncio

from typing import Awaitable

# from typing import Dict
# from typing import Optional
# from typing import List
# from typing import Sequence
# from typing import TextIO
from typing import Any

# from typing import Union
# from typing import cast
# # from dataclasses import dataclass, field

# from pathlib import Path
# from zipfile import ZipFile

from .logger import get_logger

_log: logging.Logger
# _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# _SCRIPTNAME = os.path.basename(__file__)
# _log_file: Optional[str] = os.path.splitext(_SCRIPTNAME)[0] + ".log"

# _verbose = False
# _is_windows = os.name == 'nt'
# _home = os.environ['USERPROFILE' if _is_windows else 'HOME']

# TODO: Expand this functions to execute threads and processes


async def run_sequence(*functions: Awaitable[Any]) -> None:
    for function in functions:
        await function


async def run_parallel(*functions: Awaitable[Any]) -> None:
    await asyncio.gather(*functions)


if __name__ == "__main__":
    raise Exception("This library should not be run as a standalone script")
else:
    _log = get_logger("Main")
