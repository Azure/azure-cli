# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def ams_resource_not_found(resource_name):
    bad_request_msg = "{}(s) not found. Please verify the resource(s), group or it's parent resources exist."
    ams_not_found_msg = bad_request_msg.format(resource_name)
    return build_exception_wrapper(404, ams_not_found_msg)

def storage_account_not_found():
    return build_exception_wrapper(400, "Storage Account not found. Please verify the storage account exists.")

def build_exception_wrapper(status_code, message):
    def build_exception(ex):
        from azure.mgmt.media.models.api_error import ApiErrorException
        from knack.util import CLIError

        if isinstance(ex, ApiErrorException) \
                and ex.response is not None \
                and ex.response.status_code == status_code:
            raise CLIError(ex.message if ex.message else message)
        raise ex
    return build_exception
