# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import re

from azure.cli.core.util import CLIError
from azure.cli.core.commands.parameters import get_one_of_subscription_locations
from azure.cli.core.commands.arm import resource_exists

from six.moves.urllib.request import urlopen  # pylint: disable=import-error

from ._client_factory import _compute_client_factory


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


def _get_thread_count():
    return 40


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
        with ThreadPoolExecutor(max_workers=_get_thread_count()) as executor:
            tasks = [executor.submit(_load_images_from_publisher, p.name) for p in publishers]
            for t in as_completed(tasks):
                t.result()  # don't use the result but expose exceptions from the threads
    elif publisher_num == 1:
        _load_images_from_publisher(publishers[0].name)

    return all_images


def load_images_from_aliases_doc(publisher=None, offer=None, sku=None):
    target_url = ('https://raw.githubusercontent.com/Azure/azure-rest-api-specs/'
                  'master/arm-compute/quickstart-templates/aliases.json')
    txt = urlopen(target_url).read()
    dic = json.loads(txt.decode())
    try:
        all_images = []
        result = (dic['outputs']['aliases']['value'])
        for v in result.values():  # loop around os
            for alias, vv in v.items():  # loop around distros
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


def load_extension_images_thru_services(publisher, name, version, location, show_latest=False):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from distutils.version import LooseVersion  # pylint: disable=no-name-in-module,import-error
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
                # pylint: disable=no-member
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
        with ThreadPoolExecutor(max_workers=_get_thread_count()) as executor:
            tasks = [executor.submit(_load_extension_images_from_publisher,
                                     p.name) for p in publishers]
            for t in as_completed(tasks):
                t.result()  # don't use the result but expose exceptions from the threads
    elif publisher_num == 1:
        _load_extension_images_from_publisher(publishers[0].name)

    return all_images


def get_vm_sizes(location):
    return list(_compute_client_factory().virtual_machine_sizes.list(location))


def _partial_matched(pattern, string):
    if not pattern:
        return True  # empty pattern means wildcard-match
    pattern = r'.*' + pattern
    return re.match(pattern, string, re.I)  # pylint: disable=no-member


def _create_image_instance(publisher, offer, sku, version):
    return {
        'publisher': publisher,
        'offer': offer,
        'sku': sku,
        'version': version
    }
