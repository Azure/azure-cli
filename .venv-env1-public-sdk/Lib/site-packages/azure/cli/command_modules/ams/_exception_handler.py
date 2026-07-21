# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def ams_exception_handler(ex):
    from azure.core.exceptions import HttpResponseError
    from msrest.exceptions import ValidationError
    from knack.util import CLIError

    if isinstance(ex, HttpResponseError) and ex.message:
        raise CLIError(ex.message)
    if isinstance(ex, (ValidationError, IOError, ValueError)):
        raise CLIError(ex)
    raise ex
