import os
import select

from .read_via_thread import ReadViaThread


class ReadViaThreadUnix(ReadViaThread):
    def __init__(self, stream, handler):
        super().__init__(stream, handler)
        self.file_no = self.stream.fileno()

    def _read_stream(self):
        while not (self.stream.closed or self.stop.is_set()):
            # we need to drain the stream, but periodically give chance for the thread to break if the stop event has
            # been set (this is so that an interrupt can be handled)
            if self.has_bytes():
                data = os.read(self.file_no, 1)
                self.handler(data)

    def has_bytes(self):
        read_available_list, _, __ = select.select([self.stream], [], [], 0.01)
        return len(read_available_list)

    def _drain_stream(self):
        return self.stream.read()
