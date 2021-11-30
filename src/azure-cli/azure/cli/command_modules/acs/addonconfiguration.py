# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import json

from azure.cli.core.azclierror import (
    AzCLIError,
    ClientRequestError,
)
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.client_factory import (
    get_mgmt_service_client,
)
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait, send_raw_request
from azure.core.exceptions import HttpResponseError
from knack.log import get_logger
from msrestazure.tools import parse_resource_id, resource_id

from ._client_factory import cf_resource_groups, cf_resources
from ._consts import (
    CONST_INGRESS_APPGW_ADDON_NAME,
    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID,
    CONST_INGRESS_APPGW_SUBNET_CIDR,
    CONST_INGRESS_APPGW_SUBNET_ID,
    CONST_MONITORING_ADDON_NAME,
    CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID,
    CONST_VIRTUAL_NODE_ADDON_NAME,
)
from ._resourcegroup import get_rg_location
from ._roleassignments import add_role_assignment

logger = get_logger(__name__)


# pylint: disable=too-many-locals
def ensure_default_log_analytics_workspace_for_monitoring(
    cmd, subscription_id, resource_group_name
):
    # mapping for azure public cloud
    # log analytics workspaces cannot be created in WCUS region due to capacity limits
    # so mapped to EUS per discussion with log analytics team
    AzureCloudLocationToOmsRegionCodeMap = {
        "australiasoutheast": "ASE",
        "australiaeast": "EAU",
        "australiacentral": "CAU",
        "canadacentral": "CCA",
        "centralindia": "CIN",
        "centralus": "CUS",
        "eastasia": "EA",
        "eastus": "EUS",
        "eastus2": "EUS2",
        "eastus2euap": "EAP",
        "francecentral": "PAR",
        "japaneast": "EJP",
        "koreacentral": "SE",
        "northeurope": "NEU",
        "southcentralus": "SCUS",
        "southeastasia": "SEA",
        "uksouth": "SUK",
        "usgovvirginia": "USGV",
        "westcentralus": "EUS",
        "westeurope": "WEU",
        "westus": "WUS",
        "westus2": "WUS2",
        "brazilsouth": "CQ",
        "brazilsoutheast": "BRSE",
        "norwayeast": "NOE",
        "southafricanorth": "JNB",
        "northcentralus": "NCUS",
        "uaenorth": "DXB",
        "germanywestcentral": "DEWC",
        "ukwest": "WUK",
        "switzerlandnorth": "CHN",
        "switzerlandwest": "CHW",
        "uaecentral": "AUH",
    }
    AzureCloudRegionToOmsRegionMap = {
        "australiacentral": "australiacentral",
        "australiacentral2": "australiacentral",
        "australiaeast": "australiaeast",
        "australiasoutheast": "australiasoutheast",
        "brazilsouth": "brazilsouth",
        "canadacentral": "canadacentral",
        "canadaeast": "canadacentral",
        "centralus": "centralus",
        "centralindia": "centralindia",
        "eastasia": "eastasia",
        "eastus": "eastus",
        "eastus2": "eastus2",
        "francecentral": "francecentral",
        "francesouth": "francecentral",
        "japaneast": "japaneast",
        "japanwest": "japaneast",
        "koreacentral": "koreacentral",
        "koreasouth": "koreacentral",
        "northcentralus": "northcentralus",
        "northeurope": "northeurope",
        "southafricanorth": "southafricanorth",
        "southafricawest": "southafricanorth",
        "southcentralus": "southcentralus",
        "southeastasia": "southeastasia",
        "southindia": "centralindia",
        "uksouth": "uksouth",
        "ukwest": "ukwest",
        "westcentralus": "eastus",
        "westeurope": "westeurope",
        "westindia": "centralindia",
        "westus": "westus",
        "westus2": "westus2",
        "norwayeast": "norwayeast",
        "norwaywest": "norwayeast",
        "switzerlandnorth": "switzerlandnorth",
        "switzerlandwest": "switzerlandwest",
        "uaenorth": "uaenorth",
        "germanywestcentral": "germanywestcentral",
        "germanynorth": "germanywestcentral",
        "uaecentral": "uaecentral",
        "eastus2euap": "eastus2euap",
        "brazilsoutheast": "brazilsoutheast",
    }

    # mapping for azure china cloud
    # log analytics only support China East2 region
    AzureChinaLocationToOmsRegionCodeMap = {
        "chinaeast": "EAST2",
        "chinaeast2": "EAST2",
        "chinanorth": "EAST2",
        "chinanorth2": "EAST2",
    }
    AzureChinaRegionToOmsRegionMap = {
        "chinaeast": "chinaeast2",
        "chinaeast2": "chinaeast2",
        "chinanorth": "chinaeast2",
        "chinanorth2": "chinaeast2",
    }

    # mapping for azure us governmner cloud
    AzureFairfaxLocationToOmsRegionCodeMap = {
        "usgovvirginia": "USGV",
        "usgovarizona": "PHX",
    }
    AzureFairfaxRegionToOmsRegionMap = {
        "usgovvirginia": "usgovvirginia",
        "usgovtexas": "usgovvirginia",
        "usgovarizona": "usgovarizona",
    }

    rg_location = get_rg_location(cmd.cli_ctx, resource_group_name)
    cloud_name = cmd.cli_ctx.cloud.name

    if cloud_name.lower() == "azurecloud":
        workspace_region = AzureCloudRegionToOmsRegionMap.get(
            rg_location, "eastus"
        )
        workspace_region_code = AzureCloudLocationToOmsRegionCodeMap.get(
            workspace_region, "EUS"
        )
    elif cloud_name.lower() == "azurechinacloud":
        workspace_region = AzureChinaRegionToOmsRegionMap.get(
            rg_location, "chinaeast2"
        )
        workspace_region_code = AzureChinaLocationToOmsRegionCodeMap.get(
            workspace_region, "EAST2"
        )
    elif cloud_name.lower() == "azureusgovernment":
        workspace_region = AzureFairfaxRegionToOmsRegionMap.get(
            rg_location, "usgovvirginia"
        )
        workspace_region_code = AzureFairfaxLocationToOmsRegionCodeMap.get(
            workspace_region, "USGV"
        )
    else:
        logger.error(
            "AKS Monitoring addon not supported in cloud : %s", cloud_name
        )

    default_workspace_resource_group = (
        "DefaultResourceGroup-" + workspace_region_code
    )
    default_workspace_name = "DefaultWorkspace-{0}-{1}".format(
        subscription_id, workspace_region_code
    )

    default_workspace_resource_id = (
        "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.OperationalInsights/workspaces/{2}".format(
            subscription_id,
            default_workspace_resource_group,
            default_workspace_name,
        )
    )
    resource_groups = cf_resource_groups(cmd.cli_ctx, subscription_id)
    resources = cf_resources(cmd.cli_ctx, subscription_id)

    # check if default RG exists
    if resource_groups.check_existence(default_workspace_resource_group):
        try:
            resource = resources.get_by_id(
                default_workspace_resource_id, "2015-11-01-preview"
            )
            return resource.id
        except HttpResponseError as ex:
            if ex.status_code != 404:
                raise ex
    else:
        resource_groups.create_or_update(
            default_workspace_resource_group, {"location": workspace_region}
        )

    GenericResource = cmd.get_models(
        "GenericResource", resource_type=ResourceType.MGMT_RESOURCE_RESOURCES
    )
    generic_resource = GenericResource(
        location=workspace_region, properties={"sku": {"name": "standalone"}}
    )

    async_poller = resources.begin_create_or_update_by_id(
        default_workspace_resource_id, "2015-11-01-preview", generic_resource
    )

    ws_resource_id = ""
    while True:
        result = async_poller.result(15)
        if async_poller.done():
            ws_resource_id = result.id
            break

    return ws_resource_id


