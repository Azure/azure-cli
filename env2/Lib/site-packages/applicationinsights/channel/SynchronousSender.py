from .SenderBase import SenderBase, DEFAULT_ENDPOINT_URL

class SynchronousSender(SenderBase):
    """A synchronous sender that works in conjunction with the :class:`SynchronousQueue`. The queue will call
    :func:`send` on the current instance with the data to send.
    """
    def __init__(self, service_endpoint_uri=None):
        """Initializes a new instance of the class.

        Args:
            sender (String) service_endpoint_uri the address of the service to send telemetry data to.
        """
        SenderBase.__init__(self, service_endpoint_uri or DEFAULT_ENDPOINT_URL)