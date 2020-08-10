
import datetime
import inspect
import sys
import time
import uuid

from django.http import Http404

import applicationinsights
from applicationinsights.channel import contracts
from . import common

# Pick a function to measure time; starting with 3.3, time.monotonic is available.
if sys.version_info >= (3, 3):
    TIME_FUNC = time.monotonic
else:
    TIME_FUNC = time.time

class ApplicationInsightsMiddleware(object):
    """This class is a Django middleware that automatically enables request and exception telemetry.  Django versions
    1.7 and newer are supported.
    
    To enable, add this class to your settings.py file in MIDDLEWARE_CLASSES (pre-1.10) or MIDDLEWARE (1.10 and newer):
    
    .. code:: python
    
        # If on Django < 1.10
        MIDDLEWARE_CLASSES = [
            # ... or whatever is below for you ...
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            # ... or whatever is above for you ...
            'applicationinsights.django.ApplicationInsightsMiddleware',   # Add this middleware to the end
        ]
        
        # If on Django >= 1.10
        MIDDLEWARE = [
            # ... or whatever is below for you ...
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            # ... or whatever is above for you ...
            'applicationinsights.django.ApplicationInsightsMiddleware',   # Add this middleware to the end
        ]
    
    And then, add the following to your settings.py file:
    
    .. code:: python
    
        APPLICATION_INSIGHTS = {
            # (required) Your Application Insights instrumentation key
            'ikey': "00000000-0000-0000-0000-000000000000",
            
            # (optional) By default, request names are logged as the request method
            # and relative path of the URL.  To log the fully-qualified view names
            # instead, set this to True.  Defaults to False.
            'use_view_name': True,
            
            # (optional) To log arguments passed into the views as custom properties,
            # set this to True.  Defaults to False.
            'record_view_arguments': True,
            
            # (optional) Exceptions are logged by default, to disable, set this to False.
            'log_exceptions': False,
            
            # (optional) Events are submitted to Application Insights asynchronously.
            # send_interval specifies how often the queue is checked for items to submit.
            # send_time specifies how long the sender waits for new input before recycling
            # the background thread.
            'send_interval': 1.0, # Check every second
            'send_time': 3.0, # Wait up to 3 seconds for an event
            
            # (optional, uncommon) If you must send to an endpoint other than the
            # default endpoint, specify it here:
            'endpoint': "https://dc.services.visualstudio.com/v2/track",
        }
    
    Once these are in place, each request will have an `appinsights` object placed on it.
    This object will have the following properties:
    
    * `client`: This is an instance of the :class:`applicationinsights.TelemetryClient` type, which will
      submit telemetry to the same instrumentation key, and will parent each telemetry item to the current
      request.
    * `request`: This is the :class:`applicationinsights.channel.contracts.RequestData` instance for the
      current request.  You can modify properties on this object during the handling of the current request.
      It will be submitted when the request has finished.
    * `context`: This is the :class:`applicationinsights.channel.TelemetryContext` object for the current
      ApplicationInsights sender.
    
    These properties will be present even when `DEBUG` is `True`, but it may not submit telemetry unless
    `debug_ikey` is set in `APPLICATION_INSIGHTS`, above.
    """
    def __init__(self, get_response=None):
        self.get_response = get_response

        # Get configuration
        self._settings = common.load_settings()
        self._client = common.create_client(self._settings)

    # Pre-1.10 handler
    def process_request(self, request):
        # Populate context object onto request
        addon = RequestAddon(self._client)
        data = addon.request
        context = addon.context
        request.appinsights = addon

        # Basic request properties
        data.start_time = datetime.datetime.utcnow().isoformat() + "Z"
        data.http_method = request.method
        data.url = request.build_absolute_uri()
        data.name = "%s %s" % (request.method, request.path)
        context.operation.name = data.name
        context.operation.id = data.id
        context.location.ip = request.META.get('REMOTE_ADDR', '')
        context.user.user_agent = request.META.get('HTTP_USER_AGENT', '')

        # User
        if hasattr(request, 'user'):
            if request.user is not None and not request.user.is_anonymous and request.user.is_authenticated:
                context.user.account_id = request.user.get_short_name()

        # Run and time the request
        addon.start_stopwatch()
        return None

    # Pre-1.10 handler
    def process_response(self, request, response):
        if hasattr(request, 'appinsights'):
            addon = request.appinsights
            duration = addon.measure_duration()

            data = addon.request
            context = addon.context

            # Fill in data from the response
            data.duration = addon.measure_duration()
            data.response_code = response.status_code
            data.success = response.status_code < 400 or response.status_code == 401

            # Submit and return
            self._client.channel.write(data, context)

        return response

    # 1.10 and up...
    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        self.process_response(request, response)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not hasattr(request, "appinsights"):
            return None

        data = request.appinsights.request
        context = request.appinsights.context

        # Operation name is the method + url by default (set in __call__),
        # If use_view_name is set, then we'll look up the name of the view.
        if self._settings.use_view_name:
            mod = inspect.getmodule(view_func)
            if hasattr(view_func, "__name__"):
                name = view_func.__name__
            elif hasattr(view_func, "__class__") and hasattr(view_func.__class__, "__name__"):
                name = view_func.__class__.__name__
            else:
                name = "<unknown>"

            if mod:
                opname = "%s %s.%s" % (data.http_method, mod.__name__, name)
            else:
                opname = "%s %s" % (data.http_method, name)
            data.name = opname
            context.operation.name = opname

        # Populate the properties with view arguments
        if self._settings.record_view_arguments:
            for i, arg in enumerate(view_args):
                data.properties['view_arg_' + str(i)] = arg_to_str(arg)

            for k, v in view_kwargs.items():
                data.properties['view_arg_' + k] = arg_to_str(v)

        return None

    def process_exception(self, request, exception):
        if not self._settings.log_exceptions:
            return None

        if type(exception) is Http404:
            return None

        _, _, tb = sys.exc_info()
        if tb is None or exception is None:
            # No actual traceback or exception info, don't bother logging.
            return None

        client = applicationinsights.TelemetryClient(self._client.context.instrumentation_key, self._client.channel)
        if hasattr(request, 'appinsights'):
            client.context.operation.parent_id = request.appinsights.request.id

        client.track_exception(type(exception), exception, tb)

        return None

    def process_template_response(self, request, response):
        if hasattr(request, 'appinsights') and hasattr(response, 'template_name'):
            data = request.appinsights.request
            data.properties['template_name'] = response.template_name

        return response

