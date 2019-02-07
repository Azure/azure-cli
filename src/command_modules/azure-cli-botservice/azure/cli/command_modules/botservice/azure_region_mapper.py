# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

logger = get_logger(__name__)


class AzureRegionMapper:  # pylint:disable=too-few-public-methods

    @staticmethod
    def get_app_insights_location(key):
        region_map = {
            'australiaeast': 'southeastasia',
            'australiacentral': 'southeastasia',
            'australiacentral2': 'southeastasia',
            'australiasoutheast': 'southeastasia',
            'eastasia': 'southeastasia',
            'southeastasia': 'southeastasia',
            'eastus': 'eastus',
            'eastus2': 'eastus',
            'southcentralus': 'southcentralus',
            'westcentralus': 'westus2',
            'westus': 'westus2',
            'westus2': 'westus2',
            'brazilsouth': 'southcentralus',
            'centralus': 'southcentralus',
            'northcentralus': 'southcentralus',
            'japanwest': 'southeastasia',
            'japaneast': 'southeastasia',
            'southindia': 'southeastasia',
            'centralindia': 'southeastasia',
            'westindia': 'southeastasia',
            'canadacentral': 'southcentralus',
            'canadaeast': 'eastus',
            'koreacentral': 'southeastasia',
            'koreasouth': 'southeastasia',
            'northeurope': 'northeurope',
            'westeurope': 'westeurope',
            'uksouth': 'westeurope',
            'ukwest': 'westeurope',
            'francecentral': 'westeurope',
            'francesouth': 'westeurope'
        }
        region = region_map.get(key)

        if not region:
            logger.warning('Warning: provided region ("%s") for Application Insights does not exist. Defaulting to '
                           '"southcentralus"', key)
            region = 'southcentralus'

        return region
