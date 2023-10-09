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
    "australiacentral": "eastus",
    "australiacentral2": "eastus",
    "australiaeast": "eastus",
    "australiasoutheast": "eastus",
    "brazilsouth": "eastus",
    "canadacentral": "eastus",
    "canadaeast": "eastus",
    "centralus": "centralus",
    "centralindia": "centralindia",
    "eastasia": "westeurope",
    "eastus": "eastus",
    "eastus2": "eastus2",
    "francecentral": "westeurope",
    "francesouth": "westeurope",
    "japaneast": "eastus",
    "japanwest": "eastus",
    "koreacentral": "westeurope",
    "koreasouth": "westeurope",
    "northcentralus": "eastus",
    "northeurope": "westeurope",
    "southafricanorth": "westeurope",
    "southafricawest": "westeurope",
    "southcentralus": "eastus",
    "southeastasia": "westeurope",
    "southindia": "centralindia",
    "uksouth": "westeurope",
    "ukwest": "westeurope",
    "westcentralus": "eastus",
    "westeurope": "westeurope",
    "westindia": "centralindia",
    "westus": "westus",
    "westus2": "westus2",
    "westus3": "westus",
    "norwayeast": "westeurope",
    "norwaywest": "westeurope",
    "switzerlandnorth": "westeurope",
    "switzerlandwest": "westeurope",
    "uaenorth": "westeurope",
    "germanywestcentral": "westeurope",
    "germanynorth": "westeurope",
    "uaecentral": "westeurope",
    "eastus2euap": "eastus2euap",
    "centraluseuap": "eastus2euap",
    "brazilsoutheast": "eastus",
    "jioindiacentral": "centralindia",
    "swedencentral": "westeurope",
    "swedensouth": "westeurope",
    "qatarcentral": "westeurope"
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
