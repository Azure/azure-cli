# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def ams_exception_handler(ex):
    from azure.mgmt.media.models.api_error import ApiErrorException
    from knack.util import CLIError

    if isinstance(ex, ApiErrorException) \
            and ex.response is not None:
        raise CLIError(ex.message)
    raise ex
