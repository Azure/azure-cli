# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint:disable=too-many-lines

import os

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse  # pylint: disable=import-error

from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core.azclierror import (ValidationError, ArgumentUsageError, RequiredArgumentMissingError,
                                       MutuallyExclusiveArgumentError, CLIInternalError)
from azure.cli.core.commands.validators import (
    get_default_location_from_resource_group, validate_file_or_dict, validate_parameter_set, validate_tags)
from azure.cli.core.util import (hash_string, DISALLOWED_USER_NAMES, get_default_admin_username)
from azure.cli.command_modules.vm._vm_utils import (
    check_existence, get_target_network_api, get_storage_blob_uri, list_sku_info)
from azure.cli.command_modules.vm._template_builder import StorageProfile
from azure.cli.core import keys
from azure.core.exceptions import ResourceNotFoundError

from ._client_factory import _compute_client_factory
from ._actions import _get_latest_image_version
logger = get_logger(__name__)


DEDICATED_HOST_NONE = 'NONE'


def validate_asg_names_or_ids(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_subscription_id
    ApplicationSecurityGroup = cmd.get_models('ApplicationSecurityGroup',
                                              resource_type=ResourceType.MGMT_NETWORK)

    resource_group = namespace.resource_group_name
    subscription_id = get_subscription_id(cmd.cli_ctx)
    names_or_ids = getattr(namespace, 'application_security_groups')
    ids = []

    if names_or_ids == [""] or not names_or_ids:
        return

    for val in names_or_ids:
        if not is_valid_resource_id(val):
            val = resource_id(
                subscription=subscription_id,
                resource_group=resource_group,
                namespace='Microsoft.Network', type='applicationSecurityGroups',
                name=val
            )
        ids.append(ApplicationSecurityGroup(id=val))
    setattr(namespace, 'application_security_groups', ids)


def validate_nsg_name(cmd, namespace):
    from msrestazure.tools import resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id
    vm_id = resource_id(name=namespace.vm_name, resource_group=namespace.resource_group_name,
                        namespace='Microsoft.Compute', type='virtualMachines',
                        subscription=get_subscription_id(cmd.cli_ctx))
    namespace.network_security_group_name = namespace.network_security_group_name \
        or '{}_NSG_{}'.format(namespace.vm_name, hash_string(vm_id, length=8))


def validate_keyvault(cmd, namespace):
    namespace.keyvault = _get_resource_id(cmd.cli_ctx, namespace.keyvault, namespace.resource_group_name,
                                          'vaults', 'Microsoft.KeyVault')


def validate_vm_name_for_monitor_metrics(cmd, namespace):
    if hasattr(namespace, 'resource'):
        namespace.resource = _get_resource_id(cmd.cli_ctx, namespace.resource, namespace.resource_group_name,
                                              'virtualMachines', 'Microsoft.Compute')
    elif hasattr(namespace, 'resource_uri'):
        namespace.resource_uri = _get_resource_id(cmd.cli_ctx, namespace.resource_uri, namespace.resource_group_name,
                                                  'virtualMachines', 'Microsoft.Compute')
    del namespace.resource_group_name


def _validate_proximity_placement_group(cmd, namespace):
    from msrestazure.tools import parse_resource_id

    if namespace.proximity_placement_group:
        namespace.proximity_placement_group = _get_resource_id(cmd.cli_ctx, namespace.proximity_placement_group,
                                                               namespace.resource_group_name,
                                                               'proximityPlacementGroups', 'Microsoft.Compute')

        parsed = parse_resource_id(namespace.proximity_placement_group)
        rg, name = parsed['resource_group'], parsed['name']

        if not check_existence(cmd.cli_ctx, name, rg, 'Microsoft.Compute', 'proximityPlacementGroups'):
            raise CLIError("Proximity Placement Group '{}' does not exist.".format(name))


def process_vm_secret_format(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id
    from azure.cli.core._output import (get_output_format, set_output_format)

    keyvault_usage = CLIError('usage error: [--keyvault NAME --resource-group NAME | --keyvault ID]')
    kv = namespace.keyvault
    rg = namespace.resource_group_name

    if rg:
        if not kv or is_valid_resource_id(kv):
            raise keyvault_usage
        validate_keyvault(cmd, namespace)
    else:
        if kv and not is_valid_resource_id(kv):
            raise keyvault_usage

    warning_msg = "This command does not support the {} output format. Showing JSON format instead."
    desired_formats = ["json", "jsonc"]

    output_format = get_output_format(cmd.cli_ctx)
    if output_format not in desired_formats:
        warning_msg = warning_msg.format(output_format)
        logger.warning(warning_msg)
        set_output_format(cmd.cli_ctx, desired_formats[0])


def _get_resource_group_from_vault_name(cli_ctx, vault_name):
    """
    Fetch resource group from vault name
    :param str vault_name: name of the key vault
    :return: resource group name or None
    :rtype: str
    """
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from msrestazure.tools import parse_resource_id
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_KEYVAULT).vaults
    for vault in client.list():
        id_comps = parse_resource_id(vault.id)
        if id_comps['name'] == vault_name:
            return id_comps['resource_group']
    return None


def _get_resource_id(cli_ctx, val, resource_group, resource_type, resource_namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id
    if is_valid_resource_id(val):
        return val

    kwargs = {
        'name': val,
        'resource_group': resource_group,
        'namespace': resource_namespace,
        'type': resource_type,
        'subscription': get_subscription_id(cli_ctx)
    }
    missing_kwargs = {k: v for k, v in kwargs.items() if not v}

    return resource_id(**kwargs) if not missing_kwargs else None


def _get_nic_id(cli_ctx, val, resource_group):
    return _get_resource_id(cli_ctx, val, resource_group,
                            'networkInterfaces', 'Microsoft.Network')


def validate_vm_nic(cmd, namespace):
    namespace.nic = _get_nic_id(cmd.cli_ctx, namespace.nic, namespace.resource_group_name)


def validate_vm_nics(cmd, namespace):
    rg = namespace.resource_group_name
    nic_ids = []

    for n in namespace.nics:
        nic_ids.append(_get_nic_id(cmd.cli_ctx, n, rg))
    namespace.nics = nic_ids

    if hasattr(namespace, 'primary_nic') and namespace.primary_nic:
        namespace.primary_nic = _get_nic_id(cmd.cli_ctx, namespace.primary_nic, rg)


def _validate_secrets(secrets, os_type):
    """
    Validates a parsed JSON array containing secrets for use in VM Creation
    Secrets JSON structure
    [{
        "sourceVault": { "id": "value" },
        "vaultCertificates": [{
            "certificateUrl": "value",
            "certificateStore": "cert store name (only on windows)"
        }]
    }]
    :param dict secrets: Dict fitting the JSON description above
    :param string os_type: the type of OS (linux or windows)
    :return: errors if any were found
    :rtype: list
    """
    is_windows = os_type == 'windows'
    errors = []

    try:
        loaded_secret = [validate_file_or_dict(secret) for secret in secrets]
    except Exception as err:
        raise CLIError('Error decoding secrets: {0}'.format(err))

    for idx_arg, narg_secret in enumerate(loaded_secret):
        for idx, secret in enumerate(narg_secret):
            if 'sourceVault' not in secret:
                errors.append(
                    'Secret is missing sourceVault key at index {0} in arg {1}'.format(
                        idx, idx_arg))
            if 'sourceVault' in secret and 'id' not in secret['sourceVault']:
                errors.append(
                    'Secret is missing sourceVault.id key at index {0}  in arg {1}'.format(
                        idx, idx_arg))
            if 'vaultCertificates' not in secret or not secret['vaultCertificates']:
                err = 'Secret is missing vaultCertificates array or it is empty at index {0} in ' \
                      'arg {1} '
                errors.append(err.format(idx, idx_arg))
            else:
                for jdx, cert in enumerate(secret['vaultCertificates']):
                    message = 'Secret is missing {0} within vaultCertificates array at secret ' \
                              'index {1} and vaultCertificate index {2} in arg {3}'
                    if 'certificateUrl' not in cert:
                        errors.append(message.format('certificateUrl', idx, jdx, idx_arg))
                    if is_windows and 'certificateStore' not in cert:
                        errors.append(message.format('certificateStore', idx, jdx, idx_arg))

    if errors:
        raise CLIError('\n'.join(errors))


# region VM Create Validators


# pylint: disable=too-many-return-statements
def _parse_image_argument(cmd, namespace):
    """ Systematically determines what type is supplied for the --image parameter. Updates the
        namespace and returns the type for subsequent processing. """
    from msrestazure.tools import is_valid_resource_id
    from msrestazure.azure_exceptions import CloudError
    import re

    # 1 - check if a fully-qualified ID (assumes it is an image ID)
    if is_valid_resource_id(namespace.image):
        return 'image_id'

    from ._vm_utils import is_shared_gallery_image_id, is_community_gallery_image_id
    if is_shared_gallery_image_id(namespace.image):
        return 'shared_gallery_image_id'

    if is_community_gallery_image_id(namespace.image):
        return 'community_gallery_image_id'

    # 2 - attempt to match an URN pattern
    urn_match = re.match('([^:]*):([^:]*):([^:]*):([^:]*)', namespace.image)
    if urn_match:
        namespace.os_publisher = urn_match.group(1)
        namespace.os_offer = urn_match.group(2)
        namespace.os_sku = urn_match.group(3)
        namespace.os_version = urn_match.group(4)

        if not any([namespace.plan_name, namespace.plan_product, namespace.plan_publisher]):
            image_plan = _get_image_plan_info_if_exists(cmd, namespace)
            if image_plan:
                namespace.plan_name = image_plan.name
                namespace.plan_product = image_plan.product
                namespace.plan_publisher = image_plan.publisher

        return 'urn'

    # 3 - unmanaged vhd based images?
    if urlparse(namespace.image).scheme and "://" in namespace.image:
        return 'uri'

    # 4 - attempt to match an URN alias (most likely)
    from azure.cli.command_modules.vm._actions import load_images_from_aliases_doc
    import requests
    try:
        images = None
        images = load_images_from_aliases_doc(cmd.cli_ctx)
        matched = next((x for x in images if x['urnAlias'].lower() == namespace.image.lower()), None)
        if matched:
            namespace.os_publisher = matched['publisher']
            namespace.os_offer = matched['offer']
            namespace.os_sku = matched['sku']
            namespace.os_version = matched['version']
            if not any([namespace.plan_name, namespace.plan_product, namespace.plan_publisher]):
                image_plan = _get_image_plan_info_if_exists(cmd, namespace)
                if image_plan:
                    namespace.plan_name = image_plan.name
                    namespace.plan_product = image_plan.product
                    namespace.plan_publisher = image_plan.publisher
            return 'urn'
    except requests.exceptions.ConnectionError:
        pass

    # 5 - check if an existing managed disk image resource
    compute_client = _compute_client_factory(cmd.cli_ctx)
    try:
        compute_client.images.get(namespace.resource_group_name, namespace.image)
        namespace.image = _get_resource_id(cmd.cli_ctx, namespace.image, namespace.resource_group_name,
                                           'images', 'Microsoft.Compute')
        return 'image_id'
    except CloudError:
        if images is not None:
            err = 'Invalid image "{}". Use a valid image URN, custom image name, custom image id, ' \
                  'VHD blob URI, or pick an image from {}.\nSee vm create -h for more information ' \
                  'on specifying an image.'.format(namespace.image, [x['urnAlias'] for x in images])
        else:
            err = 'Failed to connect to remote source of image aliases or find a local copy. Invalid image "{}". ' \
                  'Use a valid image URN, custom image name, custom image id, or VHD blob URI.\nSee vm ' \
                  'create -h for more information on specifying an image.'.format(namespace.image)
        raise CLIError(err)


def _get_image_plan_info_if_exists(cmd, namespace):
    from msrestazure.azure_exceptions import CloudError
    try:
        compute_client = _compute_client_factory(cmd.cli_ctx)
        if namespace.os_version.lower() == 'latest':
            image_version = _get_latest_image_version(cmd.cli_ctx, namespace.location, namespace.os_publisher,
                                                      namespace.os_offer, namespace.os_sku)
        else:
            image_version = namespace.os_version

        image = compute_client.virtual_machine_images.get(namespace.location,
                                                          namespace.os_publisher,
                                                          namespace.os_offer,
                                                          namespace.os_sku,
                                                          image_version)

        # pylint: disable=no-member
        return image.plan
    except CloudError as ex:
        logger.warning("Querying the image of '%s' failed for an error '%s'. Configuring plan settings "
                       "will be skipped", namespace.image, ex.message)


# pylint: disable=inconsistent-return-statements, too-many-return-statements
def _get_storage_profile_description(profile):
    if profile == StorageProfile.SACustomImage:
        return 'create unmanaged OS disk created from generalized VHD'
    if profile == StorageProfile.SAPirImage:
        return 'create unmanaged OS disk from Azure Marketplace image'
    if profile == StorageProfile.SASpecializedOSDisk:
        return 'attach to existing unmanaged OS disk'
    if profile == StorageProfile.ManagedCustomImage:
        return 'create managed OS disk from custom image'
    if profile == StorageProfile.ManagedPirImage:
        return 'create managed OS disk from Azure Marketplace image'
    if profile == StorageProfile.ManagedSpecializedOSDisk:
        return 'attach existing managed OS disk'
    if profile == StorageProfile.SharedGalleryImage:
        return 'create OS disk from shared gallery image'
    if profile == StorageProfile.CommunityGalleryImage:
        return 'create OS disk from community gallery image'


def _validate_location(cmd, namespace, zone_info, size_info):
    if not namespace.location:
        get_default_location_from_resource_group(cmd, namespace)
        if zone_info and size_info:
            sku_infos = list_sku_info(cmd.cli_ctx, namespace.location)
            temp = next((x for x in sku_infos if x.name.lower() == size_info.lower()), None)
            # For Stack (compute - 2017-03-30), Resource_sku doesn't implement location_info property
            if not hasattr(temp, 'location_info'):
                return
            if not temp or not [x for x in (temp.location_info or []) if x.zones]:
                raise CLIError("{}'s location can't be used to create the VM/VMSS because availability zone is not yet "
                               "supported. Please use '--location' to specify a capable one. 'az vm list-skus' can be "
                               "used to find such locations".format(namespace.resource_group_name))


# pylint: disable=too-many-branches, too-many-statements, too-many-locals
def _validate_vm_create_storage_profile(cmd, namespace, for_scale_set=False):
    from msrestazure.tools import parse_resource_id

    _validate_vm_vmss_create_ephemeral_placement(namespace)

    # specialized is only for image
    if getattr(namespace, 'specialized', None) is not None and namespace.image is None:
        raise CLIError('usage error: --specialized is only configurable when --image is specified.')

    # use minimal parameters to resolve the expected storage profile
    if getattr(namespace, 'attach_os_disk', None) and not namespace.image:
        if namespace.use_unmanaged_disk:
            # STORAGE PROFILE #3
            namespace.storage_profile = StorageProfile.SASpecializedOSDisk
        else:
            # STORAGE PROFILE #6
            namespace.storage_profile = StorageProfile.ManagedSpecializedOSDisk
    elif namespace.image and not getattr(namespace, 'attach_os_disk', None):
        image_type = _parse_image_argument(cmd, namespace)
        if image_type == 'uri':
            # STORAGE PROFILE #2
            namespace.storage_profile = StorageProfile.SACustomImage
        elif image_type == 'image_id':
            # STORAGE PROFILE #5
            namespace.storage_profile = StorageProfile.ManagedCustomImage
        elif image_type == 'shared_gallery_image_id':
            namespace.storage_profile = StorageProfile.SharedGalleryImage
        elif image_type == 'community_gallery_image_id':
            namespace.storage_profile = StorageProfile.CommunityGalleryImage
        elif image_type == 'urn':
            if namespace.use_unmanaged_disk:
                # STORAGE PROFILE #1
                namespace.storage_profile = StorageProfile.SAPirImage
            else:
                # STORAGE PROFILE #4
                namespace.storage_profile = StorageProfile.ManagedPirImage
        else:
            raise CLIError('Unrecognized image type: {}'.format(image_type))
    else:
        # did not specify image XOR attach-os-disk
        raise CLIError('incorrect usage: --image IMAGE | --attach-os-disk DISK')

    auth_params = ['admin_password', 'admin_username', 'authentication_type',
                   'generate_ssh_keys', 'ssh_dest_key_path', 'ssh_key_value']

    # perform parameter validation for the specific storage profile
    # start with the required/forbidden parameters for VM
    if namespace.storage_profile == StorageProfile.ManagedPirImage:
        required = ['image']
        forbidden = ['os_type', 'attach_os_disk', 'storage_account',
                     'storage_container_name', 'use_unmanaged_disk']
        if for_scale_set:
            forbidden.append('os_disk_name')

    elif namespace.storage_profile == StorageProfile.ManagedCustomImage:
        required = ['image']
        forbidden = ['os_type', 'attach_os_disk', 'storage_account',
                     'storage_container_name', 'use_unmanaged_disk']
        if for_scale_set:
            forbidden.append('os_disk_name')

    elif namespace.storage_profile == StorageProfile.SharedGalleryImage:
        required = ['image']
        forbidden = ['attach_os_disk', 'storage_account', 'storage_container_name', 'use_unmanaged_disk']

    elif namespace.storage_profile == StorageProfile.CommunityGalleryImage:
        required = ['image']
        forbidden = ['attach_os_disk', 'storage_account', 'storage_container_name', 'use_unmanaged_disk']

    elif namespace.storage_profile == StorageProfile.ManagedSpecializedOSDisk:
        required = ['os_type', 'attach_os_disk']
        forbidden = ['os_disk_name', 'os_caching', 'storage_account', 'ephemeral_os_disk',
                     'storage_container_name', 'use_unmanaged_disk', 'storage_sku'] + auth_params

    elif namespace.storage_profile == StorageProfile.SAPirImage:
        required = ['image', 'use_unmanaged_disk']
        forbidden = ['os_type', 'attach_os_disk', 'data_disk_sizes_gb', 'ephemeral_os_disk']

    elif namespace.storage_profile == StorageProfile.SACustomImage:
        required = ['image', 'os_type', 'use_unmanaged_disk']
        forbidden = ['attach_os_disk', 'data_disk_sizes_gb', 'ephemeral_os_disk']

    elif namespace.storage_profile == StorageProfile.SASpecializedOSDisk:
        required = ['os_type', 'attach_os_disk', 'use_unmanaged_disk']
        forbidden = ['os_disk_name', 'os_caching', 'image', 'storage_account', 'ephemeral_os_disk',
                     'storage_container_name', 'data_disk_sizes_gb', 'storage_sku'] + auth_params

    else:
        raise CLIError('Unrecognized storage profile: {}'.format(namespace.storage_profile))

    logger.debug("storage profile '%s'", namespace.storage_profile)

    if for_scale_set:
        # VMSS lacks some parameters, so scrub these out
        props_to_remove = ['attach_os_disk', 'storage_account']
        for prop in props_to_remove:
            if prop in required:
                required.remove(prop)
            if prop in forbidden:
                forbidden.remove(prop)

    # set default storage SKU if not provided and using an image based OS
    if not namespace.storage_sku and namespace.storage_profile in [StorageProfile.SAPirImage, StorageProfile.SACustomImage]:  # pylint: disable=line-too-long
        namespace.storage_sku = ['Standard_LRS'] if for_scale_set else ['Premium_LRS']

    if namespace.ultra_ssd_enabled is None and namespace.storage_sku:
        for sku in namespace.storage_sku:
            if 'ultrassd_lrs' in sku.lower():
                namespace.ultra_ssd_enabled = True

    # Now verify the presence of required and absence of forbidden parameters
    validate_parameter_set(
        namespace, required, forbidden,
        description='storage profile: {}:'.format(_get_storage_profile_description(namespace.storage_profile)))

    image_data_disks = []
    if namespace.storage_profile == StorageProfile.ManagedCustomImage:
        # extract additional information from a managed custom image
        res = parse_resource_id(namespace.image)
        namespace.aux_subscriptions = [res['subscription']]
        compute_client = _compute_client_factory(cmd.cli_ctx, subscription_id=res['subscription'])
        if res['type'].lower() == 'images':
            image_info = compute_client.images.get(res['resource_group'], res['name'])
            namespace.os_type = image_info.storage_profile.os_disk.os_type
            image_data_disks = image_info.storage_profile.data_disks or []
            image_data_disks = [{'lun': disk.lun} for disk in image_data_disks]

        elif res['type'].lower() == 'galleries':
            image_info = compute_client.gallery_images.get(resource_group_name=res['resource_group'],
                                                           gallery_name=res['name'],
                                                           gallery_image_name=res['child_name_1'])
            namespace.os_type = image_info.os_type
            gallery_image_version = res.get('child_name_2', '')
            if gallery_image_version.lower() in ['latest', '']:
                image_version_infos = compute_client.gallery_image_versions.list_by_gallery_image(
                    resource_group_name=res['resource_group'], gallery_name=res['name'],
                    gallery_image_name=res['child_name_1'])
                image_version_infos = [x for x in image_version_infos if not x.publishing_profile.exclude_from_latest]
                if not image_version_infos:
                    raise CLIError('There is no latest image version exists for "{}"'.format(namespace.image))
                image_version_info = sorted(image_version_infos, key=lambda x: x.publishing_profile.published_date)[-1]
            else:
                image_version_info = compute_client.gallery_image_versions.get(
                    resource_group_name=res['resource_group'], gallery_name=res['name'],
                    gallery_image_name=res['child_name_1'], gallery_image_version_name=res['child_name_2'])
            image_data_disks = image_version_info.storage_profile.data_disk_images or []
            image_data_disks = [{'lun': disk.lun} for disk in image_data_disks]

        else:
            raise CLIError('usage error: unrecognized image information "{}"'.format(namespace.image))

        # pylint: disable=no-member

    elif namespace.storage_profile == StorageProfile.ManagedSpecializedOSDisk:
        # accept disk name or ID
        namespace.attach_os_disk = _get_resource_id(
            cmd.cli_ctx, namespace.attach_os_disk, namespace.resource_group_name, 'disks', 'Microsoft.Compute')

    if getattr(namespace, 'attach_data_disks', None):
        if not namespace.use_unmanaged_disk:
            namespace.attach_data_disks = [_get_resource_id(cmd.cli_ctx, d, namespace.resource_group_name, 'disks',
                                                            'Microsoft.Compute') for d in namespace.attach_data_disks]

    if namespace.storage_profile == StorageProfile.SharedGalleryImage:

        if namespace.location is None:
            raise RequiredArgumentMissingError(
                'Please input the location of the shared gallery image through the parameter --location.')

        from ._vm_utils import parse_shared_gallery_image_id
        image_info = parse_shared_gallery_image_id(namespace.image)

        from ._client_factory import cf_shared_gallery_image
        shared_gallery_image_info = cf_shared_gallery_image(cmd.cli_ctx).get(
            location=namespace.location, gallery_unique_name=image_info[0], gallery_image_name=image_info[1])

        if namespace.os_type and namespace.os_type.lower() != shared_gallery_image_info.os_type.lower():
            raise ArgumentUsageError("The --os-type is not the correct os type of this shared gallery image, "
                                     "the os type of this image should be {}".format(shared_gallery_image_info.os_type))
        namespace.os_type = shared_gallery_image_info.os_type

    if namespace.storage_profile == StorageProfile.CommunityGalleryImage:

        if namespace.location is None:
            raise RequiredArgumentMissingError(
                'Please input the location of the community gallery image through the parameter --location.')

        from ._vm_utils import parse_community_gallery_image_id
        image_info = parse_community_gallery_image_id(namespace.image)

        from ._client_factory import cf_community_gallery_image
        community_gallery_image_info = cf_community_gallery_image(cmd.cli_ctx).get(
            location=namespace.location, public_gallery_name=image_info[0], gallery_image_name=image_info[1])

        if namespace.os_type and namespace.os_type.lower() != community_gallery_image_info.os_type.lower():
            raise ArgumentUsageError(
                "The --os-type is not the correct os type of this community gallery image, "
                "the os type of this image should be {}".format(community_gallery_image_info.os_type))
        namespace.os_type = community_gallery_image_info.os_type

    if not namespace.os_type:
        namespace.os_type = 'windows' if 'windows' in namespace.os_offer.lower() else 'linux'

    from ._vm_utils import normalize_disk_info
    # attach_data_disks are not exposed yet for VMSS, so use 'getattr' to avoid crash
    vm_size = (getattr(namespace, 'size', None) or getattr(namespace, 'vm_sku', None))

    # pylint: disable=line-too-long
    namespace.disk_info = normalize_disk_info(size=vm_size,
                                              image_data_disks=image_data_disks,
                                              data_disk_sizes_gb=namespace.data_disk_sizes_gb,
                                              attach_data_disks=getattr(namespace, 'attach_data_disks', []),
                                              storage_sku=namespace.storage_sku,
                                              os_disk_caching=namespace.os_caching,
                                              data_disk_cachings=namespace.data_caching,
                                              ephemeral_os_disk=getattr(namespace, 'ephemeral_os_disk', None),
                                              ephemeral_os_disk_placement=getattr(namespace, 'ephemeral_os_disk_placement', None),
                                              data_disk_delete_option=getattr(
                                                  namespace, 'data_disk_delete_option', None))


def _validate_vm_create_storage_account(cmd, namespace):
    from msrestazure.tools import parse_resource_id
    if namespace.storage_account:
        storage_id = parse_resource_id(namespace.storage_account)
        rg = storage_id.get('resource_group', namespace.resource_group_name)
        if check_existence(cmd.cli_ctx, storage_id['name'], rg, 'Microsoft.Storage', 'storageAccounts'):
            # 1 - existing storage account specified
            namespace.storage_account_type = 'existing'
            logger.debug("using specified existing storage account '%s'", storage_id['name'])
        else:
            # 2 - params for new storage account specified
            namespace.storage_account_type = 'new'
            logger.debug("specified storage account '%s' not found and will be created", storage_id['name'])
    else:
        from azure.cli.core.profiles import ResourceType
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        storage_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_STORAGE).storage_accounts

        # find storage account in target resource group that matches the VM's location
        sku_tier = 'Standard'
        for sku in namespace.storage_sku:
            if 'Premium' in sku:
                sku_tier = 'Premium'
                break

        account = next(
            (a for a in storage_client.list_by_resource_group(namespace.resource_group_name)
             if a.sku.tier == sku_tier and a.location == namespace.location), None)

        if account:
            # 3 - nothing specified - find viable storage account in target resource group
            namespace.storage_account = account.name
            namespace.storage_account_type = 'existing'
            logger.debug("suitable existing storage account '%s' will be used", account.name)
        else:
            # 4 - nothing specified - create a new storage account
            namespace.storage_account_type = 'new'
            logger.debug('no suitable storage account found. One will be created.')


def _validate_vm_create_availability_set(cmd, namespace):
    from msrestazure.tools import parse_resource_id, resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id
    if namespace.availability_set:
        as_id = parse_resource_id(namespace.availability_set)
        name = as_id['name']
        rg = as_id.get('resource_group', namespace.resource_group_name)

        if not check_existence(cmd.cli_ctx, name, rg, 'Microsoft.Compute', 'availabilitySets'):
            raise CLIError("Availability set '{}' does not exist.".format(name))

        namespace.availability_set = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=rg,
            namespace='Microsoft.Compute',
            type='availabilitySets',
            name=name)
        logger.debug("adding to specified availability set '%s'", namespace.availability_set)


