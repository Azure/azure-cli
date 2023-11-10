# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.acs.azuremonitormetrics.constants import (
    DC_TYPE
)


# DCR = 64, DCE = 44, DCRA = 64
# All DC* object names should end only in alpha numeric (after `length` trim)
# DCE remove underscore from cluster name
def sanitize_name(name, objtype, length):
    name = name[0:length]
    if objtype == DC_TYPE.DCE:
        name = ''.join(char for char in name if char.isalnum() or char == '-')
    lastIndexAlphaNumeric = len(name) - 1
    while ((name[lastIndexAlphaNumeric].isalnum() is False) and lastIndexAlphaNumeric > -1):
        lastIndexAlphaNumeric = lastIndexAlphaNumeric - 1
    if lastIndexAlphaNumeric < 0:
        return ""
    return name[0:lastIndexAlphaNumeric + 1]


def get_default_dcr_name(mac_region, cluster_name):
    default_dcr_name = "MSProm-" + mac_region + "-" + cluster_name
    return sanitize_name(default_dcr_name, DC_TYPE.DCR, 64)


def get_default_dce_name(mac_region, cluster_name):
    default_dce_name = "MSProm-" + mac_region + "-" + cluster_name
    return sanitize_name(default_dce_name, DC_TYPE.DCE, 44)


def get_default_dcra_name():
    return "ContainerInsightsMetricsExtension"
