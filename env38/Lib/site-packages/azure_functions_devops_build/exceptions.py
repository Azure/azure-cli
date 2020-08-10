# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class BaseException(Exception):
    def __init__(self, message=None):
        self.message = message

class GitOperationException(BaseException):
    pass


class RoleAssignmentException(BaseException):
    pass


class LanguageNotSupportException(BaseException):
    pass


class BuildErrorException(BaseException):
    pass


class ReleaseErrorException(BaseException):
    pass


class GithubContentNotFound(BaseException):
    pass


class GithubIntegrationRequestError(BaseException):
    pass


class GithubUnauthorizedError(BaseException):
    pass
