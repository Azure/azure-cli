# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from msrest.exceptions import ValidationError  # pylint: disable=import-error
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError, ResourceExistsError, ResourceNotFoundError


def netappfiles_exception_handler(ex):
    if isinstance(ex, (ClientAuthenticationError, HttpResponseError, ResourceExistsError, ResourceNotFoundError,
                       ValidationError, ValueError)):
        message = ex
        raise CLIError(message)

    import sys

    from six import reraise
    reraise(*sys.exc_info())
