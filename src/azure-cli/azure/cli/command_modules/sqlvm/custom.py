# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrestazure.tools import is_valid_resource_id, resource_id
from knack.prompting import prompt_pass
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.util import (
    sdk_no_wait
)

from azure.mgmt.sqlvirtualmachine.models import (
    WsfcDomainProfile,
    SqlVirtualMachineGroup,
    PrivateIPAddress,
    LoadBalancerConfiguration,
    AvailabilityGroupListener,
    WsfcDomainCredentials,
    AutoPatchingSettings,
    AutoBackupSettings,
    KeyVaultCredentialSettings,
    SqlConnectivityUpdateSettings,
    SqlWorkloadTypeUpdateSettings,
    AdditionalFeaturesServerConfigurations,
    ServerConfigurationsManagementSettings,
    SqlVirtualMachine
)


def sqlvm_list(
        client,
        resource_group_name=None):
    '''
    Lists all SQL virtual machines in a resource group or subscription.
    '''
    if resource_group_name:
        # List all sql vms  in the resource group
        return client.list_by_resource_group(resource_group_name=resource_group_name)

    # List all sql vms in the subscription
    return client.list()


def sqlvm_group_list(
        client,
        resource_group_name=None):
    '''
    Lists all SQL virtual machine groups in a resource group or subscription.
    '''
    if resource_group_name:
        # List all sql vm groups in the resource group
        return client.list_by_resource_group(resource_group_name=resource_group_name)

    # List all sql vm groups in the subscription
    return client.list()


# pylint: disable= line-too-long, too-many-arguments
def sqlvm_group_create(client, cmd, sql_virtual_machine_group_name, resource_group_name, sql_image_offer,
                       sql_image_sku, domain_fqdn, cluster_operator_account, sql_service_account,
                       storage_account_url, storage_account_key=None, location=None, cluster_bootstrap_account=None,
                       file_share_witness_path=None, ou_path=None, tags=None):
    '''
    Creates a SQL virtual machine group.
    '''
    tags = tags or {}

    if not storage_account_key:
        storage_account_key = prompt_pass('Storage Key: ', confirm=True)

    # Create the windows server failover cluster domain profile object.
    wsfc_domain_profile_object = WsfcDomainProfile(domain_fqdn=domain_fqdn,
                                                   ou_path=ou_path,
                                                   cluster_bootstrap_account=cluster_bootstrap_account,
                                                   cluster_operator_account=cluster_operator_account,
                                                   sql_service_account=sql_service_account,
                                                   file_share_witness_path=file_share_witness_path,
                                                   storage_account_url=storage_account_url,
                                                   storage_account_primary_key=storage_account_key)

    sqlvm_group_object = SqlVirtualMachineGroup(sql_image_offer=sql_image_offer,
                                                sql_image_sku=sql_image_sku,
                                                wsfc_domain_profile=wsfc_domain_profile_object,
                                                location=location,
                                                tags=tags)

    # Since it's a running operation, we will do the put and then the get to display the instance.
    LongRunningOperation(cmd.cli_ctx)(sdk_no_wait(False, client.begin_create_or_update, resource_group_name,
                                                  sql_virtual_machine_group_name, sqlvm_group_object))

    return client.get(resource_group_name, sql_virtual_machine_group_name)


