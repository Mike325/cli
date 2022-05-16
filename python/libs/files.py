#!/usr/bin/env python3

# import argparse
import logging
import os

# import subprocess
# import sys
import re
import shutil

# from typing import Dict
from typing import Optional
from typing import List

# from typing import Sequence
# from typing import TextIO
# from typing import Any
# from typing import Union
# from typing import cast
# from dataclasses import dataclass, field

from pathlib import Path
from zipfile import ZipFile
from glob import glob

from .logger import get_logger
from .shell import Job

_log: logging.Logger
# _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# _SCRIPTNAME = os.path.basename(__file__)
# _log_file: Optional[str] = os.path.splitext(_SCRIPTNAME)[0] + ".log"
# _verbose = False
# _is_windows = os.name == 'nt'
# _home = os.environ['USERPROFILE' if _is_windows else 'HOME']

_remote_regex = re.compile(r"^((([a-zA-Z]\w*)@)?([1-9]\d{0,2}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[a-zA-Z]\w*(\.\w+)*)):(.+)")


def executable(cmd: str) -> bool:
    """checks if a cmd is in the PATH and is executable

    Args:
        cmd (str): command to check

    Returns:
        True if cmd is an executable in the PATH False otherwise
    """
    return shutil.which(cmd) is not None


def isfile(filename: str, remote_host: Optional[str] = None) -> bool:
    """Checks if a file exists locally or in a remote host

    Args:
        filename (str): file path to check, accepts unix/windows paths and <remote_host>:<Path> syntax
        remote_host (Optional[str]): name/address of the remote host if the check is not perform locally

    Returns:
        True if the file exists, False otherwise
    """
    remote_match = _remote_regex.match(filename)

    if remote_host is None and not remote_match:
        return Path(filename).is_file()

    if remote_host is not None and remote_match is not None:
        raise Exception("Cannot pass both dirname with a remote host and remote_host arg")

    if remote_match is not None:
        remote_host = remote_match.group(1)
        filename = remote_match.group(6)

    remote_check = Job(["test", "-f", filename])
    remote_check.execute(remote_host=remote_host)
    return remote_check.rc == 0


def isdir(dirname: str, remote_host: Optional[str] = None) -> bool:
    """Checks if a dir exists locally or in a remote host

    Args:
        dirname (str): dir path to check, accepts unix/windows paths and <remote_host>:<Path> syntax
        remote_host (Optional[str]): name/address of the remote host if the check is not perform locally

    Returns:
        True if the dir exists, False otherwise
    """
    remote_match = _remote_regex.match(dirname)
    if remote_host is None and not remote_match:
        return Path(dirname).is_dir()

    if remote_host is not None and remote_match is not None:
        raise Exception("Cannot pass both dirname with a remote host and remote_host arg")

    if remote_match is not None:
        remote_host = remote_match.group(1)
        dirname = remote_match.group(6)

    remote_check = Job(["test", "-d", dirname])
    remote_check.execute(remote_host=remote_host)
    return remote_check.rc == 0


def exists(filename: str, remote_host: Optional[str] = None) -> bool:
    """Checks if a dir/file exists locally or in a remote host

    Args:
        filename (str): path of the directory or file to check, accepts local paths and <remote_host>:<Path> syntax
        remote_host (Optional[str]): name/address of the remote host if the check is not perform locally

    Returns:
        True if the file or directory exists, False otherwise
    """
    remote_match = _remote_regex.match(filename)
    if remote_host is None and not remote_match:
        return Path(filename).exists()

    if remote_host is not None and remote_match is not None:
        raise Exception("Cannot pass both dirname with a remote host and remote_host arg")

    if remote_match is not None:
        remote_host = remote_match.group(1)
        filename = remote_match.group(6)

    remote_check = Job(["test", "-e", filename])
    remote_check.execute(remote_host=remote_host)
    return remote_check.rc == 0


