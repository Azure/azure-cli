# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.network.aaz.latest.network.lb.address_pool.basic._delete import Delete as _LBAddressPoolBasicDelete


@register_command("network lb address-pool delete")
class LBAddressPoolDelete(_LBAddressPoolBasicDelete):
    """Delete the specified load balancer backend address pool.

    :example: Delete an address pool.
        az network lb address-pool delete -g MyResourceGroup --lb-name MyLb -n MyAddressPool
    """
