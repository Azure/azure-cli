# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=C0302
from enum import Enum

from knack.log import get_logger
from azure.cli.core.commands import LongRunningOperation

from azure.cli.core.util import (
    CLIError,
    sdk_no_wait,
)

from azure.mgmt.sqlvirtualmachine.models import(
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
    SqlStorageUpdateSettings,
    AdditionalFeaturesServerConfigurations,
    ServerConfigurationsManagementSettings,
    SqlVirtualMachine
)

def sqlvm_list(
    client,
    resource_group_name=None):
    '''
    Lists sql vms or groups in a resource group or subscription
    '''
    if resource_group_name:
        # List all sql vms or groups in the resource group
        return client.list_by_resource_group(resource_group_name=resource_group_name)

    # List all sql vms or groups in the subscription
    return client.list()


def sqlvm_group_create(client, cmd, sql_virtual_machine_group_name, resource_group_name, location, sql_image_offer, sql_image_sku,
                        domain_fqdn, cluster_operator_account, sql_service_account,
                        storage_account_url, storage_account_key, cluster_bootstrap_account=None,
                        file_share_witness_path=None, ou_path=None, tags=None):

    '''
    Creates or Updates a SQL virtual machine group.
    '''
    tags = tags or {}

    # Create the windows server failover cluster domain profile object.
    wsfc_domain_profile_object = WsfcDomainProfile(domain_fqdn=domain_fqdn,
                                            ou_path=ou_path,
                                            cluster_bootstrap_account=cluster_bootstrap_account,
                                            cluster_operator_account=cluster_operator_account,
                                            sql_service_account=sql_service_account,
                                            file_share_witness_path=file_share_witness_path,
                                            storage_account_url=storage_account_url,
                                            storage_account_primary_key=storage_account_key)

    sqlvm_group_object= SqlVirtualMachineGroup(sql_image_offer=sql_image_offer,
                                            sql_image_sku=sql_image_sku,
                                            wsfc_domain_profile=wsfc_domain_profile_object,
                                            location=location,
                                            tags=tags)

    #return client.create_or_update(resource_group_name=resource_group_name,
     #                               sql_virtual_machine_group_name=sql_virtual_machine_group_name,
      #                              parameters=sqlvm_group_object)

    # Since it's a running operation, we will do the put and then the get to display the instance.
    LongRunningOperation(cmd.cli_ctx)(sdk_no_wait(False, client.create_or_update, resource_group_name, sql_virtual_machine_group_name, sqlvm_group_object))

    return client.get(resource_group_name, sql_virtual_machine_group_name)


def sqlvm_aglistener_create(client, cmd, availability_group_listener_name, sql_virtual_machine_group_name, resource_group_name,
                            availability_group_name, ip_address, subnet_resource_id, load_balancer_resource_id, probe_port,
                            sql_virtual_machine_instances, port=1433, public_ip_address_resource_id=None):

    '''
    Creates or Updates an availability group listener
    '''

    #Create the private ip address
    private_ip_object = PrivateIPAddress(ip_address=ip_address,
                                        subnet_resource_id=subnet_resource_id)

    #Create the load balancer configurations
    load_balancer_object = LoadBalancerConfiguration(private_ip_address=private_ip_object,
                                                    public_ip_address_resource_id=public_ip_address_resource_id,
                                                    load_balancer_resource_id=load_balancer_resource_id,
                                                    probe_port=probe_port,
                                                    sql_virtual_machine_instances=sql_virtual_machine_instances)

    #Create the availability group listener object
    availability_group_listener_object = AvailabilityGroupListener(availability_group_name=availability_group_name,
                                                                    load_balancer_configurations=load_balancer_object,
                                                                    port=port)

    #return client.create_or_update(resource_group_name=resource_group_name,
     #                               sql_virtual_machine_group_name=sql_virtual_machine_group_name,
      #                              availability_group_listener_name=availability_group_listener_name,
       #                             parameters=availability_group_listener_object)

    LongRunningOperation(cmd.cli_ctx)(sdk_no_wait(False, client.create_or_update, resource_group_name, sql_virtual_machine_group_name,
                            availability_group_listener_name, availability_group_listener_object))

    return client.get(resource_group_name, sql_virtual_machine_group_name, availability_group_listener_name)


