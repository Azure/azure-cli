from azure.cli.core.aaz._command import AAZCommandGroup, register_command_group


@register_command_group("network vnet")
class __CMDGroup(AAZCommandGroup):
    """ Manage Azure Virtual Networks.

    To learn more about Virtual Networks visit https://docs.microsoft.com/azure/virtual-network/virtual-network-manage-network
    """
    pass


__all__ = [__CMDGroup]
