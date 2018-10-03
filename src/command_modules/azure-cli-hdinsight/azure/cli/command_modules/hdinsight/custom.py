# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.util import sdk_no_wait


logger = get_logger(__name__)


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def create_cluster(cmd, client, cluster_name, resource_group_name, location=None, tags=None, no_wait=False,
                   cluster_version='default', cluster_type='spark', cluster_tier=None,
                   cluster_configurations=None, component_version=None,
                   headnode_size='large', workernode_size='large', zookeepernode_size=None, edgenode_size=None,
                   workernode_count=3, workernode_data_disks_per_node=None,
                   workernode_data_disk_storage_account_type=None, workernode_data_disk_size=None,
                   http_username=None, http_password=None,
                   ssh_username='sshuser', ssh_password=None, ssh_public_key=None,
                   storage_account=None, storage_account_key=None,
                   storage_default_container=None, storage_default_filesystem=None,
                   virtual_network=None, subnet_name=None):
    from azure.mgmt.hdinsight.models import ClusterCreateParametersExtended, ClusterCreateProperties, OSType, \
        ClusterDefinition, ComputeProfile, HardwareProfile, Role, OsProfile, LinuxOperatingSystemProfile, \
        StorageProfile, StorageAccount, VirtualNetworkProfile, DataDisksGroups

    # Update optional parameters with defaults
    additional_storage_accounts = []  # TODO: Add support for additional storage accounts
    location = location or _get_rg_location(cmd.cli_ctx, resource_group_name)

    # Format dictionary/free-form arguments
    if cluster_configurations:
        import json
        try:
            cluster_configurations = json.loads(cluster_configurations)
        except ValueError as ex:
            raise CLIError('The cluster_configurations argument must be valid JSON. Error: {}'.format(str(ex)))
    else:
        cluster_configurations = dict()
    if component_version:
        # See validator
        component_version = {c: v for c, v in [version.split('=') for version in component_version]}

    # Validate whether HTTP credentials were provided
    if 'gateway' in cluster_configurations:
        gateway_config = cluster_configurations['gateway']
    else:
        gateway_config = dict()
    if http_username and 'restAuthCredential.username' in gateway_config:
        raise CLIError('An HTTP username must be specified either as a command-line parameter '
                       'or in the cluster configuration, but not both.')
    else:
        http_username = 'admin'  # Implement default logic here, in case a user specifies the username in configurations
    is_password_in_cluster_config = 'restAuthCredential.password' in gateway_config
    if http_password and is_password_in_cluster_config:
        raise CLIError('An HTTP password must be specified either as a command-line parameter '
                       'or in the cluster configuration, but not both.')
    if not (http_password or is_password_in_cluster_config):
        raise CLIError('An HTTP password is required.')

    # Update the cluster config with the HTTP credentials
    gateway_config['restAuthCredential.isEnabled'] = 'true'  # HTTP credentials are required
    http_username = http_username or gateway_config['restAuthCredential.username']
    gateway_config['restAuthCredential.username'] = http_username
    http_password = http_password or gateway_config['restAuthCredential.password']
    gateway_config['restAuthCredential.password'] = http_password
    cluster_configurations['gateway'] = gateway_config

    # Validate whether SSH credentials were provided
    if not (ssh_password or ssh_public_key):
        logger.warning("SSH credentials not specified. Using the HTTP password as the SSH password.")
        ssh_password = http_password

    # Validate storage arguments from the user
    if storage_default_container and storage_default_filesystem:
        raise CLIError('Either the default container or the default filesystem can be specified, but not both.')

    # Attempt to infer the storage account key from the endpoint
    if not storage_account_key and storage_account:
        from .util import get_key_for_storage_account
        logger.info('Storage account key not specified. Attempting to retrieve key...')
        key = get_key_for_storage_account(cmd, storage_account, resource_group_name)
        if not key:
            logger.warning('Storage account key could not be inferred from storage account.')
        else:
            storage_account_key = key

    # Attempt to provide a default container for WASB storage accounts
    if not storage_default_container and storage_account and _is_wasb_endpoint(storage_account):
        storage_default_container = cluster_name
        logger.warning('Default WASB container not specified, using "%s".', storage_default_container)

    # Validate storage info parameters
    if not _all_or_none(storage_account, storage_account_key,
                        (storage_default_container or storage_default_filesystem)):
        raise CLIError('If storage details are specified, the storage account, storage account key, '
                       'and either the default container or default filesystem must be specified.')

    # Validate network profile parameters
    if not _all_or_none(virtual_network, subnet_name):
        raise CLIError('Either both the virtual network and subnet should be specified, or neither should be.')
    # Specify virtual network profile only when network arguments are provided
    virtual_network_profile = virtual_network and VirtualNetworkProfile(
        id=virtual_network,
        subnet=subnet_name
    )

    # Validate data disk parameters
    if not workernode_data_disks_per_node and workernode_data_disk_storage_account_type:
        raise CLIError("Cannot define data disk storage account type unless disks per node is defined.")
    if not workernode_data_disks_per_node and workernode_data_disk_size:
        raise CLIError("Cannot define data disk size unless disks per node is defined.")
    # Specify data disk groups only when disk arguments are provided
    workernode_data_disk_groups = workernode_data_disks_per_node and [
        DataDisksGroups(
            disks_per_node=workernode_data_disks_per_node,
            storage_account_type=workernode_data_disk_storage_account_type,
            disk_size_gb=workernode_data_disk_size
        )
    ]

    os_profile = OsProfile(
        linux_operating_system_profile=LinuxOperatingSystemProfile(
            username=ssh_username,
            password=ssh_password,
            ssh_public_key=ssh_public_key
        )
    )

    roles = [
        # Required roles
        Role(
            name="headnode",
            target_instance_count=2,
            hardware_profile=HardwareProfile(vm_size=headnode_size),
            os_profile=os_profile,
            virtual_network_profile=virtual_network_profile
        ),
        Role(
            name="workernode",
            target_instance_count=workernode_count,
            hardware_profile=HardwareProfile(vm_size=workernode_size),
            os_profile=os_profile,
            virtual_network_profile=virtual_network_profile,
            data_disks_groups=workernode_data_disk_groups
        )
    ]
    if zookeepernode_size:
        roles.append(
            Role(
                name="zookeepernode",
                target_instance_count=3,
                hardware_profile=HardwareProfile(vm_size=zookeepernode_size),
                os_profile=os_profile,
                virtual_network_profile=virtual_network_profile
            ))
    if edgenode_size:
        roles.append(
            Role(
                name="edgenode",
                target_instance_count=1,
                hardware_profile=HardwareProfile(vm_size=edgenode_size),
                os_profile=os_profile,
                virtual_network_profile=virtual_network_profile
            ))

    storage_accounts = []
    if storage_account:
        # Specify storage account details only when storage arguments are provided
        storage_accounts.append(
            StorageAccount(
                name=storage_account,
                key=storage_account_key,
                container=storage_default_container,
                file_system=storage_default_filesystem,
                is_default=True
            ))
    if additional_storage_accounts:
        storage_accounts += [
            StorageAccount(
                name=s.storage_account,
                key=s.storage_account_key,
                container=s.container,
                is_default=False
            )
            for s in additional_storage_accounts
        ]

    create_params = ClusterCreateParametersExtended(
        location=location,
        tags=tags,
        properties=ClusterCreateProperties(
            cluster_version=cluster_version,
            os_type=OSType.linux,
            tier=cluster_tier,
            cluster_definition=ClusterDefinition(
                kind=cluster_type,
                configurations=cluster_configurations,
                component_version=component_version
            ),
            compute_profile=ComputeProfile(
                roles=roles
            ),
            storage_profile=StorageProfile(
                storageaccounts=storage_accounts
            )
        )
    )

    if no_wait:
        return sdk_no_wait(no_wait, client.create, resource_group_name, cluster_name, create_params)

    return client.create(resource_group_name, cluster_name, create_params)


def list_clusters(cmd, client, resource_group_name=None):  # pylint: disable=unused-argument
    clusters_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()

    return list(clusters_list)


def _all_or_none(*params):
    return all(params) or not any(params)


def _get_rg_location(ctx, resource_group_name, subscription_id=None):
    from ._client_factory import cf_resource_groups
    groups = cf_resource_groups(ctx, subscription_id=subscription_id)
    # Just do the get, we don't need the result, it will error out if the group doesn't exist.
    rg = groups.get(resource_group_name)
    return rg.location


def _is_wasb_endpoint(storage_endpoint):
    return '.blob.' in storage_endpoint