def sqlvm_create(client, cmd, location, sql_virtual_machine_name, resource_group_name,
                sql_server_license_type='PAYG', sql_virtual_machine_group_resource_id=None, cluster_bootstrap_account_password=None,
                cluster_operator_account_password=None, sql_service_account_password=None, enable_auto_patching=False,
                day_of_week=None, maintenance_window_starting_hour=None, maintenance_window_duration=None,
                enable_auto_backup=False, enable_encryption=False, retention_period=None, storage_account_url=None,
                storage_access_key=None, backup_password=None, backup_system_dbs=False, backup_schedule_type=None,
                full_backup_frequency=None, full_backup_start_time=None, full_backup_window_hours=None, log_backup_frequency=None,
                enable_key_vault_credential=False, credential_name=None, azure_key_vault_url=None, service_principal_name=None,
                service_principal_secret=None, connectivity_type=None, port=None, sql_auth_update_user_name=None,
                sql_auth_update_password=None, sql_workload_type=None, disk_count=None, disk_configuration_type=None,
                is_rservices_enabled=False, backup_permissions_for_azure_backup_svc=False, tags=None):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import resource_id

    '''
    Creates or Updates a SQL virtual machine.
    '''

    subscription_id = get_subscription_id(cmd.cli_ctx)

    virtual_machine_resource_id = resource_id(
        subscription=subscription_id, resource_group=resource_group_name,
        namespace='Microsoft.Compute', type='virtualMachines', name=sql_virtual_machine_name)

    tags = tags or {}

    wsfc_domain_credentials_object = WsfcDomainCredentials(cluster_bootstrap_account_password=cluster_bootstrap_account_password,
                                                            cluster_operator_account_password=cluster_operator_account_password,
                                                            sql_service_account_password=sql_service_account_password)

    auto_patching_object = AutoPatchingSettings(enable=enable_auto_patching,
                                                day_of_week=day_of_week,
                                                maintenance_window_starting_hour=maintenance_window_starting_hour,
                                                maintenance_window_duration=maintenance_window_duration)

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

    keyvault_object = KeyVaultCredentialSettings(enable=enable_key_vault_credential,
                                                credential_name=credential_name,
                                                azure_key_vault_url=azure_key_vault_url,
                                                service_principal_name=service_principal_name,
                                                service_principal_secret=service_principal_secret)

    connectivity_object = SqlConnectivityUpdateSettings(port=port,
                                                        connectivity_type=connectivity_type,
                                                        sql_auth_update_user_name=sql_auth_update_user_name,
                                                        sql_auth_update_password=sql_auth_update_password)

    workload_type_object = SqlWorkloadTypeUpdateSettings(sql_workload_type=sql_workload_type)

    storage_settings_object = SqlStorageUpdateSettings(disk_count=disk_count,
                                                        disk_configuration_type=disk_configuration_type)

    additional_features_object = AdditionalFeaturesServerConfigurations(is_rservices_enabled=is_rservices_enabled,
                                                                        backup_permissions_for_azure_backup_svc=backup_permissions_for_azure_backup_svc)

    server_configuration_object = ServerConfigurationsManagementSettings(sql_connectivity_update_settings=connectivity_object,
                                                                        sql_workload_type_update_settings=workload_type_object,
                                                                        sql_storage_update_settings=storage_settings_object,
                                                                        additional_features_server_configurations=additional_features_object)

    sqlvm_object = SqlVirtualMachine(location=location,
                                    virtual_machine_resource_id=virtual_machine_resource_id,
                                    sql_server_license_type=sql_server_license_type,
                                    sql_virtual_machine_group_resource_id=sql_virtual_machine_group_resource_id,
                                    wsfc_domain_credentials=wsfc_domain_credentials_object,
                                    auto_patching_settings=auto_patching_object,
                                    auto_backup_settings=auto_backup_object,
                                    key_vault_credential_settings=keyvault_object,
                                    server_configurations_management_settings=server_configuration_object,
                                    tags=tags)

    # Since it's a running operation, we will do the put and then the get to display the instance.
    LongRunningOperation(cmd.cli_ctx)(sdk_no_wait(False, client.create_or_update, resource_group_name, sql_virtual_machine_name, sqlvm_object))

    return client.get(resource_group_name, sql_virtual_machine_name)

