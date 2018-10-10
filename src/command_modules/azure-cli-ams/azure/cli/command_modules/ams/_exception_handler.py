# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys


def ams_exception_handler(ex):
    if sys.version_info.major < 3:
        from azure.mgmt.media.models.api_error import ApiErrorException
    else:
        from azure.mgmt.media.models.api_error_py3 import ApiErrorException
    from msrest.exceptions import ValidationError
    from knack.util import CLIError

    if isinstance(ex, ApiErrorException) and ex.message:
        raise CLIError(ex.message)
    if isinstance(ex, (ValidationError, IOError, ValueError)):
        raise CLIError(ex)
    raise ex
