# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.aaz import AAZCommandGroup, register_command_group


@register_command_group(
    "monitor activity-log alert action-group",
)
class __CMDGroup(AAZCommandGroup):  # pylint: disable=too-few-public-methods
    """Manage action groups for activity log alert rules.
    """


__all__ = ["__CMDGroup"]
