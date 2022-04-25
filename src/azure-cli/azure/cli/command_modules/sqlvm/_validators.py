# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from msrestazure.tools import resource_id, is_valid_resource_id
from azure.cli.core.util import CLIError
from azure.cli.core.commands.client_factory import get_subscription_id


# pylint: disable=too-many-statements,line-too-long
def validate_sqlvm_group(cmd, namespace):
    '''
    Validates if name or id has been provided. If name has been provided, it assumes the group is in the same resource group.
    '''
    group = namespace.sql_virtual_machine_group_resource_id

    if group and not is_valid_resource_id(group):
        namespace.sql_virtual_machine_group_resource_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.SqlVirtualMachine', type='sqlVirtualMachineGroups',
            name=group
        )


# pylint: disable=too-many-statements,line-too-long
def validate_sqlvm_list(cmd, namespace):
    '''
    Validates if name or id has been provided. If name has been provided, it assumes the vm is in the same resource group.
    '''
    vms = namespace.sql_virtual_machine_instances

    for n, sqlvm in enumerate(vms):
        if sqlvm and not is_valid_resource_id(sqlvm):
            # add the correct resource id
            namespace.sql_virtual_machine_instances[n] = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.SqlVirtualMachine', type='sqlVirtualMachines',
                name=sqlvm
            )


# pylint: disable=too-many-statements,line-too-long
def validate_load_balancer(cmd, namespace):
    '''
    Validates if name or id has been provided. If name has been provided, it assumes the load balancer is in the same group.
    '''
    lb = namespace.load_balancer_resource_id

    if not is_valid_resource_id(lb):
        namespace.load_balancer_resource_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network', type='loadBalancers',
            name=lb
        )


# pylint: disable=too-many-statements,line-too-long
def validate_public_ip_address(cmd, namespace):
    '''
    Validates if name or id has been provided. If name has been provided, it assumes the public ip address is in the same group.
    '''
    public_ip = namespace.public_ip_address_resource_id

    if public_ip and not is_valid_resource_id(public_ip):
        namespace.public_ip_address_resource_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network', type='publicIPAddresses',
            name=public_ip
        )


# pylint: disable=too-many-statements,line-too-long
def validate_subnet(cmd, namespace):
    '''
    Validates if name or id has been provided. If name has been provided, it assumes the public ip address is in the same group.
    '''
    subnet = namespace.subnet_resource_id
    vnet = namespace.vnet_name

    if vnet and '/' in vnet:
        raise CLIError("incorrect usage: --subnet ID | --subnet NAME --vnet-name NAME")

    subnet_is_id = is_valid_resource_id(subnet)
    if (subnet_is_id and vnet) or (not subnet_is_id and not vnet):
        raise CLIError("incorrect usage: --subnet ID | --subnet NAME --vnet-name NAME")

    if not subnet_is_id and vnet:
        namespace.subnet_resource_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network', type='virtualNetworks',
            name=vnet, child_type_1='subnets',
            child_name_1=subnet
        )


# pylint: disable=too-many-statements,line-too-long
def validate_sqlmanagement(namespace):
    '''
    Validates if sql management mode provided, the offer type and sku type has to be provided.
    '''
    sql_mgmt_mode = namespace.sql_management_mode

    if (sql_mgmt_mode == "NoAgent" and (namespace.sql_image_sku is None or namespace.sql_image_offer is None)):
        raise CLIError("usage error: --sql-mgmt-type NoAgent --image-sku NAME --image-offer NAME")


# pylint: disable=too-many-statements,line-too-long
def validate_expand(namespace):
    '''
    Concatenates expand parameters
    '''
    if namespace.expand is not None:
        namespace.expand = ",".join(namespace.expand)

# pylint: disable=too-many-statements,line-too-long
def validate_assessment(namespace):
    '''
    Validates assessment settings
    '''
    enable_assessment = namespace.enable_assessment
    enable_assessment_schedule = namespace.enable_assessment_schedule
    assessment_weekly_interval = namespace.assessment_weekly_interval
    assessment_monthly_occurrence = namespace.assessment_monthly_occurrence
    assessment_day_of_week = namespace.assessment_day_of_week
    assessment_start_time_local = namespace.assessment_start_time_local

    is_assessment_schedule_provided = False
    if (assessment_weekly_interval is not None or
        assessment_weekly_interval is not None or assessment_monthly_occurrence is not None or
        assessment_day_of_week is not None or assessment_start_time_local is not None):
        is_assessment_schedule_provided = True

    # Validate conflicting settings
    if (enable_assessment_schedule is False and is_assessment_schedule_provided):
        raise CLIError("Assessment schedule settings cannot be provided while enable-assessment-schedule is False")

    # Validate conflicting settings
    if (enable_assessment is False and is_assessment_schedule_provided):
        raise CLIError("Assessment schedule settings cannot be provided while enable-assessment is False")

    # Validate necessary fields for Assessment schedule
    if is_assessment_schedule_provided:
        if (assessment_weekly_interval is not None and assessment_monthly_occurrence is not None):
            raise CLIError("Both assessment-weekly-interval and assessment-montly-occurrence cannot be provided at the same time for Assessment schedule")
        if (assessment_weekly_interval is None and assessment_monthly_occurrence is None):
            raise CLIError("Either assessment-weekly-interval and assessment-montly-occurrence must be provided for Assessment schedule")
        if assessment_day_of_week is None:
            raise CLIError("assessment-day-of-week must be provided for Assessment schedule")
        if assessment_start_time_local is None:
            raise CLIError("assessment-start-time-local must be provided for Assessment schedule")

# pylint: disable=too-many-statements,line-too-long
def validate_assessment_start_time_local(namespace):
    '''
    Validates assessment start time format
    '''
    assessment_start_time_local = namespace.assessment_start_time_local

    TIME_FORMAT = '%H:%M'
    if assessment_start_time_local:
        try:
            datetime.strptime(assessment_start_time_local, TIME_FORMAT)
        except ValueError:
            raise CLIError("assessment-start-time-local input '{}' is not valid time. Valid example: 19:30".format(assessment_start_time_local))
