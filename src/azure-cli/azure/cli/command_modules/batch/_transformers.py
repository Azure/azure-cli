# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections.abc import Mapping
from azure.core.paging import ItemPaged


class Transformer:

    def __init__(self, transform_mapping):
        self.transform_mapping = transform_mapping

    def transform_result(self, result):
        if result is not None:
            result = list(result) if isinstance(result, ItemPaged) else result
            if isinstance(result, list):
                return self.transform_object_list(result)
            return self.transform_object(result)

    def transform_object(self, result):
        new_dict = {}
        for key, value in result.items():
            new_key = self.transform_mapping[key] if key in self.transform_mapping else key
            if new_key is None:
                continue
            if isinstance(value, Mapping):
                new_dict[new_key] = self.transform_result(value)
            else:
                new_dict[new_key] = value
        return new_dict

    def transform_object_list(self, result):
        new_result = []
        for item in result:
            updated_obj = self.transform_result(item)
            new_result.append(updated_obj)
        return new_result


transform_map = {
    # cmd: az batch pool list
    # cmd: az batch pool show
    'diskSizeGB': 'diskSizeGb',
    'ephemeralOSDiskSettings': 'ephemeralOsDiskSettings',
    'nodeAgentSKUId': 'nodeAgentSkuId',
    # cmd: az batch pool list
    'automaticOSUpgradePolicy': 'automaticOsUpgradePolicy',
    'dynamicVNetAssignmentScope': 'dynamicVnetAssignmentScope',
    'enableAutomaticOSUpgrade': 'enableAutomaticOsUpgrade',
    'publicIPAddressConfiguration': 'publicIpAddressConfiguration',
    # cmd: az batch node remote-login-settings show
    'remoteLoginIPAddress': 'remoteLoginIpAddress',
    # cmd:
    'inboundNATPools': 'inboundNatPools',
    'publicFQDN': 'publicFqdn',
    'publicIPAddress': 'publicIpAddress',
    'upgradingOS': 'upgradingOs',
    # cmd: az batch pool usage-metrics list (API was retired on 09/30/2024 so these should be removed soon)
    'avgCPUPercentage': 'avgCpuPercentage',
    'diskReadIOps': 'diskReadIops',
    'diskWriteIOps': 'diskWriteIops',
    'kernelCPUTime': 'kernelCpuTime',
    'readIOGiB': 'readIoGiB',
    'readIOps': 'readIops',
    'userCPUTime': 'userCpuTime',
    'writeIOGiB': 'writeIoGiB',
    'writeIOps': 'writeIops',
    # Deprecated properties
    'targetNodeCommunicationMode': None,
    'currentNodeCommunicationMode': None,
    'resourceTags': None
}

batch_transformer = Transformer(transform_map)
