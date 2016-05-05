# pylint: disable=no-self-use,too-many-arguments
from azure.mgmt.network.models import Subnet

from azure.cli.commands import LongRunningOperation
from azure.cli.command_modules.network._params import _network_client_factory

class ConvenienceNetworkCommands(object): # pylint: disable=too-few-public-methods

    def __init__(self, **_):
        pass

    def create_update_subnet(self, resource_group_name, subnet_name, vnet_name, address_prefix):
        '''Create or update a virtual network (VNet) subnet'''
        subnet_settings = Subnet(name=subnet_name, address_prefix=address_prefix)
        op = LongRunningOperation('Creating subnet', 'Subnet created')
        ncf = _network_client_factory()
        poller = ncf.subnets.create_or_update(
            resource_group_name, vnet_name, subnet_name, subnet_settings)
        return op(poller)
