from azure.cli.core.aaz import *


@register_command_group("network vnet subnet", is_experimental=True, expiration='3.0.0', redirect='network vnet')
class __CMDGroup(AAZCommandGroup):
    """Manage subnets in an Azure Virtual Network.

    To learn more about subnets visit https://docs.microsoft.com/azure/virtual-network/virtual-network-manage-subnet
    """
    pass


__all__ = ["__CMDGroup"]
