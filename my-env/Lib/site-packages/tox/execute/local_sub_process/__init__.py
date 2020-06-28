"""A execute that runs on local file system via subprocess-es"""
import logging
import os
import shutil
import sys
from subprocess import PIPE, TimeoutExpired
from typing import List, Optional, Sequence, Tuple, Type

from ..api import SIGINT, ContentHandler, Execute, ExecuteInstance, ExecuteRequest, Outcome
from .read_via_thread import WAIT_GENERAL

if sys.platform == "win32":
    from asyncio.windows_utils import Popen  # noqa # needs stdin/stdout handlers backed by overlapped IO
    from .read_via_thread_windows import ReadViaThreadWindows as ReadViaThread
    from subprocess import CREATE_NEW_PROCESS_GROUP

    CREATION_FLAGS = CREATE_NEW_PROCESS_GROUP  # custom flag needed for Windows signal send ability (CTRL+C)

else:
    from subprocess import Popen
    from .read_via_thread_unix import ReadViaThreadUnix as ReadViaThread

    CREATION_FLAGS = 0


WAIT_INTERRUPT = 0.3
WAIT_TERMINATE = 0.2


class LocalSubProcessExecutor(Execute):
    @staticmethod
    def executor() -> Type[ExecuteInstance]:
        return LocalSubProcessExecuteInstance


class LocalSubProcessExecuteInstance(ExecuteInstance):
    def __init__(self, request: ExecuteRequest, out_handler: ContentHandler, err_handler: ContentHandler) -> None:
        super().__init__(request, out_handler, err_handler)
        self.process = None
        self._cmd = []  # type: Optional[List[str]]

    @property
    def cmd(self) -> Sequence[str]:
        if not len(self._cmd):
            executable = shutil.which(self.request.cmd[0], path=self.request.env["PATH"])
            if executable is None:
                self._cmd = self.request.cmd  # if failed to find leave as it is
            else:
                # else use expanded format
                self._cmd = [executable, *self.request.cmd[1:]]
        return self._cmd

    def run(self) -> int:
        try:
            self.process = process = Popen(
                self.cmd,
                stdout=PIPE,
                stderr=PIPE,
                stdin=None if self.request.allow_stdin else PIPE,
                cwd=str(self.request.cwd),
                env=self.request.env,
                creationflags=CREATION_FLAGS,
            )
        except OSError as exception:
            exit_code = exception.errno
        else:
            with ReadViaThread(process.stderr, self.err_handler) as read_stderr:
                with ReadViaThread(process.stdout, self.out_handler) as read_stdout:
                    if sys.platform == "win32":
                        process.stderr.read = read_stderr._drain_stream
                        process.stdout.read = read_stdout._drain_stream
                    # wait it out with interruptions to allow KeyboardInterrupt on Windows
                    while process.poll() is None:
                        try:
                            # note poll in general might deadlock if output large
                            # but we drain in background threads so not an issue here
                            process.wait(timeout=WAIT_GENERAL)
                        except TimeoutExpired:
                            continue
            exit_code = process.returncode
        return exit_code

    def interrupt(self) -> int:
        if self.process is not None:
            out, err = self._handle_interrupt()  # stop it and drain it
            self._finalize_output(err, self.err_handler, out, self.out_handler)
            return self.process.returncode
        return Outcome.OK  # pragma: no cover

    @staticmethod
    def _finalize_output(err, err_handler, out, out_handler):
        out_handler(out)
        err_handler(err)

    def _handle_interrupt(self) -> Tuple[bytes, bytes]:
        """A three level stop mechanism for children - INT -> TERM -> KILL"""
        # communicate will wait for the app to stop, and then drain the standard streams and close them
        proc = self.process
        logging.error("got KeyboardInterrupt signal")
        msg = f"from {os.getpid()} {{}} pid {proc.pid}"
        if proc.poll() is None:  # still alive, first INT
            logging.warning("KeyboardInterrupt %s", msg.format("SIGINT"))
            proc.send_signal(SIGINT)
            try:
                out, err = proc.communicate(timeout=WAIT_INTERRUPT)
            except TimeoutExpired:  # if INT times out TERM
                logging.warning("KeyboardInterrupt %s", msg.format("SIGTERM"))
                proc.terminate()
                try:
                    out, err = proc.communicate(timeout=WAIT_INTERRUPT)
                except TimeoutExpired:  # if TERM times out KILL
                    logging.info("KeyboardInterrupt %s", msg.format("SIGKILL"))
                    proc.kill()
                    out, err = proc.communicate()
        else:
            try:
                out, err = proc.communicate()  # just drain # pragma: no cover
            except IndexError:
                out, err = b"", b""
        return out, err
