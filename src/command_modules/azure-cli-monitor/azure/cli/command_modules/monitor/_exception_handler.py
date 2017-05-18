# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError


def monitor_exception_handler(ex):
    from azure.mgmt.monitor.models import ErrorResponseException
    if hasattr(ex, 'inner_exception') and 'MonitoringService' in ex.inner_exception.message:
        raise CLIError(ex.inner_exception.code)
    elif isinstance(ex, ErrorResponseException):
        raise CLIError(ex)
    else:
        import sys
        from six import reraise
        reraise(*sys.exc_info())
