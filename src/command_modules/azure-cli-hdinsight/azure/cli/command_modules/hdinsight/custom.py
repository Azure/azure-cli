# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.util import sdk_no_wait
from ._client_factory import cf_hdinsight_script_actions, cf_hdinsight_script_execution_history


logger = get_logger(__name__)


# pylint: disable=too-many-locals, too-many-branches, too-many-statements, unused-argument
def create_cluster(cmd, client, cluster_name, resource_group_name, cluster_type, location=None, tags=None,
                   no_wait=False, cluster_version='default', cluster_tier=None,
                   cluster_configurations=None, component_version=None,
                   headnode_size='large', workernode_size='large', zookeepernode_size=None, edgenode_size=None,
                   workernode_count=3, workernode_data_disks_per_node=None,
                   workernode_data_disk_storage_account_type=None, workernode_data_disk_size=None,
                   http_username=None, http_password=None,
                   ssh_username='sshuser', ssh_password=None, ssh_public_key=None,
                   storage_account=None, storage_account_key=None,
                   storage_default_container=None, storage_default_filesystem=None,
                   vnet_name=None, subnet=None,
                   domain=None, ldaps_urls=None,
                   cluster_admin_account=None, cluster_admin_password=None,
                   cluster_users_group_dns=None,
                   assign_identity=None,
                   encryption_vault_uri=None, encryption_key_name=None, encryption_key_version=None,
                   encryption_algorithm='RSA-OAEP', esp=False):
    from .util import build_identities_info, build_virtual_network_profile, parse_domain_name, \
        get_storage_account_endpoint, validate_esp_cluster_create_params
    from azure.mgmt.hdinsight.models import ClusterCreateParametersExtended, ClusterCreateProperties, OSType, \
        ClusterDefinition, ComputeProfile, HardwareProfile, Role, OsProfile, LinuxOperatingSystemProfile, \
        StorageProfile, StorageAccount, DataDisksGroups, SecurityProfile, \
        DirectoryType, DiskEncryptionProperties, Tier

    validate_esp_cluster_create_params(esp, cluster_name, resource_group_name, cluster_type,
                                       subnet, domain, cluster_admin_account, assign_identity,
                                       ldaps_urls, cluster_admin_password, cluster_users_group_dns)

    if esp:
        if cluster_tier == Tier.standard:
            raise CLIError('Cluster tier cannot be {} when --esp is specified. '
                           'Please use default value or specify {} explicitly.'.format(Tier.standard, Tier.premium))
        if not cluster_tier:
            cluster_tier = Tier.premium

    # Update optional parameters with defaults
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

    # Retrieve primary blob service endpoint
    storage_account_endpoint = None
    if storage_account:
        dfs = True if storage_default_filesystem else False
        storage_account_endpoint = get_storage_account_endpoint(cmd, storage_account, dfs)

    # Attempt to infer the storage account key from the endpoint
    if not storage_account_key and storage_account:
        from .util import get_key_for_storage_account
        logger.info('Storage account key not specified. Attempting to retrieve key...')
        key = get_key_for_storage_account(cmd, storage_account)
        if not key:
            raise CLIError('Storage account key could not be inferred from storage account.')
        else:
            storage_account_key = key

    # Attempt to provide a default container for WASB storage accounts
    if not storage_default_container and storage_account_endpoint \
       and _is_wasb_endpoint(storage_account_endpoint):
        storage_default_container = cluster_name
        logger.warning('Default WASB container not specified, using "%s".', storage_default_container)

    # Validate storage info parameters
    if not _all_or_none(storage_account, storage_account_key,
                        (storage_default_container or storage_default_filesystem)):
        raise CLIError('If storage details are specified, the storage account, storage account key, '
                       'and either the default container or default filesystem must be specified.')

    # Validate disk encryption parameters
    if not _all_or_none(encryption_vault_uri, encryption_key_name, encryption_key_version):
        raise CLIError('Either the encryption vault URI, key name and key version should be specified, '
                       'or none of them should be.')

    # Specify virtual network profile only when network arguments are provided
    virtual_network_profile = subnet and build_virtual_network_profile(subnet)

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
                name=storage_account_endpoint,
                key=storage_account_key,
                container=storage_default_container,
                file_system=storage_default_filesystem,
                is_default=True
            )
        )

    additional_storage_accounts = []  # TODO: Add support for additional storage accounts
    if additional_storage_accounts:
        storage_accounts += [
            StorageAccount(
                name=s.storage_account_endpoint,
                key=s.storage_account_key,
                container=s.container,
                is_default=False
            )
            for s in additional_storage_accounts
        ]

    cluster_identity = assign_identity and build_identities_info([assign_identity])

    domain_name = domain and parse_domain_name(domain)
    if not ldaps_urls and domain_name:
        ldaps_urls = ['ldaps://{}:636'.format(domain_name)]

    security_profile = domain and SecurityProfile(
        directory_type=DirectoryType.active_directory,
        domain=domain_name,
        ldaps_urls=ldaps_urls,
        domain_username=cluster_admin_account,
        domain_user_password=cluster_admin_password,
        cluster_users_group_dns=cluster_users_group_dns,
        aadds_resource_id=domain,
        msi_resource_id=assign_identity
    )

    disk_encryption_properties = encryption_vault_uri and DiskEncryptionProperties(
        vault_uri=encryption_vault_uri,
        key_name=encryption_key_name,
        key_version=encryption_key_version,
        encryption_algorithm=encryption_algorithm,
        msi_resource_id=assign_identity
    )

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
            ),
            security_profile=security_profile,
            disk_encryption_properties=disk_encryption_properties
        ),
        identity=cluster_identity
    )

    if no_wait:
        return sdk_no_wait(no_wait, client.create, resource_group_name, cluster_name, create_params)

    return client.create(resource_group_name, cluster_name, create_params)


