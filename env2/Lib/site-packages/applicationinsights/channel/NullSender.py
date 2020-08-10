from .SenderBase import SenderBase

class NullSender(SenderBase):
    """A sender class that does not send data.  Useful for debug mode, when
    telemetry may not be desired, with no changes to the object model.
    """
    def __init__(self, *args, **kwargs):
        super(NullSender, self).__init__("nil-endpoint", *args, **kwargs)

    def send(self, data):
        pass

    def start(self):
        pass

    def stop(self):
        pass
