from azure.cli.core.aaz import *


@register_command_group("network vnet peering", is_preview=True)
class __CMDGroup(AAZCommandGroup):
    """ Manage peering connections between Azure Virtual Networks.

    To learn more about virtual network peering visit https://docs.microsoft.com/azure/virtual-network/virtual-network-manage-peering
    """
    pass


__all__ = ["__CMDGroup"]