def sanitize_loganalytics_ws_resource_id(workspace_resource_id):
    workspace_resource_id = workspace_resource_id.strip()
    if not workspace_resource_id.startswith("/"):
        workspace_resource_id = "/" + workspace_resource_id
    if workspace_resource_id.endswith("/"):
        workspace_resource_id = workspace_resource_id.rstrip("/")
    return workspace_resource_id


# pylint: disable=too-many-locals,too-many-branches,too-many-statements
def ensure_container_insights_for_monitoring(
    cmd,
    addon,
    cluster_subscription,
    cluster_resource_group_name,
    cluster_name,
    cluster_region,
    remove_monitoring=False,
    aad_route=False,
    create_dcr=False,
    create_dcra=False,
):
    """
    Either adds the ContainerInsights solution to a LA Workspace OR sets up a DCR (Data Collection Rule) and DCRA
    (Data Collection Rule Association). Both let the monitoring addon send data to a Log Analytics Workspace.

    Set aad_route == True to set up the DCR data route. Otherwise the solution route will be used. Create_dcr and
    create_dcra have no effect if aad_route == False.

    Set remove_monitoring to True and create_dcra to True to remove the DCRA from a cluster. The association makes
    it very hard to delete either the DCR or cluster. (It is not obvious how to even navigate to the association from
    the portal, and it prevents the cluster and DCR from being deleted individually).
    """
    if not addon.enabled:
        return None

    # workaround for this addon key which has been seen lowercased in the wild
    for key in list(addon.config):
        if (
            key.lower() == CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID.lower() and
            key != CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID
        ):
            addon.config[
                CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID
            ] = addon.config.pop(key)

    workspace_resource_id = addon.config[
        CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID
    ]
    workspace_resource_id = sanitize_loganalytics_ws_resource_id(
        workspace_resource_id
    )

    # extract subscription ID and resource group from workspace_resource_id URL
    try:
        subscription_id = workspace_resource_id.split("/")[2]
        resource_group = workspace_resource_id.split("/")[4]
        workspace_name = workspace_resource_id.split("/")[8]
    except IndexError:
        raise AzCLIError(
            "Could not locate resource group in workspace-resource-id URL."
        )

    # region of workspace can be different from region of RG so find the location of the workspace_resource_id
    if not remove_monitoring:
        resources = cf_resources(cmd.cli_ctx, subscription_id)
        try:
            resource = resources.get_by_id(
                workspace_resource_id, "2015-11-01-preview"
            )
            location = resource.location
        except HttpResponseError as ex:
            raise ex

    if aad_route:
        cluster_resource_id = (
            f"/subscriptions/{cluster_subscription}/resourceGroups/{cluster_resource_group_name}/"
            f"providers/Microsoft.ContainerService/managedClusters/{cluster_name}"
        )
        dataCollectionRuleName = f"MSCI-{workspace_name}"
        dcr_resource_id = (
            f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/"
            f"providers/Microsoft.Insights/dataCollectionRules/{dataCollectionRuleName}"
        )
        if create_dcr:
            # first get the association between region display names and region IDs (because for some reason
            # the "which RPs are available in which regions" check returns region display names)
            region_names_to_id = {}
            # retry the request up to two times
            for _ in range(3):
                try:
                    location_list_url = (
                        f"https://management.azure.com/subscriptions/{subscription_id}/"
                        "locations?api-version=2019-11-01"
                    )
                    r = send_raw_request(cmd.cli_ctx, "GET", location_list_url)

                    # this is required to fool the static analyzer. The else statement will only run if an exception
                    # is thrown, but flake8 will complain that e is undefined if we don't also define it here.
                    error = None
                    break
                except AzCLIError as e:
                    error = e
            else:
                # This will run if the above for loop was not broken out of. This means all three requests failed
                raise error
            json_response = json.loads(r.text)
            for region_data in json_response["value"]:
                region_names_to_id[region_data["displayName"]] = region_data[
                    "name"
                ]

            # check if region supports DCRs and DCR-A
            for _ in range(3):
                try:
                    feature_check_url = (
                        f"https://management.azure.com/subscriptions/{subscription_id}/"
                        "providers/Microsoft.Insights?api-version=2020-10-01"
                    )
                    r = send_raw_request(cmd.cli_ctx, "GET", feature_check_url)
                    error = None
                    break
                except AzCLIError as e:
                    error = e
            else:
                raise error
            json_response = json.loads(r.text)
            for resource in json_response["resourceTypes"]:
                region_ids = map(
                    lambda x: region_names_to_id[x], resource["locations"]
                )  # map is lazy, so doing this for every region isn't slow
                if (
                    resource["resourceType"].lower() == "datacollectionrules" and
                    location not in region_ids
                ):
                    raise ClientRequestError(
                        f"Data Collection Rules are not supported for LA workspace region {location}"
                    )
                if (
                    resource["resourceType"].lower() == "datacollectionruleassociations" and
                    cluster_region not in region_ids
                ):
                    raise ClientRequestError(
                        f"Data Collection Rule Associations are not supported for cluster region {location}"
                    )

            # create the DCR
            dcr_creation_body = json.dumps(
                {
                    "location": location,
                    "properties": {
                        "dataSources": {
                            "extensions": [
                                {
                                    "name": "ContainerInsightsExtension",
                                    "streams": [
                                        "Microsoft-Perf",
                                        "Microsoft-ContainerInventory",
                                        "Microsoft-ContainerLog",
                                        "Microsoft-ContainerLogV2",
                                        "Microsoft-ContainerNodeInventory",
                                        "Microsoft-KubeEvents",
                                        "Microsoft-KubeHealth",
                                        "Microsoft-KubeMonAgentEvents",
                                        "Microsoft-KubeNodeInventory",
                                        "Microsoft-KubePodInventory",
                                        "Microsoft-KubePVInventory",
                                        "Microsoft-KubeServices",
                                        "Microsoft-InsightsMetrics",
                                    ],
                                    "extensionName": "ContainerInsights",
                                }
                            ]
                        },
                        "dataFlows": [
                            {
                                "streams": [
                                    "Microsoft-Perf",
                                    "Microsoft-ContainerInventory",
                                    "Microsoft-ContainerLog",
                                    "Microsoft-ContainerLogV2",
                                    "Microsoft-ContainerNodeInventory",
                                    "Microsoft-KubeEvents",
                                    "Microsoft-KubeHealth",
                                    "Microsoft-KubeMonAgentEvents",
                                    "Microsoft-KubeNodeInventory",
                                    "Microsoft-KubePodInventory",
                                    "Microsoft-KubePVInventory",
                                    "Microsoft-KubeServices",
                                    "Microsoft-InsightsMetrics",
                                ],
                                "destinations": ["la-workspace"],
                            }
                        ],
                        "destinations": {
                            "logAnalytics": [
                                {
                                    "workspaceResourceId": workspace_resource_id,
                                    "name": "la-workspace",
                                }
                            ]
                        },
                    },
                }
            )
            dcr_url = f"https://management.azure.com/{dcr_resource_id}?api-version=2019-11-01-preview"
            for _ in range(3):
                try:
                    send_raw_request(
                        cmd.cli_ctx, "PUT", dcr_url, body=dcr_creation_body
                    )
                    error = None
                    break
                except AzCLIError as e:
                    error = e
            else:
                raise error

        if create_dcra:
            # only create or delete the association between the DCR and cluster
            association_body = json.dumps(
                {
                    "location": cluster_region,
                    "properties": {
                        "dataCollectionRuleId": dcr_resource_id,
                        "description": "routes monitoring data to a Log Analytics workspace",
                    },
                }
            )
            association_url = (
                f"https://management.azure.com/{cluster_resource_id}/providers/Microsoft.Insights/"
                f"dataCollectionRuleAssociations/send-to-{workspace_name}?api-version=2019-11-01-preview"
            )
            for _ in range(3):
                try:
                    send_raw_request(
                        cmd.cli_ctx,
                        "PUT" if not remove_monitoring else "DELETE",
                        association_url,
                        body=association_body,
                    )
                    error = None
                    break
                except AzCLIError as e:
                    error = e
            else:
                raise error

    else:
        # legacy auth with LA workspace solution
        unix_time_in_millis = int(
            (
                datetime.datetime.utcnow() -
                datetime.datetime.utcfromtimestamp(0)
            ).total_seconds() * 1000.0
        )

        solution_deployment_name = "ContainerInsights-{}".format(
            unix_time_in_millis
        )

        # pylint: disable=line-too-long
        template = {
            "$schema": "https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#",
            "contentVersion": "1.0.0.0",
            "parameters": {
                "workspaceResourceId": {
                    "type": "string",
                    "metadata": {
                        "description": "Azure Monitor Log Analytics Resource ID"
                    },
                },
                "workspaceRegion": {
                    "type": "string",
                    "metadata": {
                        "description": "Azure Monitor Log Analytics workspace region"
                    },
                },
                "solutionDeploymentName": {
                    "type": "string",
                    "metadata": {
                        "description": "Name of the solution deployment"
                    },
                },
            },
            "resources": [
                {
                    "type": "Microsoft.Resources/deployments",
                    "name": "[parameters('solutionDeploymentName')]",
                    "apiVersion": "2017-05-10",
                    "subscriptionId": "[split(parameters('workspaceResourceId'),'/')[2]]",
                    "resourceGroup": "[split(parameters('workspaceResourceId'),'/')[4]]",
                    "properties": {
                        "mode": "Incremental",
                        "template": {
                            "$schema": "https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#",
                            "contentVersion": "1.0.0.0",
                            "parameters": {},
                            "variables": {},
                            "resources": [
                                {
                                    "apiVersion": "2015-11-01-preview",
                                    "type": "Microsoft.OperationsManagement/solutions",
                                    "location": "[parameters('workspaceRegion')]",
                                    "name": "[Concat('ContainerInsights', '(', split(parameters('workspaceResourceId'),'/')[8], ')')]",
                                    "properties": {
                                        "workspaceResourceId": "[parameters('workspaceResourceId')]"
                                    },
                                    "plan": {
                                        "name": "[Concat('ContainerInsights', '(', split(parameters('workspaceResourceId'),'/')[8], ')')]",
                                        "product": "[Concat('OMSGallery/', 'ContainerInsights')]",
                                        "promotionCode": "",
                                        "publisher": "Microsoft",
                                    },
                                }
                            ],
                        },
                        "parameters": {},
                    },
                }
            ],
        }

        params = {
            "workspaceResourceId": {"value": workspace_resource_id},
            "workspaceRegion": {"value": location},
            "solutionDeploymentName": {"value": solution_deployment_name},
        }

        deployment_name = "aks-monitoring-{}".format(unix_time_in_millis)
        # publish the Container Insights solution to the Log Analytics workspace
        return _invoke_deployment(
            cmd,
            resource_group,
            deployment_name,
            template,
            params,
            validate=False,
            no_wait=False,
            subscription_id=subscription_id,
        )


