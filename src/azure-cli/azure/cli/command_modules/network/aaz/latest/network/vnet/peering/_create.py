# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/virtualNetworkPeerings/{}
from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet peering create")
class Create(AAZCommand):
    """ Create a virtual network peering connection.

    To successfully peer two virtual networks this command must be called twice with
    the values for --vnet-name and --remote-vnet reversed.
    """
    pass
