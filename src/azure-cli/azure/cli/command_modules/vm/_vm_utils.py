# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import re
import importlib
from enum import Enum

from urllib.parse import urlparse

from azure.cli.core.commands.arm import ArmTemplateBuilder
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)

MSI_LOCAL_ID = '[system]'


def get_target_network_api(cli_ctx):
    """
    The fixed version of network used by ARM template deployment.
    This is consistent with the version settings of other RP to ensure the stability of core commands "az vm create"
    and "az vmss create".
    In addition, it can also reduce the workload of re-recording a large number of vm tests after bumping the
    network api-version.
    Since it does not use the Python SDK, so it will not increase the dependence on the Python SDK
    """
    if cli_ctx.cloud.profile == 'latest':
        version = '2022-01-01'
    else:
        from azure.cli.core.profiles import get_api_version
        version = get_api_version(cli_ctx, ResourceType.MGMT_NETWORK)
    return version


def read_content_if_is_file(string_or_file):
    content = string_or_file
    if os.path.exists(string_or_file):
        with open(string_or_file, 'r') as f:
            content = f.read()
    return content


def _resolve_api_version(cli_ctx, provider_namespace, resource_type, parent_path):
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
                    parent_name=None, parent_type=None, static_version=None):
    # check for name or ID and set the type flags
    from azure.core.exceptions import HttpResponseError
    from azure.mgmt.core.tools import parse_resource_id
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
    if static_version:  # only for vnet
        api_version = static_version

    try:
        resource_client.get(rg, ns, parent_path, resource_type, resource_name, api_version)
        return True
    except HttpResponseError:
        return False


def create_data_plane_keyvault_certificate_client(cli_ctx, vault_base_url):
    from azure.cli.command_modules.keyvault._client_factory import data_plane_azure_keyvault_certificate_client
    return data_plane_azure_keyvault_certificate_client(cli_ctx, {"vault_base_url": vault_base_url})


def create_data_plane_keyvault_key_client(cli_ctx, vault_base_url):
    from azure.cli.command_modules.keyvault._client_factory import data_plane_azure_keyvault_key_client
    return data_plane_azure_keyvault_key_client(cli_ctx, {"vault_base_url": vault_base_url})


def get_key_vault_base_url(cli_ctx, vault_name):
    suffix = cli_ctx.cloud.suffixes.keyvault_dns
    return 'https://{}{}'.format(vault_name, suffix)


def list_sku_info(cli_ctx, location=None):
    from .aaz.latest.vm import ListSkus as _ListSkus

    def _match_location(loc, locations):
        return next((x for x in locations if str(x).lower() == str(loc).lower()), None)

    result = _ListSkus(cli_ctx=cli_ctx)(command_args={})
    if location:
        result = [r for r in result if _match_location(location, r['locations'])]
    return result


# pylint: disable=line-too-long
def is_sku_available(sku_info, zone):
    """
    The SKU is unavailable in the following cases:
    1. regional restriction and the region is restricted
    2. parameter --zone is input which indicates only showing skus with availability zones.
       Meanwhile, zonal restriction and all zones are restricted
    """
    is_available = True
    is_restrict_zone = False
    is_restrict_location = False
    if not sku_info.get('restrictions', []):
        return is_available
    for restriction in sku_info['restrictions']:
        if restriction.get('reasonCode', '') == 'NotAvailableForSubscription':
            if restriction['type'] == 'Zone' and not (
                    set(sku_info['locationInfo'][0].get('zones', []) or []) - set(restriction['restrictionInfo'].get('zones', []) or [])):
                is_restrict_zone = True
            if restriction['type'] == 'Location' and (
                    sku_info['locationInfo'][0]['location'] in (restriction['restrictionInfo'].get('locations', []) or [])):
                is_restrict_location = True

            if is_restrict_location or (is_restrict_zone and zone):
                is_available = False
                break
    return is_available


# pylint: disable=too-many-statements, too-many-branches, too-many-locals
def normalize_disk_info(image_data_disks=None,
                        data_disk_sizes_gb=None, attach_data_disks=None, storage_sku=None,
                        os_disk_caching=None, data_disk_cachings=None, size='',
                        ephemeral_os_disk=False, ephemeral_os_disk_placement=None,
                        data_disk_delete_option=None, source_snapshots_or_disks=None,
                        source_snapshots_or_disks_size_gb=None, source_disk_restore_point=None,
                        source_disk_restore_point_size_gb=None):
    from azure.mgmt.core.tools import is_valid_resource_id
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
    source_snapshots_or_disks = source_snapshots_or_disks or []
    source_snapshots_or_disks_size_gb = source_snapshots_or_disks_size_gb or []
    source_disk_restore_point = source_disk_restore_point or []
    source_disk_restore_point_size_gb = source_disk_restore_point_size_gb or []

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

    # add copy data disks
    i = 0
    source_resource_copy = list(source_snapshots_or_disks)
    source_resource_copy_size = list(source_snapshots_or_disks_size_gb)
    while source_resource_copy:
        while i in used_luns:
            i += 1

        used_luns.add(i)

        info[i] = {
            'lun': i,
            'createOption': 'copy',
            'managedDisk': {'storageAccountType': None},
            'diskSizeGB': source_resource_copy_size.pop(0),
            'sourceResource': {
                'id': source_resource_copy.pop(0)
            }
        }

    # add restore data disks
    i = 0
    source_resource_restore = list(source_disk_restore_point)
    source_resource_restore_size = list(source_disk_restore_point_size_gb)
    while source_resource_restore:
        while i in used_luns:
            i += 1

        used_luns.add(i)

        info[i] = {
            'lun': i,
            'createOption': 'restore',
            'managedDisk': {'storageAccountType': None},
            'diskSizeGB': source_resource_restore_size.pop(0),
            'sourceResource': {
                'id': source_resource_restore.pop(0)
            }
        }

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


