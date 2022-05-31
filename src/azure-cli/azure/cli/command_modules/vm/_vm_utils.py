# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import re

from azure.cli.core.commands.arm import ArmTemplateBuilder

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
    from azure.cli.core.profiles import get_api_version, ResourceType, AD_HOC_API_VERSIONS
    version = get_api_version(cli_ctx, ResourceType.MGMT_NETWORK)
    if cli_ctx.cloud.profile == 'latest':
        version = AD_HOC_API_VERSIONS[ResourceType.MGMT_NETWORK]['vm_default_target_network']
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
    from azure.core.exceptions import HttpResponseError
    from msrestazure.tools import parse_resource_id
    from azure.cli.core.profiles import ResourceType
    id_parts = parse_resource_id(value)
    resource_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                              subscription_id=id_parts.get('subscription', None)).resources
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
    except HttpResponseError:
        return False


def create_keyvault_data_plane_client(cli_ctx):
    from azure.cli.command_modules.keyvault._client_factory import keyvault_data_plane_factory
    return keyvault_data_plane_factory(cli_ctx)


def get_key_vault_base_url(cli_ctx, vault_name):
    suffix = cli_ctx.cloud.suffixes.keyvault_dns
    return 'https://{}{}'.format(vault_name, suffix)


def list_sku_info(cli_ctx, location=None):
    from ._client_factory import _compute_client_factory

    def _match_location(loc, locations):
        return next((x for x in locations if x.lower() == loc.lower()), None)

    client = _compute_client_factory(cli_ctx)
    result = client.resource_skus.list()
    if location:
        result = [r for r in result if _match_location(location, r.locations)]
    return result