def _validate_vm_create_vmss(cmd, namespace):
    from msrestazure.tools import parse_resource_id, resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id
    if namespace.vmss:
        as_id = parse_resource_id(namespace.vmss)
        name = as_id['name']
        rg = as_id.get('resource_group', namespace.resource_group_name)

        if not check_existence(cmd.cli_ctx, name, rg, 'Microsoft.Compute', 'virtualMachineScaleSets'):
            raise CLIError("virtual machine scale set '{}' does not exist.".format(name))

        namespace.vmss = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=rg,
            namespace='Microsoft.Compute',
            type='virtualMachineScaleSets',
            name=name)
        logger.debug("adding to specified virtual machine scale set '%s'", namespace.vmss)


def _validate_vm_create_dedicated_host(cmd, namespace):
    """
    "host": {
      "$ref": "#/definitions/SubResource",
      "description": "Specifies information about the dedicated host that the virtual machine resides in.
      <br><br>Minimum api-version: 2018-10-01."
    },
    "hostGroup": {
      "$ref": "#/definitions/SubResource",
      "description": "Specifies information about the dedicated host group that the virtual machine resides in.
      <br><br>Minimum api-version: 2020-06-01. <br><br>NOTE: User cannot specify both host and hostGroup properties."
    }

    :param cmd:
    :param namespace:
    :return:
    """
    from msrestazure.tools import resource_id, is_valid_resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id

    if namespace.dedicated_host and namespace.dedicated_host_group:
        raise CLIError('usage error: User cannot specify both --host and --host-group properties.')

    if namespace.dedicated_host and not is_valid_resource_id(namespace.dedicated_host) and namespace.dedicated_host != DEDICATED_HOST_NONE:
        raise CLIError('usage error: --host is not a valid resource ID.')

    if namespace.dedicated_host_group:
        if not is_valid_resource_id(namespace.dedicated_host_group):
            namespace.dedicated_host_group = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx), resource_group=namespace.resource_group_name,
                namespace='Microsoft.Compute', type='hostGroups', name=namespace.dedicated_host_group
            )


