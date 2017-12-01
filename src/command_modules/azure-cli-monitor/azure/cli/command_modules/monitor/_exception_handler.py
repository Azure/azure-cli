# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError


def monitor_exception_handler(ex):
    from azure.mgmt.monitor.models import ErrorResponseException
    if isinstance(ex, ErrorResponseException):
        # work around for issue: https://github.com/Azure/azure-sdk-for-python/issues/1556
        error_payload = ex.response.json()
        if 'Code' in error_payload and 'Message' in error_payload:
            raise CLIError('Operation failed. {}. [Code: {}]'.format(error_payload['Message'], error_payload['Code']))
        else:
            raise CLIError(ex)
    else:
        import sys
        from six import reraise
        reraise(*sys.exc_info())


def missing_resource_handler(exception):
    from msrest.exceptions import HttpOperationError
    if isinstance(exception, HttpOperationError) and exception.response.status_code == 404:
        raise CLIError('Can\'t find the resource.')
    else:
        raise CLIError(exception.message)
