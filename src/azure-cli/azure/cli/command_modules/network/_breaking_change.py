# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.breaking_change import register_command_group_deprecate


register_command_group_deprecate(
    "network public-ip ddos-protection-statu",
    redirect="az network public-ip ddos-protection",
)
# Warning Message: This command group has been deprecated and will be removed in next breaking change release (2.67.0).
# Use `az network public-ip ddos-protection` instead.