def _invoke_deployment(
    cmd,
    resource_group_name,
    deployment_name,
    template,
    parameters,
    validate,
    no_wait,
    subscription_id=None,
):
    DeploymentProperties = cmd.get_models(
        "DeploymentProperties",
        resource_type=ResourceType.MGMT_RESOURCE_RESOURCES,
    )
    properties = DeploymentProperties(
        template=template, parameters=parameters, mode="incremental"
    )
    smc = get_mgmt_service_client(
        cmd.cli_ctx,
        ResourceType.MGMT_RESOURCE_RESOURCES,
        subscription_id=subscription_id,
    ).deployments
    if validate:
        logger.info("==== BEGIN TEMPLATE ====")
        logger.info(json.dumps(template, indent=2))
        logger.info("==== END TEMPLATE ====")

    Deployment = cmd.get_models(
        "Deployment", resource_type=ResourceType.MGMT_RESOURCE_RESOURCES
    )
    deployment = Deployment(properties=properties)

    if validate:
        if cmd.supported_api_version(
            min_api="2019-10-01",
            resource_type=ResourceType.MGMT_RESOURCE_RESOURCES,
        ):
            validation_poller = smc.begin_validate(
                resource_group_name, deployment_name, deployment
            )
            return LongRunningOperation(cmd.cli_ctx)(validation_poller)
        return smc.validate(resource_group_name, deployment_name, deployment)

    return sdk_no_wait(
        no_wait,
        smc.begin_create_or_update,
        resource_group_name,
        deployment_name,
        deployment,
    )


