#!/usr/bin/env python3

# from datetime import datetime
# import argparse
import logging

# import sys
import re
import shutil

# import os
import subprocess
from dataclasses import dataclass, field

# from typing import Any
# from typing import Union
# from typing import Dict
from typing import IO, List, Optional, Sequence
from threading import Thread

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
        timeout: Optional[int] = None,
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

        def stdout_reader(f: Optional[IO], stdout: List[str], stderr: List[str]):
            while f is not None:
                line = f.readline().replace("\n", "")
                if line.strip():
                    # TODO: to clarify info/warning/error messages may add another step to replace
                    #       the regex match with the process name
                    if _error_regex.search(line):
                        if not line.find("\r"):
                            stderr.append(line)
                        else:
                            stderr += line.split("\r")

                        _log.error(line)
                    else:
                        if _warn_regex.search(line):
                            _log.warning(line)
                        elif background:
                            _log.debug(line)
                        else:
                            _log.info(line)

                        if not line.find("\r"):
                            stdout.append(line)
                        else:
                            stdout += line.split("\r")
                elif not line:
                    break

        def stderr_reader(f: Optional[IO], stderr: List[str]):
            while f is not None:
                line = f.readline().replace("\n", "")
                if line.strip():
                    if not line.find("\r"):
                        stderr.append(line)
                    else:
                        stderr += line.split("\r")
                    _log.error(line)
                elif not line:
                    break

        # NOTE: Should we add a retry option ?
        process = subprocess.Popen(
            cmd,
            # shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # stdin=subprocess.PIPE,
            cwd=cwd if remote_host is None else ".",
            # bufsize=0,
        )
        self.pid = process.pid

        stdout = Thread(target=stdout_reader, args=(process.stdout, self.stdout, self.stderr))
        stdout.daemon = True
        stdout.start()

        stderr = Thread(target=stderr_reader, args=(process.stderr, self.stderr))
        stderr.daemon = True
        stderr.start()

        try:
            process.wait(timeout if timeout else 60)
        except subprocess.TimeoutExpired:
            cmd_str = " ".join(cmd)
            _log.error(f'command "{cmd_str}" timeout')

        self.rc = process.returncode

        if self.rc != 0:
            _log.error(f"Command exited with {self.rc}")

        return self.rc


if __name__ == "__main__":
    raise Exception("This library should not be run as a standalone script")
else:
    _log = get_logger("Main")
