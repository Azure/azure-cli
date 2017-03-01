# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class CliTestError(Exception):
    def __init__(self, error_message):
        super(CliTestError, self).__init__(error_message)


class CliExecutionError(Exception):
    def __init__(self, exception):
        self.exception = exception
        message = 'An exception thrown during CLI execution indicates the command will fail. The ' \
                  'exception was designed to be swallowed. Exception: [{}] {}.'
        super(CliExecutionError, self).__init__(message.format(exception.__class__.__name__,
                                                               exception))


class JMESPathCheckAssertionError(AssertionError):
    def __init__(self, query, expected, actual, json_data):
        message = "Query '{}' doesn't yield expected value '{}', instead the actual value " \
                  "is '{}'. Data: \n{}\n".format(query, expected, actual, json_data)
        super(JMESPathCheckAssertionError, self).__init__(message)