def add_monitoring_role_assignment(result, cluster_resource_id, cmd):
    service_principal_msi_id = None
    # Check if service principal exists, if it does, assign permissions to service principal
    # Else, provide permissions to MSI
    if (
        hasattr(result, "service_principal_profile") and
        hasattr(result.service_principal_profile, "client_id") and
        result.service_principal_profile.client_id.lower() != "msi"
    ):
        logger.info("valid service principal exists, using it")
        service_principal_msi_id = result.service_principal_profile.client_id
        is_service_principal = True
    elif (
        (hasattr(result, "addon_profiles")) and
        (CONST_MONITORING_ADDON_NAME in result.addon_profiles) and
        (
            hasattr(
                result.addon_profiles[CONST_MONITORING_ADDON_NAME], "identity"
            )
        ) and
        (
            hasattr(
                result.addon_profiles[CONST_MONITORING_ADDON_NAME].identity,
                "object_id",
            )
        )
    ):
        logger.info("omsagent MSI exists, using it")
        service_principal_msi_id = result.addon_profiles[
            CONST_MONITORING_ADDON_NAME
        ].identity.object_id
        is_service_principal = False

    if service_principal_msi_id is not None:
        if not add_role_assignment(
            cmd,
            "Monitoring Metrics Publisher",
            service_principal_msi_id,
            is_service_principal,
            scope=cluster_resource_id,
        ):
            logger.warning(
                "Could not create a role assignment for Monitoring addon. "
                "Are you an Owner on this subscription?"
            )
    else:
        logger.warning(
            "Could not find service principal or user assigned MSI for role"
            "assignment"
        )