def _validate_vm_vmss_create_vnet(cmd, namespace, for_scale_set=False):
    from msrestazure.tools import is_valid_resource_id
    vnet = namespace.vnet_name
    subnet = namespace.subnet
    rg = namespace.resource_group_name
    location = namespace.location
    nics = getattr(namespace, 'nics', None)

    if vnet and '/' in vnet:
        raise CLIError("incorrect usage: --subnet ID | --subnet NAME --vnet-name NAME")

    if not vnet and not subnet and not nics:
        logger.debug('no subnet specified. Attempting to find an existing Vnet and subnet...')

        # if nothing specified, try to find an existing vnet and subnet in the target resource group
        client = get_network_client(cmd.cli_ctx).virtual_networks

        # find VNET in target resource group that matches the VM's location with a matching subnet
        for vnet_match in (v for v in client.list(rg) if v.location == location and v.subnets):

            # 1 - find a suitable existing vnet/subnet
            result = None
            if not for_scale_set:
                result = next((s for s in vnet_match.subnets if s.name.lower() != 'gatewaysubnet'), None)
            else:
                def _check_subnet(s):
                    if s.name.lower() == 'gatewaysubnet':
                        return False
                    subnet_mask = s.address_prefix.split('/')[-1]
                    return _subnet_capacity_check(subnet_mask, namespace.instance_count,
                                                  not namespace.disable_overprovision)

                result = next((s for s in vnet_match.subnets if _check_subnet(s)), None)
            if not result:
                continue
            namespace.subnet = result.name
            namespace.vnet_name = vnet_match.name
            namespace.vnet_type = 'existing'
            logger.debug("existing vnet '%s' and subnet '%s' found", namespace.vnet_name, namespace.subnet)
            return

    if subnet:
        subnet_is_id = is_valid_resource_id(subnet)
        if (subnet_is_id and vnet) or (not subnet_is_id and not vnet):
            raise CLIError("incorrect usage: --subnet ID | --subnet NAME --vnet-name NAME")

        subnet_exists = \
            check_existence(cmd.cli_ctx, subnet, rg, 'Microsoft.Network', 'subnets', vnet, 'virtualNetworks')

        if subnet_is_id and not subnet_exists:
            raise CLIError("Subnet '{}' does not exist.".format(subnet))
        if subnet_exists:
            # 2 - user specified existing vnet/subnet
            namespace.vnet_type = 'existing'
            logger.debug("using specified vnet '%s' and subnet '%s'", namespace.vnet_name, namespace.subnet)
            return
    # 3 - create a new vnet/subnet
    namespace.vnet_type = 'new'
    logger.debug('no suitable subnet found. One will be created.')


def _subnet_capacity_check(subnet_mask, vmss_instance_count, over_provision):
    mask = int(subnet_mask)
    # '2' are the reserved broadcasting addresses
    # '*1.5' so we have enough leeway for over-provision
    factor = 1.5 if over_provision else 1
    return ((1 << (32 - mask)) - 2) > int(vmss_instance_count * factor)


