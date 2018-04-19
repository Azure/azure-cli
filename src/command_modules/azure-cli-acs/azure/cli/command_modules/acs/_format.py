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
    from jmespath import compile as compile_jmes, Options

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
    from jmespath import compile as compile_jmes, Options

    # This expression assumes there is one node pool, and that the master and nodes upgrade in lockstep.
    parsed = compile_jmes("""{
        name: name,
        resourceGroup: resourceGroup,
        masterVersion: controlPlaneProfile.kubernetesVersion || `unknown`,
        nodePoolVersion: agentPoolProfiles[0].kubernetesVersion || `unknown`,
        upgrades: controlPlaneProfile.upgrades || [`None available`] | sort_versions(@) | join(`, `, @)
    }""")
    # use ordered dicts so headers are predictable
    return parsed.search(result, Options(dict_cls=OrderedDict, custom_functions=_custom_functions()))


def aks_versions_table_format(result):
    """Format get-versions results as a summary for display with "-o table"."""
    from jmespath import compile as compile_jmes, Options

    parsed = compile_jmes("""orchestrators[].{
        kubernetesVersion: orchestratorVersion,
        upgrades: upgrades[].orchestratorVersion || [`None available`] | sort_versions(@) | join(`, `, @)
    }""")
    # use ordered dicts so headers are predictable
    results = parsed.search(result, Options(dict_cls=OrderedDict, custom_functions=_custom_functions()))
    return sorted(results, key=lambda x: version_to_tuple(x.get('kubernetesVersion')), reverse=True)


def version_to_tuple(v):
    """Quick-and-dirty sort function to handle simple semantic versions like 1.7.12 or 1.8.7."""
    return tuple(map(int, (v.split('.'))))


def _custom_functions():

    from jmespath import functions

    class CustomFunctions(functions.Functions):  # pylint: disable=too-few-public-methods

        @functions.signature({'types': ['array']})
        def _func_sort_versions(self, s):  # pylint: disable=no-self-use
            """Custom JMESPath `sort_versions` function that sorts an array of strings as software versions."""
            try:
                return sorted(s, key=version_to_tuple)
            except (TypeError, ValueError):  # if it wasn't sortable, return the input so the pipeline continues
                return s

    return CustomFunctions()