def update_disk_caching_by_aaz(model, caching_settings):
    def _update(model, lun, value):
        luns = model.keys() if lun is None else [lun]
        for lun_item in luns:
            if lun_item not in model:
                raise CLIError("Data disk with lun of '{}' doesn't exist. Existing luns: {}."
                               .format(lun_item, list(model.keys())))
            model[lun_item]['caching'] = value

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
        luns = model.keys() if lun is None else [lun]
        for lun_item in luns:
            if lun_item not in model:
                raise CLIError("data disk with lun of '{}' doesn't exist".format(lun_item))
            model[lun_item]['write_accelerator_enabled'] = value

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


def is_valid_vmss_resource_id(vmss_resource_id):
    if not vmss_resource_id:
        return False

    vmss_id_pattern = re.compile(r'^/subscriptions/[^/]*/resourceGroups/[^/]*/providers/Microsoft.Compute/'
                                 r'virtualMachineScaleSets/.*$', re.IGNORECASE)
    if vmss_id_pattern.match(vmss_resource_id):
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


def is_valid_vm_image_id(image_image_id):
    if not image_image_id:
        return False

    image_version_id_pattern = re.compile(r'^/subscriptions/[^/]*/resourceGroups/[^/]*/providers/Microsoft.Compute/'
                                          r'images/.*$', re.IGNORECASE)
    if image_version_id_pattern.match(image_image_id):
        return True

    return False


def parse_gallery_image_id(image_reference):
    from azure.cli.core.azclierror import InvalidArgumentValueError

    if not image_reference:
        raise InvalidArgumentValueError(
            'Please pass in the gallery image id through the parameter --image')

    image_info = re.search(r'^/subscriptions/([^/]*)/resourceGroups/([^/]*)/providers/Microsoft.Compute/'
                           r'galleries/([^/]*)/images/([^/]*)/versions/.*$', image_reference, re.IGNORECASE)
    if not image_info or len(image_info.groups()) < 2:
        raise InvalidArgumentValueError(
            'The gallery image id is invalid. The valid format should be "/subscriptions/{sub_id}'
            '/resourceGroups/{rg}/providers/Microsoft.Compute/galleries/{gallery_name}'
            '/Images/{gallery_image_name}/Versions/{image_version}"')

    # Return the gallery subscription id, resource group name, gallery name and gallery image name.
    return image_info.group(1), image_info.group(2), image_info.group(3), image_info.group(4)


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


def parse_vm_image_id(image_id):
    from azure.cli.core.azclierror import InvalidArgumentValueError

    image_info = re.search(r'^/subscriptions/([^/]*)/resourceGroups/([^/]*)/providers/Microsoft.Compute/'
                           r'images/(.*$)', image_id, re.IGNORECASE)
    if not image_info or len(image_info.groups()) < 2:
        raise InvalidArgumentValueError(
            'The gallery image id is invalid. The valid format should be "/subscriptions/{sub_id}'
            '/resourceGroups/{rg}/providers/Microsoft.Compute/images/{image_name}"')

    # Return the gallery subscription id, resource group name and image name.
    return image_info.group(1), image_info.group(2), image_info.group(3)


def is_compute_gallery_image_id(image_reference):
    if not image_reference:
        return False

    compute_gallery_id_pattern = re.compile(r'^/subscriptions/[^/]*/resourceGroups/[^/]*/providers/Microsoft.Compute/'
                                            r'galleries/[^/]*/images/.*$', re.IGNORECASE)
    if compute_gallery_id_pattern.match(image_reference):
        return True

    return False


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


def is_trusted_launch_supported(supported_features):
    if not supported_features:
        return False

    trusted_launch = {'TrustedLaunchSupported', 'TrustedLaunch', 'TrustedLaunchAndConfidentialVmSupported'}

    return bool(trusted_launch.intersection({feature.value for feature in supported_features}))


def trusted_launch_warning_log(namespace, generation_version, features):
    if not generation_version:
        return

    from ._constants import TLAD_DEFAULT_CHANGE_MSG
    log_message = TLAD_DEFAULT_CHANGE_MSG.format('az vm/vmss create')

    from ._constants import COMPATIBLE_SECURITY_TYPE_VALUE, UPGRADE_SECURITY_HINT
    if generation_version == 'V1':
        if namespace.security_type and namespace.security_type == COMPATIBLE_SECURITY_TYPE_VALUE:
            logger.warning(UPGRADE_SECURITY_HINT)
        else:
            logger.warning(log_message)

    if generation_version == 'V2' and is_trusted_launch_supported(features):
        if not namespace.security_type:
            logger.warning(log_message)
        elif namespace.security_type == COMPATIBLE_SECURITY_TYPE_VALUE:
            logger.warning(UPGRADE_SECURITY_HINT)


