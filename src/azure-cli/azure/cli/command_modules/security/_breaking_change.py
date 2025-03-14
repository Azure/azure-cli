# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_command_deprecate

register_command_deprecate('security automation create_or_update')
register_command_deprecate('security automation validate')

# This command has been deprecated and will be removed in next breaking change release(2.73.0).
