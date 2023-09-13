# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.acs.azuremonitormetrics.addonput import addon_put
from azure.cli.command_modules.acs.azuremonitormetrics.amg.link import link_grafana_instance
from azure.cli.command_modules.acs.azuremonitormetrics.amw.helper import get_azure_monitor_workspace_resource
from azure.cli.command_modules.acs.azuremonitormetrics.dc.dce_api import create_dce
from azure.cli.command_modules.acs.azuremonitormetrics.dc.dcr_api import create_dcr
from azure.cli.command_modules.acs.azuremonitormetrics.dc.dcra_api import create_dcra
from azure.cli.command_modules.acs.azuremonitormetrics.dc.delete import (
    delete_dc_objects_if_prometheus_enabled,
    get_dc_objects_list
)
from azure.cli.command_modules.acs.azuremonitormetrics.helper import (
    check_azuremonitormetrics_profile,
    rp_registrations
)
from azure.cli.command_modules.acs.azuremonitormetrics.recordingrules.create import create_rules
from azure.cli.command_modules.acs.azuremonitormetrics.recordingrules.delete import delete_rules
from azure.cli.core.azclierror import InvalidArgumentValueError
from knack.util import CLIError


# pylint: disable=line-too-long
def link_azure_monitor_profile_artifacts(
        cmd,
        cluster_subscription,
        cluster_resource_group_name,
        cluster_name,
        cluster_region,
        raw_parameters,
        create_flow
):
    # MAC creation if required
    azure_monitor_workspace_resource_id, azure_monitor_workspace_location = get_azure_monitor_workspace_resource(cmd, cluster_subscription, cluster_region, raw_parameters)
    # DCE creation
    dce_resource_id = create_dce(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, azure_monitor_workspace_location)
    # DCR creation
    dcr_resource_id = create_dcr(cmd, azure_monitor_workspace_location, azure_monitor_workspace_resource_id, cluster_subscription, cluster_resource_group_name, cluster_name, dce_resource_id)
    # DCRA creation
    create_dcra(cmd, cluster_region, cluster_subscription, cluster_resource_group_name, cluster_name, dcr_resource_id)
    # Link grafana
    link_grafana_instance(cmd, raw_parameters, azure_monitor_workspace_resource_id)
    # create recording rules and alerts
    create_rules(cmd, cluster_subscription, cluster_resource_group_name, cluster_name, azure_monitor_workspace_resource_id, azure_monitor_workspace_location, raw_parameters)
    # if aks cluster create flow -> do a PUT on the AKS cluster to enable the addon
    if create_flow:
        addon_put(cmd, cluster_subscription, cluster_resource_group_name, cluster_name)


# pylint: disable=line-too-long
def unlink_azure_monitor_profile_artifacts(cmd, cluster_subscription, cluster_resource_group_name, cluster_name):
    # Remove DC* if prometheus is enabled
    dc_objects_list = get_dc_objects_list(cmd, cluster_subscription, cluster_resource_group_name, cluster_name)
    delete_dc_objects_if_prometheus_enabled(cmd, dc_objects_list, cluster_subscription, cluster_resource_group_name, cluster_name)
    # Delete rules (Conflict({"error":{"code":"InvalidResourceLocation","message":"The resource 'NodeRecordingRulesRuleGroup-<clustername>' already exists in location 'eastus2' in resource group '<clustername>'.
    # A resource with the same name cannot be created in location 'eastus'. Please select a new resource name."}})
    delete_rules(cmd, cluster_subscription, cluster_resource_group_name, cluster_name)


# pylint: disable=too-many-locals,too-many-branches,too-many-statements,line-too-long
def ensure_azure_monitor_profile_prerequisites(
    cmd,
    cluster_subscription,
    cluster_resource_group_name,
    cluster_name,
    cluster_region,
    raw_parameters,
    remove_azuremonitormetrics,
    create_flow=False
):
    cloud_name = cmd.cli_ctx.cloud.name
    if cloud_name.lower() == 'azurechinacloud':
        raise CLIError("Azure China Cloud is not supported for the Azure Monitor Metrics addon")

    if cloud_name.lower() == "azureusgovernment":
        grafana_resource_id = raw_parameters.get("grafana_resource_id")
        if grafana_resource_id is not None:
            if grafana_resource_id != "":
                raise InvalidArgumentValueError("Azure US Government cloud does not support Azure Managed Grarfana yet. Please follow this documenation for enabling it via the public cloud : aka.ms/ama-grafana-link-ff")

    if remove_azuremonitormetrics:
        unlink_azure_monitor_profile_artifacts(
            cmd,
            cluster_subscription,
            cluster_resource_group_name,
            cluster_name
        )
    else:
        # Check if already onboarded
        if create_flow is False:
            check_azuremonitormetrics_profile(cmd, cluster_subscription, cluster_resource_group_name, cluster_name)
        # Do RP registrations if required
        rp_registrations(cmd, cluster_subscription)
        link_azure_monitor_profile_artifacts(
            cmd,
            cluster_subscription,
            cluster_resource_group_name,
            cluster_name,
            cluster_region,
            raw_parameters,
            create_flow
        )
