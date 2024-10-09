# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint:disable=line-too-long


def transform_sqlvm_group_output(result):
    '''
    Transforms the result of SQL virtual machine group to eliminate unnecessary parameters.
    '''
    from collections import OrderedDict
    from azure.mgmt.core.tools import parse_resource_id
    try:
        resource_group = getattr(result, 'resource_group', None) or parse_resource_id(result.id)['resource_group']
        wsfc_object = format_wsfc_domain_profile(result.wsfc_domain_profile)
        # Create a dictionary with the relevant parameters
        output = OrderedDict([('id', result.id),
                              ('location', result.location),
                              ('name', result.name),
                              ('provisioningState', result.provisioning_state),
                              ('sqlImageOffer', result.sql_image_offer),
                              ('sqlImageSku', result.sql_image_sku),
                              ('resourceGroup', resource_group),
                              ('wsfcDomainProfile', wsfc_object),
                              ('tags', result.tags)])
        return output
    except AttributeError:
        from msrest.pipeline import ClientRawResponse
        # Return the response object if the formating fails
        return None if isinstance(result, ClientRawResponse) else result


def transform_sqlvm_group_list(group_list):
    '''
    Formats the list of results from a SQL virtual machine group
    '''
    return [transform_sqlvm_group_output(v) for v in group_list]


def transform_sqlvm_output(result):
    '''
    Transforms the result of SQL virtual machine group to eliminate unnecessary parameters.
    '''
    from collections import OrderedDict
    from azure.mgmt.core.tools import parse_resource_id
    try:
        resource_group = getattr(result, 'resource_group', None) or parse_resource_id(result.id)['resource_group']
        # Create a dictionary with the relevant parameters
        output = OrderedDict([('id', result.id),
                              ('location', result.location),
                              ('name', result.name),
                              ('provisioningState', result.provisioning_state),
                              ('sqlImageOffer', result.sql_image_offer),
                              ('sqlImageSku', result.sql_image_sku),
                              ('sqlManagement', result.sql_management),
                              ('leastPrivilegeMode', result.least_privilege_mode),
                              ('resourceGroup', resource_group),
                              ('sqlServerLicenseType', result.sql_server_license_type),
                              ('virtualMachineResourceId', result.virtual_machine_resource_id),
                              ('tags', result.tags)])

        # Note, wsfcDomainCredentials will not display
        if result.sql_virtual_machine_group_resource_id is not None:
            output['sqlVirtualMachineGroupResourceId'] = result.sql_virtual_machine_group_resource_id
        if result.auto_patching_settings is not None:
            output['autoPatchingSettings'] = format_auto_patching_settings(result.auto_patching_settings)
        if result.auto_backup_settings is not None:
            output['autoBackupSettings'] = format_auto_backup_settings(result.auto_backup_settings)
        if result.server_configurations_management_settings is not None:
            output['serverConfigurationsManagementSettings'] = format_server_configuration_management_settings(result.server_configurations_management_settings)
        if result.key_vault_credential_settings is not None:
            output['keyVaultCredentialSettings'] = format_key_vault_credential_settings(result.key_vault_credential_settings)
        if result.assessment_settings is not None:
            output['assessmentSettings'] = format_assessment_settings(result.assessment_settings)

        return output
    except AttributeError:
        from msrest.pipeline import ClientRawResponse
        # Return the response object if the formating fails
        return None if isinstance(result, ClientRawResponse) else result


def transform_sqlvm_list(vm_list):
    '''
    Formats the list of results from a SQL virtual machine
    '''
    return [transform_sqlvm_output(v) for v in vm_list]


def transform_aglistener_output(result):
    '''
    Transforms the result of Availability Group Listener to eliminate unnecessary parameters.
    '''
    from collections import OrderedDict
    from azure.mgmt.core.tools import parse_resource_id
    try:
        resource_group = getattr(result, 'resource_group', None) or parse_resource_id(result.id)['resource_group']
        # Create a dictionary with the relevant parameters
        output = OrderedDict([('id', result.id),
                              ('name', result.name),
                              ('provisioningState', result.provisioning_state),
                              ('port', result.port),
                              ('resourceGroup', resource_group)])

        # Note, wsfcDomainCredentials will not display
        if result.load_balancer_configurations is not None:
            output['loadBalancerConfigurations'] = format_load_balancer_configuration_list(result.load_balancer_configurations)

        return output
    except AttributeError:
        from msrest.pipeline import ClientRawResponse
        # Return the response object if the formating fails
        return None if isinstance(result, ClientRawResponse) else result


