# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: skip-file
# flake8: noqa

from azure.cli.core.aaz import *


@register_command_group(
    "network cross-region-lb address-pool address",
)
class __CMDGroup(AAZCommandGroup):
    """Manage backend addresses of the cross-region load balance backend address pool.
    """
    pass


__all__ = ["__CMDGroup"]
