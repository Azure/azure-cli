# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_argument_deprecate, register_output_breaking_change

# Arguments
register_argument_deprecate(
    "az batch pool create",
    argument="--target-communication"
)

# fixed with action=None but check with CLI team
register_argument_deprecate(
    "az batch pool create",
    argument="--resource-tags"
)

register_argument_deprecate(
    "az batch pool reset",
    argument="--target-communication"
)
register_argument_deprecate(
    "az batch pool set",
    argument="--target-communication"
)

# Outputs
register_output_breaking_change(
    "batch pool show",
    description="Remove output fields `targetNodeCommunicationMode`, `currentNodeCommunicationMode`, and `resourceTags`"
)

register_output_breaking_change(
    "batch pool list",
    description="Remove output fields `targetNodeCommunicationMode`, `currentNodeCommunicationMode`, and `resourceTags`"
)
