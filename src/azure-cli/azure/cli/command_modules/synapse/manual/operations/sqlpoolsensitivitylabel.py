# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.synapse.models import SensitivityLabel, SensitivityLabelSource
from knack.util import CLIError


def sqlpool_sensitivity_label_show(
        client,
        sql_pool_name,
        workspace_name,
        schema_name,
        table_name,
        column_name,
        resource_group_name):

    return client.get(
        resource_group_name,
        workspace_name,
        sql_pool_name,
        schema_name,
        table_name,
        column_name,
        SensitivityLabelSource.current)


def sqlpool_sensitivity_label_update(
        cmd,
        client,
        sql_pool_name,
        workspace_name,
        schema_name,
        table_name,
        column_name,
        resource_group_name,
        label_name=None,
        information_type=None):
    '''
    Updates a sensitivity label. Custom update function to apply parameters to instance.
    '''

    # Get the information protection policy
    from azure.mgmt.security import SecurityCenter
    from azure.core.exceptions import HttpResponseError

    security_center_client = get_mgmt_service_client(cmd.cli_ctx, SecurityCenter, asc_location="centralus")

    information_protection_policy = security_center_client.information_protection_policies.get(
        scope=_create_scope(), information_protection_policy_name="effective")

    sensitivity_label = SensitivityLabel()

    # Get the current label
    try:
        current_label = client.get(
            resource_group_name,
            workspace_name,
            sql_pool_name,
            schema_name,
            table_name,
            column_name,
            SensitivityLabelSource.current)
        # Initialize with existing values
        sensitivity_label.label_name = current_label.label_name
        sensitivity_label.label_id = current_label.label_id
        sensitivity_label.information_type = current_label.information_type
        sensitivity_label.information_type_id = current_label.information_type_id

    except HttpResponseError as ex:
        if not (ex and 'SensitivityLabelsLabelNotFound' in str(ex)):
            raise ex

    # Find the label id and information type id in the policy by the label name provided
    if label_name:
        label_id = next((id for id in information_protection_policy.labels
                         if information_protection_policy.labels[id].display_name.lower() ==
                         label_name.lower()),
                        None)
        if label_id is None:
            raise CLIError('The provided label name was not found in the information protection policy.')
        sensitivity_label.label_id = label_id
        sensitivity_label.label_name = label_name

    if information_type:
        information_type_id = next((id for id in information_protection_policy.information_types
                                    if information_protection_policy.information_types[id].display_name.lower() ==
                                    information_type.lower()),
                                   None)
        if information_type_id is None:
            raise CLIError('The provided information type was not found in the information protection policy.')
        sensitivity_label.information_type_id = information_type_id
        sensitivity_label.information_type = information_type

    return client.create_or_update(
        resource_group_name, workspace_name, sql_pool_name, schema_name, table_name, column_name, sensitivity_label)


def sqlpool_sensitivity_label_create(
        cmd,
        client,
        sql_pool_name,
        workspace_name,
        schema_name,
        table_name,
        column_name,
        resource_group_name,
        label_name,
        information_type):
    # Get the information protection policy
    from azure.mgmt.security import SecurityCenter
    security_center_client = get_mgmt_service_client(cmd.cli_ctx, SecurityCenter, asc_location="centralus")
    information_protection_policy = security_center_client.information_protection_policies.get(
        scope=_create_scope(), information_protection_policy_name="effective")

    sensitivity_label = SensitivityLabel()
    # Find the label id and information type id in the policy by the label name provided
    if label_name:
        label_id = next((id for id in information_protection_policy.labels
                         if information_protection_policy.labels[id].display_name.lower() ==
                         label_name.lower()),
                        None)
        if label_id is None:
            raise CLIError('The provided label name was not found in the information protection policy.')
        sensitivity_label.label_id = label_id
        sensitivity_label.label_name = label_name

    if information_type:
        information_type_id = next((id for id in information_protection_policy.information_types
                                    if information_protection_policy.information_types[id].display_name.lower() ==
                                    information_type.lower()),
                                   None)
        if information_type_id is None:
            raise CLIError('The provided information type was not found in the information protection policy.')
        sensitivity_label.information_type_id = information_type_id
        sensitivity_label.information_type = information_type

    return client.create_or_update(
        resource_group_name, workspace_name, sql_pool_name, schema_name, table_name, column_name, sensitivity_label)


def _create_scope():
    # Gets tenantId from current subscription.
    from azure.cli.core._profile import Profile
    profile = Profile()
    sub = profile.get_subscription()
    tenant_id = sub['tenantId']

    scope_format_string = '/providers/Microsoft.Management/managementGroups/{}'
    return scope_format_string.format(tenant_id)
