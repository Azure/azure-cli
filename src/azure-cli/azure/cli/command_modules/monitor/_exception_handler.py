# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def monitor_exception_handler(ex):
    from azure.mgmt.monitor.v2015_04_01.models import ErrorResponseException as ErrorResponseException_v2015_04_01
    from azure.mgmt.monitor.v2016_03_01.models import ErrorResponseException as ErrorResponseException_v2016_03_01
    from azure.mgmt.monitor.v2017_04_01.models import ErrorResponseException as ErrorResponseException_v2017_04_01
    from azure.mgmt.monitor.v2017_05_01_preview.models import \
        ErrorResponseException as ErrorResponseException_v2017_05_01
    from azure.mgmt.monitor.v2018_01_01.models import ErrorResponseException as ErrorResponseException_v2018_01_01
    from azure.mgmt.monitor.v2018_03_01.models import ErrorResponseException as ErrorResponseException_v2018_03_01
    from azure.mgmt.monitor.v2019_06_01.models import ErrorResponseException as ErrorResponseException_v2019_06_01

    from knack.util import CLIError

    if isinstance(ex, (ErrorResponseException_v2015_04_01,
                       ErrorResponseException_v2016_03_01,
                       ErrorResponseException_v2017_04_01,
                       ErrorResponseException_v2017_05_01,
                       ErrorResponseException_v2018_01_01,
                       ErrorResponseException_v2018_03_01,
                       ErrorResponseException_v2019_06_01
                       )):
        # work around for issue: https://github.com/Azure/azure-sdk-for-python/issues/1556
        try:
            error_payload = ex.response.json()
        except ValueError:
            raise CLIError(ex)
        error_payload = {k.lower(): v for k, v in error_payload.items()}
        if 'error' in error_payload:
            error_payload = error_payload['error']
        if 'code' in error_payload and 'message' in error_payload:
            message = '{}.'.format(error_payload['message']) if error_payload['message'] else 'Operation failed.'
            code = '[Code: "{}"]'.format(error_payload['code']) if error_payload['code'] else ''
            raise CLIError('{} {}'.format(message, code))
        raise CLIError(ex)
    import sys
    from six import reraise
    reraise(*sys.exc_info())


def missing_resource_handler(exception):
    from msrest.exceptions import HttpOperationError
    from knack.util import CLIError

    if isinstance(exception, HttpOperationError) and exception.response.status_code == 404:
        raise CLIError('Can\'t find the resource.')
    raise CLIError(exception.message)
