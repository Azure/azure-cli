from azure.cli.core.aaz._command import AAZCommandGroup, register_command_group


@register_command_group("network vnet peering")
class __CMDGroup(AAZCommandGroup):
    """ Manage peering connections between Azure Virtual Networks.

    To learn more about virtual network peering visit https://docs.microsoft.com/azure/virtual-network/virtual-network-manage-peering
    """
    pass
