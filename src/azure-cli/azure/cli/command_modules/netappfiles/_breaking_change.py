# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.breaking_change import (
    register_command_group_deprecate,
)
register_command_group_deprecate('netappfiles subvolume', message='netappfiles subvolume command group is being deprecated '\
                                 'and will be removed in a future release.')
