# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_default_value_breaking_change

register_default_value_breaking_change(
    'containerapp env create',
    '--logs-destination',
    'log-analytics',
    'azure-monitor',
    target_version=None,
    doc_link='https://github.com/Azure/azure-cli/pull/34228',
)
