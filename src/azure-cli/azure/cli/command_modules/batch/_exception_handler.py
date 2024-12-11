# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

# for data plane this should work for custom code
def batch_exception_handler(ex):
    from msrest.exceptions import ValidationError, ClientRequestError
    from azure.core.exceptions import HttpResponseError
    if isinstance(ex, HttpResponseError): # make sure the default httpresponseerror works for mgmt plane
        try:
            message = ex.model.message.value
            if ex.model.values_property:
                for detail in ex.model.values_property:
                    message += f"\n{detail.key}: {detail.value}"
            raise CLIError(message)
        except AttributeError: 
            raise CLIError(ex)
    elif isinstance(ex, (ValidationError, ClientRequestError)):
        raise CLIError(ex)
    else:
        raise ex

# custom.py
# list jobs should work for custom command check

# also do a mgmt plane code check to make sure it raises errors correctly