def _validate_vm_vmss_accelerated_networking(cli_ctx, namespace):
    if namespace.accelerated_networking is None:
        size = getattr(namespace, 'size', None) or getattr(namespace, 'vm_sku', None)
        size = size.lower()

        # Use the following code to refresh the list
        # skus = list_sku_info(cli_ctx, namespace.location)
        # aval_sizes = [x.name.lower() for x in skus if x.resource_type == 'virtualMachines' and
        #               any(c.name == 'AcceleratedNetworkingEnabled' and c.value == 'True' for c in x.capabilities)]

        aval_sizes = ['standard_b12ms', 'standard_b16ms', 'standard_b20ms', 'standard_ds2_v2', 'standard_ds3_v2',
                      'standard_ds4_v2', 'standard_ds5_v2', 'standard_ds11-1_v2', 'standard_ds11_v2',
                      'standard_ds12-1_v2', 'standard_ds12-2_v2', 'standard_ds12_v2', 'standard_ds13-2_v2',
                      'standard_ds13-4_v2', 'standard_ds13_v2', 'standard_ds14-4_v2', 'standard_ds14-8_v2',
                      'standard_ds14_v2', 'standard_ds15_v2', 'standard_ds2_v2_promo', 'standard_ds3_v2_promo',
                      'standard_ds4_v2_promo', 'standard_ds5_v2_promo', 'standard_ds11_v2_promo',
                      'standard_ds12_v2_promo', 'standard_ds13_v2_promo', 'standard_ds14_v2_promo', 'standard_f2s',
                      'standard_f4s', 'standard_f8s', 'standard_f16s', 'standard_d4s_v3', 'standard_d8s_v3',
                      'standard_d16s_v3', 'standard_d32s_v3', 'standard_d2_v2', 'standard_d3_v2', 'standard_d4_v2',
                      'standard_d5_v2', 'standard_d11_v2', 'standard_d12_v2', 'standard_d13_v2', 'standard_d14_v2',
                      'standard_d15_v2', 'standard_d2_v2_promo', 'standard_d3_v2_promo', 'standard_d4_v2_promo',
                      'standard_d5_v2_promo', 'standard_d11_v2_promo', 'standard_d12_v2_promo', 'standard_d13_v2_promo',
                      'standard_d14_v2_promo', 'standard_f2', 'standard_f4', 'standard_f8', 'standard_f16',
                      'standard_d4_v3', 'standard_d8_v3', 'standard_d16_v3', 'standard_d32_v3', 'standard_d48_v3',
                      'standard_d64_v3', 'standard_d48s_v3', 'standard_d64s_v3', 'standard_e4_v3', 'standard_e8_v3',
                      'standard_e16_v3', 'standard_e20_v3', 'standard_e32_v3', 'standard_e48_v3', 'standard_e64i_v3',
                      'standard_e64_v3', 'standard_e4-2s_v3', 'standard_e4s_v3', 'standard_e8-2s_v3',
                      'standard_e8-4s_v3', 'standard_e8s_v3', 'standard_e16-4s_v3', 'standard_e16-8s_v3',
                      'standard_e16s_v3', 'standard_e20s_v3', 'standard_e32-8s_v3', 'standard_e32-16s_v3',
                      'standard_e32s_v3', 'standard_e48s_v3', 'standard_e64-16s_v3', 'standard_e64-32s_v3',
                      'standard_e64is_v3', 'standard_e64s_v3', 'standard_l8s_v2', 'standard_l16s_v2',
                      'standard_l32s_v2', 'standard_l48s_v2', 'standard_l64s_v2', 'standard_l80s_v2', 'standard_e4_v4',
                      'standard_e8_v4', 'standard_e16_v4', 'standard_e20_v4', 'standard_e32_v4', 'standard_e48_v4',
                      'standard_e64_v4', 'standard_e4d_v4', 'standard_e8d_v4', 'standard_e16d_v4', 'standard_e20d_v4',
                      'standard_e32d_v4', 'standard_e48d_v4', 'standard_e64d_v4', 'standard_e4-2s_v4',
                      'standard_e4s_v4', 'standard_e8-2s_v4', 'standard_e8-4s_v4', 'standard_e8s_v4',
                      'standard_e16-4s_v4', 'standard_e16-8s_v4', 'standard_e16s_v4', 'standard_e20s_v4',
                      'standard_e32-8s_v4', 'standard_e32-16s_v4', 'standard_e32s_v4', 'standard_e48s_v4',
                      'standard_e64-16s_v4', 'standard_e64-32s_v4', 'standard_e64s_v4', 'standard_e4-2ds_v4',
                      'standard_e4ds_v4', 'standard_e8-2ds_v4', 'standard_e8-4ds_v4', 'standard_e8ds_v4',
                      'standard_e16-4ds_v4', 'standard_e16-8ds_v4', 'standard_e16ds_v4', 'standard_e20ds_v4',
                      'standard_e32-8ds_v4', 'standard_e32-16ds_v4', 'standard_e32ds_v4', 'standard_e48ds_v4',
                      'standard_e64-16ds_v4', 'standard_e64-32ds_v4', 'standard_e64ds_v4', 'standard_d4d_v4',
                      'standard_d8d_v4', 'standard_d16d_v4', 'standard_d32d_v4', 'standard_d48d_v4', 'standard_d64d_v4',
                      'standard_d4_v4', 'standard_d8_v4', 'standard_d16_v4', 'standard_d32_v4', 'standard_d48_v4',
                      'standard_d64_v4', 'standard_d4ds_v4', 'standard_d8ds_v4', 'standard_d16ds_v4',
                      'standard_d32ds_v4', 'standard_d48ds_v4', 'standard_d64ds_v4', 'standard_d4s_v4',
                      'standard_d8s_v4', 'standard_d16s_v4', 'standard_d32s_v4', 'standard_d48s_v4', 'standard_d64s_v4',
                      'standard_f4s_v2', 'standard_f8s_v2', 'standard_f16s_v2', 'standard_f32s_v2', 'standard_f48s_v2',
                      'standard_f64s_v2', 'standard_f72s_v2', 'standard_m208ms_v2', 'standard_m208s_v2',
                      'standard_m416-208s_v2', 'standard_m416s_v2', 'standard_m416-208ms_v2', 'standard_m416ms_v2',
                      'standard_m64', 'standard_m64m', 'standard_m128', 'standard_m128m', 'standard_m8-2ms',
                      'standard_m8-4ms', 'standard_m8ms', 'standard_m16-4ms', 'standard_m16-8ms', 'standard_m16ms',
                      'standard_m32-8ms', 'standard_m32-16ms', 'standard_m32ls', 'standard_m32ms', 'standard_m32ts',
                      'standard_m64-16ms', 'standard_m64-32ms', 'standard_m64ls', 'standard_m64ms', 'standard_m64s',
                      'standard_m128-32ms', 'standard_m128-64ms', 'standard_m128ms', 'standard_m128s',
                      'standard_d4a_v4', 'standard_d8a_v4', 'standard_d16a_v4', 'standard_d32a_v4', 'standard_d48a_v4',
                      'standard_d64a_v4', 'standard_d96a_v4', 'standard_d4as_v4', 'standard_d8as_v4',
                      'standard_d16as_v4', 'standard_d32as_v4', 'standard_d48as_v4', 'standard_d64as_v4',
                      'standard_d96as_v4', 'standard_e4a_v4', 'standard_e8a_v4', 'standard_e16a_v4', 'standard_e20a_v4',
                      'standard_e32a_v4', 'standard_e48a_v4', 'standard_e64a_v4', 'standard_e96a_v4',
                      'standard_e4as_v4', 'standard_e8as_v4', 'standard_e16as_v4', 'standard_e20as_v4',
                      'standard_e32as_v4', 'standard_e48as_v4', 'standard_e64as_v4', 'standard_e96as_v4']
        if size not in aval_sizes:
            return

        new_4core_sizes = ['Standard_D3_v2', 'Standard_D3_v2_Promo', 'Standard_D3_v2_ABC', 'Standard_DS3_v2',
                           'Standard_DS3_v2_Promo', 'Standard_D12_v2', 'Standard_D12_v2_Promo', 'Standard_D12_v2_ABC',
                           'Standard_DS12_v2', 'Standard_DS12_v2_Promo', 'Standard_F8s_v2', 'Standard_F4',
                           'Standard_F4_ABC', 'Standard_F4s', 'Standard_E8_v3', 'Standard_E8s_v3', 'Standard_D8_v3',
                           'Standard_D8s_v3']
        new_4core_sizes = [x.lower() for x in new_4core_sizes]
        if size not in new_4core_sizes:
            compute_client = _compute_client_factory(cli_ctx)
            sizes = compute_client.virtual_machine_sizes.list(namespace.location)
            size_info = next((s for s in sizes if s.name.lower() == size), None)
            if size_info is None or size_info.number_of_cores < 8:
                return

        # VMs need to be a supported image in the marketplace
        # Ubuntu 16.04 | 18.04, SLES 12 SP3, RHEL 7.4, CentOS 7.4, Flatcar, Debian "Stretch" with backports kernel
        # Oracle Linux 7.4, Windows Server 2016, Windows Server 2012R2
        publisher, offer, sku = namespace.os_publisher, namespace.os_offer, namespace.os_sku
        if not publisher:
            return
        publisher, offer, sku = publisher.lower(), offer.lower(), sku.lower()

        if publisher == 'coreos' or offer == 'coreos':
            from azure.cli.core.parser import InvalidArgumentValueError
            raise InvalidArgumentValueError("As CoreOS is deprecated and there is no image in the marketplace any more,"
                                            " please use Flatcar Container Linux instead.")

        distros = [('canonical', 'UbuntuServer', '^16.04|^18.04'),
                   ('suse', 'sles', '^12-sp3'), ('redhat', 'rhel', '^7.4'),
                   ('openlogic', 'centos', '^7.4'), ('kinvolk', 'flatcar-container-linux-free', None),
                   ('kinvolk', 'flatcar-container-linux', None), ('credativ', 'debian', '-backports'),
                   ('oracle', 'oracle-linux', '^7.4'), ('MicrosoftWindowsServer', 'WindowsServer', '^2016'),
                   ('MicrosoftWindowsServer', 'WindowsServer', '^2012-R2')]
        import re
        for p, o, s in distros:
            if p.lower() == publisher and (o is None or o.lower() == offer) and (s is None or re.match(s, sku, re.I)):
                namespace.accelerated_networking = True


def _validate_vmss_create_subnet(namespace):
    if namespace.vnet_type == 'new':
        if namespace.subnet_address_prefix is None:
            cidr = namespace.vnet_address_prefix.split('/', 1)[0]
            i = 0
            for i in range(24, 16, -1):
                if _subnet_capacity_check(i, namespace.instance_count, not namespace.disable_overprovision):
                    break
            if i < 16:
                err = "instance count '{}' is out of range of 2^16 subnet size'"
                raise CLIError(err.format(namespace.instance_count))
            namespace.subnet_address_prefix = '{}/{}'.format(cidr, i)

        if namespace.app_gateway_type and namespace.app_gateway_subnet_address_prefix is None:
            namespace.app_gateway_subnet_address_prefix = _get_next_subnet_addr_suffix(
                namespace.vnet_address_prefix, namespace.subnet_address_prefix, 24)


def _get_next_subnet_addr_suffix(vnet_cidr, subnet_cidr, new_mask):
    def _convert_to_int(address, bit_mask_len):
        a, b, c, d = [int(x) for x in address.split('.')]
        result = '{0:08b}{1:08b}{2:08b}{3:08b}'.format(a, b, c, d)
        return int(result[:-bit_mask_len], 2)

    error_msg = "usage error: --subnet-address-prefix value should be a subrange of --vnet-address-prefix's"
    # extract vnet information needed to verify the defaults we are coming out
    vnet_ip_address, mask = vnet_cidr.split('/')
    vnet_bit_mask_len = 32 - int(mask)
    vnet_int = _convert_to_int(vnet_ip_address, vnet_bit_mask_len)

    subnet_ip_address, mask = subnet_cidr.split('/')
    subnet_bit_mask_len = 32 - int(mask)

    if vnet_bit_mask_len <= subnet_bit_mask_len:
        raise CLIError(error_msg)

    candidate_int = _convert_to_int(subnet_ip_address, subnet_bit_mask_len) + 1
    if (candidate_int >> (vnet_bit_mask_len - subnet_bit_mask_len)) > vnet_int:  # overflows?
        candidate_int = candidate_int - 2  # try the other way around
        if (candidate_int >> (vnet_bit_mask_len - subnet_bit_mask_len)) > vnet_int:
            raise CLIError(error_msg)

    # format back to the cidr
    candaidate_str = '{0:32b}'.format(candidate_int << subnet_bit_mask_len)
    return '{0}.{1}.{2}.{3}/{4}'.format(int(candaidate_str[0:8], 2), int(candaidate_str[8:16], 2),
                                        int(candaidate_str[16:24], 2), int(candaidate_str[24:32], 2),
                                        new_mask)


def _validate_vm_create_nsg(cmd, namespace):

    if namespace.nsg:
        if check_existence(cmd.cli_ctx, namespace.nsg, namespace.resource_group_name,
                           'Microsoft.Network', 'networkSecurityGroups'):
            namespace.nsg_type = 'existing'
            logger.debug("using specified NSG '%s'", namespace.nsg)
        else:
            namespace.nsg_type = 'new'
            logger.debug("specified NSG '%s' not found. It will be created.", namespace.nsg)
    elif namespace.nsg == '':
        namespace.nsg_type = None
        logger.debug('no NSG will be used')
    elif namespace.nsg is None:
        namespace.nsg_type = 'new'
        logger.debug('new NSG will be created')


def _validate_vmss_create_nsg(cmd, namespace):
    if namespace.nsg:
        namespace.nsg = _get_resource_id(cmd.cli_ctx, namespace.nsg, namespace.resource_group_name,
                                         'networkSecurityGroups', 'Microsoft.Network')


def _validate_vm_vmss_create_public_ip(cmd, namespace):
    if namespace.public_ip_address:
        if check_existence(cmd.cli_ctx, namespace.public_ip_address, namespace.resource_group_name,
                           'Microsoft.Network', 'publicIPAddresses'):
            namespace.public_ip_address_type = 'existing'
            logger.debug("using existing specified public IP '%s'", namespace.public_ip_address)
        else:
            namespace.public_ip_address_type = 'new'
            logger.debug("specified public IP '%s' not found. It will be created.", namespace.public_ip_address)
    elif namespace.public_ip_address == '':
        namespace.public_ip_address_type = None
        logger.debug('no public IP address will be used')
    elif namespace.public_ip_address is None:
        namespace.public_ip_address_type = 'new'
        logger.debug('new public IP address will be created')

    from azure.cli.core.profiles import ResourceType
    PublicIPAddressSkuName, IPAllocationMethod = cmd.get_models('PublicIPAddressSkuName', 'IPAllocationMethod',
                                                                resource_type=ResourceType.MGMT_NETWORK)
    # Use standard public IP address automatically when using zones.
    if hasattr(namespace, 'zone') and namespace.zone is not None:
        namespace.public_ip_sku = PublicIPAddressSkuName.standard.value

    # Public-IP SKU is only exposed for VM. VMSS has no such needs so far
    if getattr(namespace, 'public_ip_sku', None):
        if namespace.public_ip_sku == PublicIPAddressSkuName.standard.value:
            if not namespace.public_ip_address_allocation:
                namespace.public_ip_address_allocation = IPAllocationMethod.static.value


def _validate_vmss_create_public_ip(cmd, namespace):
    if namespace.load_balancer_type is None and namespace.app_gateway_type is None:
        if namespace.public_ip_address:
            raise CLIError('--public-ip-address can only be used when creating a new load '
                           'balancer or application gateway frontend.')
        namespace.public_ip_address = ''
    _validate_vm_vmss_create_public_ip(cmd, namespace)


def validate_delete_options(resources, delete_option):
    """ Extracts multiple space-separated delete_option in key[=value] format """
    if resources and isinstance(delete_option, list):
        if len(delete_option) == 1 and len(delete_option[0].split('=', 1)) == 1:
            return delete_option[0]
        delete_option_dict = {}
        for item in delete_option:
            delete_option_dict.update(validate_delete_option(item))
        return delete_option_dict
    return None


def validate_delete_option(string):
    """ Extracts a single delete_option in key[=value] format """
    from azure.cli.core.azclierror import InvalidArgumentValueError
    result = {}
    if string:
        comps = string.split('=', 1)
        if len(comps) == 2:
            result = {comps[0]: comps[1]}
        else:
            raise InvalidArgumentValueError(
                "Invalid value for delete option. Use a singular value to apply on all resources, or use "
                "<Name>=<Value> to configure the delete behavior for individual resources.")
    return result


def _validate_vm_create_nics(cmd, namespace):
    from msrestazure.tools import resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id
    nic_ids = namespace.nics
    delete_option = validate_delete_options(nic_ids, getattr(namespace, 'nic_delete_option', None))
    nics = []

    if not nic_ids:
        namespace.nic_type = 'new'
        logger.debug('new NIC will be created')
        return

    if not isinstance(nic_ids, list):
        nic_ids = [nic_ids]

    for n in nic_ids:
        nic = {'id': n if '/' in n else resource_id(name=n,
                                                    resource_group=namespace.resource_group_name,
                                                    namespace='Microsoft.Network',
                                                    type='networkInterfaces',
                                                    subscription=get_subscription_id(cmd.cli_ctx)),
               'properties': {'primary': nic_ids[0] == n}
               }
        if delete_option:
            nic['properties']['deleteOption'] = delete_option if isinstance(delete_option, str) else \
                delete_option.get(n, None)
        nics.append(nic)

    namespace.nics = nics
    namespace.nic_type = 'existing'
    namespace.public_ip_address_type = None
    logger.debug('existing NIC(s) will be used')


