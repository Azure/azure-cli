# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}

from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet create")
class Create(AAZCommand):
    pass
