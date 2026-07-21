import platform
import locale

from applicationinsights.channel import contracts

# save off whatever is currently there
existing_device_initialize = contracts.Device._initialize
def device_initialize(self):
    """ The device initializer used to assign special properties to all device context objects"""
    existing_device_initialize(self)
    self.type = 'Other'
    self.id = platform.node()
    self.os_version = platform.version()
    self.locale = locale.getdefaultlocale()[0]

# assign the device context initializer
contracts.Device._initialize = device_initialize

class TelemetryContext(object):
    """Represents the context for sending telemetry to the Application Insights service.

    .. code:: python

        context = TelemetryContext()
        context.instrumentation_key = '<YOUR INSTRUMENTATION KEY GOES HERE>'
        context.application.ver = '1.2.3'
        context.device.id = 'My current device'
        context.device.oem_name = 'Asus'
        context.device.model = 'X31A'
        context.device.type = "Other"
        context.user.id = 'santa@northpole.net'
        track_trace('My trace with context')
    """
    def __init__(self):
        """Initializes a new instance of the class.
        """
        self.instrumentation_key = None
        self.device = contracts.Device()
        self.cloud = contracts.Cloud()
        self.application = contracts.Application()
        self.user = contracts.User()
        self.session = contracts.Session()
        self.operation = contracts.Operation()
        self.location = contracts.Location()
        self._properties = {}

    @property
    def properties(self):
        """The property context. This contains free-form properties that you can add to your telemetry.

        Returns:
            (dict). the context object.
        """
        return self._properties
