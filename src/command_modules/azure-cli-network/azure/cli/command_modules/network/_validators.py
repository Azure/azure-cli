import argparse
import base64
import socket

from azure.cli.commands.arm import is_valid_resource_id, resource_id
from azure.cli._util import CLIError

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

def process_app_gateway_namespace(namespace):

    if namespace.public_ip:
        namespace.frontend_type = "publicIp"

    elif namespace.private_ip_address:
        namespace.private_ip_address_allocation = "static"
        namespace.frontend_type = "privateIp"

    if not namespace.public_ip_type:
        namespace.public_ip_type = "none"

def validate_address_prefixes(namespace):

    subnet_prefix_set = '__SET__' in namespace.subnet_prefix
    vnet_prefix_set = '__SET__' in namespace.vnet_address_prefix
    namespace.subnet_prefix = namespace.subnet_prefix.replace('__SET__', '')
    namespace.vnet_address_prefix = namespace.vnet_address_prefix.replace('__SET__', '')

    if namespace.subnet_type != 'new' and (subnet_prefix_set or vnet_prefix_set):
        raise CLIError('Existing subnet ({}) found. Cannot specify address prefixes when '
                       'reusing an existing subnet.'.format(namespace.subnet))

def validate_servers(namespace):
    servers = []
    for item in namespace.servers if namespace.servers else []:
        try:
            socket.inet_aton(item)
            servers.append({'IpAddress': item})
        except socket.error:
            servers.append({'Fqdn': item})
    namespace.servers = servers

def validate_cert(namespace):

    default_frontend_port = namespace.frontend_port is None

    # default to frontend port 80 for http
    if default_frontend_port:
        namespace.frontend_port = 80

    params = [namespace.cert_data, namespace.cert_password]
    if all([not x for x in params]):
        return

    # if any param specified but not both
    if not all(params):
        raise argparse.ArgumentError(
            None, 'To use SSL certificate, you must specify both the filename and password')

    # extract the certificate data from the provided file
    with open(namespace.cert_data, 'rb') as f:
        contents = f.read()
        base64_data = base64.b64encode(contents)
        try:
            namespace.cert_data = base64_data.decode('utf-8')
        except UnicodeDecodeError:
            namespace.cert_data = str(base64_data)

    # change default to frontend port 443 for https
    namespace.http_listener_protocol = 'https'
    if not namespace.frontend_port:
        namespace.frontend_port = 443 if namespace.http_listener_protocol == 'https' else 80

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

class markSpecifiedAction(argparse.Action): # pylint: disable=too-few-public-methods
    """ Use this to identify when a parameter is explicitly set by the user (as opposed to a
    default). You must remove the __SET__ sentinel substring in a follow-up validator."""
    def __call__(self, parser, args, values, option_string=None):
        setattr(args, self.dest, '__SET__{}'.format(values))
