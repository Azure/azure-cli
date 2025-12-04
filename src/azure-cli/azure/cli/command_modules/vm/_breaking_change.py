# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.breaking_change import register_default_value_breaking_change, register_other_breaking_change

register_default_value_breaking_change(
    command_name="vm create",
    arg="--size",
    current_default="Standard_DS1_v2",
    new_default="Standard_D2s_v5",
    target_version=None,
)

register_default_value_breaking_change(
    command_name="vmss create",
    arg="--vm-sku",
    current_default="Standard_DS1_v2",
    new_default="Standard_D2s_v5",
    target_version=None,
)

register_other_breaking_change(
    "sig image-version create",
    "Starting api-version 2026-03-03, gallery image versions will default to:\n"
    "  - endOfLifeDate = 6 months from publish date (unless explicitly set)\n"
    "  - blockDeletionBeforeEndOfLife = true (unless explicitly set)\n"
    "By default, image deletion is blocked for 6 months. "
    "To override, set a custom endOfLifeDate or set blockDeletionBeforeEndOfLife = false",
)

register_other_breaking_change(
    "sig image-version update",
    "Starting api-version 2026-03-03, gallery image versions will default to:\n"
    "  - endOfLifeDate = 6 months from publish date (unless explicitly set)\n"
    "  - blockDeletionBeforeEndOfLife = true (unless explicitly set)\n"
    "By default, image deletion is blocked for 6 months. "
    "To override, set a custom endOfLifeDate or set blockDeletionBeforeEndOfLife = false",
)
