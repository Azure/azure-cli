# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
from enum import Enum

from knack.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)


class AzCLIErrorType(Enum):
    """ AzureCLI error types """

    # userfaults
    CommandNotFoundError = 'CommandNotFoundError'
    ArgumentParseError = 'ArgumentParseError'
    UsageError = 'UsageError'
    ResourceNotFound = 'ResourceNotFound'
    ValidationError = 'ValidationError'
    ManualInterrupt = 'ManualInterrupt'
    # service side error
    ServiceError = 'ServiceError'
    # client side error
    ClientError = 'ClientError'
    # unexpected error
    UnexpectedError = 'UnexpectedError'


class AzCLIError(CLIError):
    """ AzureCLI error definition """

    def __init__(self, error_type, error_msg, raw_exception=None, command=None):
        """
        :param error_type: The name of the AzureCLI error type.
        :type error_type: azure.cli.core.util.AzCLIErrorType
        :param error_msg: The error message detail.
        :type error_msg: str
        :param raw_exception: The raw exception.
        :type raw_exception: Exception
        :param command: The command which brings the error.
        :type command: str
        :param recommendations: The recommendations to resolve the error.
        :type recommendations: list
        """
        self.error_type = error_type
        self.error_msg = error_msg
        self.raw_exception = raw_exception
        self.command = command
        self.recommendations = []
        super().__init__(error_msg)

    def set_recommendation(self, recommendation):
        self.recommendations.append(recommendation)

    def set_raw_exception(self, raw_exception):
        self.raw_exception = raw_exception

    def print_error(self):
        from azure.cli.core.azlogging import CommandLoggerContext
        with CommandLoggerContext(logger):
            message = '{}: {}'.format(self.error_type.value, self.error_msg)
            logger.error(message)
            if self.raw_exception:
                logger.exception(self.raw_exception)
            if self.recommendations:
                for recommendation in self.recommendations:
                    print(recommendation, file=sys.stderr)

    def send_telemetry(self):
        import azure.cli.core.telemetry as telemetry
        telemetry.set_error_type(self.error_type.value)

        # For userfaults
        if self.error_type in [AzCLIErrorType.CommandNotFoundError,
                               AzCLIErrorType.ArgumentParseError,
                               AzCLIErrorType.ValidationError,
                               AzCLIErrorType.ManualInterrupt]:
            telemetry.set_user_fault(self.error_msg)

        # For failures: service side error, client side error, unexpected error
        else:
            telemetry.set_failure(self.error_msg)

        # For unexpected error
        if self.raw_exception:
            telemetry.set_exception(self.raw_exception, '')