def list_clusters(cmd, client, resource_group_name=None):  # pylint: disable=unused-argument
    clusters_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()

    return list(clusters_list)


# pylint: disable=unused-argument
def rotate_hdi_cluster_key(cmd, client, resource_group_name, cluster_name,
                           encryption_vault_uri, encryption_key_name, encryption_key_version, no_wait=False):
    from azure.mgmt.hdinsight.models import ClusterDiskEncryptionParameters
    rotate_params = ClusterDiskEncryptionParameters(
        vault_uri=encryption_vault_uri,
        key_name=encryption_key_name,
        key_version=encryption_key_version
    )

    if no_wait:
        return sdk_no_wait(no_wait, client.rotate_disk_encryption_key, resource_group_name, cluster_name, rotate_params)

    return client.rotate_disk_encryption_key(resource_group_name, cluster_name, rotate_params)


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


# pylint: disable=unused-argument
def create_hdi_application(cmd, client, resource_group_name, cluster_name, application_name,
                           script_uri, script_action_name, script_parameters=None, edgenode_size='Standard_D3_V2',
                           ssh_username='sshuser', ssh_password=None, ssh_public_key=None,
                           marketplace_identifier=None, application_type='CustomApplication', tags=None,
                           https_endpoint_access_mode=None, https_endpoint_location=None,
                           https_endpoint_destination_port=8080, https_endpoint_public_port=443,
                           ssh_endpoint_location=None, ssh_endpoint_destination_port=22, ssh_endpoint_public_port=22,
                           vnet_name=None, subnet=None):
    from .util import build_virtual_network_profile
    from azure.mgmt.hdinsight.models import Application, ApplicationProperties, ComputeProfile, RuntimeScriptAction, \
        Role, LinuxOperatingSystemProfile, HardwareProfile, \
        ApplicationGetHttpsEndpoint, ApplicationGetEndpoint, OsProfile

    # Specify virtual network profile only when network arguments are provided
    virtual_network_profile = subnet and build_virtual_network_profile(subnet)

    os_profile = (ssh_password or ssh_public_key) and OsProfile(
        linux_operating_system_profile=LinuxOperatingSystemProfile(
            username=ssh_username,
            password=ssh_password,
            ssh_public_key=ssh_public_key
        )
    )

    roles = [
        Role(
            name="edgenode",
            target_instance_count=1,
            hardware_profile=HardwareProfile(vm_size=edgenode_size),
            os_profile=os_profile,
            virtual_network_profile=virtual_network_profile
        )
    ]

    # Validate network profile parameters
    if not _all_or_none(https_endpoint_access_mode, https_endpoint_location):
        raise CLIError('Either both the https endpoint location and access mode should be specified, '
                       'or neither should be.')

    https_endpoints = []
    if https_endpoint_location:
        https_endpoints.append(
            ApplicationGetHttpsEndpoint(
                access_modes=[https_endpoint_access_mode],
                location=https_endpoint_location,
                destination_port=https_endpoint_destination_port,
                public_port=https_endpoint_public_port,
            )
        )

    ssh_endpoints = []
    if ssh_endpoint_location:
        ssh_endpoints.append(
            ApplicationGetEndpoint(
                location=ssh_endpoint_location,
                destination_port=ssh_endpoint_destination_port,
                public_port=ssh_endpoint_public_port
            )
        )

    application_properties = ApplicationProperties(
        compute_profile=ComputeProfile(
            roles=roles
        ),
        install_script_actions=[
            RuntimeScriptAction(
                name=script_action_name,
                uri=script_uri,
                parameters=script_parameters,
                roles=[role.name for role in roles]
            )
        ],
        https_endpoints=https_endpoints,
        ssh_endpoints=ssh_endpoints,
        application_type=application_type,
        marketplace_identifier=marketplace_identifier,
    )

    create_params = Application(
        tags=tags,
        properties=application_properties
    )

    return client.create(resource_group_name, cluster_name, application_name, create_params)


# pylint: disable=unused-argument
def enable_hdi_monitoring(cmd, client, resource_group_name, cluster_name, workspace_id, primary_key=None):
    return client.enable_monitoring(resource_group_name, cluster_name, workspace_id, primary_key)


# pylint: disable=unused-argument
def execute_hdi_script_action(cmd, client, resource_group_name, cluster_name,
                              script_uri, script_action_name, roles, script_parameters=None,
                              persist_on_success=False):
    from azure.mgmt.hdinsight.models import RuntimeScriptAction

    script_actions_params = [
        RuntimeScriptAction(
            name=script_action_name,
            uri=script_uri,
            parameters=script_parameters,
            roles=roles.split(',')
        )
    ]

    return client.execute_script_actions(resource_group_name, cluster_name, persist_on_success, script_actions_params)


def list_hdi_script_actions(cmd, resource_group_name, cluster_name, persisted=False):
    if persisted:
        client = cf_hdinsight_script_actions(cmd.cli_ctx)
    else:
        client = cf_hdinsight_script_execution_history(cmd.cli_ctx)

    return client.list_by_cluster(resource_group_name, cluster_name)
