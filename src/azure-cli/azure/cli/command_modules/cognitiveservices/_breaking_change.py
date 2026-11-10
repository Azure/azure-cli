# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_command_group_deprecate


register_command_group_deprecate(
    "cognitiveservices agent",
    target_version="the first release after February 28, 2027",
    hide=False,
)