class RequestAddon(object):
    def __init__(self, client):
        self._baseclient = client
        self._client = None
        self.request = contracts.RequestData()
        self.request.id = str(uuid.uuid4())
        self.context = applicationinsights.channel.TelemetryContext()
        self.context.instrumentation_key = client.context.instrumentation_key
        self.context.operation.id = self.request.id
        self._process_start_time = None

    @property
    def client(self):
        if self._client is None:
            # Create a client that submits telemetry parented to the request.
            self._client = applicationinsights.TelemetryClient(self.context.instrumentation_key, self._baseclient.channel)
            self._client.context.operation.parent_id = self.context.operation.id

        return self._client

    def start_stopwatch(self):
        self._process_start_time = TIME_FUNC()

    def measure_duration(self):
        end_time = TIME_FUNC()
        return ms_to_duration(int((end_time - self._process_start_time) * 1000))

def ms_to_duration(n):
    duration_parts = []
    for multiplier in [1000, 60, 60, 24]:
        duration_parts.append(n % multiplier)
        n //= multiplier

    duration_parts.reverse()
    duration = "%02d:%02d:%02d.%03d" % tuple(duration_parts)
    if n:
        duration = "%d.%s" % (n, duration)

    return duration

def arg_to_str_3(arg):
    if isinstance(arg, str):
        return arg
    if isinstance(arg, int):
        return str(arg)
    return repr(arg)

def arg_to_str_2(arg):
    if isinstance(arg, str) or isinstance(arg, unicode):
        return arg
    if isinstance(arg, int):
        return str(arg)
    return repr(arg)

if sys.version_info < (3, 0):
    arg_to_str = arg_to_str_2
else:
    arg_to_str = arg_to_str_3
