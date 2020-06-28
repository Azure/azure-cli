from os import getenv

from applicationinsights import TelemetryClient
from applicationinsights.channel import AsynchronousSender
from applicationinsights.channel import AsynchronousQueue
from applicationinsights.channel import TelemetryChannel
from applicationinsights.logging import LoggingHandler
from applicationinsights.requests import WSGIApplication

CONF_PREFIX = "APPINSIGHTS"

CONF_KEY = CONF_PREFIX + "_INSTRUMENTATIONKEY"
CONF_ENDPOINT_URI = CONF_PREFIX + "_ENDPOINT_URI"
CONF_DISABLE_REQUEST_LOGGING = CONF_PREFIX + "_DISABLE_REQUEST_LOGGING"
CONF_DISABLE_TRACE_LOGGING = CONF_PREFIX + "_DISABLE_TRACE_LOGGING"
CONF_DISABLE_EXCEPTION_LOGGING = CONF_PREFIX + "_DISABLE_EXCEPTION_LOGGING"


class AppInsights(object):
    """ This class represents a Flask extension that enables request telemetry,
    trace logging and exception logging for a Flask application. The telemetry
    will be sent to Application Insights service using the supplied
    instrumentation key.

    The following Flask config variables can be used to configure the extension:

    - Set ``APPINSIGHTS_INSTRUMENTATIONKEY`` to a string to provide the
      instrumentation key to send telemetry to application insights.
      Alternatively, this value can also be provided via an environment variable
      of the same name.

    - Set ``APPINSIGHTS_ENDPOINT_URI`` to a string to customize the telemetry
      endpoint to which Application Insights will send the telemetry.

    - Set ``APPINSIGHTS_DISABLE_REQUEST_LOGGING`` to ``False`` to disable
      logging of Flask requests to Application Insights.

    - Set ``APPINSIGHTS_DISABLE_TRACE_LOGGING`` to ``False`` to disable logging
      of all log traces to Application Insights.

    - Set ``APPINSIGHTS_DISABLE_EXCEPTION_LOGGING`` to ``False`` to disable
      logging of all exceptions to Application Insights.

    .. code:: python

            from flask import Flask
            from applicationinsights.flask.ext import AppInsights

            # instantiate the Flask application
            app = Flask(__name__)
            app.config['APPINSIGHTS_INSTRUMENTATIONKEY'] = '<YOUR INSTRUMENTATION KEY GOES HERE>'

            # log requests, traces and exceptions to the Application Insights service
            appinsights = AppInsights(app)

            # define a simple route
            @app.route('/')
            def hello_world():
                return 'Hello World!'

            # run the application
            if __name__ == '__main__':
                app.run()
    """
    def __init__(self, app=None):
        """
        Initialize a new instance of the extension.

        Args:
            app (flask.Flask). the Flask application for which to initialize the extension.
        """
        self._key = None
        self._endpoint_uri = None
        self._channel = None
        self._requests_middleware = None
        self._trace_log_handler = None
        self._exception_telemetry_client = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Initializes the extension for the provided Flask application.

        Args:
            app (flask.Flask). the Flask application for which to initialize the extension.
        """
        self._key = app.config.get(CONF_KEY) or getenv(CONF_KEY)

        if not self._key:
            return

        self._endpoint_uri = app.config.get(CONF_ENDPOINT_URI)

        if self._endpoint_uri:
            sender = AsynchronousSender(self._endpoint_uri)
        else:
            sender = AsynchronousSender()

        queue = AsynchronousQueue(sender)
        self._channel = TelemetryChannel(None, queue)

        self._init_request_logging(app)
        self._init_trace_logging(app)
        self._init_exception_logging(app)

    def _init_request_logging(self, app):
        """
        Sets up request logging unless ``APPINSIGHTS_DISABLE_REQUEST_LOGGING``
        is set in the Flask config.

        Args:
            app (flask.Flask). the Flask application for which to initialize the extension.
        """
        enabled = not app.config.get(CONF_DISABLE_REQUEST_LOGGING, False)

        if not enabled:
            return

        self._requests_middleware = WSGIApplication(
            self._key, app.wsgi_app, telemetry_channel=self._channel)

        app.wsgi_app = self._requests_middleware

    def _init_trace_logging(self, app):
        """
        Sets up trace logging unless ``APPINSIGHTS_DISABLE_TRACE_LOGGING`` is
        set in the Flask config.

        Args:
            app (flask.Flask). the Flask application for which to initialize the extension.
        """
        enabled = not app.config.get(CONF_DISABLE_TRACE_LOGGING, False)

        if not enabled:
            return

        self._trace_log_handler = LoggingHandler(
            self._key, telemetry_channel=self._channel)

        app.logger.addHandler(self._trace_log_handler)

    def _init_exception_logging(self, app):
        """
        Sets up exception logging unless ``APPINSIGHTS_DISABLE_EXCEPTION_LOGGING``
        is set in the Flask config.

        Args:
            app (flask.Flask). the Flask application for which to initialize the extension.
        """
        enabled = not app.config.get(CONF_DISABLE_EXCEPTION_LOGGING, False)

        if not enabled:
            return

        exception_telemetry_client = TelemetryClient(
            self._key, telemetry_channel=self._channel)

        @app.errorhandler(Exception)
        def exception_handler(exception):
            try:
                raise exception
            except Exception:
                exception_telemetry_client.track_exception()
            finally:
                raise exception

        self._exception_telemetry_client = exception_telemetry_client

    def flush(self):
        """Flushes the queued up telemetry to the service.
        """
        if self._requests_middleware:
            self._requests_middleware.flush()

        if self._trace_log_handler:
            self._trace_log_handler.flush()

        if self._exception_telemetry_client:
            self._exception_telemetry_client.flush()