# pylint: disable=line-too-long, too-many-arguments
def sqlvm_group_update(instance, domain_fqdn=None, cluster_operator_account=None, sql_service_account=None,
                       storage_account_url=None, storage_account_key=None, cluster_bootstrap_account=None,
                       file_share_witness_path=None, ou_path=None, tags=None):
    '''
    Updates a SQL virtual machine group.
    '''
    if domain_fqdn is not None:
        instance.wsfc_domain_profile.domain_fqdn = domain_fqdn
    if cluster_operator_account is not None:
        instance.wsfc_domain_profile.cluster_operator_account = cluster_operator_account
    if cluster_bootstrap_account is not None:
        instance.wsfc_domain_profile.cluster_bootstrap_account = cluster_bootstrap_account
    if sql_service_account is not None:
        instance.wsfc_domain_profile.sql_service_account = sql_service_account
    if storage_account_url is not None:
        instance.wsfc_domain_profile.storage_account_url = storage_account_url
    if storage_account_key is not None:
        instance.wsfc_domain_profile.storage_account_primary_key = storage_account_key
    if storage_account_url and not storage_account_key:
        instance.wsfc_domain_profile.storage_account_primary_key = prompt_pass('Storage Key: ', confirm=True)
    if file_share_witness_path is not None:
        instance.wsfc_domain_profile.file_share_witness_path = file_share_witness_path
    if ou_path is not None:
        instance.wsfc_domain_profile.ou_path = ou_path
    if tags is not None:
        instance.tags = tags

    return instance


# pylint: disable=line-too-long, too-many-boolean-expressions, too-many-arguments
def sqlvm_aglistener_create(client, cmd, availability_group_listener_name, sql_virtual_machine_group_name,
                            resource_group_name, availability_group_name, ip_address, subnet_resource_id,
                            load_balancer_resource_id, probe_port, sql_virtual_machine_instances, port=1433,
                            public_ip_address_resource_id=None, vnet_name=None):  # pylint: disable=unused-argument
    '''
    Creates an availability group listener
    '''
    # Create the private ip address
    private_ip_object = PrivateIPAddress(ip_address=ip_address,
                                         subnet_resource_id=subnet_resource_id
                                         if is_valid_resource_id(subnet_resource_id) else None)

    # Create the load balancer configurations
    load_balancer_object = LoadBalancerConfiguration(private_ip_address=private_ip_object,
                                                     public_ip_address_resource_id=public_ip_address_resource_id,
                                                     load_balancer_resource_id=load_balancer_resource_id,
                                                     probe_port=probe_port,
                                                     sql_virtual_machine_instances=sql_virtual_machine_instances)

    # Create the availability group listener object
    ag_listener_object = AvailabilityGroupListener(availability_group_name=availability_group_name,
                                                   load_balancer_configurations=[load_balancer_object],
                                                   port=port)

    LongRunningOperation(cmd.cli_ctx)(sdk_no_wait(False, client.begin_create_or_update, resource_group_name,
                                                  sql_virtual_machine_group_name, availability_group_listener_name,
                                                  ag_listener_object))

    return client.get(resource_group_name, sql_virtual_machine_group_name, availability_group_listener_name)


def aglistener_update(instance, sql_virtual_machine_instances=None):
    '''
    Updates an availability group listener
    '''
    # Get the list of all current machines in the ag listener
    if sql_virtual_machine_instances:
        instance.load_balancer_configurations[0].sql_virtual_machine_instances = sql_virtual_machine_instances

    return instance


