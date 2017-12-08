# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict


def aks_list_table_format(results):
    """"Format a list of managed clusters as summary results for display with "-o table"."""
    return [_aks_table_format(r) for r in results]


def aks_show_table_format(result):
    """Format a managed cluster as summary results for display with "-o table"."""
    return [_aks_table_format(result)]


def _aks_table_format(result):
    # move some nested properties up to top-level values
    properties = result.get('properties', {})
    promoted = ['kubernetesVersion', 'provisioningState', 'fqdn']
    result.update({k: properties.get(k) for k in promoted})

    columns = ['name', 'location', 'resourceGroup'] + promoted
    # put results in an ordered dict so the headers are predictable
    table_row = OrderedDict()
    for k in columns:
        table_row[k] = result.get(k)
    return table_row


def aks_get_versions_table_format(result):
    """Format get-versions upgrade results as a summary for display with "-o table"."""
    properties = result.get('properties', {})
    master = properties.get('controlPlaneProfile', {})
    result['masterVersion'] = master.get('kubernetesVersion', 'unknown')
    master_upgrades = master.get('upgrades', [])
    result['masterUpgrades'] = ', '.join(master_upgrades) if master_upgrades else 'None available'

    agents = properties.get('agentPoolProfiles', [])
    versions, upgrades = [], []
    for agent in agents:
        version = agent.get('kubernetesVersion', 'unknown')
        agent_upgrades = agent.get('upgrades', [])
        upgrade = ', '.join(agent_upgrades) if agent_upgrades else 'None available'
        name = agent.get('name')
        if name:  # multiple agent pools, presumably
            version = "{}: {}".format(name, version)
            upgrade = "{}: {}".format(name, upgrades)
        versions.append(version)
        upgrades.append(upgrade)

    result['nodePoolVersion'] = ', '.join(versions)
    result['nodePoolUpgrades'] = ', '.join(upgrades)

    columns = ['name', 'resourceGroup', 'masterVersion', 'masterUpgrades', 'nodePoolVersion', 'nodePoolUpgrades']
    # put results in an ordered dict so the headers are predictable
    table_row = OrderedDict()
    for k in columns:
        table_row[k] = result.get(k)
    return [table_row]