def transform_aglistener_list(ag_list):
    '''
    Formats the list of results from a SQL virtual machine
    '''
    return [transform_aglistener_output(v) for v in ag_list]


def format_wsfc_domain_profile(result):
    '''
    Formats the WSFCDomainProfile object removing arguments that are empty
    '''
    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()
    if result.cluster_bootstrap_account is not None:
        order_dict['clusterBootstrapAccount'] = result.cluster_bootstrap_account
    if result.domain_fqdn is not None:
        order_dict['domainFqdn'] = result.domain_fqdn
    if result.ou_path is not None:
        order_dict['ouPath'] = result.ou_path
    if result.cluster_operator_account is not None:
        order_dict['clusterOperatorAccount'] = result.cluster_operator_account
    if result.file_share_witness_path is not None:
        order_dict['fileShareWitnessPath'] = result.file_share_witness_path
    if result.sql_service_account is not None:
        order_dict['sqlServiceAccount'] = result.sql_service_account
    if result.storage_account_url is not None:
        order_dict['storageAccountUrl'] = result.storage_account_url

    return order_dict


def format_additional_features_server_configurations(result):
    '''
    Formats the AdditionalFeaturesServerConfigurations object removing arguments that are empty
    '''
    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()
    if result.is_rservices_enabled is not None:
        order_dict['isRServicesEnabled'] = result.is_rservices_enabled

    return order_dict


def format_auto_backup_settings(result):
    '''
    Formats the AutoBackupSettings object removing arguments that are empty
    '''
    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()
    if result.enable is not None:
        order_dict['enable'] = result.enable
    if result.enable_encryption is not None:
        order_dict['enableEncryption'] = result.enable_encryption
    if result.retention_period is not None:
        order_dict['retentionPeriod'] = result.retention_period
    if result.storage_account_url is not None:
        order_dict['storageAccountUrl'] = result.storage_account_url
    if result.backup_system_dbs is not None:
        order_dict['backupSystemDbs'] = result.backup_system_dbs
    if result.backup_schedule_type is not None:
        order_dict['backupScheduleType'] = result.backup_schedule_type
    if result.full_backup_frequency is not None:
        order_dict['fullBackupFrequency'] = result.full_backup_frequency
    if result.full_backup_start_time is not None:
        order_dict['fullBackupStartTime'] = result.full_backup_start_time
    if result.full_backup_window_hours is not None:
        order_dict['fullBackupWindowHours'] = result.full_backup_window_hours
    if result.log_backup_frequency is not None:
        order_dict['logBackupFrequency'] = result.log_backup_frequency

    return order_dict


def format_auto_patching_settings(result):
    '''
    Formats the AutoPatchingSettings object removing arguments that are empty
    '''
    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()
    if result.enable is not None:
        order_dict['enable'] = result.enable
    if result.day_of_week is not None:
        order_dict['dayOfWeek'] = result.day_of_week
    if result.maintenance_window_starting_hour is not None:
        order_dict['maintenanceWindowStartingHour'] = result.maintenance_window_starting_hour
    if result.maintenance_window_duration is not None:
        order_dict['maintenanceWindowDuration'] = result.maintenance_window_duration

    return order_dict


def format_key_vault_credential_settings(result):
    '''
    Formats the KeyVaultCredentialSettings object removing arguments that are empty
    '''
    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()
    if result.enable is not None:
        order_dict['enable'] = result.enable
    if result.credential_name is not None:
        order_dict['credentialName'] = result.credential_name
    if result.azure_key_vault_url is not None:
        order_dict['azureKeyVaultUrl'] = result.azure_key_vault_url

    return order_dict


def format_load_balancer_configuration_list(lb_list):
    '''
    Formats the list of results from a load configuration
    '''
    return [format_load_balancer_configuration(v) for v in lb_list]


