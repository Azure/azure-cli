# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse  # pylint: disable=import-error

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


MSI_LOCAL_ID = '[system]'


def get_target_network_api(cli_ctx):
    """ Since most compute calls don't need advanced network functionality, we can target a supported, but not
        necessarily latest, network API version is order to avoid having to re-record every test that uses VM create
        (which there are a lot) whenever NRP bumps their API version (which is often)!
    """
    from azure.cli.core.profiles import get_api_version, ResourceType
    version = get_api_version(cli_ctx, ResourceType.MGMT_NETWORK)
    if cli_ctx.cloud.profile == 'latest':
        version = '2018-01-01'
    return version


def read_content_if_is_file(string_or_file):
    content = string_or_file
    if os.path.exists(string_or_file):
        with open(string_or_file, 'r') as f:
            content = f.read()
    return content


def _resolve_api_version(cli_ctx, provider_namespace, resource_type, parent_path):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    provider = client.providers.get(provider_namespace)

    # If available, we will use parent resource's api-version
    resource_type_str = (parent_path.split('/')[0] if parent_path else resource_type)

    rt = [t for t in provider.resource_types  # pylint: disable=no-member
          if t.resource_type.lower() == resource_type_str.lower()]
    if not rt:
        raise CLIError('Resource type {} not found.'.format(resource_type_str))
    if len(rt) == 1 and rt[0].api_versions:
        npv = [v for v in rt[0].api_versions if 'preview' not in v.lower()]
        return npv[0] if npv else rt[0].api_versions[0]
    else:
        raise CLIError(
            'API version is required and could not be resolved for resource {}'
            .format(resource_type))


def log_pprint_template(template):
    logger.info('==== BEGIN TEMPLATE ====')
    logger.info(json.dumps(template, indent=2))
    logger.info('==== END TEMPLATE ====')


def check_existence(cli_ctx, value, resource_group, provider_namespace, resource_type,
                    parent_name=None, parent_type=None):
    # check for name or ID and set the type flags
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.tools import parse_resource_id
    from azure.cli.core.profiles import ResourceType
    resource_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).resources

    id_parts = parse_resource_id(value)

    rg = id_parts.get('resource_group', resource_group)
    ns = id_parts.get('namespace', provider_namespace)

    if parent_name and parent_type:
        parent_path = '{}/{}'.format(parent_type, parent_name)
        resource_name = id_parts.get('child_name_1', value)
        resource_type = id_parts.get('child_type_1', resource_type)
    else:
        parent_path = ''
        resource_name = id_parts['name']
        resource_type = id_parts.get('type', resource_type)
    api_version = _resolve_api_version(cli_ctx, provider_namespace, resource_type, parent_path)

    try:
        resource_client.get(rg, ns, parent_path, resource_type, resource_name, api_version)
        return True
    except CloudError:
        return False


def create_keyvault_data_plane_client(cli_ctx):
    from azure.cli.core._profile import Profile

    def get_token(server, resource, scope):  # pylint: disable=unused-argument
        return Profile(cli_ctx=cli_ctx).get_login_credentials(resource)[0]._token_retriever()  # pylint: disable=protected-access

    from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
    return KeyVaultClient(KeyVaultAuthentication(get_token))


def get_key_vault_base_url(cli_ctx, vault_name):
    suffix = cli_ctx.cloud.suffixes.keyvault_dns
    return 'https://{}{}'.format(vault_name, suffix)


def list_sku_info(cli_ctx, location=None):
    from ._client_factory import _compute_client_factory

    def _match_location(l, locations):
        return next((x for x in locations if x.lower() == l.lower()), None)

    client = _compute_client_factory(cli_ctx)
    result = client.resource_skus.list()
    if location:
        result = [r for r in result if _match_location(location, r.locations)]
    return result


