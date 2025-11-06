# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

from jmespath import Options
from jmespath import compile as compile_jmes
from jmespath import functions


def aks_agentpool_show_table_format(result):
    """Format an agent pool as summary results for display with "-o table"."""
    return [_aks_agentpool_table_format(result)]


def _aks_agentpool_table_format(result):
    parsed = compile_jmes("""{
        name: name,
        osType: osType,
        kubernetesVersion: orchestratorVersion,
        vmSize: vmSize,
        osDiskSizeGB: osDiskSizeGB,
        count: count,
        maxPods: maxPods,
        provisioningState: provisioningState,
        mode: mode
    }""")
    # use ordered dicts so headers are predictable
    return parsed.search(result, Options(dict_cls=OrderedDict))


def aks_agentpool_list_table_format(results):
    """Format an agent pool list for display with "-o table"."""
    return [_aks_agentpool_table_format(r) for r in results]


def aks_list_table_format(results):
    """"Format a list of managed clusters as summary results for display with "-o table"."""
    return [_aks_table_format(r) for r in results]


def aks_machine_list_table_format(results):
    return [aks_machine_show_table_format(r) for r in results]


def aks_machine_show_table_format(result: dict):
    def parser(entry: dict):
        ip_addresses = ""
        zones = ""
        if "zones" in entry and entry["zones"]:
            zones_data = entry["zones"]
            if isinstance(zones_data, list):
                zones = ', '.join(part.strip() for part in zones_data if part and part.strip())
            elif isinstance(zones_data, str):
                zones = zones_data.strip()
        # If no zones at top-level, check in properties
        elif "properties" in entry and "zones" in entry["properties"] and entry["properties"]["zones"]:
            zones_data = entry["properties"]["zones"]
            if isinstance(zones_data, list):
                zones = ', '.join(part.strip() for part in zones_data if part and part.strip())
            elif isinstance(zones_data, str):
                zones = zones_data.strip()
        if "properties" in entry and isinstance(entry["properties"], dict):
            if "network" in entry["properties"] and isinstance(entry["properties"]["network"], dict):
                if ("ipAddresses" in entry["properties"]["network"] and
                        isinstance(entry["properties"]["network"]["ipAddresses"], list)):
                    for k in entry["properties"]["network"]["ipAddresses"]:
                        if isinstance(k, dict) and "ip" in k and "family" in k:
                            ip_addresses += f"ip:{k['ip']},family:{k['family']};"
        entry["ip"] = ip_addresses
        entry["zones"] = zones
        parsed = compile_jmes("""{
                name: name,
                ip: ip,
                zones: zones
            }""")
        return parsed.search(entry, Options(dict_cls=OrderedDict))
    return parser(result)


def aks_run_command_result_format(cmdResult):
    result = OrderedDict()
    if cmdResult['provisioningState'] == "Succeeded":
        result['exit code'] = cmdResult['exitCode']
        result['logs'] = cmdResult['logs']
        return result
    if cmdResult['provisioningState'] == "Failed":
        result['provisioning state'] = cmdResult['provisioningState']
        result['reason'] = cmdResult['reason']
        return result
    result['provisioning state'] = cmdResult['provisioningState']
    result['started At'] = cmdResult['startedAt']
    return result


def aks_show_table_format(result):
    """Format a managed cluster as summary results for display with "-o table"."""
    return [_aks_table_format(result)]


def aks_namespace_list_table_format(results):
    """Format an managed namespace list for display with "-o table"."""
    return [_aks_namespace_list_table_format(r) for r in results]


def _aks_namespace_list_table_format(result):
    if not result.get("properties"):
        parsed = compile_jmes("""{
            name: name,
            resourceGroup: resourceGroup,
            location: location
        }""")
    else:
        parsed = compile_jmes("""{
            name: name,
            tags: to_string(tags),
            provisioningState: to_string(properties.provisioningState),
            labels: to_string(properties.labels),
            annotations: to_string(properties.annotations),
            cpuRequest: to_string(properties.defaultResourceQuota.cpuRequest),
            cpuLimit: to_string(properties.defaultResourceQuota.cpuLimit),
            memoryRequest: to_string(properties.defaultResourceQuota.memoryRequest),
            memoryLimit: to_string(properties.defaultResourceQuota.memoryLimit),
            ingress: to_string(properties.defaultNetworkPolicy.ingress),
            egress: to_string(properties.defaultNetworkPolicy.egress),
            adoptionPolicy: to_string(properties.adoptionPolicy),
            deletePolicy: to_string(properties.deletePolicy)
        }""")
    # use ordered dicts so headers are predictable
    return parsed.search(result, Options(dict_cls=OrderedDict))


def _aks_table_format(result):
    parsed = compile_jmes("""{
        name: name,
        location: location,
        resourceGroup: resourceGroup,
        kubernetesVersion: kubernetesVersion,
        currentKubernetesVersion: currentKubernetesVersion,
        provisioningState: provisioningState,
        fqdn: fqdn || privateFqdn
    }""")
    # use ordered dicts so headers are predictable
    return parsed.search(result, Options(dict_cls=OrderedDict))


def aks_upgrades_table_format(result):
    """Format get-upgrades results as a summary for display with "-o table"."""

    preview = {}

    def find_preview_versions(versions_bag):
        for upgrade in versions_bag.get('upgrades', []):
            if upgrade.get('isPreview', False):
                preview[upgrade['kubernetesVersion']] = True
    find_preview_versions(result.get('controlPlaneProfile', {}))

    # This expression assumes there is one node pool, and that the master and nodes upgrade in lockstep.
    parsed = compile_jmes("""{
        name: name,
        resourceGroup: resourceGroup,
        masterVersion: controlPlaneProfile.kubernetesVersion || `unknown`,
        upgrades: controlPlaneProfile.upgrades[].kubernetesVersion || [`None available`] | sort_versions(@) | set_preview_array(@) | join(`, `, @)
    }""")
    # use ordered dicts so headers are predictable
    return parsed.search(result, Options(dict_cls=OrderedDict, custom_functions=_custom_functions(preview)))


