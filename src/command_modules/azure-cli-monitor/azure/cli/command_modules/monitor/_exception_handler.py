# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def monitor_exception_handler(ex):
    from azure.mgmt.monitor.models import ErrorResponseException
    from knack.util import CLIError

    if isinstance(ex, ErrorResponseException):
        # work around for issue: https://github.com/Azure/azure-sdk-for-python/issues/1556
        error_payload = ex.response.json()
        error_payload = {k.lower(): v for k, v in error_payload.items()}
        if 'code' in error_payload and 'message' in error_payload:
            message = '{}.'.format(error_payload['message']) if error_payload['message'] else 'Operation failed.'
            code = '[Code: "{}"]'.format(error_payload['code']) if error_payload['code'] else ''
            raise CLIError('{} {}'.format(message, code))
        else:
            raise CLIError(ex)
    else:
        import sys
        from six import reraise
        reraise(*sys.exc_info())


def missing_resource_handler(exception):
    from msrest.exceptions import HttpOperationError
    from knack.util import CLIError

    if isinstance(exception, HttpOperationError) and exception.response.status_code == 404:
        raise CLIError('Can\'t find the resource.')
    else:
        raise CLIError(exception.message)
