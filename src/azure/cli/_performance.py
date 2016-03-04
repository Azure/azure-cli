import time
from ._telemetry import telemetry_log_performance

class PerfTimer(object): # pylint:disable=too-few-public-methods
    def __init__(self, event_name, properties):
        self.event_name = event_name
        self.properties = properties
        self.start = 0
        super(PerfTimer, self).__init__()

    def total_milliseconds(self):
        return (time.time() - self.start) * 1000

    def store_perf_data(self):
        self.properties["Milliseconds"] = self.total_milliseconds()
        telemetry_log_performance(self.event_name, self.properties)
