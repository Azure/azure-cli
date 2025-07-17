# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.acs.azuremonitormetrics.constants import DC_API
from azure.cli.command_modules.acs.azuremonitormetrics.dc.defaults import get_default_dcra_name
from knack.util import CLIError


# pylint: disable=line-too-long
def create_dcra(cmd, cluster_region, cluster_subscription, cluster_resource_group_name, cluster_name, dcr_resource_id):
    cluster_resource_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.ContainerService/managedClusters/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        cluster_name
    )
    dcra_name = get_default_dcra_name()
    dcra_resource_id = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Insights/dataCollectionRuleAssociations/{2}".format(
        cluster_subscription,
        cluster_resource_group_name,
        dcra_name
    )
    description_str = "Promtheus data collection association between DCR, DCE and target AKS resource"
    association_body = {
        "location": cluster_region,
        "properties": {
            "dataCollectionRuleId": dcr_resource_id,
            "description": description_str
        }
    }
    from azure.cli.command_modules.acs._client_factory import get_resources_client
    resources = get_resources_client(cmd.cli_ctx, cluster_subscription)
    try:
        resources.begin_create_or_update_by_id(
            f"{cluster_resource_id}/providers/Microsoft.Insights/dataCollectionRuleAssociations/{dcra_name}",
            DC_API,
            association_body
        )
        return dcra_resource_id
    except Exception as error:
        raise CLIError(error)
