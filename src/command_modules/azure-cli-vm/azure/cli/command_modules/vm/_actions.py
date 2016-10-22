#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse
import json
import os
import re

from azure.cli.core._util import CLIError
from azure.cli.core.application import APPLICATION
from azure.cli.core.commands.parameters import get_one_of_subscription_locations
from azure.cli.core.commands.arm import resource_exists
import azure.cli.core._logging as _logging

from six.moves.urllib.request import urlopen #pylint: disable=import-error

from ._factory import _compute_client_factory
from ._vm_utils import read_content_if_is_file

logger = _logging.get_az_logger(__name__)

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
            matched = next((x for x in images if x['urnAlias'].lower() == image.lower()), None)
            if matched is None:
                raise CLIError('Invalid image "{}". Please pick one from {}' \
                    .format(image, [x['urnAlias'] for x in images]))
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
            import getpass
            args.admin_password = getpass.getpass('Admin Password: ')
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
                    'urnAlias': alias,
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
    if kwargs['command'] != 'acs create':
        return

    args = kwargs['args']
    string_or_file = args.ssh_key_value
    content = string_or_file
    if os.path.exists(string_or_file):
        logger.info('Use existing SSH public key file: %s', string_or_file)
        with open(string_or_file, 'r') as f:
            content = f.read()
    elif not _is_valid_ssh_rsa_public_key(content) and args.generate_ssh_keys:
        #figure out appropriate file names:
        #'base_name'(with private keys), and 'base_name.pub'(with public keys)
        public_key_filepath = string_or_file
        if public_key_filepath[-4:].lower() == '.pub':
            private_key_filepath = public_key_filepath[:-4]
        else:
            private_key_filepath = public_key_filepath + '.private'
        logger.warning('Creating SSH key files: %s,%s', private_key_filepath, public_key_filepath)
        content = _generate_ssh_keys(private_key_filepath, public_key_filepath)
    args.ssh_key_value = content

def _generate_ssh_keys(private_key_filepath, public_key_filepath):
    import paramiko

    ssh_dir, _ = os.path.split(private_key_filepath)
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir)
        os.chmod(ssh_dir, 0o700)

    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(private_key_filepath)
    os.chmod(private_key_filepath, 0o600)

    with open(public_key_filepath, 'w') as public_key_file:
        public_key = '%s %s'  % (key.get_name(), key.get_base64())
        public_key_file.write(public_key)
    os.chmod(public_key_filepath, 0o644)

    return public_key

def _is_valid_ssh_rsa_public_key(openssh_pubkey):
    #http://stackoverflow.com/questions/2494450/ssh-rsa-public-key-validation-using-a-regular-expression #pylint: disable=line-too-long
    #A "good enough" check is to see if the key starts with the correct header.
    import struct
    try:
        from base64 import decodebytes as base64_decode
    except ImportError:
        #deprecated and redirected to decodebytes in Python 3
        from base64 import decodestring as base64_decode
    parts = openssh_pubkey.split()
    if len(parts) < 2:
        return False
    key_type = parts[0]
    key_string = parts[1]

    data = base64_decode(key_string.encode())#pylint:disable=deprecated-method
    int_len = 4
    str_len = struct.unpack('>I', data[:int_len])[0] # this should return 7
    return data[int_len:int_len+str_len] == key_type.encode()

APPLICATION.register(APPLICATION.COMMAND_PARSER_PARSED, _handle_container_ssh_file)