# pylint: disable=too-many-arguments, too-many-locals, line-too-long, too-many-boolean-expressions
def sqlvm_create(client, cmd, sql_virtual_machine_name, resource_group_name, sql_server_license_type=None,
                 location=None, sql_image_sku=None, enable_auto_patching=None, sql_management_mode="LightWeight",
                 day_of_week=None, maintenance_window_starting_hour=None, maintenance_window_duration=None,
                 enable_auto_backup=None, enable_encryption=False, retention_period=None, storage_account_url=None,
                 storage_access_key=None, backup_password=None, backup_system_dbs=False, backup_schedule_type=None,
                 full_backup_frequency=None, full_backup_start_time=None, full_backup_window_hours=None, log_backup_frequency=None,
                 enable_key_vault_credential=None, credential_name=None, azure_key_vault_url=None, service_principal_name=None,
                 service_principal_secret=None, connectivity_type=None, port=None, sql_auth_update_username=None,
                 sql_auth_update_password=None, sql_workload_type=None, enable_r_services=None, tags=None, sql_image_offer=None):
    '''
    Creates a SQL virtual machine.
    '''
    from azure.cli.core.commands.client_factory import get_subscription_id

    subscription_id = get_subscription_id(cmd.cli_ctx)

    virtual_machine_resource_id = resource_id(
        subscription=subscription_id, resource_group=resource_group_name,
        namespace='Microsoft.Compute', type='virtualMachines', name=sql_virtual_machine_name)

    tags = tags or {}

    # If customer has provided any auto_patching settings, enabling plugin should be True
    if (day_of_week or maintenance_window_duration or maintenance_window_starting_hour):
        enable_auto_patching = True

    auto_patching_object = AutoPatchingSettings(enable=enable_auto_patching,
                                                day_of_week=day_of_week,
                                                maintenance_window_starting_hour=maintenance_window_starting_hour,
                                                maintenance_window_duration=maintenance_window_duration)

    # If customer has provided any auto_backup settings, enabling plugin should be True
    if (enable_encryption or retention_period or storage_account_url or storage_access_key or backup_password or
            backup_system_dbs or backup_schedule_type or full_backup_frequency or full_backup_start_time or
            full_backup_window_hours or log_backup_frequency):
        enable_auto_backup = True
        if not storage_access_key:
            storage_access_key = prompt_pass('Storage Key: ', confirm=True)
        if enable_encryption and not backup_password:
            backup_password = prompt_pass('Backup Password: ', confirm=True)

    auto_backup_object = AutoBackupSettings(enable=enable_auto_backup,
                                            enable_encryption=enable_encryption if enable_auto_backup else None,
                                            retention_period=retention_period,
                                            storage_account_url=storage_account_url,
                                            storage_access_key=storage_access_key,
                                            password=backup_password,
                                            backup_system_dbs=backup_system_dbs if enable_auto_backup else None,
                                            backup_schedule_type=backup_schedule_type,
                                            full_backup_frequency=full_backup_frequency,
                                            full_backup_start_time=full_backup_start_time,
                                            full_backup_window_hours=full_backup_window_hours,
                                            log_backup_frequency=log_backup_frequency)

    # If customer has provided any key_vault_credential settings, enabling plugin should be True
    if (credential_name or azure_key_vault_url or service_principal_name or service_principal_secret):
        enable_key_vault_credential = True
        if not service_principal_secret:
            service_principal_secret = prompt_pass('Service Principal Secret: ', confirm=True)

    keyvault_object = KeyVaultCredentialSettings(enable=enable_key_vault_credential,
                                                 credential_name=credential_name,
                                                 azure_key_vault_url=azure_key_vault_url,
                                                 service_principal_name=service_principal_name,
                                                 service_principal_secret=service_principal_secret)

    connectivity_object = SqlConnectivityUpdateSettings(port=port,
                                                        connectivity_type=connectivity_type,
                                                        sql_auth_update_user_name=sql_auth_update_username,
                                                        sql_auth_update_password=sql_auth_update_password)

    workload_type_object = SqlWorkloadTypeUpdateSettings(sql_workload_type=sql_workload_type)

    additional_features_object = AdditionalFeaturesServerConfigurations(is_rservices_enabled=enable_r_services)

    server_configuration_object = ServerConfigurationsManagementSettings(sql_connectivity_update_settings=connectivity_object,
                                                                         sql_workload_type_update_settings=workload_type_object,
                                                                         additional_features_server_configurations=additional_features_object)

    sqlvm_object = SqlVirtualMachine(location=location,
                                     virtual_machine_resource_id=virtual_machine_resource_id,
                                     sql_server_license_type=sql_server_license_type,
                                     sql_image_sku=sql_image_sku,
                                     sql_management=sql_management_mode,
                                     sql_image_offer=sql_image_offer,
                                     auto_patching_settings=auto_patching_object,
                                     auto_backup_settings=auto_backup_object,
                                     key_vault_credential_settings=keyvault_object,
                                     server_configurations_management_settings=server_configuration_object,
                                     tags=tags)

    # Since it's a running operation, we will do the put and then the get to display the instance.
    LongRunningOperation(cmd.cli_ctx)(sdk_no_wait(False, client.begin_create_or_update,
                                                  resource_group_name, sql_virtual_machine_name, sqlvm_object))

    return client.get(resource_group_name, sql_virtual_machine_name)