def format_load_balancer_configuration(result):
    '''
    Formats the LoadBalancerConfiguration object removing arguments that are empty
    '''
    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()
    if result.private_ip_address is not None:
        order_dict['privateIpAddress'] = format_private_ip_address(result.private_ip_address)
    if result.public_ip_address_resource_id is not None:
        order_dict['publicIpAddressResourceId'] = result.public_ip_address_resource_id
    if result.load_balancer_resource_id is not None:
        order_dict['loadBalancerResourceId'] = result.load_balancer_resource_id
    if result.probe_port is not None:
        order_dict['probePort'] = result.probe_port
    if result.sql_virtual_machine_instances is not None:
        order_dict['sqlVirtualMachineInstances'] = result.sql_virtual_machine_instances

    return order_dict


def format_private_ip_address(result):
    '''
    Formats the PrivateIPAddress object removing arguments that are empty
    '''
    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()
    if result.ip_address is not None:
        order_dict['ipAddress'] = result.ip_address
    if result.subnet_resource_id is not None:
        order_dict['subnetResourceId'] = result.subnet_resource_id

    return order_dict


def format_server_configuration_management_settings(result):
    '''
    Formats the ServerConfigurationsManagementSettings object removing arguments that are empty
    '''
    from collections import OrderedDict
    order_dict = OrderedDict()

    settings = format_sql_connectivity_update_settings(result.sql_connectivity_update_settings)
    if settings:
        order_dict['sqlConnectivityUpdateSettings'] = settings

    settings = format_sql_workload_type_update_settings(result.sql_workload_type_update_settings)
    if settings:
        order_dict['sqlWorkloadTypeUpdateSettings'] = settings

    settings = format_sql_storage_update_settings(result.sql_storage_update_settings)
    if settings:
        order_dict['sqlStorageUpdateSettings'] = settings

    settings = format_additional_features_server_configurations(result.additional_features_server_configurations)
    if settings:
        order_dict['additionalFeaturesServerConfigurations'] = settings

    settings = format_azure_ad_authentication_settings(result.azure_ad_authentication_settings)
    if settings:
        order_dict['azureAdAuthenticationSettings'] = settings

    return order_dict


def format_sql_connectivity_update_settings(result):
    '''
    Formats the SqlConnectivityUpdateSettings object removing arguments that are empty
    '''

    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()
    if result.connectivity_type is not None:
        order_dict['connectivityType'] = result.connectivity_type
    if result.port is not None:
        order_dict['port'] = result.port
    if result.sql_auth_update_user_name is not None:
        order_dict['sqlAuthUpdateUserName'] = result.sql_auth_update_user_name

    return order_dict


def format_sql_storage_update_settings(result):
    '''
    Formats the SqlStorageUpdateSettings object removing arguments that are empty
    '''

    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()
    if result.disk_count is not None:
        order_dict['diskCount'] = result.disk_count
    if result.disk_configuration_type is not None:
        order_dict['diskConfigurationType'] = result.disk_configuration_type

    return order_dict


def format_sql_workload_type_update_settings(result):
    '''
    Formats the SqlWorkloadTypeUpdateSettings object removing arguments that are empty
    '''

    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()
    if result.sql_workload_type is not None:
        order_dict['sqlWorkloadType'] = result.sql_workload_type

    return order_dict


def format_assessment_settings(result):
    '''
    Formats the AssessmentSettings object removing arguments that are empty
    '''
    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()

    if result.enable is not None:
        order_dict['enable'] = result.enable

    schedule = format_assessment_schedule(result.schedule)
    if schedule:
        order_dict['schedule'] = schedule

    return order_dict


def format_assessment_schedule(result):
    '''
    Formats the AssessmentSchedule object removing arguments that are empty
    '''

    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()
    if result.enable is not None:
        order_dict['enable'] = result.enable
    if result.weekly_interval is not None:
        order_dict['weeklyInterval'] = result.weekly_interval
    if result.monthly_occurrence is not None:
        order_dict['monthlyOccurrence'] = result.monthly_occurrence
    if result.day_of_week is not None:
        order_dict['dayOfWeek'] = result.day_of_week
    if result.start_time is not None:
        order_dict['startTimeLocal'] = result.start_time

    return order_dict


def format_azure_ad_authentication_settings(result):
    '''
    Formats the AzureAD authentication object removing arguments that are empty
    '''

    from collections import OrderedDict
    # Only display parameters that have content
    order_dict = OrderedDict()
    if result is not None and result.client_id is not None:
        order_dict['clientId'] = result.client_id

    return order_dict
