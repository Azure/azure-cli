# pylint: disable=no-self-use,too-many-arguments
from azure.mgmt.network.models import Subnet
from ._factory import _network_client_factory

def create_update_subnet(resource_group_name, subnet_name, virtual_network_name, address_prefix):
    '''Create or update a virtual network (VNet) subnet'''
    subnet_settings = Subnet(name=subnet_name, address_prefix=address_prefix)
    ncf = _network_client_factory()
    return ncf.subnets.create_or_update(
        resource_group_name, virtual_network_name, subnet_name, subnet_settings)
