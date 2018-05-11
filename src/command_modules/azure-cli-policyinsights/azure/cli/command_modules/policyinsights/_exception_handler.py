# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError

def policyinsights_exception_handler(ex):
    from azure.mgmt.policyinsights.models import QueryFailure

    if isinstance(ex, QueryFailure):
        message = ex.error.message
        raise CLIError(message)
    else:
        import sys
        from six import reraise

        reraise(*sys.exc_info())