def remove(
    src: str,
    force: bool = False,
) -> bool:
    """Delete a file or a directory locally or remotely

    Args:
        src (str): path of the file/dir to remove, accepts unix/windows paths and <remote_host>:<Path> syntax
        force (bool): ignore warnings and remove recursively directories

    Returns:
        True if the deletion succeed, False otherwise
    """
    src_match = _remote_regex.match(src)
    if not src_match:
        if not exists(src):
            return True

        try:
            if isfile(src):
                os.remove(src)
            else:
                # TODO: may add force flag check here
                shutil.rmtree(src)
        except Exception:
            # TODO: Add traceback as debug message
            _log.error(f"Failed to remove {src}")
            return False

        return True

    remote_host = src_match.group(1)
    src = src_match.group(6)

    args = "-rf" if force else "-r"
    remote_check = Job(["rm", args, src])
    remote_check.execute(remote_host=remote_host)
    return remote_check.rc == 0


def move(
    src: str,
    dest: str,
    force: bool = False,
) -> bool:
    """Moves src to dest

    Args:
        src (str): path of file/directory to be move, accepts unix/windows paths and <remote_host>:<Path> syntax
        dest (str): destination to move src to, accepts unix/windows paths and <remote_host>:<Path> syntax
        force (bool): remove dest if exists before moving src into it

    Returns:
        True on success False otherwise
    """
    src_match = _remote_regex.match(src)
    dest_match = _remote_regex.match(dest)
    if not src_match and not dest_match:
        if exists(dest) and not force:
            _log.error(f"Cannot move {src} to {dest}, destination alrady exists")
            return False
        elif exists(dest) and force:
            remove(dest, force)

        try:
            shutil.move(src, dest)
        except Exception:
            # TODO: Add traceback as debug message
            _log.error(f"Failed to move {src} to {dest}")
            return False
        return True

    if not executable("scp"):
        raise Exception("Missing scp, cannot move from/to remote hosts")

    remote_check = Job(["scp", "-r", src, dest])
    remote_check.execute()
    if remote_check.rc == 0:
        return remove(src)
    return False


# TODO: May be good to allow to rename destination start from the src basename
def rename(
    src: str,
    dest: str,
    force: bool = False,
) -> bool:
    """Renames src to dest

    Args:
        src (str): path of file/directory to be rename, accepts unix/windows paths and <remote_host>:<Path> syntax
        dest (str): destination to rename src to, accepts unix/windows paths and <remote_host>:<Path> syntax
        force (bool): remove dest if exists before renaming src

    Returns:
        True on success False otherwise
    """
    src_match = _remote_regex.match(src)
    dest_match = _remote_regex.match(dest)
    if not src_match and not dest_match:
        if exists(dest) and not force:
            _log.error(f"Cannot rename {src} to {dest}, destination alrady exists")
            return False
        elif exists(dest) and force:
            remove(dest, force)

        src_path = Path(src)
        src_path.rename(dest)
        return True

    if not executable("scp"):
        raise Exception("Missing scp, cannot move from/to remote hosts")

    remote_check = Job(["scp", "-r", src, dest])
    remote_check.execute()
    if remote_check.rc == 0:
        return remove(src)
    return False


def copy(
    src: str,
    dest: str,
    force: bool = False,
) -> bool:
    """Copies src to dest

    Args:
        src (str): path of file/directory to be copy, accepts unix/windows paths and <remote_host>:<Path> syntax
        dest (str): destination to copy src to, accepts unix/windows paths and <remote_host>:<Path> syntax
        force (bool): remove dest if exists before copy src

    Returns:
        True on success False otherwise
    """
    src_match = _remote_regex.match(src)
    dest_match = _remote_regex.match(dest)
    if not src_match and not dest_match:
        if exists(dest) and not force:
            _log.error(f"Cannot copy {src} to {dest}, destination alrady exists")
            return False
        elif exists(dest) and force:
            remove(dest, force)

        try:
            if isfile(src):
                shutil.copyfile(src, dest)
            else:
                shutil.copytree(src, dest)
        except Exception:
            # TODO: Add traceback as debug message
            _log.error(f"Failed to copy {src} to {dest}")
            return False

        return True

    if not executable("scp"):
        raise Exception("Missing scp, cannot move from/to remote hosts")

    remote_check = Job(["scp", "-r", src, dest])
    remote_check.execute()
    return remote_check.rc == 0