def _validate_vm_nic_delete_option(namespace):
    if not namespace.nics and namespace.nic_delete_option:
        if len(namespace.nic_delete_option) == 1 and len(namespace.nic_delete_option[0].split('=')) == 1:  # pylint: disable=line-too-long
            namespace.nic_delete_option = namespace.nic_delete_option[0]
        elif len(namespace.nic_delete_option) > 1 or any((len(delete_option.split('=')) > 1 for delete_option in namespace.nic_delete_option)):  # pylint: disable=line-too-long
            from azure.cli.core.parser import InvalidArgumentValueError
            raise InvalidArgumentValueError("incorrect usage: Cannot specify individual delete option when no nic is "
                                            "specified. Either specify a list of nics and their delete option like: "
                                            "--nics nic1 nic2 --nic-delete-option nic1=Delete nic2=Detach or specify "
                                            "delete option for all: --nics nic1 nic2 --nic-delete-option Delete or "
                                            "specify delete option for the new nic created: --nic-delete-option Delete")


def _validate_vm_vmss_create_auth(namespace, cmd=None):
    if namespace.storage_profile in [StorageProfile.ManagedSpecializedOSDisk,
                                     StorageProfile.SASpecializedOSDisk]:
        return

    if namespace.admin_username is None:
        namespace.admin_username = get_default_admin_username()
    if namespace.admin_username and namespace.os_type:
        namespace.admin_username = _validate_admin_username(namespace.admin_username, namespace.os_type)

    # if not namespace.os_type:
    #     raise CLIError("Unable to resolve OS type. Specify '--os-type' argument.")

    if not namespace.authentication_type:
        # if both ssh key and password, infer that authentication_type is all.
        if namespace.ssh_key_value and namespace.admin_password:
            namespace.authentication_type = 'all'
        else:
            # apply default auth type (password for Windows, ssh for Linux) by examining the OS type
            namespace.authentication_type = 'password' \
                if ((namespace.os_type and namespace.os_type.lower() == 'windows') or
                    namespace.admin_password) else 'ssh'

    if namespace.os_type and namespace.os_type.lower() == 'windows' and namespace.authentication_type == 'ssh':
        raise CLIError('SSH not supported for Windows VMs.')

    # validate proper arguments supplied based on the authentication type
    if namespace.authentication_type == 'password':
        if namespace.ssh_key_value or namespace.ssh_dest_key_path:
            raise CLIError('SSH key cannot be used with password authentication type.')

        # if password not given, attempt to prompt user for password.
        if not namespace.admin_password:
            _prompt_for_password(namespace)

        # validate password
        _validate_admin_password(namespace.admin_password, namespace.os_type)

    elif namespace.authentication_type == 'ssh':

        if namespace.admin_password:
            raise CLIError('Admin password cannot be used with SSH authentication type.')

        validate_ssh_key(namespace, cmd)

        if not namespace.ssh_dest_key_path:
            namespace.ssh_dest_key_path = '/home/{}/.ssh/authorized_keys'.format(namespace.admin_username)

    elif namespace.authentication_type == 'all':
        if namespace.os_type and namespace.os_type.lower() == 'windows':
            raise CLIError('SSH not supported for Windows VMs. Use password authentication.')

        if not namespace.admin_password:
            _prompt_for_password(namespace)
        _validate_admin_password(namespace.admin_password, namespace.os_type)

        validate_ssh_key(namespace, cmd)
        if not namespace.ssh_dest_key_path:
            namespace.ssh_dest_key_path = '/home/{}/.ssh/authorized_keys'.format(namespace.admin_username)


def _prompt_for_password(namespace):
    from knack.prompting import prompt_pass, NoTTYException
    try:
        namespace.admin_password = prompt_pass('Admin Password: ', confirm=True)
    except NoTTYException:
        raise CLIError('Please specify password in non-interactive mode.')


def _validate_admin_username(username, os_type):
    import re
    if not username:
        raise CLIError("admin user name can not be empty")
    is_linux = (os_type.lower() == 'linux')
    # pylint: disable=line-too-long
    pattern = (r'[\\\/"\[\]:|<>+=;,?*@#()!A-Z]+' if is_linux else r'[\\\/"\[\]:|<>+=;,?*@]+')
    linux_err = r'admin user name cannot contain upper case character A-Z, special characters \/"[]:|<>+=;,?*@#()! or start with $ or -'
    win_err = r'admin user name cannot contain special characters \/"[]:|<>+=;,?*@# or ends with .'
    if re.findall(pattern, username):
        raise CLIError(linux_err if is_linux else win_err)
    if is_linux and re.findall(r'^[$-]+', username):
        raise CLIError(linux_err)
    if not is_linux and username.endswith('.'):
        raise CLIError(win_err)
    if username.lower() in DISALLOWED_USER_NAMES:
        raise CLIError("This user name '{}' meets the general requirements, but is specifically disallowed for this image. Please try a different value.".format(username))
    return username


def _validate_admin_password(password, os_type):
    import re
    is_linux = (os_type.lower() == 'linux')
    max_length = 72 if is_linux else 123
    min_length = 12

    contains_lower = re.findall('[a-z]+', password)
    contains_upper = re.findall('[A-Z]+', password)
    contains_digit = re.findall('[0-9]+', password)
    contains_special_char = re.findall(r'[ `~!@#$%^&*()=+_\[\]{}\|;:.\/\'\",<>?]+', password)
    count = len([x for x in [contains_lower, contains_upper,
                             contains_digit, contains_special_char] if x])

    # pylint: disable=line-too-long
    error_msg = ("The password length must be between {} and {}. Password must have the 3 of the following: "
                 "1 lower case character, 1 upper case character, 1 number and 1 special character.").format(min_length, max_length)
    if len(password) not in range(min_length, max_length + 1) or count < 3:
        raise CLIError(error_msg)


def validate_ssh_key(namespace, cmd=None):
    from azure.core.exceptions import HttpResponseError
    if hasattr(namespace, 'ssh_key_name') and namespace.ssh_key_name:
        client = _compute_client_factory(cmd.cli_ctx)
        # --ssh-key-name
        if not namespace.ssh_key_value and not namespace.generate_ssh_keys:
            # Use existing key, key must exist
            try:
                ssh_key_resource = client.ssh_public_keys.get(namespace.resource_group_name, namespace.ssh_key_name)
            except HttpResponseError:
                raise ValidationError('SSH key {} does not exist!'.format(namespace.ssh_key_name))
            namespace.ssh_key_value = [ssh_key_resource.public_key]
            logger.info('Get a key from --ssh-key-name successfully')
        elif namespace.ssh_key_value:
            raise ValidationError('--ssh-key-name and --ssh-key-values cannot be used together')
        elif namespace.generate_ssh_keys:
            parameters = {}
            parameters['location'] = namespace.location
            public_key = _validate_ssh_key_helper("", namespace.generate_ssh_keys)
            parameters['public_key'] = public_key
            client.ssh_public_keys.create(resource_group_name=namespace.resource_group_name,
                                          ssh_public_key_name=namespace.ssh_key_name,
                                          parameters=parameters)
            namespace.ssh_key_value = [public_key]
    elif namespace.ssh_key_value:
        if namespace.generate_ssh_keys and len(namespace.ssh_key_value) > 1:
            logger.warning("Ignoring --generate-ssh-keys as multiple ssh key values have been specified.")
            namespace.generate_ssh_keys = False

        processed_ssh_key_values = []
        for ssh_key_value in namespace.ssh_key_value:
            processed_ssh_key_values.append(_validate_ssh_key_helper(ssh_key_value, namespace.generate_ssh_keys))
        namespace.ssh_key_value = processed_ssh_key_values
    # if no ssh keys processed, try to generate new key / use existing at root.
    else:
        namespace.ssh_key_value = [_validate_ssh_key_helper("", namespace.generate_ssh_keys)]


def _validate_ssh_key_helper(ssh_key_value, should_generate_ssh_keys):
    string_or_file = (ssh_key_value or
                      os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub'))
    content = string_or_file
    if os.path.exists(string_or_file):
        logger.info('Use existing SSH public key file: %s', string_or_file)
        with open(string_or_file, 'r') as f:
            content = f.read()
    elif not keys.is_valid_ssh_rsa_public_key(content):
        if should_generate_ssh_keys:
            # figure out appropriate file names:
            # 'base_name'(with private keys), and 'base_name.pub'(with public keys)
            public_key_filepath = string_or_file
            if public_key_filepath[-4:].lower() == '.pub':
                private_key_filepath = public_key_filepath[:-4]
            else:
                private_key_filepath = public_key_filepath + '.private'
            content = keys.generate_ssh_keys(private_key_filepath, public_key_filepath)
            logger.warning("SSH key files '%s' and '%s' have been generated under ~/.ssh to "
                           "allow SSH access to the VM. If using machines without "
                           "permanent storage, back up your keys to a safe location.",
                           private_key_filepath, public_key_filepath)
        else:
            raise CLIError('An RSA key file or key value must be supplied to SSH Key Value. '
                           'You can use --generate-ssh-keys to let CLI generate one for you')
    return content


def _validate_vm_vmss_msi(cmd, namespace, is_identity_assign=False):

    # For the creation of VM and VMSS, "--role" and "--scope" should be passed in at the same time
    # when assigning a role to the managed identity
    if not is_identity_assign and namespace.assign_identity is not None:
        if (namespace.identity_scope and not namespace.identity_role) or \
                (not namespace.identity_scope and namespace.identity_role):
            raise ArgumentUsageError(
                "usage error: please specify both --role and --scope when assigning a role to the managed identity")

    # For "az vm identity assign", "--scope" must be passed in when assigning a role to the managed identity
    if is_identity_assign:
        role_is_explicitly_specified = getattr(namespace.identity_role, 'is_default', None) is None
        if not namespace.identity_scope and role_is_explicitly_specified:
            raise ArgumentUsageError(
                "usage error: please specify --scope when assigning a role to the managed identity")

    # Assign managed identity
    if is_identity_assign or namespace.assign_identity is not None:
        identities = namespace.assign_identity or []
        from ._vm_utils import MSI_LOCAL_ID
        for i, _ in enumerate(identities):
            if identities[i] != MSI_LOCAL_ID:
                identities[i] = _get_resource_id(cmd.cli_ctx, identities[i], namespace.resource_group_name,
                                                 'userAssignedIdentities', 'Microsoft.ManagedIdentity')

        user_assigned_identities = [x for x in identities if x != MSI_LOCAL_ID]
        if user_assigned_identities and not cmd.supported_api_version(min_api='2017-12-01'):
            raise ArgumentUsageError('usage error: user assigned identity is only available under profile '
                                     'with minimum Compute API version of 2017-12-01')
        if namespace.identity_scope:
            if identities and MSI_LOCAL_ID not in identities:
                raise ArgumentUsageError("usage error: '--scope'/'--role' is only applicable when "
                                         "assign system identity")
            # keep 'identity_role' for output as logical name is more readable
            setattr(namespace, 'identity_role_id', _resolve_role_id(cmd.cli_ctx, namespace.identity_role,
                                                                    namespace.identity_scope))
    elif namespace.identity_scope or namespace.identity_role:
        raise ArgumentUsageError('usage error: --assign-identity [--scope SCOPE] [--role ROLE]')


def _validate_vm_vmss_set_applications(cmd, namespace):  # pylint: disable=unused-argument
    if namespace.application_configuration_overrides and \
       len(namespace.application_version_ids) != len(namespace.application_configuration_overrides):
        raise ArgumentUsageError('usage error: --app-config-overrides should have the same number of items as'
                                 ' --application-version-ids')


def _resolve_role_id(cli_ctx, role, scope):
    import re
    import uuid
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION).role_definitions

    role_id = None
    if re.match(r'/subscriptions/.+/providers/Microsoft.Authorization/roleDefinitions/',
                role, re.I):
        role_id = role
    else:
        try:
            uuid.UUID(role)
            role_id = '/subscriptions/{}/providers/Microsoft.Authorization/roleDefinitions/{}'.format(
                client.config.subscription_id, role)
        except ValueError:
            pass
        if not role_id:  # retrieve role id
            role_defs = list(client.list(scope, "roleName eq '{}'".format(role)))
            if not role_defs:
                raise CLIError("Role '{}' doesn't exist.".format(role))
            if len(role_defs) > 1:
                ids = [r.id for r in role_defs]
                err = "More than one role matches the given name '{}'. Please pick an id from '{}'"
                raise CLIError(err.format(role, ids))
            role_id = role_defs[0].id
    return role_id


