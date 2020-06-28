import logging
import applicationinsights

enabled_instrumentation_keys = {}

def enable(instrumentation_key, *args, **kwargs):
    """Enables the Application Insights logging handler for the root logger for the supplied instrumentation key.
    Multiple calls to this function with different instrumentation keys result in multiple handler instances.

    .. code:: python

        import logging
        from applicationinsights.logging import enable

        # set up logging
        enable('<YOUR INSTRUMENTATION KEY GOES HERE>')

        # log something (this will be sent to the Application Insights service as a trace)
        logging.info('This is a message')

        # logging shutdown will cause a flush of all un-sent telemetry items
        # alternatively set up an async channel via enable('<YOUR INSTRUMENTATION KEY GOES HERE>', telemetry_channel=...)

    Args:
        instrumentation_key (str). the instrumentation key to use while sending telemetry to the service.

    Returns:
        :class:`ApplicationInsightsHandler`. the newly created or existing handler.
    """
    if not instrumentation_key:
        raise Exception('Instrumentation key was required but not provided')
    if instrumentation_key in enabled_instrumentation_keys:
        logging.getLogger().removeHandler(enabled_instrumentation_keys[instrumentation_key])
    handler = LoggingHandler(instrumentation_key, *args, **kwargs)
    handler.setLevel(logging.INFO)
    enabled_instrumentation_keys[instrumentation_key] = handler
    logging.getLogger().addHandler(handler)
    return handler


class LoggingHandler(logging.Handler):
    """This class represents an integration point between Python's logging framework and the Application Insights
    service.

    Logging records are sent to the service either as simple Trace telemetry or as Exception telemetry (in the case
    of exception information being available).

    .. code:: python

        import logging
        from applicationinsights.logging import ApplicationInsightsHandler

        # set up logging
        handler = ApplicationInsightsHandler('<YOUR INSTRUMENTATION KEY GOES HERE>')
        logging.basicConfig(handlers=[ handler ], format='%(levelname)s: %(message)s', level=logging.DEBUG)

        # log something (this will be sent to the Application Insights service as a trace)
        logging.info('This is a message')

        # logging shutdown will cause a flush of all un-sent telemetry items
        # alternatively flush manually via handler.flush()
    """
    def __init__(self, instrumentation_key, *args, **kwargs):
        """
        Initialize a new instance of the class.

        Args:
            instrumentation_key (str). the instrumentation key to use while sending telemetry to the service.
        """
        if not instrumentation_key:
            raise Exception('Instrumentation key was required but not provided')
        telemetry_channel = kwargs.get('telemetry_channel')
        if 'telemetry_channel' in kwargs:
            del kwargs['telemetry_channel']
        self.client = applicationinsights.TelemetryClient(instrumentation_key, telemetry_channel)
        super(LoggingHandler, self).__init__(*args, **kwargs)

    def flush(self):
        """Flushes the queued up telemetry to the service.
        """
        self.client.flush()
        return super(LoggingHandler, self).flush()

    def emit(self, record):
        """Emit a record.

        If a formatter is specified, it is used to format the record. If exception information is present, an Exception
        telemetry object is sent instead of a Trace telemetry object.

        Args:
            record (:class:`logging.LogRecord`). the record to format and send.
        """
        # the set of properties that will ride with the record
        properties = {
            'process': record.processName,
            'module': record.module,
            'fileName': record.filename,
            'lineNumber': record.lineno,
            'level': record.levelname,
        }

        # if we have exec_info, we will use it as an exception
        if record.exc_info:
            self.client.track_exception(*record.exc_info, properties=properties)
            return

        # if we don't simply format the message and send the trace
        formatted_message = self.format(record)
        self.client.track_trace(formatted_message, properties=properties, severity=record.levelname)
