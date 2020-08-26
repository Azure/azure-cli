# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)


def get_notary_command(is_diagnostics_context=False):
    from ._errors import NOTARY_COMMAND_ERROR
    from subprocess import PIPE, Popen
    from platform import system

    if system() == "Windows":
        notary_command = "notary.exe"
    else:
        notary_command = "notary"

    try:
        p = Popen([notary_command, "--help"], stdout=PIPE, stderr=PIPE)
        _, stderr = p.communicate()
    except OSError as e:
        logger.debug("Could not run '%s' command. Exception: %s", notary_command, str(e))
        if is_diagnostics_context:
            return None, NOTARY_COMMAND_ERROR
        raise CLIError(NOTARY_COMMAND_ERROR.get_error_message())

    if stderr:
        if is_diagnostics_context:
            return None, NOTARY_COMMAND_ERROR.append_error_message(stderr.decode())
        raise CLIError(NOTARY_COMMAND_ERROR.append_error_message(stderr.decode()).get_error_message())

    return notary_command, None
