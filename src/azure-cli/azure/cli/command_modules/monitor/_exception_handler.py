# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def exception_handler(ex):
    from azure.core.exceptions import HttpResponseError, ODataV4Format
    if isinstance(ex, HttpResponseError):
        # Workaround for issue: https://github.com/Azure/azure-sdk-for-python/issues/1556 in track2
        if hasattr(ex, 'model'):
            additional_properties = getattr(ex.model, 'additional_properties', {})
            if 'Code' in additional_properties and 'Message' in additional_properties:
                ex.error = ODataV4Format({'code': additional_properties['Code'],
                                          'message': additional_properties['Message']})
                raise HttpResponseError(message=additional_properties['Message'], error=ex.error, response=ex.response)
        elif hasattr(ex, 'error'):
            additional_properties = getattr(ex.error, 'additional_properties', {})
            if 'Code' in additional_properties and 'Message' in additional_properties:
                ex.error.code = additional_properties['Code']
                ex.error.message = additional_properties['Message']
                ex.message = additional_properties['Message']
    raise ex
