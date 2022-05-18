#!/usr/bin/env python3

# from datetime import datetime
# import argparse
import logging

# import os
import subprocess

# import sys
import re
import shutil

# from typing import Dict
from typing import Optional
from typing import List
from typing import Sequence
from typing import IO

# from typing import Any
# from typing import Union
from typing import cast

from dataclasses import dataclass, field

# from pathlib import Path
# from zipfile import ZipFile

from .logger import get_logger

_warn_regex = re.compile(r"(<warn(ing)?>\s*:?|\[warn(ing)?\])", re.IGNORECASE)
_error_regex = re.compile(r"(<(err(or)?|fail(ed)?)>\s*:?|\[(err(or)?|fail(ed)?)\])", re.IGNORECASE)

_log: logging.Logger
# _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# _SCRIPTNAME = os.path.basename(__file__)
# _log_file: Optional[str] = os.path.splitext(_SCRIPTNAME)[0] + ".log"
# _verbose = False
# _is_windows = os.name == 'nt'
# _home = os.environ['USERPROFILE' if _is_windows else 'HOME']


@dataclass
class Job(object):
    """docstring for Job"""

    cmd: Sequence[str]
    stdout: List[str] = field(init=False, repr=False)
    stderr: List[str] = field(init=False, repr=False)
    pid: int = field(init=False)
    rc: int = field(init=False)

    # # NOTE: Needed it with python < 3.7
    # def __init__(self, cmd: Sequence[str]):
    #     """Create a shell command wrapper
    #
    #     Args:
    #         cmd (Sequence[str]): command with its arguments, first element must
    #                              be and executable or a path to the executable
    #     """
    #     self.cmd = cmd

    def head(self, size: int = 10) -> List[str]:
        """Emulate head shell util

        Args:
            size (int): first N elements of the stdout

        Returns:
            List of string with the first N elements
        """
        if size <= 0:
            raise Exception("Size cannot be less than 0")
        return self.stdout[0:size]

    def tail(self, size: int = 10) -> List[str]:
        """Emulate tail shell util

        Args:
            size (int): last N elements of the stdout

        Returns:
            List of string with the last N elements
        """
        if size <= 0:
            raise Exception("Size cannot be less than 0")
        return self.stdout[::-1][0:size]

    def execute(
        self,
        background: bool = True,
        cwd: Optional[str] = None,
        remote_host: Optional[str] = None,
        # sshkey: Optional[str] = None,
    ) -> int:
        """Execute the cmd

        Args:
            background (bool): execute as async process
            cwd (Optional[str]): path where the cmd is execute, default to CWD
            remote_host (Optional[str]): execute the command remotly using ssh

        Returns:
            Return-code integer of the cmd
        """

        if remote_host is not None and shutil.which("ssh") is None:
            raise Exception("Cannot execute the remote command, missing ssh executable")

        cmd: Sequence[str]
        if remote_host is not None:
            cwd = "$HOME" if cwd is None else cwd
            # Verbose always overrides background output

            cmd = ["ssh"]
            # if sshkey is not None:
            #     cmd += ["-i", sshkey]
            cmd += ["-t", remote_host]
            original_cmd = f"cd {cwd} ; {' '.join(self.cmd)}"
            # original_cmd = f"{' '.join(self.cmd)}"
            cmd += [f"{original_cmd}"]
        else:
            cmd = self.cmd
            cwd = "." if cwd is None else cwd

        _log.debug(f"Executing cmd: {cmd}" + "" if not remote_host else f" {remote_host}")
        _log.debug("Sending job to background" if background else "Running in foreground")

        self.stdout = []
        self.stderr = []

        process = subprocess.Popen(
            cmd,
            # shell=True,
            # text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # stdin=subprocess.PIPE,
            cwd=cwd if remote_host is None else ".",
            # bufsize=0,
        )

        self.pid = process.pid

        # TODO: Add timeout kill
        while process.poll() is None:
            stdout = cast(IO[bytes], process.stdout).readline().decode().replace("\n", "")
            stderr = cast(IO[bytes], process.stderr).readline().decode().replace("\n", "")

            if stdout.strip():
                # TODO: to clarify info/warning/error messages may add another step to replace
                #       the regex match with the process name
                if _error_regex.search(stdout):
                    if not stdout.find("\r"):
                        self.stderr.append(stdout)
                    else:
                        self.stderr += stdout.split("\r")

                    _log.error(stdout)
                else:
                    if _warn_regex.search(stdout):
                        _log.warning(stdout)
                    elif background:
                        _log.debug(stdout)
                    else:
                        _log.info(stdout)

                    if not stdout.find("\r"):
                        self.stdout.append(stdout)
                    else:
                        self.stdout += stdout.split("\r")

            if stderr.strip():
                if not stderr.find("\r"):
                    self.stderr.append(stderr)
                else:
                    self.stderr += stderr.split("\r")
                _log.error(stderr)

        self.rc = process.returncode

        if self.rc != 0:
            _log.error(f"Command exited with {self.rc}")

        return self.rc


if __name__ == "__main__":
    raise Exception("This library should not be run as a standalone script")
else:
    _log = get_logger("Main")
