# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json

from knack.util import CLIError

from azure.cli.core.commands.parameters import get_one_of_subscription_locations
from azure.cli.core.commands.arm import resource_exists

from ._client_factory import _compute_client_factory


def _resource_not_exists(cli_ctx, resource_type):
    def _handle_resource_not_exists(namespace):
        # TODO: hook up namespace._subscription_id once we support it
        ns, t = resource_type.split('/')
        if resource_exists(cli_ctx, namespace.resource_group_name, namespace.name, ns, t):
            raise CLIError('Resource {} of type {} in group {} already exists.'.format(
                namespace.name,
                resource_type,
                namespace.resource_group_name))
    return _handle_resource_not_exists


def _get_thread_count():
    return 5  # don't increase too much till https://github.com/Azure/msrestazure-for-python/issues/6 is fixed


def load_images_thru_services(cli_ctx, publisher, offer, sku, location):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    all_images = []
    client = _compute_client_factory(cli_ctx)
    if location is None:
        location = get_one_of_subscription_locations(cli_ctx)

    def _load_images_from_publisher(publisher):
        offers = client.virtual_machine_images.list_offers(location, publisher)
        if offer:
            offers = [o for o in offers if _matched(offer, o.name)]
        for o in offers:
            skus = client.virtual_machine_images.list_skus(location, publisher, o.name)
            if sku:
                skus = [s for s in skus if _matched(sku, s.name)]
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
        publishers = [p for p in publishers if _matched(publisher, p.name)]

    publisher_num = len(publishers)
    if publisher_num > 1:
        with ThreadPoolExecutor(max_workers=_get_thread_count()) as executor:
            tasks = [executor.submit(_load_images_from_publisher, p.name) for p in publishers]
            for t in as_completed(tasks):
                t.result()  # don't use the result but expose exceptions from the threads
    elif publisher_num == 1:
        _load_images_from_publisher(publishers[0].name)

    return all_images


def load_images_from_aliases_doc(cli_ctx, publisher=None, offer=None, sku=None):
    import requests
    from azure.cli.core.cloud import CloudEndpointNotSetException
    from azure.cli.core.util import should_disable_connection_verify
    try:
        target_url = cli_ctx.cloud.endpoints.vm_image_alias_doc
    except CloudEndpointNotSetException:
        raise CLIError("'endpoint_vm_image_alias_doc' isn't configured. Please invoke 'az cloud update' to configure "
                       "it or use '--all' to retrieve images from server")
    # under hack mode(say through proxies with unsigned cert), opt out the cert verification
    response = requests.get(target_url, verify=(not should_disable_connection_verify()))
    if response.status_code != 200:
        raise CLIError("Failed to retrieve image alias doc '{}'. Error: '{}'".format(target_url, response))
    dic = json.loads(response.content.decode())
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

        all_images = [i for i in all_images if (_matched(publisher, i['publisher']) and
                                                _matched(offer, i['offer']) and
                                                _matched(sku, i['sku']))]
        return all_images
    except KeyError:
        raise CLIError('Could not retrieve image list from {}'.format(target_url))


def load_extension_images_thru_services(cli_ctx, publisher, name, version, location,
                                        show_latest=False, partial_match=True):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from distutils.version import LooseVersion  # pylint: disable=no-name-in-module,import-error
    all_images = []
    client = _compute_client_factory(cli_ctx)
    if location is None:
        location = get_one_of_subscription_locations(cli_ctx)

    def _load_extension_images_from_publisher(publisher):
        from msrestazure.azure_exceptions import CloudError
        try:
            types = client.virtual_machine_extension_images.list_types(location, publisher)
        except CloudError:  # PIR image publishers might not have any extension images, exception could raise
            types = []
        if name:
            types = [t for t in types if _matched(name, t.name, partial_match)]
        for t in types:
            versions = client.virtual_machine_extension_images.list_versions(location,
                                                                             publisher,
                                                                             t.name)
            if version:
                versions = [v for v in versions if _matched(version, v.name, partial_match)]

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
        publishers = [p for p in publishers if _matched(publisher, p.name, partial_match)]

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


def get_vm_sizes(cli_ctx, location):
    return list(_compute_client_factory(cli_ctx).virtual_machine_sizes.list(location))


def _matched(pattern, string, partial_match=True):
    if not pattern:
        return True  # empty pattern means wildcard-match
    pattern, string = pattern.lower(), string.lower()
    return pattern in string if partial_match else pattern == string


def _create_image_instance(publisher, offer, sku, version):
    return {
        'publisher': publisher,
        'offer': offer,
        'sku': sku,
        'version': version
    }


def _get_latest_image_version(cli_ctx, location, publisher, offer, sku):
    top_one = _compute_client_factory(cli_ctx).virtual_machine_images.list(location,
                                                                           publisher,
                                                                           offer,
                                                                           sku,
                                                                           top=1,
                                                                           orderby='name desc')
    if not top_one:
        raise CLIError("Can't resolve the vesion of '{}:{}:{}'".format(publisher, offer, sku))
    return top_one[0].name