def add_ingress_appgw_addon_role_assignment(result, cmd):
    service_principal_msi_id = None
    # Check if service principal exists, if it does, assign permissions to service principal
    # Else, provide permissions to MSI
    if (
        hasattr(result, "service_principal_profile") and
        hasattr(result.service_principal_profile, "client_id") and
        result.service_principal_profile.client_id != "msi"
    ):
        service_principal_msi_id = result.service_principal_profile.client_id
        is_service_principal = True
    elif (
        (hasattr(result, "addon_profiles")) and
        (CONST_INGRESS_APPGW_ADDON_NAME in result.addon_profiles) and
        (
            hasattr(
                result.addon_profiles[CONST_INGRESS_APPGW_ADDON_NAME],
                "identity",
            )
        ) and
        (
            hasattr(
                result.addon_profiles[CONST_INGRESS_APPGW_ADDON_NAME].identity,
                "object_id",
            )
        )
    ):
        service_principal_msi_id = result.addon_profiles[
            CONST_INGRESS_APPGW_ADDON_NAME
        ].identity.object_id
        is_service_principal = False

    if service_principal_msi_id is not None:
        config = result.addon_profiles[CONST_INGRESS_APPGW_ADDON_NAME].config
        if CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID in config:
            appgw_id = config[CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID]
            parsed_appgw_id = parse_resource_id(appgw_id)
            appgw_group_id = resource_id(
                subscription=parsed_appgw_id["subscription"],
                resource_group=parsed_appgw_id["resource_group"],
            )
            if not add_role_assignment(
                cmd,
                "Contributor",
                service_principal_msi_id,
                is_service_principal,
                scope=appgw_group_id,
            ):
                logger.warning(
                    "Could not create a role assignment for application gateway: %s "
                    "specified in %s addon. "
                    "Are you an Owner on this subscription?",
                    appgw_id,
                    CONST_INGRESS_APPGW_ADDON_NAME,
                )
        if CONST_INGRESS_APPGW_SUBNET_ID in config:
            subnet_id = config[CONST_INGRESS_APPGW_SUBNET_ID]
            if not add_role_assignment(
                cmd,
                "Network Contributor",
                service_principal_msi_id,
                is_service_principal,
                scope=subnet_id,
            ):
                logger.warning(
                    "Could not create a role assignment for subnet: %s "
                    "specified in %s addon. "
                    "Are you an Owner on this subscription?",
                    subnet_id,
                    CONST_INGRESS_APPGW_ADDON_NAME,
                )
        if CONST_INGRESS_APPGW_SUBNET_CIDR in config:
            if result.agent_pool_profiles[0].vnet_subnet_id is not None:
                parsed_subnet_vnet_id = parse_resource_id(
                    result.agent_pool_profiles[0].vnet_subnet_id
                )
                vnet_id = resource_id(
                    subscription=parsed_subnet_vnet_id["subscription"],
                    resource_group=parsed_subnet_vnet_id["resource_group"],
                    namespace="Microsoft.Network",
                    type="virtualNetworks",
                    name=parsed_subnet_vnet_id["name"],
                )
                if not add_role_assignment(
                    cmd,
                    "Contributor",
                    service_principal_msi_id,
                    is_service_principal,
                    scope=vnet_id,
                ):
                    logger.warning(
                        "Could not create a role assignment for virtual network: %s "
                        "specified in %s addon. "
                        "Are you an Owner on this subscription?",
                        vnet_id,
                        CONST_INGRESS_APPGW_ADDON_NAME,
                    )


