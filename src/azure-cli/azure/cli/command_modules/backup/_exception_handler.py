# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def backup_exception_handler(ex):
    from azure.core.exceptions import HttpResponseError
    if isinstance(ex, HttpResponseError) and ex.message:
        raise HttpResponseError(ex.message)
    raise ex
