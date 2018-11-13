# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=C0302
from enum import Enum

from knack.log import get_logger

from azure.cli.core.util import (
    CLIError,
    sdk_no_wait,
)


from ._util import (
    get_sqlvirtualmachine_availability_group_listeners_operations,
    get_sqlvirtualmachine_sql_virtual_machine_groups_operations,
    get_sqlvirtualmachine_sql_virtual_machines_operations
)

from azure.mgmt.sqlvirtualmachine.models import(
    WSFCDomainProfile,
    SqlVirtualMachineGroup,
    PrivateIPAddress,
    LoadBalancerConfiguration,
    AvailabilityGroupListener,
    WSFCDomainCredentials,
    AutoTelemetrySettings,
    AutoPatchingSettings,
    AutoBackupSettings,
    KeyVaultCredentialSettings
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


def sqlvm_group_create(client, sql_virtual_machine_group_name, resource_group_name, location, sql_image_offer, sql_image_sku,
                        domain_fqdn, cluster_operator_account, sql_service_account,
                        storage_account_url, storage_account_key, cluster_bootstrap_account=None,
                        file_share_witness_path=None, ou_path=None, tags=None):

    '''
    Creates or Updates a SQL virtual machine group.
    '''
    tags = tags or {}

    # Create the windows server failover cluster domain profile object.
    wsfc_domain_profile_object = WSFCDomainProfile(domain_fqdn=domain_fqdn,
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

    return client.create_or_update(resource_group_name=resource_group_name,
                                    sql_virtual_machine_group_name=sql_virtual_machine_group_name,
                                    parameters=sqlvm_group_object)


def sqlvm_aglistener_create(client, availability_group_listener_name, sql_virtual_machine_group_name, resource_group_name,
                            availability_group_name, ip_address, subnet_resource_id, load_balancer_resource_id, probe_port,
                            sql_virtual_machine_instances, port='1433', public_ip_address_resource_id=None):

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

    return client.create_or_update(resource_group_name=resource_group_name,
                                    sql_virtual_machine_group_name=sql_virtual_machine_group_name,
                                    availability_group_listener_name=availability_group_listener_name,
                                    parameters=availability_group_listener_object)

def sqlvm_create(client, virtual_machine_resource_id, sql_virtual_machine_name, resource_group_name,
                sql_server_license_type='PAYG', sql_virtual_machine_group_resource_id=None, cluster_bootstrap_account_password=None,
                cluster_operator_account_password=None, sql_service_account_password=None, region=None, enable_auto_patching=False,
                day_of_week=None, maintenance_window_starting_hour=None, maintenance_window_duration=None,
                enable_auto_backup=False, enable_encryption=False, retention_period=None, storage_account_url=None,
                storage_access_key=None, backup_password=None, backup_system_dbs=False, backup_schedule_type=None,
                full_backup_frequency=None, full_backup_start_time=None, full_backup_window_hours=None, log_backup_frequency=None,
                enable_key_vault_credential=False, credential_name=None, azure_key_vault_url=None, service_principal_name=None,
                service_principal_secret=None, tags=None):

    '''
    Creates or Updates a SQL virtual machine.
    '''
    tags = tags or {}

    wsfc_domain_credentials_object = WSFCDomainCredentials(cluster_bootstrap_account_password=cluster_bootstrap_account_password,
                                                            cluster_operator_account_password=cluster_operator_account_password,
                                                            sql_service_account_password=sql_service_account_password)

    auto_telemetry_object = AutoTelemetrySettings(region=region)

    auto_patching_object = AutoPatchingSettings(enable=enable_auto_patching,
                                                day_of_week=day_of_week,
                                                maintenance_window_starting_hour=maintenance_window_starting_hour,
                                                maintenance_window_duration=maintenance_window_duration)

    auto_backup_object = AutoBackupSettings(enable=enable_auto_backup,
                                            enable_encryption=enable_encryption,
                                            retention_period=retention_period,
                                            storage_account_url=storage_account_url,
                                            storage_access_key=storage_access_key,
                                            password=backup_password,
                                            backup_system_dbs=backup_system_dbs,
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

    #return True
    print (wsfc_domain_credentials_object)
    print (keyvault_object)
    print (auto_backup_object)
    print (auto_patching_object)
    print (auto_telemetry_object)