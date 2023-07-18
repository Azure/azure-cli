# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.core.exceptions import HttpResponseError
from azure.core.paging import ItemPaged
from azure.cli.command_modules.vm._client_factory import cf_log_analytics_data_sources, cf_log_analytics
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.command_modules.vm.custom import (
    list_extensions,
    set_extension
)
from ._assessment_data_source import data_source_name
from ._assessment_data_source import custom_log_name, dcr_source_pattern
from azure.cli.core.util import send_raw_request
from ._template_builder import build_ama_install_resource, build_dcr_vm_linkage_resource
from azure.cli.command_modules.vm._vm_utils import ArmTemplateBuilder20190401
from azure.cli.core.commands.client_factory import get_mgmt_service_client

from azure.cli.core.commands import LongRunningOperation

WINDOWS_LA_EXT_NAME = 'MicrosoftMonitoringAgent'
WINDOWS_LA_EXT_PUBLISHER = 'Microsoft.EnterpriseCloud.Monitoring'
WINDOWS_LA_EXT_VERSION = '1.0'


def get_sqlvirtualmachine_management_client(cli_ctx):
    from azure.mgmt.sqlvirtualmachine import SqlVirtualMachineManagementClient

    # Normal production scenario.
    return get_mgmt_service_client(cli_ctx, SqlVirtualMachineManagementClient)


def get_sqlvirtualmachine_availability_group_listeners_operations(cli_ctx, _):
    return get_sqlvirtualmachine_management_client(
        cli_ctx).availability_group_listeners


def get_sqlvirtualmachine_sql_virtual_machine_groups_operations(cli_ctx, _):
    return get_sqlvirtualmachine_management_client(
        cli_ctx).sql_virtual_machine_groups


def get_sqlvirtualmachine_sql_virtual_machines_operations(cli_ctx, _):
    return get_sqlvirtualmachine_management_client(
        cli_ctx).sql_virtual_machines


def get_sqlvirtualmachine_operations(cli_ctx, _):
    return get_sqlvirtualmachine_management_client(cli_ctx).operations


def _get_log_analytics_client(cmd):
    subscription_id = get_subscription_id(cmd.cli_ctx)
    return cf_log_analytics(cmd.cli_ctx, subscription_id)


def get_workspace_id_from_log_analytics_extension(
        cmd, resource_group_name, sql_virtual_machine_name):
    '''
    Get workspace id from Log Analytics extension on VM
    '''
    extensions = list_extensions(
        cmd,
        resource_group_name,
        sql_virtual_machine_name)
    for ext in extensions:
        if (ext.publisher == WINDOWS_LA_EXT_PUBLISHER and
                ext.type_properties_type == WINDOWS_LA_EXT_NAME):
            return ext.settings.get('workspaceId', None)

    return None


def set_log_analytics_extension(
        cmd,
        resource_group_name,
        vm_name,
        workspace_rg,
        workspace_name):
    '''
    Deploy Log Analytics extension to the Windows VM
    '''
    log_client = _get_log_analytics_client(cmd)

    # Get workspace id and key
    customer_id = log_client.workspaces.get(
        workspace_rg, workspace_name).customer_id
    settings = {
        'workspaceId': customer_id,
        'stopOnMultipleConnections': 'true'
    }
    primary_shared_key = log_client.shared_keys.get_shared_keys(
        workspace_rg, workspace_name).primary_shared_key
    protected_settings = {
        'workspaceKey': primary_shared_key
    }

    return set_extension(cmd, resource_group_name, vm_name,
                         WINDOWS_LA_EXT_NAME,
                         WINDOWS_LA_EXT_PUBLISHER,
                         WINDOWS_LA_EXT_VERSION,
                         settings,
                         protected_settings), customer_id


def get_workspace_in_sub(cmd, workspace_id):
    '''
    Get workspace details for given workspace id
    '''
    log_client = _get_log_analytics_client(cmd)
    obj_list = log_client.workspaces.list()
    workspaces = list(obj_list) if isinstance(
        obj_list, ItemPaged) else obj_list  # Convert iterable to list
    return next((w for w in workspaces if w.customer_id == workspace_id), None)


def does_custom_log_exist(cmd, workspace_name, workspace_rg, workspace_sub):
    '''
    Validate and deploy custom log definition for assessment feature
    '''
    subscription_id = workspace_sub
    data_sources_client = cf_log_analytics_data_sources(
        cmd.cli_ctx, subscription_id)

    try:
        # Verify if required custom log definition already exists. Same for custom table.
        # Does this detect new custom tables? Checks if LA workspace has this
        # data source
        data_sources_client.get(workspace_rg, workspace_name, data_source_name)
    except HttpResponseError as err:
        # Required custom log definition does not exist so deploy it
        if err.status_code == 404:
            return False
        raise err
    return True


