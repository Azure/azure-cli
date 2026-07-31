# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.breaking_change import register_default_value_breaking_change

register_default_value_breaking_change(command_name='sig image-version create',
                                       arg='--end-of-life-date',
                                       current_default=None,
                                       new_default='6 months from publish date',
                                       target_version=None)

register_default_value_breaking_change(command_name='sig image-version create',
                                       arg='--block-deletion-before-end-of-life',
                                       current_default=None,
                                       new_default=True,
                                       target_version=None)

register_default_value_breaking_change(command_name='sig image-version update',
                                       arg='--end-of-life-date',
                                       current_default=None,
                                       new_default='6 months from publish date',
                                       target_version=None)

register_default_value_breaking_change(command_name='sig image-version update',
                                       arg='--block-deletion-before-end-of-life',
                                       current_default=None,
                                       new_default=True,
                                       target_version=None)
