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