def validate_vm_disk_trusted_launch(namespace, disk_security_profile):
    from ._constants import UPGRADE_SECURITY_HINT

    if disk_security_profile is None:
        logger.warning(UPGRADE_SECURITY_HINT)
        return

    security_type = disk_security_profile.security_type if hasattr(disk_security_profile, 'security_type') else None
    if security_type and security_type.lower() == 'trustedlaunch':
        if namespace.enable_secure_boot is None:
            namespace.enable_secure_boot = True
        if namespace.enable_vtpm is None:
            namespace.enable_vtpm = True
        namespace.security_type = 'TrustedLaunch'
    elif security_type and security_type.lower() == 'standard':
        logger.warning(UPGRADE_SECURITY_HINT)


def validate_image_trusted_launch(namespace):
    from ._constants import UPGRADE_SECURITY_HINT

    if namespace.security_type and namespace.security_type.lower() != 'trustedlaunch':
        logger.warning(UPGRADE_SECURITY_HINT)


def display_region_recommendation(cmd, namespace):

    identified_region_maps = {
        'westeurope': 'uksouth',
        'francecentral': 'northeurope',
        'germanywestcentral': 'northeurope'
    }

    identified_region = identified_region_maps.get(namespace.location)
    from azure.cli.core import telemetry
    telemetry.set_region_identified(namespace.location, identified_region)

    if identified_region and cmd.cli_ctx.config.getboolean('core', 'display_region_identified', True):
        from azure.cli.core.style import Style, print_styled_text
        import sys
        recommend_region = 'Selecting "' + identified_region + '" may reduce your costs. ' \
                           'The region you\'ve selected may cost more for the same services. ' \
                           'You can disable this message in the future with the command '
        disable_config = '"az config set core.display_region_identified=false". '
        learn_more_msg = 'Learn more at https://go.microsoft.com/fwlink/?linkid=222571 '
        # Since the output of the "az vm create" command is a JSON object
        # which can be used for automated script parsing
        # So we output the notification message to sys.stderr
        print_styled_text([(Style.WARNING, recommend_region), (Style.ACTION, disable_config),
                           (Style.WARNING, learn_more_msg)], file=sys.stderr)
        print_styled_text(file=sys.stderr)


def import_aaz_by_profile(profile, module_name):
    from azure.cli.core.aaz.utils import get_aaz_profile_module_name
    profile_module_name = get_aaz_profile_module_name(profile_name=profile)
    return importlib.import_module(f"azure.cli.command_modules.vm.aaz.{profile_module_name}.{module_name}")


def generate_ssh_keys_ed25519(private_key_filepath, public_key_filepath):
    def _open(filename, mode):
        return os.open(filename, flags=os.O_WRONLY | os.O_TRUNC | os.O_CREAT, mode=mode)

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    ssh_dir = os.path.dirname(private_key_filepath)
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir, mode=0o700)

    if os.path.isfile(private_key_filepath):
        # Try to use existing private key if it exists.
        with open(private_key_filepath, "rb") as f:
            private_bytes = f.read()
        private_key = serialization.load_ssh_private_key(private_bytes, password=None)
        logger.warning("Private SSH key file '%s' was found in the directory: '%s'. "
                       "A paired public key file '%s' will be generated.",
                       private_key_filepath, ssh_dir, public_key_filepath)

    else:
        # Otherwise generate new private key.
        private_key = Ed25519PrivateKey.generate()

        # The private key will look like:
        # -----BEGIN OPENSSH PRIVATE KEY-----
        # ...
        # -----END OPENSSH PRIVATE KEY-----
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption()
        )

        with os.fdopen(_open(private_key_filepath, 0o600), "wb") as f:
            f.write(private_bytes)

    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH)

    with os.fdopen(_open(public_key_filepath, 0o644), 'wb') as f:
        f.write(public_bytes)

    return public_bytes.decode()


def _gen_guid():
    import uuid
    return uuid.uuid4()


def assign_identity(cli_ctx, getter, setter, identity_role=None, identity_scope=None):
    from azure.cli.core.commands.arm import create_role_assignment

    # get
    resource = getter()
    resource = setter(resource)

    # create role assignment:
    if identity_scope:
        principal_id = resource.get('identity', {}).get('principalId') or resource.get('identity', {}).get('principal_id')
        create_role_assignment(cli_ctx, principal_id, identity_role, identity_scope)
    return resource


class IdentityType(Enum):
    SYSTEM_ASSIGNED = 'SystemAssigned'
    USER_ASSIGNED = 'UserAssigned'
    SYSTEM_ASSIGNED_USER_ASSIGNED = 'SystemAssigned, UserAssigned'
    NONE = 'None'
