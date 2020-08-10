import datetime
import re
import uuid
import applicationinsights

class WSGIApplication(object):
    """ This class represents a WSGI wrapper that enables request telemetry for existing WSGI applications. The request
    telemetry will be sent to Application Insights service using the supplied instrumentation key.

    .. code:: python

            from applicationinsights.requests import WSGIApplication
            from paste.httpserver import serve
            from pyramid.response import Response
            from pyramid.view import view_config

            @view_config()
            def hello(request):
                return Response('Hello')

            if __name__ == '__main__':
                from pyramid.config import Configurator
                config = Configurator()
                config.scan()
                app = config.make_wsgi_app()

                # Enable Application Insights middleware
                app = WSGIApplication('<YOUR INSTRUMENTATION KEY GOES HERE>', app, common_properties={'service': 'hello_world_service'})

                serve(app, host='0.0.0.0')
    """
    def __init__(self, instrumentation_key, wsgi_application, *args, **kwargs):
        """
        Initialize a new instance of the class.

        Args:
            instrumentation_key (str). the instrumentation key to use while sending telemetry to the service.\n
            wsgi_application (func). the WSGI application that we're wrapping.
        """
        if not instrumentation_key:
            raise Exception('Instrumentation key was required but not provided')
        if not wsgi_application:
            raise Exception('WSGI application was required but not provided')
        telemetry_channel = kwargs.pop('telemetry_channel', None)
        if not telemetry_channel:
            sender = applicationinsights.channel.AsynchronousSender()
            queue = applicationinsights.channel.AsynchronousQueue(sender)
            telemetry_channel = applicationinsights.channel.TelemetryChannel(None, queue)
        self.client = applicationinsights.TelemetryClient(instrumentation_key, telemetry_channel)
        self.client.context.device.type = "PC"
        self._wsgi_application = wsgi_application
        self._common_properties = kwargs.pop('common_properties', {})

    def flush(self):
        """Flushes the queued up telemetry to the service.
        """
        self.client.flush()

    def __call__(self, environ, start_response):
        """Callable implementation for WSGI middleware.

        Args:
            environ (dict). a dictionary containing all WSGI environment properties for this request.\n
            start_response (func). a function used to store the status, HTTP headers to be sent to the client and optional exception information.

        Returns:
            (obj). the response to send back to the client.
        """
        start_time = datetime.datetime.utcnow()
        name = environ.get('PATH_INFO') or '/'
        closure = {'status': '200 OK'}
        http_method = environ.get('REQUEST_METHOD', 'GET')

        self.client.context.operation.id = str(uuid.uuid4())
        # operation.parent_id ought to be the request id (not the operation id, but we don't have it yet)
        self.client.context.operation.name = http_method + ' ' + name

        def status_interceptor(status_string, headers_array, exc_info=None):
            closure['status'] = status_string
            start_response(status_string, headers_array, exc_info)

        for part in self._wsgi_application(environ, status_interceptor):
            yield part

        success = True
        response_match = re.match(r'\s*(?P<code>\d+)', closure['status'])
        if response_match:
            response_code = response_match.group('code')
            if int(response_code) >= 400:
                success = False
        else:
            response_code = closure['status']
            success = False
            
        url = name
        query_string = environ.get('QUERY_STRING')
        if query_string:
            url += '?' + query_string

        scheme = environ.get('wsgi.url_scheme', 'http')
        host =  environ.get('HTTP_HOST', environ.get('SERVER_NAME', 'unknown'))

        url = scheme + '://' + host + url

        end_time = datetime.datetime.utcnow()
        duration = int((end_time - start_time).total_seconds() * 1000)

        self.client.track_request(name, url, success, start_time.isoformat() + 'Z', duration, response_code, http_method, self._common_properties)
