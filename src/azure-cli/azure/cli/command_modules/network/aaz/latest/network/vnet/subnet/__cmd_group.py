from azure.cli.core.aaz._command import AAZCommandGroup, register_command_group


@register_command_group("network vnet subnet", is_experimental=True)
class __CMDGroup(AAZCommandGroup):
    """Manage subnets in an Azure Virtual Network.

    To learn more about subnets visit https://docs.microsoft.com/azure/virtual-network/virtual-network-manage-subnet
    """
    pass
