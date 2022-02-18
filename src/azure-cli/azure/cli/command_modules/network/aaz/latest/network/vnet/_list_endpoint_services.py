
# Resources:
#   - /subscriptions/{}/providers/Microsoft.Network/locations/{}/virtualNetworkAvailableEndpointServices


from azure.cli.core.aaz import *


@register_command("network vnet list-endpoint-services")
class ListEndpointServices(AAZCommand):
    """ List which services support VNET service tunneling in a given region.

    To learn more about service endpoints visit https://docs.microsoft.com/azure/virtual-network/virtual-network-service-endpoints-configure#azure-cli

    :example: List the endpoint services available for use in the West US region.
        az network vnet list-endpoint-services -l westus -o table

    """
    pass


__all__ = ["ListEndpointServices"]