def process_vm_create_namespace(cmd, namespace):
    validate_tags(namespace)
    _validate_location(cmd, namespace, namespace.zone, namespace.size)
    validate_edge_zone(cmd, namespace)
    if namespace.count is not None:
        _validate_count(namespace)
    validate_asg_names_or_ids(cmd, namespace)
    _validate_vm_create_storage_profile(cmd, namespace)
    if namespace.storage_profile in [StorageProfile.SACustomImage,
                                     StorageProfile.SAPirImage]:
        _validate_vm_create_storage_account(cmd, namespace)

    _validate_vm_create_availability_set(cmd, namespace)
    _validate_vm_create_vmss(cmd, namespace)
    _validate_vm_vmss_create_vnet(cmd, namespace)
    _validate_vm_create_nsg(cmd, namespace)
    _validate_vm_vmss_create_public_ip(cmd, namespace)
    _validate_vm_create_nics(cmd, namespace)
    _validate_vm_vmss_accelerated_networking(cmd.cli_ctx, namespace)
    _validate_vm_vmss_create_auth(namespace, cmd)

    _validate_proximity_placement_group(cmd, namespace)
    _validate_vm_create_dedicated_host(cmd, namespace)

    if namespace.secrets:
        _validate_secrets(namespace.secrets, namespace.os_type)
    _validate_vm_vmss_msi(cmd, namespace)
    if namespace.boot_diagnostics_storage:
        namespace.boot_diagnostics_storage = get_storage_blob_uri(cmd.cli_ctx, namespace.boot_diagnostics_storage)

    _validate_capacity_reservation_group(cmd, namespace)
    _validate_vm_nic_delete_option(namespace)
    _validate_community_gallery_legal_agreement_acceptance(cmd, namespace)

# endregion


def process_vm_update_namespace(cmd, namespace):
    _validate_vm_create_dedicated_host(cmd, namespace)
    _validate_capacity_reservation_group(cmd, namespace)
    _validate_vm_vmss_update_ephemeral_placement(cmd, namespace)


# region VMSS Create Validators
def _get_default_address_pool(cli_ctx, resource_group, balancer_name, balancer_type):
    option_name = '--backend-pool-name'
    client = getattr(get_network_client(cli_ctx), balancer_type, None)
    if not client:
        raise CLIError('unrecognized balancer type: {}'.format(balancer_type))

    balancer = client.get(resource_group, balancer_name)
    values = [x.name for x in balancer.backend_address_pools]
    if len(values) > 1:
        raise CLIError("Multiple possible values found for '{0}': {1}\nSpecify '{0}' "
                       "explicitly.".format(option_name, ', '.join(values)))
    if not values:
        raise CLIError("No existing values found for '{0}'. Create one first and try "
                       "again.".format(option_name))
    return values[0]


# Client end hack per: https://github.com/Azure/azure-cli/issues/9943
def _validate_vmss_single_placement_group(namespace):
    if namespace.zones or namespace.instance_count > 100:
        if namespace.single_placement_group is None:
            namespace.single_placement_group = False


def _validate_vmss_create_load_balancer_or_app_gateway(cmd, namespace):
    from msrestazure.tools import parse_resource_id
    from azure.cli.core.profiles import ResourceType
    from azure.core.exceptions import HttpResponseError
    std_lb_is_available = cmd.supported_api_version(min_api='2017-08-01', resource_type=ResourceType.MGMT_NETWORK)

    if namespace.load_balancer and namespace.application_gateway:
        raise CLIError('incorrect usage: --load-balancer NAME_OR_ID | '
                       '--application-gateway NAME_OR_ID')

    # Resolve the type of balancer (if any) being used
    balancer_type = 'None'
    if namespace.load_balancer is None and namespace.application_gateway is None:
        if std_lb_is_available:
            balancer_type = 'loadBalancer'
        else:  # needed for Stack profile 2017_03_09
            balancer_type = 'loadBalancer' if namespace.single_placement_group is not False else 'applicationGateway'
            logger.debug("W/o STD LB, defaulting to '%s' under because single placement group is disabled",
                         balancer_type)

    elif namespace.load_balancer:
        balancer_type = 'loadBalancer'
    elif namespace.application_gateway:
        balancer_type = 'applicationGateway'

    if balancer_type == 'applicationGateway':

        if namespace.application_gateway:
            client = get_network_client(cmd.cli_ctx).application_gateways
            try:
                rg = parse_resource_id(namespace.application_gateway).get(
                    'resource_group', namespace.resource_group_name)
                ag_name = parse_resource_id(namespace.application_gateway)['name']
                client.get(rg, ag_name)
                namespace.app_gateway_type = 'existing'
                namespace.backend_pool_name = namespace.backend_pool_name or \
                    _get_default_address_pool(cmd.cli_ctx, rg, ag_name, 'application_gateways')
                logger.debug("using specified existing application gateway '%s'", namespace.application_gateway)
            except HttpResponseError:
                namespace.app_gateway_type = 'new'
                logger.debug("application gateway '%s' not found. It will be created.", namespace.application_gateway)
        elif namespace.application_gateway == '':
            namespace.app_gateway_type = None
            logger.debug('no application gateway will be used')
        elif namespace.application_gateway is None:
            namespace.app_gateway_type = 'new'
            logger.debug('new application gateway will be created')

        # AppGateway frontend
        required = []
        if namespace.app_gateway_type == 'new':
            required.append('app_gateway_sku')
            required.append('app_gateway_capacity')
            if namespace.vnet_type != 'new':
                required.append('app_gateway_subnet_address_prefix')
        elif namespace.app_gateway_type == 'existing':
            required.append('backend_pool_name')
        forbidden = ['nat_pool_name', 'load_balancer', 'health_probe']
        validate_parameter_set(namespace, required, forbidden, description='network balancer: application gateway')

    elif balancer_type == 'loadBalancer':
        # LoadBalancer frontend
        required = []
        forbidden = ['app_gateway_subnet_address_prefix', 'application_gateway', 'app_gateway_sku',
                     'app_gateway_capacity']
        validate_parameter_set(namespace, required, forbidden, description='network balancer: load balancer')

        if namespace.load_balancer:
            rg = parse_resource_id(namespace.load_balancer).get('resource_group', namespace.resource_group_name)
            lb_name = parse_resource_id(namespace.load_balancer)['name']
            lb = get_network_lb(cmd.cli_ctx, namespace.resource_group_name, lb_name)
            if lb:
                namespace.load_balancer_type = 'existing'
                namespace.backend_pool_name = namespace.backend_pool_name or \
                    _get_default_address_pool(cmd.cli_ctx, rg, lb_name, 'load_balancers')
                if not namespace.nat_pool_name:
                    if len(lb.inbound_nat_pools) > 1:
                        raise CLIError("Multiple possible values found for '{0}': {1}\nSpecify '{0}' explicitly.".format(  # pylint: disable=line-too-long
                            '--nat-pool-name', ', '.join([n.name for n in lb.inbound_nat_pools])))
                    if not lb.inbound_nat_pools:  # Associated scaleset will be missing ssh/rdp, so warn here.
                        logger.warning("No inbound nat pool was configured on '%s'", namespace.load_balancer)
                    else:
                        namespace.nat_pool_name = lb.inbound_nat_pools[0].name
                logger.debug("using specified existing load balancer '%s'", namespace.load_balancer)
            else:
                namespace.load_balancer_type = 'new'
                logger.debug("load balancer '%s' not found. It will be created.", namespace.load_balancer)
        elif namespace.load_balancer == '':
            namespace.load_balancer_type = None
            logger.debug('no load balancer will be used')
        elif namespace.load_balancer is None:
            namespace.load_balancer_type = 'new'
            logger.debug('new load balancer will be created')

        if namespace.load_balancer_type == 'new' and namespace.single_placement_group is False and std_lb_is_available:
            LBSkuName = cmd.get_models('LoadBalancerSkuName', resource_type=ResourceType.MGMT_NETWORK)
            if namespace.load_balancer_sku is None:
                namespace.load_balancer_sku = LBSkuName.standard.value
                logger.debug("use Standard sku as single placement group is turned off")
            elif namespace.load_balancer_sku == LBSkuName.basic.value:
                if namespace.zones:
                    err = "'Standard' load balancer is required for zonal scale-sets"
                elif namespace.instance_count > 100:
                    err = "'Standard' load balancer is required for scale-sets with 100+ instances"
                else:
                    err = "'Standard' load balancer is required because 'single placement group' is turned off"

                raise CLIError('usage error:{}'.format(err))


def get_network_client(cli_ctx):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK, api_version=get_target_network_api(cli_ctx))


def get_network_lb(cli_ctx, resource_group_name, lb_name):
    from azure.core.exceptions import HttpResponseError
    network_client = get_network_client(cli_ctx)
    try:
        return network_client.load_balancers.get(resource_group_name, lb_name)
    except HttpResponseError:
        return None


def process_vmss_create_namespace(cmd, namespace):
    from azure.cli.core.azclierror import InvalidArgumentValueError
    # uniform_str = 'Uniform'
    flexible_str = 'Flexible'
    if namespace.orchestration_mode.lower() == flexible_str.lower():

        # The commentted parameters are also forbidden, but they have default values.
        # I don't know whether they are provided by user.

        namespace.load_balancer_sku = 'Standard'  # lb sku MUST be standard
        # namespace.public_ip_per_vm = True  # default to true for VMSS Flex

        if namespace.single_placement_group:
            raise ArgumentUsageError('usage error: --single-placement-group can only be set to False for Flex mode')
        namespace.single_placement_group = False

        namespace.upgrade_policy_mode = None
        namespace.use_unmanaged_disk = None

        banned_params = {
            '--disable-overprovision': namespace.disable_overprovision,
            '--health-probe': namespace.health_probe,
            '--host-group': namespace.host_group,
            '--nat-pool-name': namespace.nat_pool_name,
            '--scale-in-policy': namespace.scale_in_policy,
            '--user-data': namespace.user_data
        }

        for param, value in banned_params.items():
            if value is not None:
                raise ArgumentUsageError(f'usage error: {param} is not supported for Flex mode')

        if namespace.vm_sku and not namespace.image:
            raise ArgumentUsageError('usage error: please specify the --image when you want to specify the VM SKU')

        if namespace.image:

            if namespace.vm_sku is None:
                from azure.cli.core.cloud import AZURE_US_GOV_CLOUD
                if cmd.cli_ctx.cloud.name != AZURE_US_GOV_CLOUD.name:
                    namespace.vm_sku = 'Standard_DS1_v2'
                else:
                    namespace.vm_sku = 'Standard_D1_v2'

            if namespace.network_api_version is None:
                namespace.network_api_version = '2020-11-01'

            if namespace.platform_fault_domain_count is None:
                namespace.platform_fault_domain_count = 1

            if namespace.computer_name_prefix is None:
                namespace.computer_name_prefix = namespace.vmss_name[:8]

        # if namespace.platform_fault_domain_count is None:
        #     raise CLIError("usage error: --platform-fault-domain-count is required in Flexible mode")

        if namespace.tags is not None:
            validate_tags(namespace)
        _validate_location(cmd, namespace, namespace.zones, namespace.vm_sku)
        validate_edge_zone(cmd, namespace)
        if namespace.application_security_groups is not None:
            validate_asg_names_or_ids(cmd, namespace)

        if getattr(namespace, 'attach_os_disk', None) or namespace.image is not None:
            _validate_vm_create_storage_profile(cmd, namespace, for_scale_set=True)

        if namespace.vnet_name or namespace.subnet or namespace.image:
            _validate_vm_vmss_create_vnet(cmd, namespace, for_scale_set=True)
            _validate_vmss_create_subnet(namespace)

        if namespace.load_balancer or namespace.application_gateway or namespace.image:
            _validate_vmss_create_load_balancer_or_app_gateway(cmd, namespace)

        if namespace.public_ip_address or namespace.image:
            _validate_vmss_create_public_ip(cmd, namespace)

        if namespace.nsg is not None:
            _validate_vmss_create_nsg(cmd, namespace)
        if namespace.accelerated_networking is not None:
            _validate_vm_vmss_accelerated_networking(cmd.cli_ctx, namespace)
        if any([namespace.admin_password, namespace.ssh_dest_key_path, namespace.generate_ssh_keys,
                namespace.authentication_type, namespace.os_type]):
            _validate_vm_vmss_create_auth(namespace, cmd)
        if namespace.assign_identity == '[system]':
            raise InvalidArgumentValueError('usage error: only user assigned indetity is suppoprted for Flex mode.')
        if namespace.assign_identity is not None:
            _validate_vm_vmss_msi(cmd, namespace)  # -- UserAssignedOnly
        _validate_proximity_placement_group(cmd, namespace)
        _validate_vmss_terminate_notification(cmd, namespace)
        if namespace.automatic_repairs_grace_period is not None:
            _validate_vmss_create_automatic_repairs(cmd, namespace)
        _validate_vmss_create_host_group(cmd, namespace)

        if namespace.secrets is not None:
            _validate_secrets(namespace.secrets, namespace.os_type)

        if namespace.eviction_policy and not namespace.priority:
            raise ArgumentUsageError('usage error: --priority PRIORITY [--eviction-policy POLICY]')

        return

    # Uniform mode
    if namespace.disable_overprovision is None:
        namespace.disable_overprovision = False
    validate_tags(namespace)
    if namespace.vm_sku is None:
        from azure.cli.core.cloud import AZURE_US_GOV_CLOUD
        if cmd.cli_ctx.cloud.name != AZURE_US_GOV_CLOUD.name:
            namespace.vm_sku = 'Standard_DS1_v2'
        else:
            namespace.vm_sku = 'Standard_D1_v2'
    _validate_location(cmd, namespace, namespace.zones, namespace.vm_sku)
    validate_edge_zone(cmd, namespace)
    validate_asg_names_or_ids(cmd, namespace)
    _validate_vm_create_storage_profile(cmd, namespace, for_scale_set=True)
    _validate_vm_vmss_create_vnet(cmd, namespace, for_scale_set=True)

    _validate_vmss_single_placement_group(namespace)
    _validate_vmss_create_load_balancer_or_app_gateway(cmd, namespace)
    _validate_vmss_create_subnet(namespace)
    _validate_vmss_create_public_ip(cmd, namespace)
    _validate_vmss_create_nsg(cmd, namespace)
    _validate_vm_vmss_accelerated_networking(cmd.cli_ctx, namespace)
    _validate_vm_vmss_create_auth(namespace, cmd)
    _validate_vm_vmss_msi(cmd, namespace)
    _validate_proximity_placement_group(cmd, namespace)
    _validate_vmss_terminate_notification(cmd, namespace)
    _validate_vmss_create_automatic_repairs(cmd, namespace)
    _validate_vmss_create_host_group(cmd, namespace)

    if namespace.secrets:
        _validate_secrets(namespace.secrets, namespace.os_type)

    if not namespace.public_ip_per_vm and namespace.vm_domain_name:
        raise ArgumentUsageError('usage error: --vm-domain-name can only be used when --public-ip-per-vm is enabled')

    if namespace.eviction_policy and not namespace.priority:
        raise ArgumentUsageError('usage error: --priority PRIORITY [--eviction-policy POLICY]')

    _validate_capacity_reservation_group(cmd, namespace)
    _validate_community_gallery_legal_agreement_acceptance(cmd, namespace)


