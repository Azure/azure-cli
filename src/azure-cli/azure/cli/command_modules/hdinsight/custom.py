# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.prompting import prompt_pass, NoTTYException
from knack.util import CLIError
from azure.cli.core.util import sdk_no_wait, user_confirmation

logger = get_logger(__name__)


# pylint: disable=too-many-locals, too-many-branches, too-many-statements, unused-argument
def create_cluster(cmd, client, cluster_name, resource_group_name, cluster_type,
                   location=None, tags=None, no_wait=False, cluster_version='default', cluster_tier=None,
                   cluster_configurations=None, component_version=None,
                   headnode_size='large', workernode_size='large', zookeepernode_size=None, edgenode_size=None,
                   kafka_management_node_size=None, kafka_management_node_count=2,
                   kafka_client_group_id=None, kafka_client_group_name=None,
                   workernode_count=3, workernode_data_disks_per_node=None,
                   workernode_data_disk_storage_account_type=None, workernode_data_disk_size=None,
                   http_username=None, http_password=None,
                   ssh_username='sshuser', ssh_password=None, ssh_public_key=None,
                   storage_account=None, storage_account_key=None,
                   storage_default_container=None, storage_default_filesystem=None,
                   storage_account_managed_identity=None,
                   vnet_name=None, subnet=None,
                   domain=None, ldaps_urls=None,
                   cluster_admin_account=None, cluster_admin_password=None,
                   cluster_users_group_dns=None,
                   assign_identity=None,
                   minimal_tls_version=None,
                   encryption_vault_uri=None, encryption_key_name=None, encryption_key_version=None,
                   encryption_algorithm='RSA-OAEP', encryption_in_transit=None,
                   autoscale_type=None, autoscale_min_workernode_count=None, autoscale_max_workernode_count=None,
                   timezone=None, days=None, time=None, autoscale_workernode_count=None,
                   encryption_at_host=None, esp=False, idbroker=False,
                   resource_provider_connection=None, enable_private_link=None, enable_compute_isolation=None,
                   host_sku=None, no_validation_timeout=False):
    from .util import build_identities_info, build_virtual_network_profile, parse_domain_name, \
        get_storage_account_endpoint, validate_esp_cluster_create_params
    from azure.mgmt.hdinsight.models import ClusterCreateParametersExtended, ClusterCreateProperties, OSType, \
        ClusterDefinition, ComputeProfile, HardwareProfile, Role, OsProfile, LinuxOperatingSystemProfile, \
        StorageProfile, StorageAccount, DataDisksGroups, SecurityProfile, \
        DirectoryType, DiskEncryptionProperties, Tier, SshProfile, SshPublicKey, \
        KafkaRestProperties, ClientGroupInfo, EncryptionInTransitProperties, \
        Autoscale, AutoscaleCapacity, AutoscaleRecurrence, AutoscaleSchedule, AutoscaleTimeAndCapacity, \
        NetworkProperties, PrivateLink, ComputeIsolationProperties

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
    if not cluster_configurations:
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
    if not http_username:
        http_username = 'admin'  # Implement default logic here, in case a user specifies the username in configurations

    if not http_password:
        try:
            http_password = prompt_pass('HTTP password for the cluster:', confirm=True)
        except NoTTYException:
            raise CLIError('Please specify --http-password in non-interactive mode.')

    # Update the cluster config with the HTTP credentials
    gateway_config['restAuthCredential.isEnabled'] = 'true'  # HTTP credentials are required
    http_username = http_username or gateway_config['restAuthCredential.username']
    gateway_config['restAuthCredential.username'] = http_username
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
    is_wasb = not storage_account_managed_identity
    storage_account_endpoint = None
    if storage_account:
        storage_account_endpoint = get_storage_account_endpoint(cmd, storage_account, is_wasb)

    # Attempt to infer the storage account key from the endpoint
    if not storage_account_key and storage_account and is_wasb:
        from .util import get_key_for_storage_account
        logger.info('Storage account key not specified. Attempting to retrieve key...')
        key = get_key_for_storage_account(cmd, storage_account)
        if not key:
            raise CLIError('Storage account key could not be inferred from storage account.')
        storage_account_key = key

    # Attempt to provide a default container for WASB storage accounts
    if not storage_default_container and storage_account and is_wasb:
        storage_default_container = cluster_name.lower()
        logger.warning('Default WASB container not specified, using "%s".', storage_default_container)
    elif not storage_default_filesystem and not is_wasb:
        storage_default_filesystem = cluster_name.lower()
        logger.warning('Default ADLS file system not specified, using "%s".', storage_default_filesystem)

    # Validate storage info parameters
    if is_wasb and not _all_or_none(storage_account, storage_account_key, storage_default_container):
        raise CLIError('If storage details are specified, the storage account, storage account key, '
                       'and the default container must be specified.')
    if not is_wasb and not _all_or_none(storage_account, storage_default_filesystem):
        raise CLIError('If storage details are specified, the storage account, '
                       'and the default filesystem must be specified.')

    # Validate disk encryption parameters
    if not _all_or_none(encryption_vault_uri, encryption_key_name, encryption_key_version):
        raise CLIError('Either the encryption vault URI, key name and key version should be specified, '
                       'or none of them should be.')

    # Validate kafka rest proxy parameters
    if not _all_or_none(kafka_client_group_id, kafka_client_group_name):
        raise CLIError('Either the kafka client group id and kafka client group name should be specified, '
                       'or none of them should be')

    # Validate and initialize autoscale setting
    autoscale_configuration = None
    load_based_type = "Load"
    schedule_based_type = "Schedule"
    if autoscale_type and autoscale_type.lower() == load_based_type.lower():
        if not all([autoscale_min_workernode_count, autoscale_max_workernode_count]):
            raise CLIError(
                'When the --autoscale-type is Load, '
                'both --autoscale-min-workernode-count and --autoscale-max-workernode-count should be specified.')

        autoscale_configuration = Autoscale(
            capacity=AutoscaleCapacity(
                min_instance_count=autoscale_min_workernode_count,
                max_instance_count=autoscale_max_workernode_count
            )
        )
    elif autoscale_type and autoscale_type.lower() == schedule_based_type.lower():
        if not all([timezone, days, time, autoscale_workernode_count]):
            raise CLIError(
                'When the --autoscale-type is Schedule, all of the --timezone, --days, --time, '
                '--autoscale-workernode-count should be specified.')

        autoscale_configuration = Autoscale(
            recurrence=AutoscaleRecurrence(
                time_zone=timezone,
                schedule=[AutoscaleSchedule(
                    days=days,
                    time_and_capacity=AutoscaleTimeAndCapacity(
                        time=time,
                        min_instance_count=autoscale_workernode_count,
                        max_instance_count=autoscale_workernode_count
                    )
                )]
            )
        )

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
            ssh_profile=ssh_public_key and SshProfile(
                public_keys=[SshPublicKey(
                    certificate_data=ssh_public_key
                )]
            )
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
            data_disks_groups=workernode_data_disk_groups,
            autoscale_configuration=autoscale_configuration
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
    if kafka_management_node_size:
        # generate kafkaRestProperties
        roles.append(
            Role(
                name="kafkamanagementnode",
                target_instance_count=kafka_management_node_count,
                hardware_profile=HardwareProfile(vm_size=kafka_management_node_size),
                os_profile=os_profile,
                virtual_network_profile=virtual_network_profile
            )
        )

    if esp and idbroker:
        roles.append(
            Role(
                name="idbrokernode",
                target_instance_count=2,
                virtual_network_profile=virtual_network_profile
            )
        )

    storage_accounts = []
    if storage_account:
        # Specify storage account details only when storage arguments are provided
        storage_accounts.append(
            StorageAccount(
                name=storage_account_endpoint,
                key=storage_account_key,
                container=storage_default_container,
                file_system=storage_default_filesystem,
                resource_id=storage_account,
                msi_resource_id=storage_account_managed_identity,
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

    assign_identities = []
    if assign_identity:
        assign_identities.append(assign_identity)

    if storage_account_managed_identity:
        assign_identities.append(storage_account_managed_identity)

    cluster_identity = build_identities_info(assign_identities) if assign_identities else None

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

    if encryption_at_host:
        if disk_encryption_properties:
            disk_encryption_properties.encryption_at_host = encryption_at_host
        else:
            disk_encryption_properties = DiskEncryptionProperties(encryption_at_host=encryption_at_host)

    kafka_rest_properties = (kafka_client_group_id and kafka_client_group_name) and KafkaRestProperties(
        client_group_info=ClientGroupInfo(
            group_id=kafka_client_group_id,
            group_name=kafka_client_group_name
        )
    )

    encryption_in_transit_properties = encryption_in_transit and EncryptionInTransitProperties(
        is_encryption_in_transit_enabled=encryption_in_transit
    )

    # relay outbound and private link
    network_properties = (resource_provider_connection or enable_private_link) and NetworkProperties(
        resource_provider_connection=resource_provider_connection,
        private_link=PrivateLink.enabled if enable_private_link is True else PrivateLink.disabled
    )

    # compute isolation
    compute_isolation_properties = enable_compute_isolation and ComputeIsolationProperties(
        enable_compute_isolation=enable_compute_isolation,
        host_sku=host_sku
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
            disk_encryption_properties=disk_encryption_properties,
            kafka_rest_properties=kafka_rest_properties,
            min_supported_tls_version=minimal_tls_version,
            encryption_in_transit_properties=encryption_in_transit_properties,
            network_properties=network_properties,
            compute_isolation_properties=compute_isolation_properties
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


# pylint: disable=unused-argument
def create_hdi_application(cmd, client, resource_group_name, cluster_name, application_name,
                           script_uri, script_action_name, script_parameters=None, edgenode_size='Standard_D3_V2',
                           ssh_username='sshuser', ssh_password=None, ssh_public_key=None,
                           marketplace_identifier=None, application_type='CustomApplication', tags=None,
                           https_endpoint_access_mode='WebPage', https_endpoint_destination_port=8080,
                           sub_domain_suffix=None, disable_gateway_auth=None,
                           vnet_name=None, subnet=None, no_validation_timeout=False):
    from .util import build_virtual_network_profile
    from azure.mgmt.hdinsight.models import Application, ApplicationProperties, ComputeProfile, RuntimeScriptAction, \
        Role, LinuxOperatingSystemProfile, HardwareProfile, \
        ApplicationGetHttpsEndpoint, OsProfile, SshProfile, SshPublicKey

    # Specify virtual network profile only when network arguments are provided
    virtual_network_profile = subnet and build_virtual_network_profile(subnet)

    os_profile = (ssh_password or ssh_public_key) and OsProfile(
        linux_operating_system_profile=LinuxOperatingSystemProfile(
            username=ssh_username,
            password=ssh_password,
            ssh_profile=ssh_public_key and SshProfile(
                public_keys=[SshPublicKey(
                    certificate_data=ssh_public_key
                )]
            )
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
    https_endpoints = []
    if sub_domain_suffix:
        https_endpoints.append(
            ApplicationGetHttpsEndpoint(
                access_modes=[https_endpoint_access_mode],
                destination_port=https_endpoint_destination_port,
                sub_domain_suffix=sub_domain_suffix,
                disable_gateway_auth=disable_gateway_auth
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
        application_type=application_type,
        marketplace_identifier=marketplace_identifier,
    )

    create_params = Application(
        tags=tags,
        properties=application_properties
    )

    return client.create(resource_group_name, cluster_name, application_name, create_params)


# pylint: disable=unused-argument
def enable_hdi_monitoring(cmd, client, resource_group_name, cluster_name, workspace,
                          primary_key=None, workspace_type='resource_id', no_validation_timeout=False):
    from msrestazure.tools import parse_resource_id
    from ._client_factory import cf_log_analytics

    if workspace_type != 'resource_id' and not primary_key:
        raise CLIError('primary key is required when workspace ID is provided')

    workspace_id = workspace
    if workspace_type == 'resource_id':
        parsed_workspace = parse_resource_id(workspace)
        workspace_resource_group_name = parsed_workspace['resource_group']
        workspace_name = parsed_workspace['resource_name']

        log_analytics_client = cf_log_analytics(cmd.cli_ctx)
        log_analytics_workspace = log_analytics_client.workspaces.get(workspace_resource_group_name, workspace_name)
        if not log_analytics_workspace:
            raise CLIError('Fails to retrieve workspace by {}'.format(workspace))

        # Only retrieve primary key when not provided
        if not primary_key:
            shared_keys = log_analytics_client.shared_keys.get_shared_keys(workspace_resource_group_name,
                                                                           workspace_name)
            if not shared_keys:
                raise CLIError('Fails to retrieve shared key for workspace {}'.format(log_analytics_workspace))

            primary_key = shared_keys.primary_shared_key

        workspace_id = log_analytics_workspace.customer_id

    return client.enable_monitoring(
        resource_group_name,
        cluster_name,
        workspace_id,
        primary_key)


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
            roles=roles
        )
    ]

    return client.execute_script_actions(resource_group_name, cluster_name, persist_on_success, script_actions_params)


# pylint: disable=redefined-builtin
def create_autoscale(cmd, client, resource_group_name, cluster_name, type, min_workernode_count=None,
                     max_workernode_count=None, timezone=None, days=None, time=None, workernode_count=None,
                     no_wait=False, yes=False):
    from azure.mgmt.hdinsight.models import Autoscale, AutoscaleCapacity, AutoscaleRecurrence, AutoscaleSchedule, \
        AutoscaleTimeAndCapacity
    load_based_type = "Load"
    schedule_based_type = "Schedule"
    autoscale_configuration = None

    if type.lower() == load_based_type.lower():
        if not all([min_workernode_count, max_workernode_count]):
            raise CLIError(
                'When the --type is Load, both --min-workernode-count and --max-workernode-count should be specified.')

        autoscale_configuration = Autoscale(
            capacity=AutoscaleCapacity(
                min_instance_count=min_workernode_count,
                max_instance_count=max_workernode_count
            )
        )
    elif type.lower() == schedule_based_type.lower():
        if not all([timezone, days, time, workernode_count]):
            raise CLIError(
                'When the --type is Schedule, all of the --timezone, --days, --time, '
                '--workernode-count should be specified.')

        autoscale_configuration = Autoscale(
            recurrence=AutoscaleRecurrence(
                time_zone=timezone,
                schedule=[AutoscaleSchedule(
                    days=days,
                    time_and_capacity=AutoscaleTimeAndCapacity(
                        time=time,
                        min_instance_count=workernode_count,
                        max_instance_count=workernode_count
                    )
                )]
            )
        )

    user_confirmation(
        "This operation will override previous autoscale configuration. "
        "Are you sure you want to perform this operation", yes)

    return sdk_no_wait(no_wait, client.update_auto_scale_configuration, resource_group_name, cluster_name,
                       autoscale_configuration)


def update_autoscale(cmd, client, resource_group_name, cluster_name, min_workernode_count=None,
                     max_workernode_count=None, timezone=None, no_wait=False):
    from azure.mgmt.hdinsight.models import AutoscaleCapacity, AutoscaleRecurrence
    cluster = client.get(resource_group_name, cluster_name)
    autoscale_configuration = _extract_and_validate_autoscale_configuration(cluster)

    # try to update load-based configuration
    if autoscale_configuration.capacity:
        if min_workernode_count:
            autoscale_configuration.capacity.min_instance_count = min_workernode_count
        if max_workernode_count:
            autoscale_configuration.capacity.max_instance_count = max_workernode_count

    if not autoscale_configuration.capacity:
        if min_workernode_count or max_workernode_count:
            autoscale_configuration.capacity = AutoscaleCapacity()
            if min_workernode_count:
                autoscale_configuration.capacity.min_instance_count = min_workernode_count
            if max_workernode_count:
                autoscale_configuration.capacity.max_instance_count = max_workernode_count

    # try to update schedule-based configuration
    if timezone:
        if autoscale_configuration.recurrence:
            autoscale_configuration.recurrence.time_zone = timezone
        elif not autoscale_configuration.recurrence:
            autoscale_configuration.recurrence = AutoscaleRecurrence(time_zone=timezone)

    return sdk_no_wait(no_wait, client.update_auto_scale_configuration, resource_group_name, cluster_name,
                       autoscale_configuration)


def show_autoscale(cmd, client, resource_group_name, cluster_name):
    cluster = client.get(resource_group_name, cluster_name)
    autoscale_configuration = _extract_and_validate_autoscale_configuration(cluster)
    return autoscale_configuration


def delete_autoscale(cmd, client, resource_group_name, cluster_name, no_wait=False):
    cluster = client.get(resource_group_name, cluster_name)
    _extract_and_validate_autoscale_configuration(cluster)
    autoscale_configuration = None

    return sdk_no_wait(no_wait, client.update_auto_scale_configuration, resource_group_name, cluster_name,
                       autoscale_configuration)


def list_timezones(cmd, client):
    from .util import AUTOSCALE_TIMEZONES
    return AUTOSCALE_TIMEZONES


def create_autoscale_condition(cmd, client, resource_group_name, cluster_name, days, time, workernode_count,
                               no_wait=False):
    from azure.mgmt.hdinsight.models import AutoscaleRecurrence, AutoscaleSchedule, AutoscaleTimeAndCapacity
    cluster = client.get(resource_group_name, cluster_name)
    autoscale_configuration = _extract_and_validate_autoscale_configuration(cluster)

    # try to add schedule condition
    condition = AutoscaleSchedule(
        days=days,
        time_and_capacity=AutoscaleTimeAndCapacity(
            time=time,
            min_instance_count=workernode_count,
            max_instance_count=workernode_count)
    )
    if autoscale_configuration.recurrence:
        autoscale_configuration.recurrence.schedule.append(condition)
    elif not autoscale_configuration.recurrence:
        autoscale_configuration.recurrence = AutoscaleRecurrence(
            schedule=[condition]
        )

    return sdk_no_wait(no_wait, client.update_auto_scale_configuration, resource_group_name, cluster_name,
                       autoscale_configuration)


def update_autoscale_condition(cmd, client, resource_group_name, cluster_name, index, days=None, time=None,
                               workernode_count=None, no_wait=False):
    cluster = client.get(resource_group_name, cluster_name)
    autoscale_configuration = _extract_and_validate_autoscale_configuration(cluster)
    _validate_schedule_configuration(autoscale_configuration)

    if index >= len(autoscale_configuration.recurrence.schedule):
        raise CLIError(
            'This cluster only has {} condition(s). Please specify a correct index which starts with 0.'.format(
                len(autoscale_configuration.recurrence.schedule)))

    # try to update schedule condition
    if days:
        autoscale_configuration.recurrence.schedule[index].days = days
    if time:
        autoscale_configuration.recurrence.schedule[index].time_and_capacity.time = time
    if workernode_count:
        autoscale_configuration.recurrence.schedule[index].time_and_capacity.min_instance_count = workernode_count
        autoscale_configuration.recurrence.schedule[index].time_and_capacity.max_instance_count = workernode_count

    return sdk_no_wait(no_wait, client.update_auto_scale_configuration, resource_group_name, cluster_name,
                       autoscale_configuration)


def delete_autoscale_condition(cmd, client, resource_group_name, cluster_name, index, no_wait=False):
    cluster = client.get(resource_group_name, cluster_name)
    autoscale_configuration = _extract_and_validate_autoscale_configuration(cluster)
    _validate_schedule_configuration(autoscale_configuration)

    conditions_count = len(autoscale_configuration.recurrence.schedule)
    if len(index) >= conditions_count:
        raise CLIError('Deleting all conditions is not allowed.'
                       'If you want to disable autoscale please use `az hdinsight autoscale delete`.')
    autoscale_configuration.recurrence.schedule = [autoscale_configuration.recurrence.schedule[i] for i in
                                                   range(conditions_count) if i not in index]
    return sdk_no_wait(no_wait, client.update_auto_scale_configuration, resource_group_name, cluster_name,
                       autoscale_configuration)


def list_autoscale_condition(cmd, client, resource_group_name, cluster_name):
    cluster = client.get(resource_group_name, cluster_name)
    autoscale_configuration = _extract_and_validate_autoscale_configuration(cluster)
    _validate_schedule_configuration(autoscale_configuration)
    return autoscale_configuration.recurrence.schedule


def _extract_and_validate_autoscale_configuration(cluster):
    autoscale_configuration = None
    for role in cluster.properties.compute_profile.roles:
        if role.name == "workernode":
            autoscale_configuration = role.autoscale_configuration
            break
    if not autoscale_configuration:
        raise CLIError('The cluster has not enabled autoscale.')
    return autoscale_configuration


def _validate_schedule_configuration(autoscale_configuration):
    if not autoscale_configuration.recurrence:
        raise CLIError('The cluster has not enabled Schedule-based autoscale.')
