from knack.util import CLIError


def alertsmanagement_exception_handler(ex):
    from azure.mgmt.alertsmanagement.models import ErrorResponseException
    if isinstance(ex, ErrorResponseException):
        message = ex.error.error.message
        raise CLIError(message)
    import sys
    from six import reraise
    reraise(*sys.exc_info())
