#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse
import json
import math
import os
import re
import time

from azure.cli._util import CLIError
from azure.cli.application import APPLICATION
from azure.cli.commands.parameters import get_one_of_subscription_locations
from azure.cli.commands.arm import resource_id, resource_exists

from six.moves.urllib.request import urlopen #pylint: disable=import-error

from ._factory import _compute_client_factory
from ._vm_utils import read_content_if_is_file

class VMImageFieldAction(argparse.Action): #pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        image = values
        match = re.match('([^:]*):([^:]*):([^:]*):([^:]*)', image)

        if image.lower().endswith('.vhd'):
            namespace.os_disk_type = 'custom'
            namespace.custom_os_disk_uri = image
        elif match:
            namespace.os_type = 'Custom'
            namespace.os_publisher = match.group(1)
            namespace.os_offer = match.group(2)
            namespace.os_sku = match.group(3)
            namespace.os_version = match.group(4)
        else:
            images = load_images_from_aliases_doc()
            matched = next((x for x in images if x['urn alias'].lower() == image.lower()), None)
            if matched is None:
                raise CLIError('Invalid image "{}". Please pick one from {}' \
                    .format(image, [x['urn alias'] for x in images]))
            namespace.os_type = 'Custom'
            namespace.os_publisher = matched['publisher']
            namespace.os_offer = matched['offer']
            namespace.os_sku = matched['sku']
            namespace.os_version = matched['version']


class VMSSHFieldAction(argparse.Action): #pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        namespace.ssh_key_value = read_content_if_is_file(values)

class VMDNSNameAction(argparse.Action): #pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        dns_value = values

        if dns_value:
            namespace.dns_name_type = 'new'

        namespace.dns_name_for_public_ip = dns_value

class PrivateIpAction(argparse.Action): #pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        private_ip = values
        namespace.private_ip_address = private_ip

        if private_ip:
            namespace.private_ip_address_allocation = 'static'

def _handle_vm_nics(namespace):
    from azure.cli.commands.client_factory import get_subscription_id
    nics_value = namespace.network_interface_ids
    nics = []

    if not nics_value:
        namespace.network_interface_type = 'new'
        return

    namespace.network_interface_type = 'existing'

    if not isinstance(nics_value, list):
        nics_value = [nics_value]

    for n in nics_value:
        nics.append({
            'id': n if '/' in n else resource_id(name=n,
                                                 resource_group=namespace.resource_group_name,
                                                 namespace='Microsoft.Network',
                                                 type='networkInterfaces',
                                                 subscription=get_subscription_id()),
            'properties': {
                'primary': nics_value[0] == n
            }
        })

    namespace.network_interface_ids = nics
    namespace.network_interface_type = 'existing'

    namespace.public_ip_address_type = 'none'

def _resource_not_exists(resource_type):
    def _handle_resource_not_exists(namespace):
        # TODO: hook up namespace._subscription_id once we support it
        ns, t = resource_type.split('/')
        if resource_exists(namespace.resource_group_name, namespace.name, ns, t):
            raise CLIError('Resource {} of type {} in group {} already exists.'.format(
                namespace.name,
                resource_type,
                namespace.resource_group_name))
    return _handle_resource_not_exists

def _find_default_vnet(namespace):
    if not namespace.virtual_network and not namespace.virtual_network_type:
        from azure.mgmt.network import NetworkManagementClient
        from azure.cli.commands.client_factory import get_mgmt_service_client

        client = get_mgmt_service_client(NetworkManagementClient).virtual_networks

        vnet = next((v for v in
                     client.list(namespace.resource_group_name)),
                    None)
        if vnet:
            try:
                namespace.subnet_name = vnet.subnets[0].name
                namespace.virtual_network = vnet.name
                namespace.virtual_network_type = 'existingName'
            except KeyError:
                pass

def _find_default_storage_account(namespace):
    if not namespace.storage_account and not namespace.storage_account_type:
        from azure.mgmt.storage import StorageManagementClient
        from azure.cli.commands.client_factory import get_mgmt_service_client

        client = get_mgmt_service_client(StorageManagementClient).storage_accounts

        sku_tier = 'Premium' if 'Premium' in namespace.storage_type else 'Standard'
        account = next((a for a in client.list_by_resource_group(namespace.resource_group_name)
                        if a.sku.tier.value == sku_tier), None)

        if account:
            namespace.storage_account = account.name
            namespace.storage_account_type = 'existingName'

def _os_disk_default(namespace):
    if not namespace.os_disk_name:
        namespace.os_disk_name = 'osdisk{}'.format(str(int(math.ceil(time.time()))))

def _handle_auth_types(**kwargs):
    if kwargs['command'] != 'vm create' and kwargs['command'] != 'vmss create':
        return

    args = kwargs['args']

    is_windows = 'Windows' in args.os_offer \
        and getattr(args, 'custom_os_disk_type', None) != 'linux'

    if not args.authentication_type:
        args.authentication_type = 'password' if is_windows else 'ssh'

    if args.authentication_type == 'password':
        if args.ssh_dest_key_path:
            raise CLIError('SSH parameters cannot be used with password authentication type')
        elif not args.admin_password:
            raise CLIError('Admin password is required with password authentication type')
    elif args.authentication_type == 'ssh':
        if args.admin_password:
            raise CLIError('Admin password cannot be used with SSH authentication type')

        ssh_key_file = os.path.join(os.path.expanduser('~'), '.ssh/id_rsa.pub')
        if not args.ssh_key_value:
            if os.path.isfile(ssh_key_file):
                with open(ssh_key_file) as f:
                    args.ssh_key_value = f.read()
            else:
                raise CLIError('An RSA key file or key value must be supplied to SSH Key Value')

    if hasattr(args, 'network_security_group_type'):
        args.network_security_group_rule = 'RDP' if is_windows else 'SSH'

    if hasattr(args, 'nat_backend_port') and not args.nat_backend_port:
        args.nat_backend_port = '3389' if is_windows else '22'

