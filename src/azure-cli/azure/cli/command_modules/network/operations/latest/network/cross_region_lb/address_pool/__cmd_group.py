# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: skip-file
# flake8: noqa

from azure.cli.core.aaz import *


@register_command_group(
    "network cross-region-lb address-pool",
)
class __CMDGroup(AAZCommandGroup):
    """Manage address pools of a cross-region load balancer.
    """
    pass


__all__ = ["__CMDGroup"]
