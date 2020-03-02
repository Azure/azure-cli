# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

def private_endpoint_exception_handler(ex):

    if ex.status_code == 400:
        message = ''
        code = ex.code
        raise CLIError('{} {}'.format(message, code))
    raise ex