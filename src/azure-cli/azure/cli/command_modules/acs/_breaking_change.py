# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_logic_breaking_change

# Breaking change: change default SSH key handling in `az aks create`
register_logic_breaking_change(
    'aks create',
    summary="Default SSH key behavior will change. When no SSH key parameters are provided, "
            "the command will behave as if '--no-ssh-key' was passed instead of failing"
)
