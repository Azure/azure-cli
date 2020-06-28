from asyncio.windows_utils import BUFSIZE, PipeHandle

import _overlapped

from .read_via_thread import ReadViaThread


class ReadViaThreadWindows(ReadViaThread):
    def __init__(self, stream, handler):
        super().__init__(stream, handler)
        self.closed = False
        assert isinstance(stream, PipeHandle)

    def _read_stream(self):
        ov = None
        while not self.stop.is_set():
            if ov is None:
                ov = _overlapped.Overlapped(0)
                try:
                    ov.ReadFile(self.stream.handle, 1)
                except BrokenPipeError:
                    self.closed = True
                    return
            data = ov.getresult(10)  # wait for 10ms
            ov = None
            self.handler(data)

    def _drain_stream(self):
        length, result = 0 if self.closed else 1, b""
        while 0 < length <= BUFSIZE:
            ov = _overlapped.Overlapped(0)
            buffer = bytes(BUFSIZE)
            try:
                ov.ReadFileInto(self.stream.handle, buffer)
                length = ov.getresult()
                result += buffer[:length]
            except BrokenPipeError:
                break
        return result
