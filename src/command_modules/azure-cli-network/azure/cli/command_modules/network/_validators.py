from azure.cli.commands.azure_resource_id import AzureResourceId
from azure.cli._util import CLIError

def _convert_id_list_to_object(data):
    if not data:
        return None

    if not isinstance(data, list):
        data = [data]
    data_list = []
    for val in data:
        # currently only supports accepting ids, not names
        try:
            data_list.append({'id': str(AzureResourceId(val))})
        except ValueError:
            raise CLIError('Please supply a space-separated list of well-formed IDs.')
    return data_list

def process_nic_namespace(namespace):
    if namespace.public_ip_address_name:
        namespace.public_ip_address_type = 'existing'

    if namespace.network_security_group_name:
        namespace.network_security_group_type = 'existing'

    if namespace.private_ip_address:
        namespace.private_ip_address_allocation = 'static'

    namespace.load_balancer_backend_address_pool_ids = _convert_id_list_to_object(
        namespace.load_balancer_backend_address_pool_ids)

    namespace.load_balancer_inbound_nat_rule_ids = _convert_id_list_to_object(
        namespace.load_balancer_inbound_nat_rule_ids)
