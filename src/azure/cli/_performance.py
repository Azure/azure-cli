import time

class PerfTimer(object): # pylint:disable=too-few-public-methods
    _last_result = 0

    def __init__(self, *args, **kwargs):
        self.start = 0
        self.end = 0
        super(PerfTimer, self).__init__(*args, **kwargs)

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        PerfTimer._last_result = (self.end - self.start) * 1000

    @staticmethod
    def last_measured_milliseconds():
        return PerfTimer._last_result