def validate_vmss_update_namespace(cmd, namespace):  # pylint: disable=unused-argument
    if not namespace.instance_id:
        if namespace.protect_from_scale_in is not None or namespace.protect_from_scale_set_actions is not None:
            raise CLIError("usage error: protection policies can only be applied to VM instances within a VMSS."
                           " Please use --instance-id to specify a VM instance")
    _validate_vmss_update_terminate_notification_related(cmd, namespace)
    _validate_vmss_update_automatic_repairs(cmd, namespace)
    _validate_capacity_reservation_group(cmd, namespace)
    _validate_vm_vmss_update_ephemeral_placement(cmd, namespace)
# endregion


# region disk, snapshot, image validators
def process_vm_disk_attach_namespace(cmd, namespace):
    disks = []
    if not namespace.disks:
        if not namespace.disk:
            raise RequiredArgumentMissingError("Please use --name or --disks to specify the disk names")

        disks = [_get_resource_id(cmd.cli_ctx, namespace.disk, namespace.resource_group_name,
                                  'disks', 'Microsoft.Compute')]
    else:
        if namespace.disk:
            raise MutuallyExclusiveArgumentError("You can only specify one of --name and --disks")

        for disk in namespace.disks:
            disks.append(_get_resource_id(cmd.cli_ctx, disk, namespace.resource_group_name,
                                          'disks', 'Microsoft.Compute'))
    namespace.disks = disks

    if len(disks) > 1 and namespace.lun:
        raise MutuallyExclusiveArgumentError("You cannot specify the --lun for multiple disks")


def validate_vmss_disk(cmd, namespace):
    if namespace.disk:
        namespace.disk = _get_resource_id(cmd.cli_ctx, namespace.disk,
                                          namespace.resource_group_name, 'disks', 'Microsoft.Compute')
    if bool(namespace.disk) == bool(namespace.size_gb):
        raise CLIError('usage error: --disk EXIST_DISK --instance-id ID | --size-gb GB')
    if bool(namespace.disk) != bool(namespace.instance_id):
        raise CLIError('usage error: --disk EXIST_DISK --instance-id ID')


def process_disk_or_snapshot_create_namespace(cmd, namespace):
    from msrestazure.azure_exceptions import CloudError
    validate_tags(namespace)
    validate_edge_zone(cmd, namespace)
    if namespace.source:
        usage_error = 'usage error: --source {SNAPSHOT | DISK} | --source VHD_BLOB_URI [--source-storage-account-id ID]'
        try:
            namespace.source_blob_uri, namespace.source_disk, namespace.source_snapshot, source_info = \
                _figure_out_storage_source(cmd.cli_ctx, namespace.resource_group_name, namespace.source)
            if not namespace.source_blob_uri and namespace.source_storage_account_id:
                raise CLIError(usage_error)
            # autodetect copy_start for `az snapshot create`
            if 'snapshot create' in cmd.name and hasattr(namespace, 'copy_start') and namespace.copy_start is None:
                if not source_info:
                    from azure.cli.core.util import parse_proxy_resource_id
                    result = parse_proxy_resource_id(namespace.source_disk or namespace.source_snapshot)
                    try:
                        source_info, _ = _get_disk_or_snapshot_info(cmd.cli_ctx,
                                                                    result['resource_group'],
                                                                    result['name'])
                    except Exception:  # pylint: disable=broad-except
                        # There's a chance that the source doesn't exist, eg, vmss os disk.
                        # You can get the id of vmss os disk by
                        #   `az vmss show -g {} -n {} --instance-id {} --query storageProfile.osDisk.managedDisk.id`
                        # But `az disk show --ids {}` will return ResourceNotFound error
                        # We don't autodetect copy_start in this situation
                        return
                if not namespace.location:
                    get_default_location_from_resource_group(cmd, namespace)
                # if the source location differs from target location, then it's copy_start scenario
                namespace.copy_start = source_info.location != namespace.location
        except CloudError:
            raise CLIError(usage_error)


def process_image_create_namespace(cmd, namespace):
    from msrestazure.tools import parse_resource_id
    validate_tags(namespace)
    validate_edge_zone(cmd, namespace)
    source_from_vm = False
    try:
        # try capturing from VM, a most common scenario
        res_id = _get_resource_id(cmd.cli_ctx, namespace.source, namespace.resource_group_name,
                                  'virtualMachines', 'Microsoft.Compute')
        res = parse_resource_id(res_id)
        if res['type'] == 'virtualMachines':
            compute_client = _compute_client_factory(cmd.cli_ctx, subscription_id=res['subscription'])
            vm_info = compute_client.virtual_machines.get(res['resource_group'], res['name'])
            source_from_vm = True
    except ResourceNotFoundError:
        pass

    if source_from_vm:
        # pylint: disable=no-member
        namespace.os_type = vm_info.storage_profile.os_disk.os_type
        namespace.source_virtual_machine = res_id
        if namespace.data_disk_sources:
            raise CLIError("'--data-disk-sources' is not allowed when capturing "
                           "images from virtual machines")
    else:
        namespace.os_blob_uri, namespace.os_disk, namespace.os_snapshot, _ = _figure_out_storage_source(cmd.cli_ctx, namespace.resource_group_name, namespace.source)  # pylint: disable=line-too-long
        namespace.data_blob_uris = []
        namespace.data_disks = []
        namespace.data_snapshots = []
        if namespace.data_disk_sources:
            for data_disk_source in namespace.data_disk_sources:
                source_blob_uri, source_disk, source_snapshot, _ = _figure_out_storage_source(
                    cmd.cli_ctx, namespace.resource_group_name, data_disk_source)
                if source_blob_uri:
                    namespace.data_blob_uris.append(source_blob_uri)
                if source_disk:
                    namespace.data_disks.append(source_disk)
                if source_snapshot:
                    namespace.data_snapshots.append(source_snapshot)
        if not namespace.os_type:
            raise CLIError("usage error: os type is required to create the image, "
                           "please specify '--os-type OS_TYPE'")


def _figure_out_storage_source(cli_ctx, resource_group_name, source):
    source_blob_uri = None
    source_disk = None
    source_snapshot = None
    source_info = None
    if urlparse(source).scheme:  # a uri?
        source_blob_uri = source
    elif '/disks/' in source.lower():
        source_disk = source
    elif '/snapshots/' in source.lower():
        source_snapshot = source
    else:
        source_info, is_snapshot = _get_disk_or_snapshot_info(cli_ctx, resource_group_name, source)
        if is_snapshot:
            source_snapshot = source_info.id
        else:
            source_disk = source_info.id

    return (source_blob_uri, source_disk, source_snapshot, source_info)


def _get_disk_or_snapshot_info(cli_ctx, resource_group_name, source):
    compute_client = _compute_client_factory(cli_ctx)
    is_snapshot = True

    try:
        info = compute_client.snapshots.get(resource_group_name, source)
    except ResourceNotFoundError:
        is_snapshot = False
        info = compute_client.disks.get(resource_group_name, source)

    return info, is_snapshot


def process_disk_encryption_namespace(cmd, namespace):
    namespace.disk_encryption_keyvault = _get_resource_id(cmd.cli_ctx, namespace.disk_encryption_keyvault,
                                                          namespace.resource_group_name,
                                                          'vaults', 'Microsoft.KeyVault')

    if namespace.key_encryption_keyvault:
        if not namespace.key_encryption_key:
            raise CLIError("Incorrect usage '--key-encryption-keyvault': "
                           "'--key-encryption-key' is required")
        namespace.key_encryption_keyvault = _get_resource_id(cmd.cli_ctx, namespace.key_encryption_keyvault,
                                                             namespace.resource_group_name,
                                                             'vaults', 'Microsoft.KeyVault')


def process_assign_identity_namespace(cmd, namespace):
    _validate_vm_vmss_msi(cmd, namespace, is_identity_assign=True)


def process_remove_identity_namespace(cmd, namespace):
    if namespace.identities:
        from ._vm_utils import MSI_LOCAL_ID
        for i in range(len(namespace.identities)):
            if namespace.identities[i] != MSI_LOCAL_ID:
                namespace.identities[i] = _get_resource_id(cmd.cli_ctx, namespace.identities[i],
                                                           namespace.resource_group_name,
                                                           'userAssignedIdentities',
                                                           'Microsoft.ManagedIdentity')


def process_set_applications_namespace(cmd, namespace):  # pylint: disable=unused-argument
    _validate_vm_vmss_set_applications(cmd, namespace)


