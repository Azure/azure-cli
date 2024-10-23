# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_default_value_breaking_change

register_default_value_breaking_change('extension add', '--allow-preview',
                                       'true', 'false')
register_default_value_breaking_change('extension update', '--allow-preview',
                                       'true', 'false')
# The default value of '--allow-preview' will be changed to 'false' from 'true' in next breaking change release(2.67.0).
