# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from azure.cli.core.util import CLIError
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)

def duplicate_resource_exception_handler(ex):
    # pylint:disable=line-too-long
    # wraps DocumentDB 409 error in CLIError
    from pydocumentdb.errors import HTTPFailure
    if isinstance(ex, HTTPFailure) and ex.status_code == 409:
        raise CLIError('Operation Failed: Resource Already Exists (Server returned status code 409)')
    raise ex

def resource_not_found_exception_handler(ex):
    # pylint:disable=line-too-long
    # wraps DocumentDB 404 error in CLIError
    from pydocumentdb.errors import HTTPFailure
    if isinstance(ex, HTTPFailure) and ex.status_code == 404:
        raise CLIError('Operation Failed: Resource Not Found (Server returned status code 404)')
    raise ex

def invalid_arg_found_exception_handler(ex):
    # wraps DocumentDB 400 error in CLIError
    from pydocumentdb.errors import HTTPFailure
    if isinstance(ex, HTTPFailure) and ex.status_code == 400:
        cli_error = None
        try:
            # pylint:disable=protected-access
            if ex._http_error_message:
                msg = json.loads(ex._http_error_message)
                if msg['message']:
                    msg = msg['message'].split('\n')[0]
                    msg = msg[len('Message: '):] if msg.find('Message: ') == 0 else msg
                    # pylint:disable=line-too-long
                    cli_error = CLIError('Operation Failed: Invalid Arg (Server returned status code 400 {})'.format(str(msg)))
        # pylint:disable=broad-except
        except Exception:
            pass
        if cli_error:
            # pylint:disable=raising-bad-type
            raise cli_error
        # pylint:disable=line-too-long
        raise CLIError('Operation Failed: Invalid Arg (Server returned status code 400\n {})'.format(str(ex)))
    raise ex

def exception_handler_chain_builder(handlers):
    # creates a handler which chains the handler
    # as soon as one of the chained handlers raises CLIError, it raises CLIError
    # if no handler raises CLIError it raises the original exception
    # pylint:disable=broad-except
    def chained_handler(ex):
        if isinstance(ex, CLIError):
            raise ex
        for h in handlers:
            try:
                h(ex)
            except CLIError as cli_error:
                raise cli_error
            except Exception:
                pass
        raise ex
    return chained_handler

def network_exception_handler(ex):
    import requests as requests
    # wraps a connection exception in CLIError
    # pylint:disable=line-too-long
    if isinstance(ex, requests.exceptions.ConnectionError) or isinstance(ex, requests.exceptions.HTTPError):
        raise CLIError('Please ensure you have network connection. Error detail: ' + str(ex))
    raise ex

def generic_exception_handler(ex):
    # pylint:disable=line-too-long
    logger.debug(ex)
    chained_handler = exception_handler_chain_builder([duplicate_resource_exception_handler, resource_not_found_exception_handler, invalid_arg_found_exception_handler, network_exception_handler])
    chained_handler(ex)