def normalize_disk_info(image_data_disks=None, data_disk_sizes_gb=None, attach_data_disks=None, storage_sku=None,
                        os_disk_caching=None, data_disk_cachings=None):
    # we should return a dictionary with info like below and will emoit when see conflictions
    # {
    #   'os': { caching: 'Read', write_accelerator: None},
    #   0: { caching: 'None', write_accelerator: True},
    #   1: { caching: 'None', write_accelerator: True},
    # }
    from msrestazure.tools import is_valid_resource_id
    info = {}
    attach_data_disks = attach_data_disks or []
    image_data_disks = image_data_disks or []
    data_disk_sizes_gb = data_disk_sizes_gb or []
    info['os'] = {}

    for i in range(len(image_data_disks) + len(data_disk_sizes_gb) + len(attach_data_disks)):
        info[i] = {
            'lun': i
        }

    # fill in storage sku for managed data disks
    for i in range(len(image_data_disks) + len(data_disk_sizes_gb)):
        info[i]['managedDisk'] = {'storageAccountType': storage_sku}

    # fill in createOption
    for i in range(len(image_data_disks)):
        info[i]['createOption'] = 'fromImage'
    base = len(image_data_disks)
    for i in range(base, base + len(data_disk_sizes_gb)):
        info[i]['createOption'] = 'empty'
        info[i]['diskSizeGB'] = data_disk_sizes_gb[i]
    base = len(image_data_disks) + len(data_disk_sizes_gb)
    for i in range(base, base + len(attach_data_disks)):
        info[i]['createOption'] = 'attach'

    # fill in attached data disks details
    base = len(image_data_disks) + len(data_disk_sizes_gb)
    for i, d in enumerate(attach_data_disks):
        if is_valid_resource_id(d):
            info[base + i]['managedDisk'] = {'id': d}
        else:
            info[base + i]['vhd'] = {'uri': d}
            info[base + i]['name'] = d.split('/')[-1].split('.')[0]

    # fill in data disk caching
    if data_disk_cachings:
        update_disk_caching(info, data_disk_cachings)

    # default os disk caching to 'ReadWrite' unless set otherwise
    if os_disk_caching:
        info['os']['caching'] = os_disk_caching
    else:
        info['os']['caching'] = 'ReadWrite'
    return info


def update_disk_caching(model, caching_settings):

    def _update(model, lun, value):
        if isinstance(model, dict):
            luns = model.keys() if lun is None else [lun]
            for l in luns:
                if l not in model:
                    raise CLIError("data disk with lun of '{}' doesn't exist".format(lun))
                model[l]['caching'] = value
        else:
            if lun is None:
                disks = [model.os_disk] + (model.data_disks or [])
            elif lun == 'os':
                disks = [model.os_disk]
            else:
                disk = next((d for d in model.data_disks if d.lun == lun), None)
                if not disk:
                    raise CLIError("data disk with lun of '{}' doesn't exist".format(lun))
                disks = [disk]
            for disk in disks:
                disk.caching = value

    if len(caching_settings) == 1 and '=' not in caching_settings[0]:
        _update(model, None, caching_settings[0])
    else:
        for x in caching_settings:
            if '=' not in x:
                raise CLIError("usage error: please use 'LUN=VALUE' to configure caching on individual disk")
            lun, value = x.split('=', 1)
            lun = lun.lower()
            lun = int(lun) if lun != 'os' else lun
            _update(model, lun, value)


def update_write_accelerator_settings(model, write_accelerator_settings):

    def _update(model, lun, value):
        if isinstance(model, dict):
            luns = model.keys() if lun is None else [lun]
            for l in luns:
                if l not in model:
                    raise CLIError("data disk with lun of '{}' doesn't exist".format(lun))
                model[l]['writeAcceleratorEnabled'] = value
        else:
            if lun is None:
                disks = [model.os_disk] + (model.data_disks or [])
            elif lun == 'os':
                disks = [model.os_disk]
            else:
                disk = next((d for d in model.data_disks if d.lun == lun), None)
                if not disk:
                    raise CLIError("data disk with lun of '{}' doesn't exist".format(lun))
                disks = [disk]
            for disk in disks:
                disk.write_accelerator_enabled = value

    if len(write_accelerator_settings) == 1 and '=' not in write_accelerator_settings[0]:
        _update(model, None, write_accelerator_settings[0].lower() == 'true')
    else:
        for x in write_accelerator_settings:
            if '=' not in x:
                raise CLIError("usage error: please use 'LUN=VALUE' to configure write accelerator"
                               " on individual disk")
            lun, value = x.split('=', 1)
            lun = lun.lower()
            lun = int(lun) if lun != 'os' else lun
            _update(model, lun, value.lower() == 'true')


def get_storage_blob_uri(cli_ctx, storage):
    from azure.cli.core.profiles._shared import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    if urlparse(storage).scheme:
        storage_uri = storage
    else:
        storage_mgmt_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_STORAGE)
        storage_accounts = storage_mgmt_client.storage_accounts.list()
        storage_account = next((a for a in list(storage_accounts)
                                if a.name.lower() == storage.lower()), None)
        if storage_account is None:
            raise CLIError('{} does\'t exist.'.format(storage))
        storage_uri = storage_account.primary_endpoints.blob
    return storage_uri
