# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/virtualNetworkPeerings/{}
from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet peering show")
class Show(AAZCommand):
    """ Show details of a peering.
    """
    pass
