# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from enum import Enum

AKS_CLUSTER_API = "2023-01-01"
MAC_API = "2023-04-03"
DC_API = "2022-06-01"
GRAFANA_API = "2022-08-01"
GRAFANA_ROLE_ASSIGNMENT_API = "2022-04-01"
RULES_API = "2023-03-01"
FEATURE_API = "2020-09-01"
RP_API = "2021-04-01"
ALERTS_API = "2023-01-01-preview"
RP_LOCATION_API = "2022-01-01"


MapToClosestMACRegion = {
    "australiacentral": "australiacentral",
    "australiacentral2": "australiacentral",
    "australiaeast": "australiasoutheast",
    "australiasoutheast": "australiasoutheast",
    "brazilsouth": "brazilsouth",
    "canadacentral": "canadacentral",
    "canadaeast": "canadacentral",
    "centralus": "centralus",
    "centralindia": "centralindia",
    "eastasia": "eastasia",
    "eastus": "eastus",
    "eastus2": "eastus2",
    "francecentral": "francesouth",
    "francesouth": "francesouth",
    "japaneast": "japanwest",
    "japanwest": "japanwest",
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
    "ukwest": "westeurope",
    "westcentralus": "westcentralus",
    "westeurope": "westeurope",
    "westindia": "centralindia",
    "westus": "westus",
    "westus2": "westus2",
    "westus3": "westus",
    "norwayeast": "norwayeast",
    "norwaywest": "norwayeast",
    "switzerlandnorth": "switzerlandnorth",
    "switzerlandwest": "switzerlandnorth",
    "uaenorth": "uaenorth",
    "germanywestcentral": "germanywestcentral",
    "germanynorth": "germanywestcentral",
    "uaecentral": "westeurope",
    "eastus2euap": "eastus2euap",
    "centraluseuap": "eastus2euap",
    "brazilsoutheast": "eastus",
    "jioindiacentral": "centralindia",
    "swedencentral": "westeurope",
    "swedensouth": "westeurope",
    "qatarcentral": "westeurope",
    "israelcentral": "israelcentral",
    "italynorth": "italynorth"
}


class GrafanaLink(Enum):
    """
    Status of Grafana link to the Prometheus Addon
    """
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ALREADYPRESENT = "ALREADYPRESENT"
    NOPARAMPROVIDED = "NOPARAMPROVIDED"


class DC_TYPE(Enum):
    """
    Types of DC* objects
    """
    DCE = "DCE"
    DCR = "DCR"
    DCRA = "DCRA"
