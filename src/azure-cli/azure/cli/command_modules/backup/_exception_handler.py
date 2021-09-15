# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def backup_exception_handler(ex):
    from azure.core.exceptions import HttpResponseError
    if isinstance(ex, HttpResponseError):
        text = ex.response.text(encoding='utf-8')
        if len(ex.args) == 1 and isinstance(ex.args[0], str):
            ex.args = tuple([ex.args[0] + ": \n" + text])
    raise ex
