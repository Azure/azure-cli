# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def response_exception_handler(ex):
    from azure.mgmt.servicebus.models import ErrorResponseException
    from knack.util import CLIError

    if isinstance(ex, ErrorResponseException):
        error_message = ex.response.json()
        error_message = {k.lower(): v for k, v in error_message.items()}
        if 'error' in error_message:
            error_message = error_message['error']
        if 'code' in error_message and 'message' in error_message:
            message = '{}.'.format(error_message['message']) if error_message['message'] else 'Operation failed.'
            code = '[Code: "{}"]'.format(error_message['code']) if error_message['code'] else ''
            raise CLIError('{} - {}'.format(code, message))
        else:
            raise CLIError(ex)
    else:
        import sys
        from six import reraise
        reraise(*sys.exc_info())


# pylint: disable=inconsistent-return-statements
def empty_on_404(ex):
    from azure.mgmt.eventhub.models import ErrorResponseException
    if isinstance(ex, ErrorResponseException) and ex.response.status_code == 404:
        return None
    raise ex