# pylint: disable=too-many-statements, line-too-long, too-many-boolean-expressions
def sqlvm_update(instance, sql_server_license_type=None, sql_image_sku=None, enable_auto_patching=None,
                 day_of_week=None, maintenance_window_starting_hour=None, maintenance_window_duration=None,
                 enable_auto_backup=None, enable_encryption=False, retention_period=None, storage_account_url=None, prompt=True,
                 storage_access_key=None, backup_password=None, backup_system_dbs=False, backup_schedule_type=None, sql_management_mode=None,
                 full_backup_frequency=None, full_backup_start_time=None, full_backup_window_hours=None, log_backup_frequency=None,
                 enable_key_vault_credential=None, credential_name=None, azure_key_vault_url=None, service_principal_name=None,
                 service_principal_secret=None, connectivity_type=None, port=None, sql_workload_type=None, enable_r_services=None, tags=None):
    '''
    Updates a SQL virtual machine.
    '''
    if tags is not None:
        instance.tags = tags
    if sql_server_license_type is not None:
        instance.sql_server_license_type = sql_server_license_type
    if sql_image_sku is not None:
        instance.sql_image_sku = sql_image_sku
    if sql_management_mode is not None and instance.sql_management != "Full":
        from knack.prompting import prompt_y_n
        if not prompt:
            instance.sql_management = sql_management_mode
        else:
            confirmation = prompt_y_n("Upgrading SQL manageability mode to Full will restart the SQL Server. Proceed?")
            if confirmation:
                instance.sql_management = sql_management_mode

    if (enable_auto_patching is not None or day_of_week is not None or maintenance_window_starting_hour is not None or maintenance_window_duration is not None):

        enable_auto_patching = enable_auto_patching if enable_auto_patching is False else True
        instance.auto_patching_settings = AutoPatchingSettings(enable=enable_auto_patching,
                                                               day_of_week=day_of_week,
                                                               maintenance_window_starting_hour=maintenance_window_starting_hour,
                                                               maintenance_window_duration=maintenance_window_duration)

    if (enable_auto_backup is not None or enable_encryption or retention_period is not None or storage_account_url is not None or
            storage_access_key is not None or backup_password is not None or backup_system_dbs or backup_schedule_type is not None or
            full_backup_frequency is not None or full_backup_start_time is not None or full_backup_window_hours is not None or
            log_backup_frequency is not None):

        enable_auto_backup = enable_auto_backup if enable_auto_backup is False else True
        if not storage_access_key:
            storage_access_key = prompt_pass('Storage Key: ', confirm=True)
        if enable_encryption and not backup_password:
            backup_password = prompt_pass('Backup Password: ', confirm=True)

        instance.auto_backup_settings = AutoBackupSettings(enable=enable_auto_backup,
                                                           enable_encryption=enable_encryption if enable_auto_backup else None,
                                                           retention_period=retention_period,
                                                           storage_account_url=storage_account_url,
                                                           storage_access_key=storage_access_key,
                                                           password=backup_password,
                                                           backup_system_dbs=backup_system_dbs if enable_auto_backup else None,
                                                           backup_schedule_type=backup_schedule_type,
                                                           full_backup_frequency=full_backup_frequency,
                                                           full_backup_start_time=full_backup_start_time,
                                                           full_backup_window_hours=full_backup_window_hours,
                                                           log_backup_frequency=log_backup_frequency)

    if (enable_key_vault_credential is not None or credential_name is not None or azure_key_vault_url is not None or
            service_principal_name is not None or service_principal_secret is not None):

        enable_key_vault_credential = enable_key_vault_credential if enable_key_vault_credential is False else True
        if not service_principal_secret:
            service_principal_secret = prompt_pass('Service Principal Secret: ', confirm=True)

        instance.key_vault_credential_settings = KeyVaultCredentialSettings(enable=enable_key_vault_credential,
                                                                            credential_name=credential_name,
                                                                            service_principal_name=service_principal_name,
                                                                            service_principal_secret=service_principal_secret,
                                                                            azure_key_vault_url=azure_key_vault_url)

    instance.server_configurations_management_settings = ServerConfigurationsManagementSettings()

    if (connectivity_type is not None or port is not None):
        instance.server_configurations_management_settings.sql_connectivity_update_settings = SqlConnectivityUpdateSettings(connectivity_type=connectivity_type,
                                                                                                                            port=port)

    if sql_workload_type is not None:
        instance.server_configurations_management_settings.sql_workload_type_update_settings = SqlWorkloadTypeUpdateSettings(sql_workload_type=sql_workload_type)

    if enable_r_services is not None:
        instance.server_configurations_management_settings.additional_features_server_configurations = AdditionalFeaturesServerConfigurations(is_rservices_enabled=enable_r_services)

    # If none of the settings was modified, reset server_configurations_management_settings to be null
    if (instance.server_configurations_management_settings.sql_connectivity_update_settings is None and
            instance.server_configurations_management_settings.sql_workload_type_update_settings is None and
            instance.server_configurations_management_settings.sql_storage_update_settings is None and
            instance.server_configurations_management_settings.additional_features_server_configurations is None):
        instance.server_configurations_management_settings = None

    return instance