def aks_versions_table_format(result):
    """Format get-versions results as a summary for display with "-o table"."""

    version_table = flatten_version_table(result.get("values", []))

    parsed = compile_jmes("""[].{
        kubernetesVersion: version,
        isPreview: isPreview,
        upgrades: upgrades || [`None available`] | sort_versions(@) | join(`, `, @),
        supportPlan: supportPlan | join(`, `, @)
    }""")

    # use ordered dicts so headers are predictable
    results = parsed.search(version_table, Options(
        dict_cls=OrderedDict, custom_functions=_custom_functions({})))
    return sorted(results, key=lambda x: version_to_tuple(x.get("kubernetesVersion")), reverse=True)


def aks_list_nodepool_snapshot_table_format(results):
    """"Format a list of nodepool snapshots as summary results for display with "-o table"."""
    return [_aks_nodepool_snapshot_table_format(r) for r in results]


def aks_show_nodepool_snapshot_table_format(result):
    """Format a nodepool snapshot as summary results for display with "-o table"."""
    return [_aks_nodepool_snapshot_table_format(result)]


def _aks_nodepool_snapshot_table_format(result):
    parsed = compile_jmes("""{
        name: name,
        location: location,
        resourceGroup: resourceGroup,
        nodeImageVersion: nodeImageVersion,
        kubernetesVersion: kubernetesVersion,
        osType: osType,
        enableFIPS: enableFIPS
    }""")
    # use ordered dicts so headers are predictable
    return parsed.search(result, Options(dict_cls=OrderedDict))


def version_to_tuple(version):
    """Removes preview suffix"""
    if version.endswith('(preview)'):
        version = version[:-len('(preview)')]
    return tuple(map(int, (version.split('.'))))


def flatten_version_table(release_info):
    """Flattens version table"""
    flattened = []
    for release in release_info:
        isPreview = release.get("isPreview", False)
        supportPlan = release.get("capabilities", {}).get("supportPlan", {})
        for k, v in release.get("patchVersions", {}).items():
            item = {"version": k, "upgrades": v.get("upgrades", []), "isPreview": isPreview, "supportPlan": supportPlan}
            flattened.append(item)
    return flattened


def _custom_functions(preview_versions):
    class CustomFunctions(functions.Functions):  # pylint: disable=too-few-public-methods

        @functions.signature({'types': ['array']})
        def _func_sort_versions(self, versions):  # pylint: disable=no-self-use
            """Custom JMESPath `sort_versions` function that sorts an array of strings as software versions."""
            try:
                return sorted(versions, key=version_to_tuple)
            # if it wasn't sortable, return the input so the pipeline continues
            except (TypeError, ValueError):
                return versions

        @functions.signature({'types': ['array']})
        def _func_set_preview_array(self, versions):
            """Custom JMESPath `set_preview_array` function that suffixes preview version"""
            try:
                for i, _ in enumerate(versions):
                    versions[i] = self._func_set_preview(versions[i])
                return versions
            except (TypeError, ValueError):
                return versions

        @functions.signature({'types': ['string']})
        def _func_set_preview(self, version):  # pylint: disable=no-self-use
            """Custom JMESPath `set_preview` function that suffixes preview version"""
            try:
                if preview_versions.get(version, False):
                    return version + '(preview)'
                return version
            except (TypeError, ValueError):
                return version

    return CustomFunctions()


def aks_mesh_revisions_table_format(result):
    """Format a list of mesh revisions as summary results for display with "-o table". """
    revision_table = flatten_mesh_revision_table(result['meshRevisions'])
    parsed = compile_jmes("""[].{
        revision: revision,
        upgrades: upgrades || [`None available`] | sort_versions(@) | join(`, `, @),
        compatibleWith: compatibleWith_name,
        compatibleVersions: compatibleVersions || [`None available`] | sort_versions(@) | join(`, `, @)
    }""")
    # Use ordered dicts so headers are predictable
    results = parsed.search(revision_table, Options(
        dict_cls=OrderedDict, custom_functions=_custom_functions({})))

    return results


# Helper function used by aks_mesh_revisions_table_format
def flatten_mesh_revision_table(revision_info):
    """Flattens revision information"""
    flattened = []
    for revision_data in revision_info:
        flattened.extend(_format_mesh_revision_entry(revision_data))
    return flattened


def aks_mesh_upgrades_table_format(result):
    """Format a list of mesh upgrades as summary results for display with "-o table". """
    upgrades_table = _format_mesh_revision_entry(result)
    parsed = compile_jmes("""[].{
        revision: revision,
        upgrades: upgrades || [`None available`] | sort_versions(@) | join(`, `, @),
        compatibleWith: compatibleWith_name,
        compatibleVersions: compatibleVersions || [`None available`] | sort_versions(@) | join(`, `, @)
    }""")
    # Use ordered dicts so headers are predictable
    results = parsed.search(upgrades_table, Options(
        dict_cls=OrderedDict, custom_functions=_custom_functions({})))
    return results


def _format_mesh_revision_entry(revision):
    flattened = []
    revision_entry = revision['revision']
    upgrades = revision['upgrades']
    compatible_with_list = revision['compatibleWith']
    for compatible_with in compatible_with_list:
        item = {
            'revision': revision_entry,
            'upgrades': upgrades,
            'compatibleWith_name': compatible_with['name'],
            'compatibleVersions': compatible_with['versions']
        }
        flattened.append(item)
    return flattened
