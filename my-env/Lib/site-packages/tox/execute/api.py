import logging
import signal
import sys
import threading
from abc import ABC, abstractmethod
from functools import partial
from timeit import default_timer as timer
from typing import Callable, Sequence, Type

from colorama import Fore

from .request import ExecuteRequest, shell_cmd
from .stream import CollectWrite

ContentHandler = Callable[[bytes], None]
Executor = Callable[[ExecuteRequest, ContentHandler, ContentHandler], int]
SIGINT = signal.CTRL_C_EVENT if sys.platform == "win32" else signal.SIGINT


class ExecuteInstance:
    def __init__(self, request: ExecuteRequest, out_handler: ContentHandler, err_handler: ContentHandler) -> None:
        def _safe_handler(handler, data):
            # noinspection PyBroadException
            try:
                handler(data)
            except Exception:  # pragma: no cover
                pass  # pragma: no cover

        self.request = request
        self.out_handler = partial(_safe_handler, out_handler)
        self.err_handler = partial(_safe_handler, err_handler)

    @abstractmethod
    def run(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def interrupt(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def cmd(self) -> Sequence[str]:
        raise NotImplementedError


class Outcome:
    OK = 0

    def __init__(
        self,
        request: ExecuteRequest,
        show_on_standard: bool,
        exit_code: int,
        out: str,
        err: str,
        start: float,
        end: float,
        cmd: Sequence[str],
    ):
        self.request = request
        self.show_on_standard = show_on_standard
        self.exit_code = exit_code
        self.out = out
        self.err = err
        self.start = start
        self.end = end
        self.cmd = cmd

    def __bool__(self):
        return self.exit_code == self.OK

    def assert_success(self, logger):
        if self.exit_code != self.OK:
            self._assert_fail(logger)

    def _assert_fail(self, logger: logging.Logger):
        if self.show_on_standard is False:
            if self.out:
                print(self.out, file=sys.stdout)
            if self.err:
                print(Fore.RED, file=sys.stderr, end="")
                print(self.err, file=sys.stderr, end="")
                print(Fore.RESET, file=sys.stderr)
        logger.critical(
            "exit code %d for %s: %s in %s", self.exit_code, self.request.cwd, self.shell_cmd, self.elapsed,
        )
        raise SystemExit(self.exit_code)

    @property
    def elapsed(self):
        return self.end - self.start

    @property
    def shell_cmd(self):
        return shell_cmd(self.cmd)


class ToxKeyboardInterrupt(KeyboardInterrupt):
    def __init__(self, outcome: Outcome, exc: KeyboardInterrupt):
        self.outcome = outcome
        self.exc = exc


class Execute(ABC):
    def __call__(self, request: ExecuteRequest, show_on_standard: bool) -> Outcome:
        start = timer()
        executor = self.executor()
        interrupt = None
        try:
            with CollectWrite(sys.stdout if show_on_standard else None) as out:
                with CollectWrite(sys.stderr if show_on_standard else None, Fore.RED) as err:
                    instance = executor(request, out.collect, err.collect)  # type: ExecuteInstance
                    try:
                        exit_code = instance.run()
                    except KeyboardInterrupt as exception:
                        interrupt = exception
                        while True:
                            try:
                                is_main = threading.current_thread() == threading.main_thread()
                                if is_main:
                                    # disable further interrupts until we finish this, main thread only
                                    if sys.platform != "win32":
                                        signal.signal(SIGINT, signal.SIG_IGN)
                            except KeyboardInterrupt:  # pragma: no cover
                                continue  # pragma: no cover
                            else:
                                try:
                                    exit_code = instance.interrupt()
                                    break
                                finally:
                                    if is_main and sys.platform != "win32":  # restore signal handler on main thread
                                        signal.signal(SIGINT, signal.default_int_handler)
        finally:
            end = timer()
        result = Outcome(request, show_on_standard, exit_code, out.text, err.text, start, end, instance.cmd)
        if interrupt is not None:
            raise ToxKeyboardInterrupt(result, interrupt)
        return result

    @staticmethod
    @abstractmethod
    def executor() -> Type[ExecuteInstance]:
        raise NotImplementedError
