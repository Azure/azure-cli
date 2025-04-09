# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------

from azure.cli.core.breaking_change import register_default_value_breaking_change

register_default_value_breaking_change(
    'aks create',
    '--node-vm-size',
    'Standard_DS2_V2 (Linux), Standard_DS2_V3 (Windows)',
    'Dynamically Selected By Azure'
)
