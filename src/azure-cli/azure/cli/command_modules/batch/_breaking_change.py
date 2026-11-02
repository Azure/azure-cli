# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_command_deprecate

USAGE_METRICS_REMOVAL = 'May 2027'

register_command_deprecate(
    'batch pool usage-metrics list',
    target_version=USAGE_METRICS_REMOVAL,
    message=f"This command has been deprecated and will be removed in {USAGE_METRICS_REMOVAL}. The Azure Batch "
            "service retired the pool usage metrics API on September 30, 2024, so this command always returns an "
            "error. For more information, see https://github.com/Azure/Batch/issues/140."
)
