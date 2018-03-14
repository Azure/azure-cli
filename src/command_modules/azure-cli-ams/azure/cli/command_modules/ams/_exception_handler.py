# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def build_exception_wrapper(message=None):
    def build_exception(ex):
        from azure.mediav3.models.api_error import ApiErrorException
        from knack.util import CLIError

        if isinstance(ex, ApiErrorException) \
                and ex.response is not None:
            raise CLIError(ex.message if ex.message else message)
        raise ex
    return build_exception
