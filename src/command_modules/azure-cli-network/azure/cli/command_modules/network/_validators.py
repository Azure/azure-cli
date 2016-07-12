import argparse

from azure.cli.commands.arm import is_valid_resource_id, resource_id

def _convert_id_list_to_object(data):
    if not data:
        return None

    if not isinstance(data, list):
        data = [data]
    data_list = []
    for val in data:
        data_list.append({'id': val})
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

def process_network_lb_create_namespace(namespace):

    if namespace.public_ip_dns_name:
        namespace.dns_name_type = 'new'

    if namespace.private_ip_address:
        namespace.private_ip_address_allocation = 'static'

    if namespace.subnet and namespace.public_ip_address:
        raise argparse.ArgumentError(
            None, 'Must specify a subnet OR a public IP address, not both.')

def validate_public_ip_type(namespace): # pylint: disable=unused-argument
    if namespace.subnet:
        namespace.public_ip_address_type = 'none'

def process_public_ip_create_namespace(namespace):
    if namespace.dns_name:
        namespace.public_ip_address_type = 'dns'

def validate_nsg_name_or_id(namespace):
    """ Validates a NSG ID or, if a name is provided, formats it as an ID. """
    if namespace.network_security_group:
        from azure.cli.commands.client_factory import get_subscription_id
        # determine if network_security_group is name or ID
        is_id = is_valid_resource_id(namespace.network_security_group)
        if not is_id:
            namespace.network_security_group = resource_id(
                subscription=get_subscription_id(),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Network',
                type='networkSecurityGroups',
                name=namespace.network_security_group)


