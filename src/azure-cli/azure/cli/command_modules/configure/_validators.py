# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def validate_local_context(cmd, namespace):  # pylint: disable=unused-argument
    if not cmd.cli_ctx.local_context.is_on:
        raise CLIError('Local context is off, this command can only be run when local context is on.')
    if not cmd.cli_ctx.local_context.current_dir:
        raise CLIError('The working directory has been deleted or recreated. You can change to another working '
                       'directory or reenter current one if it is recreated.')

