# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.prompting import prompt_pass
from azure.cli.core.azclierror import (
    RequiredArgumentMissingError,
    AzureResponseError,
    HTTPError
)
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.util import (
    sdk_no_wait
)
from azure.mgmt.core.tools import is_valid_resource_id, resource_id
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
    Schedule,
    AssessmentSettings,
    SqlVirtualMachine,
    AADAuthenticationSettings
)

from ._util import (
    does_custom_log_exist,
    create_custom_table,
    validate_dcr,
    does_name_exist,
    create_ama_and_dcra
)

from azure.cli.command_modules.sqlvm._template_builder import (
    build_dcr_resource,
    build_dce_resource
)
import re

# from azure.mgmt.resource import ResourceManagementClient


def sqlvm_list(
        client,
        resource_group_name=None):
    '''
    Lists all SQL virtual machines in a resource group or subscription.
    '''
    if resource_group_name:
        # List all sql vms  in the resource group
        return client.list_by_resource_group(
            resource_group_name=resource_group_name)

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
        return client.list_by_resource_group(
            resource_group_name=resource_group_name)

    # List all sql vm groups in the subscription
    return client.list()


# pylint: disable= line-too-long, too-many-arguments
def sqlvm_group_create(
        client,
        cmd,
        sql_virtual_machine_group_name,
        resource_group_name,
        sql_image_offer,
        sql_image_sku,
        domain_fqdn,
        cluster_operator_account,
        sql_service_account,
        storage_account_url,
        cluster_subnet_type="SingleSubnet",
        storage_account_key=None,
        location=None,
        cluster_bootstrap_account=None,
        file_share_witness_path=None,
        ou_path=None,
        tags=None):
    '''
    Creates a SQL virtual machine group.
    '''
    tags = tags or {}

    if not storage_account_key:
        storage_account_key = prompt_pass('Storage Key: ', confirm=True)

    # Create the windows server failover cluster domain profile object.
    wsfc_domain_profile_object = WsfcDomainProfile(
        domain_fqdn=domain_fqdn,
        ou_path=ou_path,
        cluster_bootstrap_account=cluster_bootstrap_account,
        cluster_operator_account=cluster_operator_account,
        sql_service_account=sql_service_account,
        file_share_witness_path=file_share_witness_path,
        storage_account_url=storage_account_url,
        storage_account_primary_key=storage_account_key,
        cluster_subnet_type=cluster_subnet_type)

    sqlvm_group_object = SqlVirtualMachineGroup(
        sql_image_offer=sql_image_offer,
        sql_image_sku=sql_image_sku,
        wsfc_domain_profile=wsfc_domain_profile_object,
        location=location,
        tags=tags)

    # Since it's a running operation, we will do the put and then the get to
    # display the instance.
    LongRunningOperation(
        cmd.cli_ctx)(
        sdk_no_wait(
            False,
            client.begin_create_or_update,
            resource_group_name,
            sql_virtual_machine_group_name,
            sqlvm_group_object))

    return client.get(resource_group_name, sql_virtual_machine_group_name)


# pylint: disable=line-too-long, too-many-arguments
def sqlvm_group_update(
        instance,
        domain_fqdn=None,
        cluster_operator_account=None,
        sql_service_account=None,
        storage_account_url=None,
        storage_account_key=None,
        cluster_bootstrap_account=None,
        file_share_witness_path=None,
        ou_path=None,
        tags=None,
        cluster_subnet_type=None):
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
        instance.wsfc_domain_profile.storage_account_primary_key = prompt_pass(
            'Storage Key: ', confirm=True)
    if file_share_witness_path is not None:
        instance.wsfc_domain_profile.file_share_witness_path = file_share_witness_path
    if ou_path is not None:
        instance.wsfc_domain_profile.ou_path = ou_path
    if cluster_subnet_type is not None:
        instance.wsfc_domain_profile.cluster_subnet_type = cluster_subnet_type
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
    load_balancer_object = LoadBalancerConfiguration(
        private_ip_address=private_ip_object,
        public_ip_address_resource_id=public_ip_address_resource_id,
        load_balancer_resource_id=load_balancer_resource_id,
        probe_port=probe_port,
        sql_virtual_machine_instances=sql_virtual_machine_instances)

    # Create the availability group listener object
    ag_listener_object = AvailabilityGroupListener(
        availability_group_name=availability_group_name,
        load_balancer_configurations=[load_balancer_object],
        port=port)

    LongRunningOperation(
        cmd.cli_ctx)(
        sdk_no_wait(
            False,
            client.begin_create_or_update,
            resource_group_name,
            sql_virtual_machine_group_name,
            availability_group_listener_name,
            ag_listener_object))

    return client.get(
        resource_group_name,
        sql_virtual_machine_group_name,
        availability_group_listener_name)


