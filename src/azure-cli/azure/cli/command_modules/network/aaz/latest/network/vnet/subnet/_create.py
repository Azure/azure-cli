# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}

from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet subnet create")
class Create(AAZCommand):
    pass