def add_virtual_node_role_assignment(cmd, result, vnet_subnet_id):
    # Remove trailing "/subnets/<SUBNET_NAME>" to get the vnet id
    vnet_id = vnet_subnet_id.rpartition("/")[0]
    vnet_id = vnet_id.rpartition("/")[0]

    service_principal_msi_id = None
    is_service_principal = False
    os_type = "Linux"
    addon_name = CONST_VIRTUAL_NODE_ADDON_NAME + os_type
    # Check if service principal exists, if it does, assign permissions to service principal
    # Else, provide permissions to MSI
    if (
        hasattr(result, "service_principal_profile") and
        hasattr(result.service_principal_profile, "client_id") and
        result.service_principal_profile.client_id.lower() != "msi"
    ):
        logger.info("valid service principal exists, using it")
        service_principal_msi_id = result.service_principal_profile.client_id
        is_service_principal = True
    elif (
        (hasattr(result, "addon_profiles")) and
        (addon_name in result.addon_profiles) and
        (hasattr(result.addon_profiles[addon_name], "identity")) and
        (hasattr(result.addon_profiles[addon_name].identity, "object_id"))
    ):
        logger.info("virtual node MSI exists, using it")
        service_principal_msi_id = result.addon_profiles[
            addon_name
        ].identity.object_id
        is_service_principal = False

    if service_principal_msi_id is not None:
        if not add_role_assignment(
            cmd,
            "Contributor",
            service_principal_msi_id,
            is_service_principal,
            scope=vnet_id,
        ):
            logger.warning(
                "Could not create a role assignment for virtual node addon. "
                "Are you an Owner on this subscription?"
            )
    else:
        logger.warning(
            "Could not find service principal or user assigned MSI for role"
            "assignment"
        )
