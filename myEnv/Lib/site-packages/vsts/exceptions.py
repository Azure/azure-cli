# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.exceptions import (
    ClientException,
    ClientRequestError,
    AuthenticationError,
)


class VstsClientError(ClientException):
    pass


class VstsAuthenticationError(AuthenticationError):
    pass


class VstsClientRequestError(ClientRequestError):
    pass


class VstsServiceError(VstsClientRequestError):
    """VstsServiceError.
    """

    def __init__(self, wrapped_exception):
        self.inner_exception = None
        if wrapped_exception.inner_exception is not None:
            self.inner_exception = VstsServiceError(wrapped_exception.inner_exception)
        super(VstsServiceError, self).__init__(message=wrapped_exception.message,
                                               inner_exception=self.inner_exception)
        self.message = wrapped_exception.message
        self.exception_id = wrapped_exception.exception_id
        self.type_name = wrapped_exception.type_name
        self.type_key = wrapped_exception.type_key
        self.error_code = wrapped_exception.error_code
        self.event_id = wrapped_exception.event_id
        self.custom_properties = wrapped_exception.custom_properties
