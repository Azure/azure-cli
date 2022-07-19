# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys

from azure.cli.core import telemetry
from knack.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)
# pylint: disable=unnecessary-pass


# Error types in AzureCLI are from different sources, and there are many general error types like CLIError, AzureError.
# Besides, many error types with different names are actually showing the same kind of error.
# For example, CloudError, CLIError and ValidationError all could be a resource-not-found error.
# Therefore, here we define the new error classes to map and categorize all of the error types from different sources.


# region: Base Layer
# Base class for all the AzureCLI defined error classes.
class AzCLIError(CLIError):
    """ Base class for all the AzureCLI defined error classes.
    DO NOT raise this error class in your codes. """

    def __init__(self, error_msg, recommendation=None):
        # error message
        self.error_msg = error_msg

        # manual recommendations provided based on developers' knowledge
        self.recommendations = []
        self.set_recommendation(recommendation)

        # AI recommendations provided by Aladdin service, with tuple form: (recommendation, description)
        self.aladdin_recommendations = []

        # exception trace for the error
        self.exception_trace = None
        super().__init__(error_msg)

    def set_recommendation(self, recommendation):
        """" Set manual recommendations for the error.
        Command module or extension authors could call this method to provide recommendations,
        the recommendations will be printed after the error message, one recommendation per line
        """
        if isinstance(recommendation, str):
            self.recommendations.append(recommendation)
        elif isinstance(recommendation, list):
            self.recommendations.extend(recommendation)

    def set_aladdin_recommendation(self, recommendations):
        """ Set aladdin recommendations for the error.
        One item should be a tuple with the form: (recommendation, description)
        """
        self.aladdin_recommendations.extend(recommendations)

    def set_exception_trace(self, exception_trace):
        self.exception_trace = exception_trace

    def print_error(self):
        from azure.cli.core.azlogging import CommandLoggerContext
        from azure.cli.core.style import print_styled_text
        with CommandLoggerContext(logger):
            # print error message
            logger.error(self.error_msg)

            # print exception trace if there is
            if self.exception_trace:
                logger.exception(self.exception_trace)

        # print recommendations to action
        if self.recommendations:
            for recommendation in self.recommendations:
                print(recommendation, file=sys.stderr)

        if self.aladdin_recommendations:
            print('\nExamples from AI knowledge base:', file=sys.stderr)
            for recommendation, description in self.aladdin_recommendations:
                print_styled_text(recommendation, file=sys.stderr)
                print_styled_text(description, file=sys.stderr)

    def send_telemetry(self):
        telemetry.set_error_type(self.__class__.__name__)
# endregion


# region: Second Layer
# Main categories of the AzureCLI error types, used for Telemetry analysis
class UserFault(AzCLIError):
    """ Users should be responsible for the errors.
    DO NOT raise this error class in your codes. """
    def send_telemetry(self):
        super().send_telemetry()
        telemetry.set_user_fault(self.error_msg)


class ServiceError(AzCLIError):
    """ Azure Services should be responsible for the errors.
    DO NOT raise this error class in your codes. """
    def send_telemetry(self):
        super().send_telemetry()
        telemetry.set_failure(self.error_msg)


class ClientError(AzCLIError):
    """ AzureCLI should be responsible for the errors.
    DO NOT raise this error class in your codes. """
    def send_telemetry(self):
        super().send_telemetry()
        telemetry.set_failure(self.error_msg)
        if self.exception_trace:
            telemetry.set_exception(self.exception_trace, '')


class UnknownError(AzCLIError):
    """ Unclear errors, could not know who should be responsible for the errors.
    DO NOT raise this error class in your codes. """
    def send_telemetry(self):
        super().send_telemetry()
        telemetry.set_failure(self.error_msg)

# endregion


# region: Third Layer
# Specific categories of the AzureCLI error types
# Raise the error classes here in your codes. Avoid using fallback error classes unless you can not find a proper one.
# Command related error types
class CommandNotFoundError(UserFault):
    """ Command is misspelled or not recognized by AzureCLI. """
    pass


# Argument related error types
class UnrecognizedArgumentError(UserFault):
    """ Argument is misspelled or not recognized by AzureCLI. """
    pass


class RequiredArgumentMissingError(UserFault):
    """ Required argument is not specified. """
    pass


class MutuallyExclusiveArgumentError(UserFault):
    """ Arguments can not be specified together. """
    pass


class InvalidArgumentValueError(UserFault):
    """ Argument value is not valid. """
    pass


class ArgumentUsageError(UserFault):
    """ Fallback of the argument usage related errors.
    Avoid using this class unless the error can not be classified
    into the Argument related specific error types. """
    pass


# Response related error types
class BadRequestError(UserFault):
    """ Bad request from client: 400 error """
    pass


class UnauthorizedError(UserFault):
    """ Unauthorized request: 401 error """
    pass


class ForbiddenError(UserFault):
    """ Service refuse to response: 403 error """
    pass


class ResourceNotFoundError(UserFault):
    """ Can not find Azure resources: 404 error """
    pass


class AzureInternalError(ServiceError):
    """ Azure service internal error: 5xx error """
    pass


class AzureResponseError(UserFault):
    """ Fallback of the response related errors.
    Avoid using this class unless the error can not be classified
    into the Response related specific error types. """
    pass


# Request related error types
class AzureConnectionError(UserFault):
    """ Connection issues like connection timeout, aborted or broken. """
    pass


class ClientRequestError(UserFault):
    """ Fallback of the request related errors. Error occurs while attempting
    to make a request to the service. No request is sent.
    Avoid using this class unless the error can not be classified
    into the Request related specific errors types. """
    pass


# File operation related error types
class FileOperationError(UserFault):
    """ For file or directory operation related errors. """
    pass


# Keyboard interrupt error type
class ManualInterrupt(UserFault):
    """ Keyboard interrupt. """
    pass


class NoTTYError(UserFault):
    """ No tty available for prompt. """
    pass


# ARM template related error types
class InvalidTemplateError(UserFault):
    """ ARM template validation fails. It could be caused by incorrect template files or parameters """
    pass


class DeploymentError(UserFault):
    """ ARM template deployment fails. Template file is valid, and error occurs in deployment. """
    pass


# Validation related error types
class ValidationError(UserFault):
    """ Fallback of the errors in validation functions.
    Avoid using this class unless the error can not be classified into
    the Argument, Request and Response related specific error types. """
    pass


class UnclassifiedUserFault(UserFault):
    """ Fallback of the UserFault related error types.
    Avoid using this class unless the error can not be classified into
    the UserFault related specific error types.
    """
    pass


# CLI internal error type
class CLIInternalError(ClientError):
    """ AzureCLI internal error """
    pass


# Client error for az next
class RecommendationError(ClientError):
    """ The client error raised by `az next`. It is needed in `az next` to skip error records. """
    pass


class AuthenticationError(ServiceError):
    """ Raised when AAD authentication fails. """


class HTTPError(CLIError):
    """ Raised when send_raw_request receives HTTP status code >=400. """
    def __init__(self, error_msg, response):
        super().__init__(error_msg)
        self.response = response

# endregion