APPLICATION.register(APPLICATION.COMMAND_PARSER_PARSED, _handle_auth_types)

def load_images_from_aliases_doc(publisher=None, offer=None, sku=None):
    target_url = ('https://raw.githubusercontent.com/Azure/azure-rest-api-specs/'
                  'master/arm-compute/quickstart-templates/aliases.json')
    txt = urlopen(target_url).read()
    dic = json.loads(txt.decode())
    try:
        all_images = []
        result = (dic['outputs']['aliases']['value'])
        for v in result.values(): #loop around os
            for alias, vv in v.items(): #loop around distros
                all_images.append({
                    'urn alias': alias,
                    'publisher': vv['publisher'],
                    'offer': vv['offer'],
                    'sku': vv['sku'],
                    'version': vv['version']
                    })

        all_images = [i for i in all_images if (_partial_matched(publisher, i['publisher']) and
                                                _partial_matched(offer, i['offer']) and
                                                _partial_matched(sku, i['sku']))]
        return all_images
    except KeyError:
        raise CLIError('Could not retrieve image list from {}'.format(target_url))

def load_images_thru_services(publisher, offer, sku, location):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    all_images = []
    client = _compute_client_factory()
    if location is None:
        location = get_one_of_subscription_locations()

    def _load_images_from_publisher(publisher):
        offers = client.virtual_machine_images.list_offers(location, publisher)
        if offer:
            offers = [o for o in offers if _partial_matched(offer, o.name)]
        for o in offers:
            skus = client.virtual_machine_images.list_skus(location, publisher, o.name)
            if sku:
                skus = [s for s in skus if _partial_matched(sku, s.name)]
            for s in skus:
                images = client.virtual_machine_images.list(location, publisher, o.name, s.name)
                for i in images:
                    all_images.append({
                        'publisher': publisher,
                        'offer': o.name,
                        'sku': s.name,
                        'version': i.name})

    publishers = client.virtual_machine_images.list_publishers(location)
    if publisher:
        publishers = [p for p in publishers if _partial_matched(publisher, p.name)]

    publisher_num = len(publishers)
    if publisher_num > 1:
        with ThreadPoolExecutor(max_workers=40) as executor:
            tasks = [executor.submit(_load_images_from_publisher, p.name) for p in publishers]
            for t in as_completed(tasks):
                t.result() # don't use the result but expose exceptions from the threads
    elif publisher_num == 1:
        _load_images_from_publisher(publishers[0].name)

    return all_images

def load_extension_images_thru_services(publisher, name, version, location, show_latest=False):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    ##pylint: disable=no-name-in-module,import-error
    from distutils.version import LooseVersion
    all_images = []
    client = _compute_client_factory()
    if location is None:
        location = get_one_of_subscription_locations()

    def _load_extension_images_from_publisher(publisher):
        types = client.virtual_machine_extension_images.list_types(location, publisher)
        if name:
            types = [t for t in types if _partial_matched(name, t.name)]
        for t in types:
            versions = client.virtual_machine_extension_images.list_versions(location,
                                                                             publisher,
                                                                             t.name)
            if version:
                versions = [v for v in versions if _partial_matched(version, v.name)]

            if show_latest:
                #pylint: disable=no-member
                versions.sort(key=lambda v: LooseVersion(v.name), reverse=True)
                all_images.append({
                    'publisher': publisher,
                    'name': t.name,
                    'version': versions[0].name})
            else:
                for v in versions:
                    all_images.append({
                        'publisher': publisher,
                        'name': t.name,
                        'version': v.name})

    publishers = client.virtual_machine_images.list_publishers(location)
    if publisher:
        publishers = [p for p in publishers if _partial_matched(publisher, p.name)]

    publisher_num = len(publishers)
    if publisher_num > 1:
        with ThreadPoolExecutor(max_workers=40) as executor:
            tasks = [executor.submit(_load_extension_images_from_publisher,
                                     p.name) for p in publishers]
            for t in as_completed(tasks):
                t.result() # don't use the result but expose exceptions from the threads
    elif publisher_num == 1:
        _load_extension_images_from_publisher(publishers[0].name)

    return all_images

def get_vm_sizes(location):
    return list(_compute_client_factory().virtual_machine_sizes.list(location))

def _partial_matched(pattern, string):
    if not pattern:
        return True # empty pattern means wildcard-match
    pattern = r'.*' + pattern
    return re.match(pattern, string, re.I)

def _create_image_instance(publisher, offer, sku, version):
    return {
        'publisher': publisher,
        'offer': offer,
        'sku': sku,
        'version': version
    }

def _handle_container_ssh_file(**kwargs):
    if kwargs['command'] != 'vm container create':
        return

    args = kwargs['args']

    args.ssh_key_value = read_content_if_is_file(args.ssh_key_value)

APPLICATION.register(APPLICATION.COMMAND_PARSER_PARSED, _handle_container_ssh_file)

