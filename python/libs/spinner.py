#!/usr/bin/env python3

import sys
import time
import threading

from typing import Generator, Optional, cast

from dataclasses import dataclass, field

# _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# _SCRIPTNAME = os.path.basename(__file__)
# _log_file: Optional[str] = os.path.splitext(_SCRIPTNAME)[0] + ".log"

_verbose = False
_delete_current_line = "\x1b[1K\r"
# _delete_current_char = "\b"
# _log: logging.Logger
# _is_windows = os.name == 'nt'
# _home = os.environ['USERPROFILE' if _is_windows else 'HOME']


@dataclass()
class Spinner:
    busy: bool = field(init=False, default=False)
    delay: float = field(init=True, default=0.1)
    enable: bool = field(init=True, default=True)
    spinner_generator: Optional[Generator[str, None, None]] = field(init=False, repr=False, default=None)

    @staticmethod
    def spinning_cursor() -> Generator[str, None, None]:
        while True:
            for cursor in "|/-\\":
                yield cursor

    def __post_init__(self):
        if not self.spinner_generator:
            self.spinner_generator = self.spinning_cursor()

        # force spinner disable if we are not in the main thread
        if self.enable:
            self.enable = threading.current_thread() is threading.main_thread()

    def spinner_task(self):
        self.spinner_generator = cast(Generator[str, None, None], self.spinner_generator)
        start = time.time()
        while self.busy:
            output = "{0} Running for {1}"
            running = time.time() - start
            time_str = ""
            if running > 60:
                time_str = f"{running/60.0:.2f}min"
            else:
                time_str = f"{running:.2f}s"

            sys.stdout.write(output.format(next(self.spinner_generator), time_str))
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write(_delete_current_line)
            sys.stdout.flush()

    def __enter__(self):
        if not _verbose and self.enable:
            self.busy = True
            threading.Thread(target=self.spinner_task).start()

    def __exit__(self, exception, value, tb):
        self.busy = False
        time.sleep(self.delay)
        if exception is not None:
            return False


if __name__ == "__main__":
    raise Exception("This library should not be run as a standalone script")
