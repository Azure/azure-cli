# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/virtualNetworkPeerings/{}
from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet peering delete")
class Delete(AAZCommand):
    pass
