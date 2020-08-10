import sys
from applicationinsights import TelemetryClient, channel

original_excepthook = None
telemetry_channel = None
enabled_instrumentation_keys = []

def enable(instrumentation_key, *args, **kwargs):
    """Enables the automatic collection of unhandled exceptions. Captured exceptions will be sent to the Application
    Insights service before being re-thrown. Multiple calls to this function with different instrumentation keys result
    in multiple instances being submitted, one for each key.

    .. code:: python

        from applicationinsights.exceptions import enable

        # set up exception capture
        enable('<YOUR INSTRUMENTATION KEY GOES HERE>')

        # raise an exception (this will be sent to the Application Insights service as an exception telemetry object)
        raise Exception('Boom!')

    Args:
        instrumentation_key (str). the instrumentation key to use while sending telemetry to the service.
    """
    if not instrumentation_key:
        raise Exception('Instrumentation key was required but not provided')
    global original_excepthook
    global telemetry_channel
    telemetry_channel = kwargs.get('telemetry_channel')
    if not original_excepthook:
        original_excepthook = sys.excepthook
        sys.excepthook = intercept_excepthook
    if instrumentation_key not in enabled_instrumentation_keys:
        enabled_instrumentation_keys.append(instrumentation_key)


def intercept_excepthook(type, value, traceback):
    client = TelemetryClient('temp_key', telemetry_channel)
    for instrumentation_key in enabled_instrumentation_keys:
        client.context.instrumentation_key = instrumentation_key
        client.track_exception(type, value, traceback)
    client.flush()
    original_excepthook(type, value, traceback)