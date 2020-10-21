# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys

import azure.cli.core.telemetry as telemetry
from knack.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)
# pylint: disable=unnecessary-pass


# Error types in AzureCLI are from different sources, and there are many general error types like CLIError, AzureError.
# Besides, many error types with different names are actually showing the same kind of error.
# For example, CloudError, CLIError and ValidtionError all could be a resource-not-found error.
# Therefore, here we define the new error classes to map and categorize all of the error types from different sources.


# region: Base Layer
# Base class for all the AzureCLI defined error classes.
# DO NOT raise the error class here directly in your codes.
class AzCLIError(CLIError):
    """ Base class for all the AzureCLI defined error classes. """

    def __init__(self, error_msg, recommendation=None):
        # error message
        self.error_msg = error_msg

        # set recommendations to fix the error if the message is not actionable,
        # they will be printed to users after the error message, one recommendation per line
        self.recommendations = []
        if isinstance(recommendation, str):
            self.recommendations = [recommendation]
        elif isinstance(recommendation, list):
            self.recommendations = recommendation

        # exception trace for the error
        self.exception_trace = None
        super().__init__(error_msg)

    def set_recommendation(self, recommendation):
        self.recommendations.append(recommendation)

    def set_exception_trace(self, exception_trace):
        self.exception_trace = exception_trace

    def print_error(self):
        from azure.cli.core.azlogging import CommandLoggerContext
        with CommandLoggerContext(logger):
            # print error type and error message
            message = '{}: {}'.format(self.__class__.__name__, self.error_msg)
            logger.error(message)
            # print exception trace if there is
            if self.exception_trace:
                logger.exception(self.exception_trace)
            # print recommendations to action
            if self.recommendations:
                for recommendation in self.recommendations:
                    print(recommendation, file=sys.stderr)

    def send_telemetry(self):
        telemetry.set_error_type(self.__class__.__name__)
# endregion


# region: Second Layer
# Main categories of the AzureCLI error types, used for Telemetry analysis
# DO NOT raise the error classes here directly in your codes.
class UserFault(AzCLIError):
    """ Users should be responsible for the errors. """
    def send_telemetry(self):
        super().send_telemetry()
        telemetry.set_user_fault(self.error_msg)


class ServiceError(AzCLIError):
    """ Azure Services should be responsible for the errors.  """
    def send_telemetry(self):
        super().send_telemetry()
        telemetry.set_failure(self.error_msg)


class ClientError(AzCLIError):
    """ AzureCLI should be responsible for the errors. """
    def send_telemetry(self):
        super().send_telemetry()
        telemetry.set_failure(self.error_msg)
        if self.exception_trace:
            telemetry.set_exception(self.exception_trace, '')
# endregion


# region: Third Layer
# Sub-categories of the AzureCLI error types, shown to users
# Raise the error classes here in your codes
# Avoid using fallback error classes unless you can not find a proper one
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
    """ Arguments can not be specfied together. """
    pass


class InvalidArgumentValueError(UserFault):
    """ Argument value is not valid. """
    pass


class ArgumentParseError(UserFault):
    """ Fallback of the argument parsing related errors.
    Avoid using this class unless the error can not be classified
    into the above Argument related error types. """
    pass


class UsageError(UserFault):
    """ Fallback of the argument usage related errors.
    Avoid using this class unless the error can not be classified
    into the above Argument related error types. """
    pass


# Response related error types
class BadRequestError(UserFault):
    """ Bad request from client: 400 error """
    pass


class UnauthorizedError(UserFault):
    """ Unauthorized request: 401 error """


class ForbiddenError(UserFault):
    """ Service refuse to response: 403 error """


class ResourceNotFoundError(UserFault):
    """ Can not find Azure resources: 404 error """
    pass


class AzureInternalError(ServiceError):
    """ Azure service internal error: 5xx error """
    pass


class AzureResponseError(UserFault):
    """ Fallback of the response related errors.
    Avoid using this class unless the error can not be classified
    into the above Response related error types. """


# Request related error types
class AzureConnectionError(UserFault):
    """ Connection issues like connection timeout, aborted or broken. """
    pass


class ClientRequestError(UserFault):
    """ Fallback of the request related errors. Error occurs while attempting
    to make a request to the service. No request is sent.
    Avoid using this class unless the error can not be classified
    into the above Request related errors types. """


# Validation related error types
class ValidationError(UserFault):
    """ Fallback of the errors in validation functions.
    Avoid using this class unless the error can not be classified into
    the Argument, Request and Response related error types above. """
    pass


# CLI internal error type
class CLIInternalError(ClientError):
    """ AzureCLI internal error """
    pass


# Keyboard interrupt error type
class ManualInterrupt(UserFault):
    """ Keyboard interrupt. """
    pass


# Unknow error type
class UnknownError(UserFault):
    """ Reserved for the errors which can not be categorized into the error types above.
    Usually for the very general error type like CLIError, AzureError.
    Error type info will not printed to users for this class. """
    def print_error(self):
        from azure.cli.core.azlogging import CommandLoggerContext
        with CommandLoggerContext(logger):
            # print only error message (no error type)
            logger.error(self.error_msg)
            # print recommendations to action
            if self.recommendations:
                for recommendation in self.recommendations:
                    print(recommendation, file=sys.stderr)

# endregion
