import argparse
import json
import os
import re

from azure.cli._util import CLIError
from azure.cli.application import APPLICATION

from six.moves.urllib.request import urlopen #pylint: disable=import-error

from ._factory import _compute_client_factory, _subscription_client_factory

class VMImageFieldAction(argparse.Action): #pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        image = values
        match = re.match('([^:]*):([^:]*):([^:]*):([^:]*)', image)

        if image.lower().endswith('.vhd'):
            namespace.os_disk_uri = image
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
        ssh_value = values

        if os.path.exists(ssh_value):
            with open(ssh_value, 'r') as f:
                namespace.ssh_key_value = f.read()
        else:
            namespace.ssh_key_value = ssh_value

class VMDNSNameAction(argparse.Action): #pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        dns_value = values

        if dns_value:
            namespace.dns_name_type = 'new'

        namespace.dns_name_for_public_ip = dns_value

def _handle_auth_types(**kwargs):
    if kwargs['command'] != 'vm create':
        return

    args = kwargs['args']

    if not args.authentication_type:
        args.authentication_type = 'password' if 'Windows' in args.os_offer else 'ssh'

    if args.authentication_type == 'password':
        if args.ssh_dest_key_path or args.ssh_key_value:
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
        result = get_subscription_locations()
        if result:
            location = next((r.name for r in result if r.name.lower() == 'westus'), result[0].name)
        else:
            #this should never happen, just in case
            raise CLIError('Current subscription does not have valid location list')

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

def get_subscription_locations():
    subscription_client, subscription_id = _subscription_client_factory()
    result = list(subscription_client.subscriptions.list_locations(subscription_id))
    return result

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