def aglistener_update(instance, sql_virtual_machine_instances=None):
    '''
    Updates an availability group listener
    '''
    # Get the list of all current machines in the ag listener
    if sql_virtual_machine_instances:
        instance.load_balancer_configurations[0].sql_virtual_machine_instances = sql_virtual_machine_instances

    return instance


# pylint: disable=too-many-arguments, too-many-locals, line-too-long, too-many-boolean-expressions
def sqlvm_create(
        client,
        cmd,
        sql_virtual_machine_name,
        resource_group_name,
        sql_server_license_type=None,
        location=None,
        sql_image_sku=None,
        enable_auto_patching=None,
        sql_management_mode="LightWeight",
        least_privilege_mode=None,
        day_of_week=None,
        maintenance_window_starting_hour=None,
        maintenance_window_duration=None,
        enable_auto_backup=None,
        enable_encryption=False,
        retention_period=None,
        storage_account_url=None,
        storage_access_key=None,
        backup_password=None,
        backup_system_dbs=False,
        backup_schedule_type=None,
        full_backup_frequency=None,
        full_backup_start_time=None,
        full_backup_window_hours=None,
        log_backup_frequency=None,
        enable_key_vault_credential=None,
        credential_name=None,
        azure_key_vault_url=None,
        service_principal_name=None,
        service_principal_secret=None,
        connectivity_type=None,
        port=None,
        sql_auth_update_username=None,
        sql_auth_update_password=None,
        sql_workload_type=None,
        enable_r_services=None,
        tags=None,
        sql_image_offer=None):
    '''
    Creates a SQL virtual machine.
    '''
    from azure.cli.core.commands.client_factory import get_subscription_id

    subscription_id = get_subscription_id(cmd.cli_ctx)

    virtual_machine_resource_id = resource_id(
        subscription=subscription_id,
        resource_group=resource_group_name,
        namespace='Microsoft.Compute',
        type='virtualMachines',
        name=sql_virtual_machine_name)

    tags = tags or {}

    # If customer has provided any auto_patching settings, enabling plugin
    # should be True
    if (day_of_week or maintenance_window_duration or maintenance_window_starting_hour):
        enable_auto_patching = True

    auto_patching_object = AutoPatchingSettings(
        enable=enable_auto_patching,
        day_of_week=day_of_week,
        maintenance_window_starting_hour=maintenance_window_starting_hour,
        maintenance_window_duration=maintenance_window_duration)

    # If customer has provided any auto_backup settings, enabling plugin
    # should be True
    if (enable_encryption or retention_period or storage_account_url or storage_access_key or backup_password or
            backup_system_dbs or backup_schedule_type or full_backup_frequency or full_backup_start_time or
            full_backup_window_hours or log_backup_frequency):
        enable_auto_backup = True
        if not storage_access_key:
            storage_access_key = prompt_pass('Storage Key: ', confirm=True)
        if enable_encryption and not backup_password:
            backup_password = prompt_pass('Backup Password: ', confirm=True)

    auto_backup_object = AutoBackupSettings(
        enable=enable_auto_backup,
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

    # If customer has provided any key_vault_credential settings, enabling
    # plugin should be True
    if (credential_name or azure_key_vault_url or service_principal_name or service_principal_secret):
        enable_key_vault_credential = True
        if not service_principal_secret:
            service_principal_secret = prompt_pass(
                'Service Principal Secret: ', confirm=True)

    keyvault_object = KeyVaultCredentialSettings(
        enable=enable_key_vault_credential,
        credential_name=credential_name,
        azure_key_vault_url=azure_key_vault_url,
        service_principal_name=service_principal_name,
        service_principal_secret=service_principal_secret)

    connectivity_object = SqlConnectivityUpdateSettings(
        port=port,
        connectivity_type=connectivity_type,
        sql_auth_update_user_name=sql_auth_update_username,
        sql_auth_update_password=sql_auth_update_password)

    workload_type_object = SqlWorkloadTypeUpdateSettings(
        sql_workload_type=sql_workload_type)

    additional_features_object = AdditionalFeaturesServerConfigurations(
        is_r_services_enabled=enable_r_services)

    server_configuration_object = ServerConfigurationsManagementSettings(
        sql_connectivity_update_settings=connectivity_object,
        sql_workload_type_update_settings=workload_type_object,
        additional_features_server_configurations=additional_features_object)

    sqlvm_object = SqlVirtualMachine(
        location=location,
        virtual_machine_resource_id=virtual_machine_resource_id,
        sql_server_license_type=sql_server_license_type,
        least_privilege_mode=least_privilege_mode,
        sql_image_sku=sql_image_sku,
        sql_management=sql_management_mode,
        sql_image_offer=sql_image_offer,
        auto_patching_settings=auto_patching_object,
        auto_backup_settings=auto_backup_object,
        key_vault_credential_settings=keyvault_object,
        server_configurations_management_settings=server_configuration_object,
        tags=tags)

    # Since it's a running operation, we will do the put and then the get to
    # display the instance.
    LongRunningOperation(
        cmd.cli_ctx)(
        sdk_no_wait(
            False,
            client.begin_create_or_update,
            resource_group_name,
            sql_virtual_machine_name,
            sqlvm_object))

    return client.get(resource_group_name, sql_virtual_machine_name)


# pylint: disable=too-many-statements, line-too-long, too-many-boolean-expressions, unused-argument
def sqlvm_update(
        cmd,
        instance,
        sql_virtual_machine_name,
        resource_group_name,
        sql_server_license_type=None,
        sql_image_sku=None,
        least_privilege_mode=None,
        enable_auto_patching=None,
        day_of_week=None,
        maintenance_window_starting_hour=None,
        maintenance_window_duration=None,
        enable_auto_backup=None,
        enable_encryption=False,
        retention_period=None,
        storage_account_url=None,
        prompt=True,
        storage_access_key=None,
        backup_password=None,
        backup_system_dbs=False,
        backup_schedule_type=None,
        sql_management_mode=None,
        full_backup_frequency=None,
        full_backup_start_time=None,
        full_backup_window_hours=None,
        log_backup_frequency=None,
        enable_key_vault_credential=None,
        credential_name=None,
        azure_key_vault_url=None,
        service_principal_name=None,
        service_principal_secret=None,
        connectivity_type=None,
        port=None,
        sql_workload_type=None,
        enable_r_services=None,
        tags=None,
        enable_assessment=None,
        enable_assessment_schedule=None,
        assessment_weekly_interval=None,
        assessment_monthly_occurrence=None,
        assessment_day_of_week=None,
        assessment_start_time_local=None,
        workspace_name=None,
        workspace_rg=None,
        workspace_sub=None,
        agent_rg=None):
    '''
    Updates a SQL virtual machine.
    '''
    if tags is not None:
        instance.tags = tags
    if sql_server_license_type is not None:
        instance.sql_server_license_type = sql_server_license_type
    if sql_image_sku is not None:
        instance.sql_image_sku = sql_image_sku
    if sql_management_mode is not None:
        instance.sql_management = sql_management_mode
    if least_privilege_mode is not None:
        instance.least_privilege_mode = least_privilege_mode

    if (enable_auto_patching is not None or day_of_week is not None or maintenance_window_starting_hour is not None or maintenance_window_duration is not None):

        enable_auto_patching = enable_auto_patching if enable_auto_patching is False else True
        instance.auto_patching_settings = AutoPatchingSettings(
            enable=enable_auto_patching,
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

        instance.auto_backup_settings = AutoBackupSettings(
            enable=enable_auto_backup,
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
            service_principal_secret = prompt_pass(
                'Service Principal Secret: ', confirm=True)

        instance.key_vault_credential_settings = KeyVaultCredentialSettings(
            enable=enable_key_vault_credential,
            credential_name=credential_name,
            service_principal_name=service_principal_name,
            service_principal_secret=service_principal_secret,
            azure_key_vault_url=azure_key_vault_url)

    instance.server_configurations_management_settings = ServerConfigurationsManagementSettings()

    if (connectivity_type is not None or port is not None):
        instance.server_configurations_management_settings.sql_connectivity_update_settings = SqlConnectivityUpdateSettings(
            connectivity_type=connectivity_type, port=port)

    if sql_workload_type is not None:
        instance.server_configurations_management_settings.sql_workload_type_update_settings = SqlWorkloadTypeUpdateSettings(
            sql_workload_type=sql_workload_type)

    if enable_r_services is not None:
        instance.server_configurations_management_settings.additional_features_server_configurations = AdditionalFeaturesServerConfigurations(
            is_r_services_enabled=enable_r_services)

    # If none of the settings was modified, reset
    # server_configurations_management_settings to be null
    if (instance.server_configurations_management_settings.sql_connectivity_update_settings is None and
            instance.server_configurations_management_settings.sql_workload_type_update_settings is None and
            instance.server_configurations_management_settings.sql_storage_update_settings is None and
            instance.server_configurations_management_settings.additional_features_server_configurations is None):
        instance.server_configurations_management_settings = None

    set_assessment_properties(cmd,
                              instance,
                              enable_assessment,
                              enable_assessment_schedule,
                              assessment_weekly_interval,
                              assessment_monthly_occurrence,
                              assessment_day_of_week,
                              assessment_start_time_local,
                              resource_group_name,
                              sql_virtual_machine_name,
                              workspace_rg,
                              workspace_name,
                              workspace_sub,
                              agent_rg)

    return instance


# pylint: disable=unused-argument
def sqlvm_enable_azure_ad_auth(client, cmd, sql_virtual_machine_name, resource_group_name, msi_client_id=None, skip_client_validation=None):
    ''' Enable Azure AD authentication on a SQL virtual machine.

        :param cmd: The CLI command.
        :type cmd: AzCliCommand.
        :param instance: The Sql Virtual Machine instance.
        :type instance: SqlVirtualMachine.
        :param resource_group_name: The resource group name
        :type resource_group_name: str.
        :param msi_client_id: The clientId of the managed identity used in Azure AD authentication.
                              None means system-assigned managed identity
        :type: str.
        :param skip_client_validation: Whether to skip the client side validation. The server side validation always happens.
                                       This parameter is used in the validation and ignored here.
        :type: bool.

        :return: The updated Sql Virtual Machine instance.
        :rtype: SqlVirtualMachine.
    '''

    sqlvm_object = client.get(resource_group_name, sql_virtual_machine_name)

    if sqlvm_object.server_configurations_management_settings is None:
        sqlvm_object.server_configurations_management_settings = ServerConfigurationsManagementSettings()

    sqlvm_object.server_configurations_management_settings.azure_ad_authentication_settings = AADAuthenticationSettings(client_id=msi_client_id if msi_client_id else '')

    # Since it's a running operation, we will do the put and then the get to display the instance.
    LongRunningOperation(cmd.cli_ctx)(sdk_no_wait(False, client.begin_create_or_update,
                                                  resource_group_name, sql_virtual_machine_name, sqlvm_object))

    return client.get(resource_group_name, sql_virtual_machine_name)


# pylint: disable=unused-argument
def validate_azure_ad_auth(cmd, sql_virtual_machine_name, resource_group_name, msi_client_id=None):
    ''' Valida if Azure AD authentication is ready on a SQL virtual machine.
        The logic of validation is in the validator method. If the SQL virtual machine passes the validator,
        it means this SQL virtual machine is valid for Azure AD authentication

        :param cmd: The CLI command.
        :type cmd: AzCliCommand.
        :param resource_group_name: The resource group name
        :type resource_group_name: str.
        :param msi_client_id: The clientId of the managed identity used in Azure AD authentication.
                              None means system-assigned managed identity
        :type: str.

        :return: The updated Sql Virtual Machine instance.
        :rtype: SqlVirtualMachine.
    '''

    passing_validation_message = "Sql virtual machine {} is valid for Azure AD authentication.".format(sql_virtual_machine_name)

    return passing_validation_message


def sqlvm_add_to_group(
        client,
        cmd,
        sql_virtual_machine_name,
        resource_group_name,
        sql_virtual_machine_group_resource_id,
        sql_service_account_password=None,
        cluster_operator_account_password=None,
        cluster_bootstrap_account_password=None):
    '''
    Adds a SQL virtual machine to a group.
    '''

    sqlvm_object = client.get(resource_group_name, sql_virtual_machine_name)

    if not sql_service_account_password:
        sql_service_account_password = prompt_pass(
            'SQL Service account password: ', confirm=True)
    if not cluster_operator_account_password:
        cluster_operator_account_password = prompt_pass(
            'Cluster operator account password: ',
            confirm=True,
            help_string='Password to authenticate with the domain controller.')

    sqlvm_object.sql_virtual_machine_group_resource_id = sql_virtual_machine_group_resource_id

    sqlvm_object.wsfc_domain_credentials = WsfcDomainCredentials(
        cluster_bootstrap_account_password=cluster_bootstrap_account_password,
        cluster_operator_account_password=cluster_operator_account_password,
        sql_service_account_password=sql_service_account_password)

    # Since it's a running operation, we will do the put and then the get to
    # display the instance.
    LongRunningOperation(
        cmd.cli_ctx)(
        sdk_no_wait(
            False,
            client.begin_create_or_update,
            resource_group_name,
            sql_virtual_machine_name,
            sqlvm_object))

    return client.get(resource_group_name, sql_virtual_machine_name)


def sqlvm_remove_from_group(
        client,
        cmd,
        sql_virtual_machine_name,
        resource_group_name):
    '''
    Removes a SQL virtual machine from a group.
    '''

    sqlvm_object = client.get(resource_group_name, sql_virtual_machine_name)

    sqlvm_object.sql_virtual_machine_group_resource_id = None
    sqlvm_object.wsfc_domain_credentials = None

    # Since it's a running operation, we will do the put and then the get to
    # display the instance.
    LongRunningOperation(
        cmd.cli_ctx)(
        sdk_no_wait(
            False,
            client.begin_create_or_update,
            resource_group_name,
            sql_virtual_machine_name,
            sqlvm_object))

    return client.get(resource_group_name, sql_virtual_machine_name)


# region Helpers for custom commands
# pylint: disable=too-many-branches
def set_assessment_properties(
        cmd,
        instance,
        enable_assessment,
        enable_assessment_schedule,
        assessment_weekly_interval,
        assessment_monthly_occurrence,
        assessment_day_of_week,
        assessment_start_time_local,
        resource_group_name,
        sql_virtual_machine_name,
        workspace_rg,
        workspace_name,
        workspace_sub,
        agent_rg):
    '''
    Set assessment properties to be sent in sql vm update
    '''

    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.cli.core.util import random_string, send_raw_request
    from azure.cli.command_modules.vm._vm_utils import ArmTemplateBuilder20190401
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from ._assessment_data_source import table_name
    from itertools import count

    # If assessment.schedule settings are provided but enable schedule is
    # skipped, then ensure schedule is enabled
    if (enable_assessment_schedule is None and (
            assessment_weekly_interval is not None or assessment_monthly_occurrence or assessment_day_of_week or assessment_start_time_local)):
        enable_assessment_schedule = True

    # If assessment schedule is enabled but enable assessment is skipped, then
    # ensure assessment is enabled
    if (enable_assessment_schedule is not None and enable_assessment is None):
        enable_assessment = True

    if enable_assessment is not None:
        instance.assessment_settings = AssessmentSettings()
        instance.assessment_settings.enable = enable_assessment

        if enable_assessment_schedule is not None:
            instance.assessment_settings.schedule = Schedule()
            instance.assessment_settings.schedule.enable = enable_assessment_schedule

            if enable_assessment_schedule:
                instance.assessment_settings.schedule.weekly_interval = assessment_weekly_interval
                instance.assessment_settings.schedule.monthly_occurrence = assessment_monthly_occurrence
                instance.assessment_settings.schedule.day_of_week = assessment_day_of_week
                instance.assessment_settings.schedule.start_time = assessment_start_time_local

    # Validate and deploy pre-requisites if necessary
    # 1. Log Analytics extension for given workspace
    # 2. Custom log definition on workspace
    if enable_assessment:
        workspace_id = None
        curr_subscription = get_subscription_id(cmd.cli_ctx)
        # Raise error if workspace arguments not provided by user
        if workspace_name is None or workspace_rg is None:
            raise RequiredArgumentMissingError(
                'Assessment requires a Log Analytics workspace and Log Analytics extension on VM - '
                'workspace name and workspace resource group must be specified to deploy pre-requisites.')
        if agent_rg is None:
            agent_rg = resource_group_name
            # raise Warning -
            # raise RequiredArgumentMissingError(
            # 'Assessment requires a Resource Group to deploy the AMA Agent resources- '

        if workspace_sub is None:
            # raise warning => --workspace-sub not provided. Using current
            # subscription to find LA WS
            workspace_sub = curr_subscription
        api_version = "2021-12-01-preview"
        la_url = f"https://management.azure.com/subscriptions/{workspace_sub}/resourcegroups/{workspace_rg}/providers/Microsoft.OperationalInsights/workspaces/{workspace_name}?api-version={api_version}"

        try:
            la_response = send_raw_request(
                cmd.cli_ctx, method="GET", url=la_url)
        except Exception as e:
            raise AzureResponseError(
                f'Could not connect to the LA workspace - Error {e}.'
                ' If the workspace is not in the same subscription as the VM, use the --workspace-sub parameter')

        la_response = la_response.json()
        workspace_id = la_response['properties']['customerId']
        workspace_loc = la_response['location']

        workspace_res_id = la_response['id']

        # Validate the agent_rg -> Check if DCR + DCE exist already
        ama_sub = curr_subscription
        url = f"https://management.azure.com/subscriptions/{ama_sub}/resourceGroups/{agent_rg}/providers/Microsoft.Insights/dataCollectionRules?api-version=2022-06-01"
        try:
            dcr_response = send_raw_request(cmd.cli_ctx, method="GET", url=url)
        except HTTPError as e:
            raise AzureResponseError(
                f'An Http Error occured: {e}'
                'could not connect to the provided agent resource group {agent_rg}. Ensure the resource in the same subscription as {ama_sub}')

        # response contains list of dcr's
        dcr_response = dcr_response.json()
        dcr_list = dcr_response['value']
        dcr_found = False

        # get list of all dcr names found
        dcr_name_list = []

        for dcr in dcr_list:
            # Validate each dcr. Validation passes = reuse dcr

            # Fully qualified resource url that can be used
            dcr_id = dcr['id']

            # Define the regex pattern for extracting the required fields
            dcr_pattern = r'/subscriptions/([^/]+)/resourceGroups/([^/]+)/.*?/dataCollectionRules/([^/]+)'

            # Search the id in dcr_List for the fields
            dcr_match = re.search(dcr_pattern, dcr_id)

            if dcr_match:
                dcr_subId = dcr_match.group(1)
                dcr_rg = dcr_match.group(2)
                dcr_name = dcr_match.group(3)

            dcr_name_list.append(dcr_name)

            # Validate DCR Name with regex before continuing
            dcr_name_pattern = re.compile(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_[a-z0-9]+_DCR_\d+$",
                re.IGNORECASE)

            if dcr_name_pattern.match(dcr_name):
                url = f"https://management.azure.com/subscriptions/{dcr_subId}/resourceGroups/{dcr_rg}/providers/Microsoft.Insights/dataCollectionRules/{dcr_name}?api-version=2022-06-01"

                try:
                    dcr_response = send_raw_request(
                        cmd.cli_ctx, method="GET", url=url)
                except HTTPError:
                    # continue as we couldn't connect to DCR. If all
                    # connections fail we create new anyway
                    continue
            else:
                # If DCR Name doesn't match then skip to check next DCR
                continue
            # Validate dcr response
            dcr_response = dcr_response.json()

            dcr_location = dcr_response['location']
            dce_endpoint_id = dcr_response['properties']['dataCollectionEndpointId']
            dcr_source_filePattern = dcr_response['properties']['dataSources']['logFiles'][0]['filePatterns'][0]
            dcr_custom_log = dcr_response['properties']['dataFlows'][0]['outputStream']
            # Custom-SqlAssessment_CL
            dcr_la_id = dcr_response['properties']['destinations']['logAnalytics'][0]['workspaceId']
            # CustomerId is the workspace Id GUID. ResourceId is full qualified resource path
            # dcr_la_name = dcr_response['properties']['destinations']['logAnalytics'][0]['name']
            # workspace name is arbitrary name given by DCR resource metadata

            dcr_found = validate_dcr(
                cmd,
                dcr_location,
                workspace_loc,
                dcr_source_filePattern,
                dcr_custom_log,
                dcr_la_id,
                workspace_id,
                dce_endpoint_id)
            if dcr_found:
                validated_dcr_res_id = dcr_id
                break

            # Match all the stuff
            # collect a list of all dcr names found in this rg and ensure no
            # collision in new create name

            # Validate_DCR():
            # dcr follows naming convention
            # Sample DCR NAME => 0009fc4d-e310-4e40-8e63-c48a23e9cdc1_eastus_DCR_1
            # dcr location = la workspace location as they must be in same

        # New Custom table deployment workflow:
        # Check if old table exists - if yes - run POST command.
        # If does not exist add to the deployment template
        log_exists = does_custom_log_exist(
            cmd, workspace_name, workspace_rg, workspace_sub)

        # Check if log exists. V1 log checked with above. V2 log checked with
        # GET https://management.azure.com/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}/providers/Microsoft.OperationalInsights/workspaces/{workspaceName}/tables/{tableName}?api-version=2021-12-01-preview
        # **This may be redundant if above checks v2 table by default **
        custom_table_url = f"https://management.azure.com/subscriptions/{curr_subscription}/resourceGroups/{workspace_rg}/providers/Microsoft.OperationalInsights/workspaces/{workspace_name}/tables/{table_name}?api-version=2021-12-01-preview"

        try:
            response = send_raw_request(
                cmd.cli_ctx, method="GET", url=custom_table_url)
            if response.status_code == 200:
                log_exists = True
            elif response.status_code == 404:
                log_exists = log_exists or False
            else:
                return False
        except HTTPError:
            log_exists = log_exists or False

        if log_exists:
            # Run a POST on the existing table for migration
            # POST
            # https://management.azure.com/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}/providers/Microsoft.OperationalInsights/workspaces/{workspaceName}/tables/{tableName}/migrate?api-version=2021-12-01-preview
            try:
                # Does a GET on the dce to ensure no http errors - suffices
                table_migration_url = f"https://management.azure.com/subscriptions/{workspace_sub}/resourceGroups/{workspace_rg}/providers/Microsoft.OperationalInsights/workspaces/{workspace_name}/tables/{table_name}/migrate?api-version=2021-12-01-preview"

                send_raw_request(
                    cmd.cli_ctx,
                    method="POST",
                    url=table_migration_url)
            except Exception as e:
                raise AzureResponseError(
                    f"Old Custom Log detected. Migrating to Custom Table failed for url {table_migration_url}. Exception: {e}")
        else:
            # Define the endpoint URL
            url = f"/subscriptions/{workspace_sub}/resourceGroups/{workspace_rg}/providers/Microsoft.OperationalInsights/workspaces/{workspace_name}/tables/{table_name}?api-version=2021-12-01-preview"

            # Define the request headers
            headers = [
                'Content-Type=application/json'
            ]
            body = create_custom_table()

            try:
                send_raw_request(
                    cmd.cli_ctx,
                    method='PUT',
                    url=url,
                    headers=headers,
                    body=body)
            except Exception as e:
                raise AzureResponseError(
                    f"Creating new Custom Table failed with error {e}")

        if not dcr_found:
            # Create DCE, DCR, DCRA, AMA Agent
            dce_name = ""
            dcr_name = ""
            dcra_name = ""
            # These resources must be deployed to a Resource Group in the same
            # region as the LA workspace

            # we must do get req and loop on dce till we get an http error so we know it does not exist
            # else increase x and try again

            base_url = f"https://management.azure.com/subscriptions/{curr_subscription}/resourceGroups/{agent_rg}/providers/Microsoft.Insights/dataCollectionEndpoints/"
            api_version = "?api-version=2022-06-01"

            for index in count(start=1):
                dce_name = f"{workspace_loc}-DCE-{index}"
                dce_url = f"{base_url}{dce_name}{api_version}"
                if not does_name_exist(cmd, dce_url):
                    break

            dce_res = f"/subscriptions/{curr_subscription}/resourceGroups/{agent_rg}/providers/Microsoft.Insights/dataCollectionEndpoints/{dce_name}"

            base_url = f"https://management.azure.com/subscriptions/{curr_subscription}/resourceGroups/{agent_rg}/providers/Microsoft.Insights/dataCollectionRules/"
            api_version = "?api-version=2022-06-01"
            for index in count(start=1):
                dcr_name = f"{workspace_id}_{workspace_loc}_DCR_{index}"
                dcr_url = f"{base_url}{dcr_name}{api_version}"
                if not does_name_exist(cmd, dcr_url):
                    break

            master_template = ArmTemplateBuilder20190401()
            dce = build_dce_resource(dce_name, workspace_loc)
            master_template.add_resource(dce)
            dcr = build_dcr_resource(
                dcr_name,
                workspace_loc,
                workspace_name,
                workspace_res_id,
                dce_res,
                dce_name)
            master_template.add_resource(dcr)

            # amainstall = build_ama_install_resource(sql_virtual_machine_name, vm.location, resource_group_name, curr_subscription)
            # master_template.add_resource(amainstall)

            # /subscriptions/0009fc4d-e310-4e40-8e63-c48a23e9cdc1/resourceGroups/abhaga-iaasrg/providers/Microsoft.Insights/dataCollectionRules/0009fc4d-e310-4e40-8e63-c48a23e9cdc1_eastus_DCR_1
            dcr_resource_id = f"/subscriptions/{curr_subscription}/resourceGroups/{agent_rg}/providers/Microsoft.Insights/dataCollectionRules/{dcr_name}"

            # GET
            # https://management.azure.com/{resourceUri}/providers/Microsoft.Insights/dataCollectionRuleAssociations/{associationName}?api-version=2022-06-01

            # dcrlinkage = build_dcr_vm_linkage_resource(sql_virtual_machine_name, dcra_name, dcr_resource_id, dcr_name)

            # For DCRA do a put request after template deployment
            # PUT https://management.azure.com/subscriptions/703362b3-f278-4e4b-9179-c76eaf41ffc2/resourceGroups/myResourceGroup/providers/Microsoft.Compute/virtualMachines/myVm/providers/Microsoft.Insights/dataCollectionRuleAssociations/myAssociation?api-version=2022-06-01
            # {
            # "properties": {
            #   "dataCollectionRuleId": "/subscriptions/703362b3-f278-4e4b-9179-c76eaf41ffc2/resourceGroups/myResourceGroup/providers/Microsoft.Insights/dataCollectionRules/myCollectionRule"
            # }
            # }
            # master_template.add_resource(dcrlinkage)

            template = master_template.build()

            # deploy ARM template
            deployment_name = 'vm_deploy_' + random_string(32)
            client = get_mgmt_service_client(
                cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
            DeploymentProperties = cmd.get_models(
                'DeploymentProperties',
                resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)

            properties = DeploymentProperties(
                template=template, parameters={}, mode='incremental')

            Deployment = cmd.get_models(
                'Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
            deployment = Deployment(properties=properties)

            # creates the AMA DEPLOYMENT
            LongRunningOperation(
                cmd.cli_ctx)(
                client.begin_create_or_update(
                    agent_rg,
                    deployment_name,
                    deployment))

            # amainstall = build_ama_install_resource(sql_virtual_machine_name, vm.location, resource_group_name, curr_subscription)
            # master_template.add_resource(amainstall)

            create_ama_and_dcra(cmd, curr_subscription, resource_group_name, sql_virtual_machine_name, workspace_id, workspace_loc, dcr_resource_id)

        else:

            # DCR and DCE were validated
            # build ARM template for linkage resource and AMA installation
            create_ama_and_dcra(cmd, curr_subscription, resource_group_name, sql_virtual_machine_name, workspace_id, workspace_loc, validated_dcr_res_id)
            return

    elif enable_assessment is False:
        # Delete DCRA
        # Otherwise AssessmentSetting payload is set above
        # GET DCRA ATTACHED TO VM: Validate for Assessment and delete
        # Unless we can track assessment dcra resource id.

        # GET
        # https://management.azure.com/subscriptions/703362b3-f278-4e4b-9179-c76eaf41ffc2/resourceGroups/myResourceGroup/providers/Microsoft.Compute/virtualMachines/myVm/providers/Microsoft.Insights/dataCollectionRuleAssociations?api-version=2022-06-01

        vm_sub = get_subscription_id(cmd.cli_ctx)
        vm_rg = resource_group_name
        vm_name = sql_virtual_machine_name

        dcra_get_url = f"https://management.azure.com/subscriptions/{vm_sub}/resourceGroups/{vm_rg}/providers/Microsoft.Compute/virtualMachines/{vm_name}/providers/Microsoft.Insights/dataCollectionRuleAssociations?api-version=2022-06-01"
        try:
            # GET on VM DCRA endpoint to list all DCRA attached to this VM
            dcra_list = send_raw_request(
                cmd.cli_ctx, method="GET", url=dcra_get_url)
        except HTTPError:
            # No DCRA Found. Assessment is disabled through AMA.
            return
        dcra_list = dcra_list.json()
        if 'value' in dcra_list and not dcra_list['value']:
            # Raise warning or message saying no DCRA found
            return
        for dcra in dcra_list['value']:

            dcra_name = dcra['name']
            pattern = re.compile(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_[a-z0-9]+_DCRA_\d+$",
                re.IGNORECASE)
            if pattern.match(dcra_name):

                # Match from response the values and add to url then delete

                curr_subscription = get_subscription_id(cmd.cli_ctx)
                resourceUri = f"subscriptions/{curr_subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute/virtualMachines/{sql_virtual_machine_name}"
                # DELETE
                # https://management.azure.com/{resourceUri}/providers/Microsoft.Insights/dataCollectionRuleAssociations/{associationName}?api-version=2022-06-01
                dcra_url = f"https://management.azure.com/{resourceUri}/providers/Microsoft.Insights/dataCollectionRuleAssociations/{dcra_name}?api-version=2022-06-01"
                send_raw_request(
                    cmd.cli_ctx, method="DELETE", url=dcra_url)
                return
            # Raise message DCRA deleted. Assessment disabled succesfully.

# endregion Helpers for custom commands