def create_custom_table():
    import json
    # Define the payload
    body = {
        "properties": {
            "schema": {
                "name": "SqlAssessment_CL",
                "columns": [
                    {
                        "name": "TimeGenerated",
                        "type": "DateTime"
                    },
                    {
                        "name": "RawData",
                        "type": "String"
                    }
                ]
            }
        }
    }

    # Convert body to a string
    body = json.dumps(body)

    return body


# pylint: disable=broad-except
def validate_dcr(cmd, dcr_location, workspace_loc, dcr_source_filePattern,
                 dcr_custom_log, dcr_la_id, workspace_id, dce_endpoint_id):
    import re
    if dcr_location != workspace_loc:
        return False
    if dcr_source_filePattern != dcr_source_pattern:
        return False
    if dcr_custom_log != custom_log_name:
        return False
    if dcr_la_id != workspace_id:
        return False

    dce_pattern = r'/subscriptions/([^/]+)/resourceGroups/([^/]+)/.*?/dataCollectionEndpoints/([^/]+)'

    # Does the dcr_custom_log exist in the dcr_la_id -> Should we double check this? And do the POST/create accordingly?
    # Validate Log exists else set flag so it is created later

    # Search for the pattern in the string
    dce_match = re.search(dce_pattern, dce_endpoint_id)

    if dce_match:
        dce_sub = dce_match.group(1)
        dce_rg = dce_match.group(2)
        dce_name = dce_match.group(3)

    # dce_url = f"https://management.azure.com/subscriptions/{dce_sub}"
    # /resourceGroups/{dce_rg}/providers/Microsoft.Insights/dataCollectionEndpoints/
    # {dce_name}?api-version=2022-06-01"
    dce_url = (
        f"https://management.azure.com/subscriptions/{dce_sub}"
        f"/resourceGroups/{dce_rg}"
        f"/providers/Microsoft.Insights/dataCollectionEndpoints/{dce_name}"
        f"?api-version=2022-06-01"
    )
    try:
        # Does a GET on the dce to ensure no http errors - suffices
        send_raw_request(cmd.cli_ctx, method="GET", url=dce_url)
    except Exception:
        # Validation on DCE Endpoint failed return False
        # We can consider not returning false - creating a DCE and patching the
        # DCR here
        return False
    return True


def does_name_exist(cmd, res_url):

    try:
        # Does a GET on the dce/dcr/dcra res to ensure no http errors
        send_raw_request(cmd.cli_ctx, method="GET", url=res_url)
    except Exception:
        # dce does not exist. so we do not need to bump name
        return False
    return True


def create_dcra(dcr_res_id):
    import json
    # Define the payload
    body = {
        "properties": {
            "dataCollectionRuleId": dcr_res_id
        }
    }

    # Convert body to a string
    body = json.dumps(body)

    return body


# pylint: disable=too-many-locals
def create_ama_and_dcra(cmd, curr_subscription, resource_group_name,
                        sql_virtual_machine_name, workspace_id, workspace_loc, dcr_id):
    master_template = ArmTemplateBuilder20190401()

    vm_resource_uri = (f"subscriptions/{curr_subscription}/"
                       f"resourceGroups/{resource_group_name}/"
                       f"providers/Microsoft.Compute/virtualMachines/{sql_virtual_machine_name}/")

    base_url = (f"https://management.azure.com/{vm_resource_uri}/"
                f"providers/Microsoft.Insights/dataCollectionRuleAssociations/")
    api_version = "?api-version=2022-06-01"
    from itertools import count
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.util import random_string
    for index in count(start=1):
        dcra_name = f"{workspace_id}_{workspace_loc}_DCRA_{index}"
        dcra_url = f"{base_url}{dcra_name}{api_version}"
        if not does_name_exist(cmd, dcra_url):
            break
    from azure.cli.command_modules.vm.custom import get_vm

    vm = get_vm(
        cmd,
        resource_group_name,
        sql_virtual_machine_name,
        'instanceView')
    amainstall = build_ama_install_resource(
        sql_virtual_machine_name, vm.location)

    master_template.add_resource(amainstall)

    dcrlinkage = build_dcr_vm_linkage_resource(sql_virtual_machine_name, dcra_name, dcr_id)
    master_template.add_resource(dcrlinkage)

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

    LongRunningOperation(cmd.cli_ctx)(client.begin_create_or_update(
        resource_group_name, deployment_name, deployment))
