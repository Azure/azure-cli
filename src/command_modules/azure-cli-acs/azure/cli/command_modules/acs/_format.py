# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict
from distutils.version import StrictVersion

from jmespath import compile as compile_jmes, functions, Options


class CustomFunctions(functions.Functions):

    @functions.signature({'types': ['array']})
    def _func_sort_versions(self, s):
        """Custom JMESPath `sort_versions` function that sorts an array of strings as software versions."""
        return sorted(s, key=StrictVersion)


def aks_list_table_format(results):
    """"Format a list of managed clusters as summary results for display with "-o table"."""
    return [_aks_table_format(r) for r in results]


def aks_show_table_format(result):
    """Format a managed cluster as summary results for display with "-o table"."""
    return [_aks_table_format(result)]


def _aks_table_format(result):
    parsed = compile_jmes("""{
        name: name,
        location: location,
        resourceGroup: resourceGroup,
        kubernetesVersion: kubernetesVersion,
        provisioningState: provisioningState,
        fqdn: fqdn
    }""")
    # use ordered dicts so headers are predictable
    return parsed.search(result, Options(dict_cls=OrderedDict))


def aks_upgrades_table_format(result):
    """Format get-upgrades results as a summary for display with "-o table"."""
    # This expression assumes there is one node pool, and that the master and nodes upgrade in lockstep.
    parsed = compile_jmes("""{
        name: name,
        resourceGroup: resourceGroup,
        masterVersion: controlPlaneProfile.kubernetesVersion || `unknown`,
        nodePoolVersion: agentPoolProfiles[0].kubernetesVersion || `unknown`,
        upgrades: agentPoolProfiles[0].upgrades | sort_versions(@) | join(`, `, @) || `None available`
    }""")
    # use ordered dicts so headers are predictable
    return parsed.search(result, Options(dict_cls=OrderedDict, custom_functions=CustomFunctions()))


def aks_versions_table_format(result):
    """Format get-versions results as a summary for display with "-o table"."""
    parsed = compile_jmes("""orchestrators[].{
        kubernetesVersion: orchestratorVersion,
        upgradesAvailable: upgrades[].orchestratorVersion | sort_versions(@) | join(`, `, @) || `None available`
    }""")
    # use ordered dicts so headers are predictable
    results = parsed.search(result, Options(dict_cls=OrderedDict, custom_functions=CustomFunctions()))
    return sorted(results, key=lambda x: StrictVersion(x.get('kubernetesVersion')), reverse=True)
