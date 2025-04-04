# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------

from azure.cli.core.breaking_change import (
    AzCLIOtherChange,
    register_default_value_breaking_change,
    register_conditional_breaking_change,
)

register_default_value_breaking_change(
    'aks create',
    '--node-vm-size',
    'Standard_DS2_V2 (Linux), Standard_DS2_V3 (Windows)',
    'Dynamically Selected By Azure'
)

register_conditional_breaking_change(
    tag="aks_create_cluster_autoscaler_profile",
    breaking_change=AzCLIOtherChange(
        cmd="aks create",
        message="The option `--cluster-autoscaler-profile` in command `az aks create` will be changed to "
        "allow multiple values for the same key, separated by commas. Different key-value pairs will be separated by "
        "spaces.",
    ),
)

register_conditional_breaking_change(
    tag="aks_update_cluster_autoscaler_profile",
    breaking_change=AzCLIOtherChange(
        cmd="aks update",
        message="The option `--cluster-autoscaler-profile` in command `az aks update` will be changed to "
        "allow multiple values for the same key, separated by commas. Different key-value pairs will be separated by "
        "spaces.",
    ),
)