def mkdir(dirname: str, force: bool = False, remote_host: Optional[str] = None):
    """Create directories in <dirname> path

    Args:
        dirname (str): path of directory to be created, accepts unix/windows paths and <remote_host>:<Path> syntax
        force (bool): Creates directories recursively
        remote_host (Optional[str]): name/address of the remote host if the check is not perform locally

    Returns:
        True on success False otherwise
    """
    if dirname == "":
        _log.error("Dirname cannot be empty")
        return False

    dir_match = _remote_regex.match(dirname)
    if remote_host is None and not dir_match:
        try:
            dir = Path(dirname)
            _log.debug(f"Creating new directory in: {dirname}")
            dir.mkdir(parents=force, exist_ok=True)
        except Exception:
            # _log.debug(traceback.traceback())
            _log.error(f"Failed to create directory: {dirname}")
            return False
        return True

    if remote_host is not None and dir_match is not None:
        raise Exception("Cannot pass both dirname with a remote host and remote_host arg")

    if dir_match is not None:
        remote_host = dir_match.group(1)
        dirname = dir_match.group(6)

    cmd = ["mkdir"]
    if force:
        cmd.append("-p")
    cmd.append(dirname)

    remote_check = Job(cmd)
    remote_check.execute(remote_host=remote_host)
    return remote_check.rc == 0


# TODO: Support more archive formats
def extract(archive: str, dest: Optional[str] = None, remote_host: Optional[str] = None):
    """Extracts a zip file

    Args:
        archive (str): path of the zip archive, accepts unix/windows paths and <remote_host>:<Path> syntax
        dest (Optional[str]): Destination of the extracted files
        remote_host (Optional[str]): remove ssh host where the zip archive is located

    Returns:
        True if the extraction succeed, False otherwise
    """
    archive_match = _remote_regex.match(archive)
    if not archive_match and not remote_host:
        if not isfile(archive):
            return False
        dest = os.getcwd() if dest is None else dest

        with ZipFile(archive) as zf:
            zf.extractall(dest)

    if remote_host is not None and archive_match is not None:
        raise Exception("Cannot pass both dirname with a remote host and remote_host arg")

    if archive_match is not None:
        remote_host = archive_match.group(1)
        archive = archive_match.group(6)

    remote_check = Job(["unzip", "-o", archive, "-d", "." if dest is None else dest])
    remote_check.execute(remote_host=remote_host, cwd="." if dest is None else dest)
    return remote_check.rc == 0


def list_content(dirname: str, glob_pattern: str = "*", remote_host: Optional[str] = None) -> List[str]:
    dir_match = _remote_regex.match(dirname)
    if not dir_match and not remote_host:
        if not isdir(dirname):
            return []
        files = glob(os.path.join(dirname, glob_pattern))
        return files

    raise Exception("Not implemented")


def get_files(
    dirname: str,
    glob_pattern: str = "*",
    remote_host: Optional[str] = None,
) -> List[str]:
    dir_match = _remote_regex.match(dirname)
    if not dir_match and not remote_host:
        files = list_content(dirname, glob_pattern, remote_host)
        return [i for i in files if isfile(i)]

    raise Exception("Not implemented")


def get_dirs(dirname: str, glob_pattern: str = "*", remote_host: Optional[str] = None) -> List[str]:
    dir_match = _remote_regex.match(dirname)
    if not dir_match and not remote_host:
        dirs = list_content(dirname, glob_pattern, remote_host)
        return [i for i in dirs if isdir(i)]

    raise Exception("Not implemented")


if __name__ == "__main__":
    raise Exception("This library should not be run as a standalone script")
else:
    _log = get_logger("Main")
