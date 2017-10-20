# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError

def subscriptiondefinition_exception_handler(ex):
    from azure.mgmt.subscriptiondefinition.models import ErrorResponseException
    if isinstance(ex, ErrorResponseException):
        message = ex.error.error.message
        raise CLIError(message)
    else:
        import sys
        from sys import reraise
        reraise(*sys.exc_info())
