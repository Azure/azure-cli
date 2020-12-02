# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def exception_handler(ex):
    from msrest.exceptions import HttpOperationError
    from azure.mgmt.loganalytics.models import DataExportErrorResponseException
    if isinstance(ex, (DataExportErrorResponseException,)):
        ex.message = ex.response.text
    elif isinstance(ex, HttpOperationError):
        # work around for issue: https://github.com/Azure/azure-sdk-for-python/issues/1556
        additional_properties = getattr(ex.error, 'additional_properties', {})
        if 'Code' in additional_properties and 'Message' in additional_properties:
            ex.error.code = additional_properties['Code']
            ex.error.message = additional_properties['Message']
            ex.message = additional_properties['Message']
    raise ex
