from .middleware import ApplicationInsightsMiddleware
from .logging import LoggingHandler
from . import common

__all__ = ['ApplicationInsightsMiddleware', 'LoggingHandler', 'create_client']

def create_client():
    """Returns an :class:`applicationinsights.TelemetryClient` instance using the instrumentation key
    and other settings found in the current Django project's `settings.py` file."""
    return common.create_client()