# pylint: disable=too-many-statements, too-many-branches
def normalize_disk_info(image_data_disks=None,
                        data_disk_sizes_gb=None, attach_data_disks=None, storage_sku=None,
                        os_disk_caching=None, data_disk_cachings=None, size='',
                        ephemeral_os_disk=False, ephemeral_os_disk_placement=None,
                        data_disk_delete_option=None):
    from msrestazure.tools import is_valid_resource_id
    from ._validators import validate_delete_options
    is_lv_size = re.search('_L[0-9]+s', size, re.I)
    # we should return a dictionary with info like below
    # {
    #   'os': { caching: 'Read', write_accelerator: None},
    #   0: { caching: 'None', write_accelerator: True},
    #   1: { caching: 'None', write_accelerator: True},
    # }
    info = {}
    used_luns = set()

    attach_data_disks = attach_data_disks or []
    data_disk_sizes_gb = data_disk_sizes_gb or []
    image_data_disks = image_data_disks or []

    if data_disk_delete_option:
        if attach_data_disks:
            data_disk_delete_option = validate_delete_options(attach_data_disks, data_disk_delete_option)
        else:
            if isinstance(data_disk_delete_option, list) and len(data_disk_delete_option) == 1 and len(
                    data_disk_delete_option[0].split('=')) == 1:  # pylint: disable=line-too-long
                data_disk_delete_option = data_disk_delete_option[0]
    info['os'] = {}
    # update os diff disk settings
    if ephemeral_os_disk:
        info['os']['diffDiskSettings'] = {'option': 'Local'}
        # local os disks require readonly caching, default to ReadOnly if os_disk_caching not specified.
        if not os_disk_caching:
            os_disk_caching = 'ReadOnly'
        if ephemeral_os_disk_placement:
            info['os']['diffDiskSettings']['placement'] = ephemeral_os_disk_placement

    # add managed image data disks
    for data_disk in image_data_disks:
        i = data_disk['lun']
        info[i] = {
            'lun': i,
            'managedDisk': {'storageAccountType': None},
            'createOption': 'fromImage'
        }
        used_luns.add(i)

    # add empty data disks, do not use existing luns
    i = 0
    sizes_copy = list(data_disk_sizes_gb)
    while sizes_copy:
        # get free lun
        while i in used_luns:
            i += 1

        used_luns.add(i)

        info[i] = {
            'lun': i,
            'managedDisk': {'storageAccountType': None},
            'createOption': 'empty',
            'diskSizeGB': sizes_copy.pop(0),
        }
        if isinstance(data_disk_delete_option, str):
            info[i]['deleteOption'] = data_disk_delete_option

    # update storage skus for managed data disks
    if storage_sku is not None:
        update_disk_sku_info(info, storage_sku)

    # check that os storage account type is not UltraSSD_LRS
    if info['os'].get('storageAccountType', "").lower() == 'ultrassd_lrs':
        logger.warning("Managed os disk storage account sku cannot be UltraSSD_LRS. Using service default.")
        info['os']['storageAccountType'] = None

    # add attached data disks
    i = 0
    attach_data_disks_copy = list(attach_data_disks)
    while attach_data_disks_copy:
        # get free lun
        while i in used_luns:
            i += 1

        used_luns.add(i)

        # use free lun
        info[i] = {
            'lun': i,
            'createOption': 'attach'
        }

        d = attach_data_disks_copy.pop(0)
        info[i]['name'] = d.split('/')[-1].split('.')[0]
        if is_valid_resource_id(d):
            info[i]['managedDisk'] = {'id': d}
            if data_disk_delete_option:
                info[i]['deleteOption'] = data_disk_delete_option if isinstance(data_disk_delete_option, str) \
                    else data_disk_delete_option.get(info[i]['name'], None)
        else:
            info[i]['vhd'] = {'uri': d}
            if data_disk_delete_option:
                info[i]['deleteOption'] = data_disk_delete_option if isinstance(data_disk_delete_option, str) \
                    else data_disk_delete_option.get(info[i]['name'], None)

    # fill in data disk caching
    if data_disk_cachings:
        update_disk_caching(info, data_disk_cachings)

    # default os disk caching to 'ReadWrite' unless set otherwise
    if os_disk_caching:
        info['os']['caching'] = os_disk_caching
    else:
        info['os']['caching'] = 'None' if is_lv_size else 'ReadWrite'

    # error out on invalid vm sizes
    if is_lv_size:
        for v in info.values():
            if v.get('caching', 'None').lower() != 'none':
                raise CLIError('usage error: for Lv series of machines, "None" is the only supported caching mode')

    result_info = {'os': info['os']}

    # in python 3 insertion order matters during iteration. This ensures that luns are retrieved in numerical order
    for key in sorted([key for key in info if key != 'os']):
        result_info[key] = info[key]

    return result_info


def update_disk_caching(model, caching_settings):
    def _update(model, lun, value):
        if isinstance(model, dict):
            luns = model.keys() if lun is None else [lun]
            for lun_item in luns:
                if lun_item not in model:
                    raise CLIError("Data disk with lun of '{}' doesn't exist. Existing luns: {}."
                                   .format(lun_item, list(model.keys())))
                model[lun_item]['caching'] = value
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
            for lun_item in luns:
                if lun_item not in model:
                    raise CLIError("data disk with lun of '{}' doesn't exist".format(lun_item))
                model[lun_item]['writeAcceleratorEnabled'] = value
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


def update_disk_sku_info(info_dict, skus):
    usage_msg = 'Usage:\n\t[--storage-sku SKU | --storage-sku ID=SKU ID=SKU ID=SKU...]\n' \
                'where each ID is "os" or a 0-indexed lun.'

    def _update(info, lun, value):
        luns = info.keys()
        if lun not in luns:
            raise CLIError("Data disk with lun of '{}' doesn't exist. Existing luns: {}.".format(lun, luns))
        if lun == 'os':
            info[lun]['storageAccountType'] = value
        else:
            info[lun]['managedDisk']['storageAccountType'] = value

    if len(skus) == 1 and '=' not in skus[0]:
        for lun in info_dict.keys():
            _update(info_dict, lun, skus[0])
    else:
        for sku in skus:
            if '=' not in sku:
                raise CLIError("A sku's format is incorrect.\n{}".format(usage_msg))

            lun, value = sku.split('=', 1)
            lun = lun.lower()
            try:
                lun = int(lun) if lun != "os" else lun
            except ValueError:
                raise CLIError("A sku ID is incorrect.\n{}".format(usage_msg))
            _update(info_dict, lun, value)


