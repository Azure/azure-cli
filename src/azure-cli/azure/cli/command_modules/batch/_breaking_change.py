# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import (AzCLIOtherChange, register_command_deprecate,
                                            register_conditional_breaking_change)

# The target version of every pre-announcement in this file: the CLI's breaking change release in June 2027.
# The messages are custom, so they include it too, as TARGET_TEXT.
TARGET_VERSION = '2.100.0'
TARGET_TEXT = f'{TARGET_VERSION} (June 2027)'

register_command_deprecate(
    'batch pool usage-metrics list',
    target_version=TARGET_VERSION,
    message=f"This command has been deprecated and will be removed in {TARGET_TEXT}. The Azure Batch "
            "service retired the pool usage metrics API on September 30, 2024, so this command always returns an "
            "error. For more information, see https://github.com/Azure/Batch/issues/140."
)

# Printed by validate_retained_data_option only when the value 'retaineddata' is used
RETAINED_DATA_TAG = 'retaineddata'


def _register_retained_data_removal(command, option):
    register_conditional_breaking_change(RETAINED_DATA_TAG, AzCLIOtherChange(
        command,
        f"The value 'retaineddata' of '{option}' has been deprecated and will be removed in {TARGET_TEXT}, "
        "because Azure Batch API version 2026-10-01 removes it. Upload task data to Azure Storage in your task "
        "and use 'taskcompletion' instead.",
        arg=option,
        target_version=TARGET_VERSION))


_register_retained_data_removal('batch pool resize', '--node-deallocation-option')
_register_retained_data_removal('batch node delete', '--node-deallocation-option')
_register_retained_data_removal('batch node reboot', '--node-reboot-option')
