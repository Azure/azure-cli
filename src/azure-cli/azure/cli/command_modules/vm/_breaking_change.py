# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.breaking_change import register_default_value_breaking_change

register_default_value_breaking_change('vm create', '--size', 'Standard_DS1_v2', 'Standard_D2s_v5', target_version=None)
register_default_value_breaking_change('vmss create', '--vm-sku', 'Standard_DS1_v2', 'Standard_D2s_v5', target_version=None)