def is_shared_gallery_image_id(image_reference):
    if not image_reference:
        return False

    shared_gallery_id_pattern = re.compile(r'^/SharedGalleries/[^/]*/Images/[^/]*/Versions/.*$', re.IGNORECASE)
    if shared_gallery_id_pattern.match(image_reference):
        return True

    return False


def is_valid_vm_resource_id(vm_resource_id):
    if not vm_resource_id:
        return False

    vm_id_pattern = re.compile(r'^/subscriptions/[^/]*/resourceGroups/[^/]*/providers/Microsoft.Compute/'
                               r'virtualMachines/.*$', re.IGNORECASE)
    if vm_id_pattern.match(vm_resource_id):
        return True

    return False


def is_valid_image_version_id(image_version_id):
    if not image_version_id:
        return False

    image_version_id_pattern = re.compile(r'^/subscriptions/[^/]*/resourceGroups/[^/]*/providers/Microsoft.Compute/'
                                          r'galleries/[^/]*/images/[^/]*/versions/.*$', re.IGNORECASE)
    if image_version_id_pattern.match(image_version_id):
        return True

    return False


def parse_shared_gallery_image_id(image_reference):
    from azure.cli.core.azclierror import InvalidArgumentValueError

    if not image_reference:
        raise InvalidArgumentValueError(
            'Please pass in the shared gallery image id through the parameter --image')

    image_info = re.search(r'^/SharedGalleries/([^/]*)/Images/([^/]*)/Versions/.*$', image_reference, re.IGNORECASE)
    if not image_info or len(image_info.groups()) < 2:
        raise InvalidArgumentValueError(
            'The shared gallery image id is invalid. The valid format should be '
            '"/SharedGalleries/{gallery_unique_name}/Images/{gallery_image_name}/Versions/{image_version}"')

    # Return the gallery unique name and gallery image name parsed from shared gallery image id
    return image_info.group(1), image_info.group(2)


def is_community_gallery_image_id(image_reference):
    if not image_reference:
        return False

    community_gallery_id_pattern = re.compile(r'^/CommunityGalleries/[^/]*/Images/[^/]*/Versions/.*$', re.IGNORECASE)
    if community_gallery_id_pattern.match(image_reference):
        return True

    return False


def parse_community_gallery_image_id(image_reference):
    from azure.cli.core.azclierror import InvalidArgumentValueError

    if not image_reference:
        raise InvalidArgumentValueError(
            'Please pass in the community gallery image id through the parameter --image')

    image_info = re.search(r'^/CommunityGalleries/([^/]*)/Images/([^/]*)/Versions/.*$', image_reference, re.IGNORECASE)
    if not image_info or len(image_info.groups()) < 2:
        raise InvalidArgumentValueError(
            'The community gallery image id is invalid. The valid format should be '
            '"/CommunityGalleries/{gallery_unique_name}/Images/{gallery_image_name}/Versions/{image_version}"')

    # Return the gallery unique name and gallery image name parsed from community gallery image id
    return image_info.group(1), image_info.group(2)


class ArmTemplateBuilder20190401(ArmTemplateBuilder):

    def __init__(self):
        super().__init__()
        self.template['$schema'] = 'https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#'


def raise_unsupported_error_for_flex_vmss(vmss, error_message):
    if hasattr(vmss, 'orchestration_mode') and vmss.orchestration_mode \
            and vmss.orchestration_mode.lower() == 'flexible':
        from azure.cli.core.azclierror import ArgumentUsageError
        raise ArgumentUsageError(error_message)