def sqlvm_add_to_group(client, cmd, sql_virtual_machine_name, resource_group_name,
                       sql_virtual_machine_group_resource_id, sql_service_account_password=None,
                       cluster_operator_account_password=None, cluster_bootstrap_account_password=None):
    '''
    Adds a SQL virtual machine to a group.
    '''

    sqlvm_object = client.get(resource_group_name, sql_virtual_machine_name)

    if not sql_service_account_password:
        sql_service_account_password = prompt_pass('SQL Service account password: ', confirm=True)
    if not cluster_operator_account_password:
        cluster_operator_account_password = prompt_pass('Cluster operator account password: ', confirm=True,
                                                        help_string='Password to authenticate with the domain controller.')

    sqlvm_object.sql_virtual_machine_group_resource_id = sql_virtual_machine_group_resource_id

    sqlvm_object.wsfc_domain_credentials = WsfcDomainCredentials(cluster_bootstrap_account_password=cluster_bootstrap_account_password,
                                                                 cluster_operator_account_password=cluster_operator_account_password,
                                                                 sql_service_account_password=sql_service_account_password)

    # Since it's a running operation, we will do the put and then the get to display the instance.
    LongRunningOperation(cmd.cli_ctx)(sdk_no_wait(False, client.begin_create_or_update,
                                                  resource_group_name, sql_virtual_machine_name, sqlvm_object))

    return client.get(resource_group_name, sql_virtual_machine_name)


def sqlvm_remove_from_group(client, cmd, sql_virtual_machine_name, resource_group_name):
    '''
    Removes a SQL virtual machine from a group.
    '''

    sqlvm_object = client.get(resource_group_name, sql_virtual_machine_name)

    sqlvm_object.sql_virtual_machine_group_resource_id = None
    sqlvm_object.wsfc_domain_credentials = None

    # Since it's a running operation, we will do the put and then the get to display the instance.
    LongRunningOperation(cmd.cli_ctx)(sdk_no_wait(False, client.begin_create_or_update,
                                                  resource_group_name, sql_virtual_machine_name, sqlvm_object))

    return client.get(resource_group_name, sql_virtual_machine_name)
