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
    # put results in an ordered dict so the headers are predictable
    table_row = OrderedDict()
    for k in ['name', 'location', 'resourceGroup', 'kubernetesVersion', 'provisioningState', 'fqdn']:
        table_row[k] = result.get(k)
    return table_row


def aks_get_versions_table_format(result):
    """Format get-versions upgrade results as a summary for display with "-o table"."""
    master = result.get('controlPlaneProfile', {})
    result['masterVersion'] = master.get('kubernetesVersion', 'unknown')
    master_upgrades = master.get('upgrades', [])
    result['masterUpgrades'] = ', '.join(master_upgrades) if master_upgrades else 'None available'

    agents = result.get('agentPoolProfiles', [])
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

    # put results in an ordered dict so the headers are predictable
    table_row = OrderedDict()
    for k in ['name', 'resourceGroup', 'masterVersion', 'masterUpgrades', 'nodePoolVersion', 'nodePoolUpgrades']:
        table_row[k] = result.get(k)
    return [table_row]
