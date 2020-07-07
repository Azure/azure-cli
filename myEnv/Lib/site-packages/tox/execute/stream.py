from contextlib import contextmanager
from threading import Event, Lock, Timer
from typing import IO, Optional

from colorama import Fore


class CollectWrite:
    """A stream collector that is both time triggered and newline"""

    REFRESH_RATE = 0.1

    def __init__(self, target: Optional[IO[bytes]], color: Optional[str] = None) -> None:
        self._content = bytearray()
        self._print_to = None if target is None else target.buffer  # type:Optional[IO[bytes]]
        self._do_print = target is not None  # type: bool
        self._keep_printing = Event()  # type: Event
        self._content_lock = Lock()  # type: Lock
        self._print_lock = Lock()  # type: Lock
        self._at = 0  # type: int
        self._color = color  # type: Optional[str]

    def __enter__(self):
        if self._do_print:
            self._start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._do_print:
            self._cancel()
            self._print(len(self._content))

    def _start(self):
        self.timer = Timer(self.REFRESH_RATE, self._trigger_timer)
        self.timer.start()

    def _cancel(self):
        self.timer.cancel()

    def collect(self, content: bytes):
        with self._content_lock:
            self._content.extend(content)
            if self._do_print is False:
                return
            at = content.rfind(b"\n")
            if at != -1:
                at = len(self._content) - len(content) + at + 1
        if at != -1:
            self._cancel()
            try:
                self._print(at)
            finally:
                self._start()

    def _trigger_timer(self):
        with self._content_lock:
            at = len(self._content)
        self._print(at)

    def _print(self, at):
        with self._print_lock:
            if at > self._at:
                try:
                    with self.colored():
                        self._print_to.write(self._content[self._at : at])
                    self._print_to.flush()
                finally:
                    self._at = at

    @contextmanager
    def colored(self):
        if self._color is None:
            yield
        else:
            self._print_to.write(self._color.encode("utf-8"))
            try:
                yield
            finally:
                self._print_to.write(Fore.RESET.encode("utf-8"))

    @property
    def text(self):
        with self._content_lock:
            return self._content.decode("utf-8")