def process_gallery_image_version_namespace(cmd, namespace):
    from azure.cli.core.azclierror import InvalidArgumentValueError
    TargetRegion, EncryptionImages, OSDiskImageEncryption, DataDiskImageEncryption, ConfidentialVMEncryptionType = \
        cmd.get_models('TargetRegion', 'EncryptionImages', 'OSDiskImageEncryption', 'DataDiskImageEncryption',
                       'ConfidentialVMEncryptionType')
    storage_account_types_list = [item.lower() for item in ['Standard_LRS', 'Standard_ZRS', 'Premium_LRS']]
    storage_account_types_str = ", ".join(storage_account_types_list)

    if namespace.target_regions:
        if hasattr(namespace, 'target_region_encryption') and namespace.target_region_encryption:
            if len(namespace.target_regions) != len(namespace.target_region_encryption):
                raise InvalidArgumentValueError(
                    'usage error: Length of --target-region-encryption should be as same as length of target regions')

        if hasattr(namespace, 'target_region_cvm_encryption') and namespace.target_region_cvm_encryption:
            OSDiskImageSecurityProfile = cmd.get_models('OSDiskImageSecurityProfile')
            if len(namespace.target_regions) != len(namespace.target_region_cvm_encryption):
                raise InvalidArgumentValueError(
                    'usage error: Length of --target_region_cvm_encryption should be as same as '
                    'length of target regions')

        regions_info = []
        for i, t in enumerate(namespace.target_regions):
            parts = t.split('=', 2)
            replica_count = None
            storage_account_type = None

            # Region specified, but also replica count or storage account type
            if len(parts) == 2:
                try:
                    replica_count = int(parts[1])
                except ValueError:
                    storage_account_type = parts[1]
                    if parts[1].lower() not in storage_account_types_list:
                        raise ArgumentUsageError(
                            "usage error: {} is an invalid target region argument. "
                            "The second part is neither an integer replica count or a valid storage account type. "
                            "Storage account types must be one of {}.".format(t, storage_account_types_str))

            # Region specified, but also replica count and storage account type
            elif len(parts) == 3:
                try:
                    replica_count = int(parts[1])   # raises ValueError if this is not a replica count, try other order.
                    storage_account_type = parts[2]
                    if storage_account_type not in storage_account_types_list:
                        raise ArgumentUsageError(
                            "usage error: {} is an invalid target region argument. "
                            "The third part is not a valid storage account type. "
                            "Storage account types must be one of {}.".format(t, storage_account_types_str))
                except ValueError:
                    raise ArgumentUsageError(
                        "usage error: {} is an invalid target region argument. "
                        "The second part must be a valid integer replica count.".format(t))

            # Parse target region encryption, example: ['des1,0,des2,1,des3', 'null', 'des4']
            encryption = None
            if hasattr(namespace, 'target_region_encryption') and namespace.target_region_encryption:
                terms = namespace.target_region_encryption[i].split(',')
                # OS disk
                os_disk_image = terms[0]
                if os_disk_image == 'null':
                    os_disk_image = None
                else:
                    des_id = _disk_encryption_set_format(cmd, namespace, os_disk_image)
                    security_profile = None
                    if hasattr(namespace, 'target_region_cvm_encryption') and namespace.target_region_cvm_encryption:
                        cvm_terms = namespace.target_region_cvm_encryption[i].split(',')
                        if not cvm_terms or len(cvm_terms) != 2:
                            raise ArgumentUsageError(
                                "usage error: {} is an invalid target region cvm encryption. "
                                "Both os_cvm_encryption_type and os_cvm_des parameters are required.".format(cvm_terms))

                        storage_profile_types = [profile_type.value for profile_type in ConfidentialVMEncryptionType]
                        storage_profile_types_str = ", ".join(storage_profile_types)
                        if cvm_terms[0] not in storage_profile_types:
                            raise ArgumentUsageError(
                                "usage error: {} is an invalid os_cvm_encryption_type. "
                                "The valid values for os_cvm_encryption_type are {}".format(
                                    cvm_terms, storage_profile_types_str))
                        if cvm_terms[1]:
                            cvm_des_id = _disk_encryption_set_format(cmd, namespace, cvm_terms[1])
                        else:
                            cvm_des_id = None
                        security_profile = OSDiskImageSecurityProfile(confidential_vm_encryption_type=cvm_terms[0],
                                                                      secure_vm_disk_encryption_set_id=cvm_des_id)

                    os_disk_image = OSDiskImageEncryption(disk_encryption_set_id=des_id,
                                                          security_profile=security_profile)
                # Data disk
                if len(terms) > 1:
                    data_disk_images = terms[1:]
                    data_disk_images_len = len(data_disk_images)
                    if data_disk_images_len % 2 != 0:
                        raise ArgumentUsageError(
                            'usage error: LUN and disk encryption set for data disk should appear in pair in '
                            '--target-region-encryption. Example: osdes,0,datades0,1,datades1')
                    data_disk_image_encryption_list = []
                    for j in range(int(data_disk_images_len / 2)):
                        lun = data_disk_images[j * 2]
                        des_id = data_disk_images[j * 2 + 1]
                        des_id = _disk_encryption_set_format(cmd, namespace, des_id)
                        data_disk_image_encryption_list.append(DataDiskImageEncryption(
                            lun=lun, disk_encryption_set_id=des_id))
                    data_disk_images = data_disk_image_encryption_list
                else:
                    data_disk_images = None
                encryption = EncryptionImages(os_disk_image=os_disk_image, data_disk_images=data_disk_images)

            # At least the region is specified
            if len(parts) >= 1:
                regions_info.append(TargetRegion(name=parts[0], regional_replica_count=replica_count,
                                                 storage_account_type=storage_account_type,
                                                 encryption=encryption))

        namespace.target_regions = regions_info


def _disk_encryption_set_format(cmd, namespace, name):
    """
    Transform name to ID. If it's already a valid ID, do nothing.
    :param name: string
    :return: ID
    """
    from msrestazure.tools import resource_id, is_valid_resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id
    if name is not None and not is_valid_resource_id(name):
        name = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=namespace.resource_group_name,
            namespace='Microsoft.Compute', type='diskEncryptionSets', name=name)
    return name
# endregion


def process_vm_vmss_stop(cmd, namespace):  # pylint: disable=unused-argument
    if "vmss" in cmd.name:
        logger.warning("About to power off the VMSS instances...\nThey will continue to be billed. "
                       "To deallocate VMSS instances, run: az vmss deallocate.")
    else:
        logger.warning("About to power off the specified VM...\nIt will continue to be billed. "
                       "To deallocate a VM, run: az vm deallocate.")


def _validate_vmss_update_terminate_notification_related(cmd, namespace):  # pylint: disable=unused-argument
    """
    Validate vmss update enable_terminate_notification and terminate_notification_time.
    If terminate_notification_time is specified, enable_terminate_notification should not be false
    If enable_terminate_notification is true, must specify terminate_notification_time
    """
    if namespace.enable_terminate_notification is False and namespace.terminate_notification_time is not None:
        raise CLIError("usage error: please enable --enable-terminate-notification")
    if namespace.enable_terminate_notification is True and namespace.terminate_notification_time is None:
        raise CLIError("usage error: please set --terminate-notification-time")
    _validate_vmss_terminate_notification(cmd, namespace)


def _validate_vmss_terminate_notification(cmd, namespace):  # pylint: disable=unused-argument
    """
    Transform minutes to ISO 8601 formmat
    """
    if namespace.terminate_notification_time is not None:
        namespace.terminate_notification_time = 'PT' + namespace.terminate_notification_time + 'M'


def _validate_vmss_create_automatic_repairs(cmd, namespace):  # pylint: disable=unused-argument
    if namespace.automatic_repairs_grace_period is not None or namespace.automatic_repairs_action is not None:
        if namespace.load_balancer is None or namespace.health_probe is None:
            raise ArgumentUsageError("usage error: --load-balancer and --health-probe are required "
                                     "when creating vmss with automatic repairs")
    _validate_vmss_automatic_repairs(cmd, namespace)


def _validate_vmss_update_automatic_repairs(cmd, namespace):  # pylint: disable=unused-argument
    if namespace.enable_automatic_repairs is False and \
            (namespace.automatic_repairs_grace_period is not None or namespace.automatic_repairs_action is not None):
        raise ArgumentUsageError("usage error: please enable --enable-automatic-repairs")
    if namespace.enable_automatic_repairs is True and namespace.automatic_repairs_grace_period is None\
            and namespace.automatic_repairs_action is None:
        raise ArgumentUsageError("usage error: please set --automatic-repairs-grace-period or"
                                 " --automatic-repairs-action")
    _validate_vmss_automatic_repairs(cmd, namespace)


def _validate_vmss_automatic_repairs(cmd, namespace):  # pylint: disable=unused-argument
    """
        Transform minutes to ISO 8601 formmat
    """
    if namespace.automatic_repairs_grace_period is not None:
        namespace.automatic_repairs_grace_period = 'PT' + namespace.automatic_repairs_grace_period + 'M'


def _validate_vmss_create_host_group(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id
    if namespace.host_group:
        if not is_valid_resource_id(namespace.host_group):
            namespace.host_group = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx), resource_group=namespace.resource_group_name,
                namespace='Microsoft.Compute', type='hostGroups', name=namespace.host_group
            )


def _validate_count(namespace):
    if namespace.count < 2 or namespace.count > 250:
        raise ValidationError(
            '--count should be in [2, 250]. Please make sure your subscription has enough quota of resources')
    banned_params = [
        namespace.attach_data_disks,
        namespace.attach_os_disk,
        namespace.boot_diagnostics_storage,
        namespace.computer_name,
        namespace.dedicated_host,
        namespace.dedicated_host_group,
        namespace.nics,
        namespace.os_disk_name,
        namespace.private_ip_address,
        namespace.public_ip_address,
        namespace.public_ip_address_dns_name,
        namespace.storage_account,
        namespace.storage_container_name,
        namespace.use_unmanaged_disk,
    ]
    params_str = [
        '--attach-data-disks',
        '--attach-os-disk',
        '--boot-diagnostics-storage',
        '--computer-name',
        '--host',
        '--host-group',
        '--nics',
        '--os-disk-name',
        '--private-ip-address',
        '--public-ip-address',
        '--public-ip-address-dns-name',
        '--storage-account',
        '--storage-container-name',
        '--subnet',
        '--use-unmanaged-disk',
        '--vnet-name'
    ]
    if any(param for param in banned_params):
        raise ValidationError('When --count is specified, {} are not allowed'.format(', '.join(params_str)))


def validate_edge_zone(cmd, namespace):  # pylint: disable=unused-argument
    if namespace.edge_zone:
        namespace.edge_zone = {
            'name': namespace.edge_zone,
            'type': 'EdgeZone'
        }


def _validate_capacity_reservation_group(cmd, namespace):

    if namespace.capacity_reservation_group and namespace.capacity_reservation_group != 'None':

        from msrestazure.tools import is_valid_resource_id, resource_id
        from azure.cli.core.commands.client_factory import get_subscription_id
        if not is_valid_resource_id(namespace.capacity_reservation_group):
            namespace.capacity_reservation_group = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Compute',
                type='CapacityReservationGroups',
                name=namespace.capacity_reservation_group
            )


def _validate_vm_vmss_create_ephemeral_placement(namespace):
    ephemeral_os_disk = getattr(namespace, 'ephemeral_os_disk', None)
    ephemeral_os_disk_placement = getattr(namespace, 'ephemeral_os_disk_placement', None)
    if ephemeral_os_disk_placement and not ephemeral_os_disk:
        raise ArgumentUsageError('usage error: --ephemeral-os-disk-placement is only configurable when '
                                 '--ephemeral-os-disk is specified.')


def _validate_vm_vmss_update_ephemeral_placement(cmd, namespace):  # pylint: disable=unused-argument
    size = getattr(namespace, 'size', None)
    vm_sku = getattr(namespace, 'vm_sku', None)
    ephemeral_os_disk_placement = getattr(namespace, 'ephemeral_os_disk_placement', None)
    source = getattr(namespace, 'command').split()[0]
    if ephemeral_os_disk_placement:
        if source == 'vm' and not size:
            raise ArgumentUsageError('usage error: --ephemeral-os-disk-placement is only configurable when '
                                     '--size is specified.')
        if source == 'vmss' and not vm_sku:
            raise ArgumentUsageError('usage error: --ephemeral-os-disk-placement is only configurable when '
                                     '--vm-sku is specified.')


def _validate_community_gallery_legal_agreement_acceptance(cmd, namespace):
    from ._vm_utils import is_community_gallery_image_id, parse_community_gallery_image_id
    if not is_community_gallery_image_id(namespace.image) or namespace.accept_term:
        return

    community_gallery_name, _ = parse_community_gallery_image_id(namespace.image)
    from ._client_factory import cf_community_gallery
    try:
        community_gallery_info = cf_community_gallery(cmd.cli_ctx).get(namespace.location, community_gallery_name)
        eula = community_gallery_info.additional_properties['communityMetadata']['eula']
    except Exception as err:
        raise CLIInternalError('Get the eula from community gallery failed: {0}'.format(err))

    from knack.prompting import prompt_y_n
    msg = "To create the VM/VMSS from community gallery image, you must accept the license agreement and " \
          "privacy statement: {}. (If you want to accept the legal terms by default, " \
          "please use the option '--accept-term' when creating VM/VMSS)".format(eula)

    if not prompt_y_n(msg, default="y"):
        import sys
        sys.exit(0)
