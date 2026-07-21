
from . import common
from applicationinsights import logging

import sys

class LoggingHandler(logging.LoggingHandler):
    """This class is a LoggingHandler that uses the same settings as the Django middleware to configure
    the telemetry client.  This can be referenced from LOGGING in your Django settings.py file.  As an
    example, this code would send all Django log messages--WARNING and up--to Application Insights:
    
    .. code:: python
    
            LOGGING = {
                'version': 1,
                'disable_existing_loggers': False,
                'handlers': {
                    # The application insights handler is here
                    'appinsights': {
                        'class': 'applicationinsights.django.LoggingHandler',
                        'level': 'WARNING'
                    }
                },
                'loggers': {
                    'django': {
                        'handlers': ['appinsights'],
                        'level': 'WARNING',
                        'propagate': True,
                    }
                }
            }
            
            # You will need this anyway if you're using the middleware.
            # See the middleware documentation for more information on configuring
            # this setting:
            APPLICATION_INSIGHTS = {
                'ikey': '00000000-0000-0000-0000-000000000000'
            }
    """
    def __init__(self, *args, **kwargs):
        client = common.create_client()
        new_kwargs = {}
        new_kwargs.update(kwargs)
        new_kwargs['telemetry_channel'] = client.channel
        super(LoggingHandler, self).__init__(client.context.instrumentation_key, *args, **new_kwargs)
