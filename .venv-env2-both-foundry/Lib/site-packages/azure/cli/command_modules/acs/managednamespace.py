# pylint: disable=too-many-lines
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.acs._client_factory import (
    get_container_service_client,
)
from azure.cli.command_modules.acs._consts import (
    CONST_NAMESPACE_ADOPTION_POLICY_ALWAYS,
    CONST_NAMESPACE_ADOPTION_POLICY_IFIDENTICAL,
    CONST_NAMESPACE_ADOPTION_POLICY_NEVER,
    CONST_NAMESPACE_DELETE_POLICY_DELETE,
    CONST_NAMESPACE_DELETE_POLICY_KEEP,
    CONST_NAMESPACE_NETWORK_POLICY_RULE_ALLOWALL,
    CONST_NAMESPACE_NETWORK_POLICY_RULE_ALLOWSAMENAMESPACE,
    CONST_NAMESPACE_NETWORK_POLICY_RULE_DENYALL,
)
from azure.cli.core.azclierror import (
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
)
from azure.cli.core.util import sdk_no_wait
from azure.cli.core.profiles import ResourceType


def get_cluster_location(cmd, resource_group_name, cluster_name):
    containerservice_client = get_container_service_client(cmd.cli_ctx)
    cluster = containerservice_client.managed_clusters.get(resource_group_name, cluster_name)
    return cluster.location


def aks_managed_namespace_add(cmd, client, raw_parameters, headers, no_wait):
    resource_group_name = raw_parameters.get("resource_group_name")
    cluster_name = raw_parameters.get("cluster_name")
    namespace_name = raw_parameters.get("name")

    namespace_config = constructNamespace(cmd, raw_parameters, namespace_name)
    namespace_config.location = get_cluster_location(cmd, resource_group_name, cluster_name)

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        namespace_name,
        namespace_config,
        headers=headers,
    )


def constructNamespace(cmd, raw_parameters, namespace_name):
    tags = raw_parameters.get("tags", {})
    labels_raw = raw_parameters.get("labels")
    labels = parse_key_value_list(labels_raw)
    annotations_raw = raw_parameters.get("annotations")
    annotations = parse_key_value_list(annotations_raw)

    NamespaceProperties = cmd.get_models(
        "NamespaceProperties",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_namespaces"
    )

    namespace_properties = NamespaceProperties(
        labels=labels,
        annotations=annotations,
        default_resource_quota=setResourceQuota(cmd, raw_parameters),
        default_network_policy=setNetworkPolicyRule(cmd, raw_parameters),
        adoption_policy=setAdoptionPolicy(raw_parameters),
        delete_policy=setDeletePolicy(raw_parameters)
    )

    Namespace = cmd.get_models(
        "ManagedNamespace",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_namespaces"
    )

    namespace_config = Namespace()
    namespace_config.name = namespace_name
    namespace_config.tags = tags
    namespace_config.properties = namespace_properties
    return namespace_config


def setResourceQuota(cmd, raw_parameters):
    cpu_request = raw_parameters.get("cpu_request")
    cpu_limit = raw_parameters.get("cpu_limit")
    memory_request = raw_parameters.get("memory_request")
    memory_limit = raw_parameters.get("memory_limit")

    if any(param is None for param in [cpu_request, cpu_limit, memory_request, memory_limit]):
        raise RequiredArgumentMissingError(
            "Please specify --cpu-request, --cpu-limit, --memory-request, and --memory-limit."
        )

    ResourceQuota = cmd.get_models(
        "ResourceQuota",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_namespaces"
    )

    rq = ResourceQuota(
        cpu_request=cpu_request,
        cpu_limit=cpu_limit,
        memory_request=memory_request,
        memory_limit=memory_limit
    )

    return rq


def setNetworkPolicyRule(cmd, raw_parameters):
    ingress_policy = raw_parameters.get("ingress_policy") or CONST_NAMESPACE_NETWORK_POLICY_RULE_ALLOWSAMENAMESPACE
    egress_policy = raw_parameters.get("egress_policy") or CONST_NAMESPACE_NETWORK_POLICY_RULE_ALLOWALL

    valid_network_policy_rules = {
        CONST_NAMESPACE_NETWORK_POLICY_RULE_DENYALL,
        CONST_NAMESPACE_NETWORK_POLICY_RULE_ALLOWSAMENAMESPACE,
        CONST_NAMESPACE_NETWORK_POLICY_RULE_ALLOWALL
    }

    if ingress_policy not in valid_network_policy_rules:
        raise InvalidArgumentValueError(
            f"Invalid ingress_policy '{ingress_policy}'. Must be one of: "
            f"{', '.join(valid_network_policy_rules)}"
        )

    if egress_policy not in valid_network_policy_rules:
        raise InvalidArgumentValueError(
            f"Invalid egress_policy '{egress_policy}'. Must be one of: "
            f"{', '.join(valid_network_policy_rules)}"
        )

    NetworkPolicies = cmd.get_models(
        "NetworkPolicies",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_namespaces"
    )

    np = NetworkPolicies(
        ingress=ingress_policy,
        egress=egress_policy
    )

    return np


def setAdoptionPolicy(raw_parameters):
    adoption_policy = raw_parameters.get("adoption_policy") or CONST_NAMESPACE_ADOPTION_POLICY_NEVER

    valid_adoption_policy = {
        CONST_NAMESPACE_ADOPTION_POLICY_NEVER,
        CONST_NAMESPACE_ADOPTION_POLICY_IFIDENTICAL,
        CONST_NAMESPACE_ADOPTION_POLICY_ALWAYS
    }

    if adoption_policy not in valid_adoption_policy:
        raise InvalidArgumentValueError(
            f"Invalid adoption policy '{adoption_policy}'. Must be one of: "
            f"{', '.join(valid_adoption_policy)}"
        )

    return adoption_policy


def setDeletePolicy(raw_parameters):
    delete_policy = raw_parameters.get("delete_policy") or CONST_NAMESPACE_DELETE_POLICY_KEEP

    valid_delete_policy = {
        CONST_NAMESPACE_DELETE_POLICY_KEEP,
        CONST_NAMESPACE_DELETE_POLICY_DELETE
    }

    if delete_policy not in valid_delete_policy:
        raise InvalidArgumentValueError(
            f"Invalid delete policy '{delete_policy}'. Must be one of: "
            f"{', '.join(valid_delete_policy)}"
        )

    return delete_policy


def parse_key_value_list(pairs):
    result = {}
    if pairs is None:
        return result
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid format '{pair}'. Expected format key=value.")
        key, value = pair.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def aks_managed_namespace_update(cmd, client, raw_parameters, headers, existedNamespace, no_wait):
    resource_group_name = raw_parameters.get("resource_group_name")
    cluster_name = raw_parameters.get("cluster_name")
    namespace_name = raw_parameters.get("name")

    namespace_config = updateNamespace(cmd, raw_parameters, existedNamespace)
    namespace_config.location = get_cluster_location(cmd, resource_group_name, cluster_name)

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        namespace_name,
        namespace_config,
        headers=headers,
    )


def updateNamespace(cmd, raw_parameters, existedNamespace):
    tags = raw_parameters.get("tags", {})
    labels_raw = raw_parameters.get("labels")
    labels = parse_key_value_list(labels_raw)
    annotations_raw = raw_parameters.get("annotations")
    annotations = parse_key_value_list(annotations_raw)

    NamespaceProperties = cmd.get_models(
        "NamespaceProperties",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_namespaces"
    )

    namespace_properties = NamespaceProperties(
        labels=labels,
        annotations=annotations,
        default_resource_quota=updateResourceQuota(cmd, raw_parameters, existedNamespace),
        default_network_policy=updateNetworkPolicyRule(cmd, raw_parameters, existedNamespace),
        adoption_policy=updateAdoptionPolicy(raw_parameters, existedNamespace),
        delete_policy=updateDeletePolicy(raw_parameters, existedNamespace)
    )

    Namespace = cmd.get_models(
        "ManagedNamespace",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_namespaces"
    )

    namespace_config = Namespace()
    namespace_config.name = existedNamespace.name
    namespace_config.tags = tags
    namespace_config.properties = namespace_properties
    return namespace_config


def updateResourceQuota(cmd, raw_parameters, existedNamespace):
    cpu_request = raw_parameters.get("cpu_request")
    cpu_limit = raw_parameters.get("cpu_limit")
    memory_request = raw_parameters.get("memory_request")
    memory_limit = raw_parameters.get("memory_limit")

    if cpu_request is None:
        cpu_request = existedNamespace.properties.default_resource_quota.cpu_request

    if cpu_limit is None:
        cpu_limit = existedNamespace.properties.default_resource_quota.cpu_limit

    if memory_request is None:
        memory_request = existedNamespace.properties.default_resource_quota.memory_request

    if memory_limit is None:
        memory_limit = existedNamespace.properties.default_resource_quota.memory_limit

    ResourceQuota = cmd.get_models(
        "ResourceQuota",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_namespaces"
    )

    rq = ResourceQuota(
        cpu_request=cpu_request,
        cpu_limit=cpu_limit,
        memory_request=memory_request,
        memory_limit=memory_limit
    )

    return rq


def updateNetworkPolicyRule(cmd, raw_parameters, existedNamespace):
    ingress_policy = raw_parameters.get("ingress_policy")
    egress_policy = raw_parameters.get("egress_policy")

    valid_network_policy_rules = {
        CONST_NAMESPACE_NETWORK_POLICY_RULE_DENYALL,
        CONST_NAMESPACE_NETWORK_POLICY_RULE_ALLOWSAMENAMESPACE,
        CONST_NAMESPACE_NETWORK_POLICY_RULE_ALLOWALL
    }

    if ingress_policy is not None and ingress_policy not in valid_network_policy_rules:
        raise InvalidArgumentValueError(
            f"Invalid ingress_policy '{ingress_policy}'. Must be one of: "
            f"{', '.join(valid_network_policy_rules)}"
        )

    if egress_policy is not None and egress_policy not in valid_network_policy_rules:
        raise InvalidArgumentValueError(
            f"Invalid egress_policy '{egress_policy}'. Must be one of: "
            f"{', '.join(valid_network_policy_rules)}"
        )

    if ingress_policy is None:
        ingress_policy = existedNamespace.properties.default_network_policy.ingress

    if egress_policy is None:
        egress_policy = existedNamespace.properties.default_network_policy.egress

    NetworkPolicies = cmd.get_models(
        "NetworkPolicies",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_namespaces"
    )

    np = NetworkPolicies(
        ingress=ingress_policy,
        egress=egress_policy
    )

    return np


def updateAdoptionPolicy(raw_parameters, existedNamespace):
    adoption_policy = raw_parameters.get("adoption_policy")

    valid_adoption_policy = {
        CONST_NAMESPACE_ADOPTION_POLICY_NEVER,
        CONST_NAMESPACE_ADOPTION_POLICY_IFIDENTICAL,
        CONST_NAMESPACE_ADOPTION_POLICY_ALWAYS
    }

    if adoption_policy is not None and adoption_policy not in valid_adoption_policy:
        raise InvalidArgumentValueError(
            f"Invalid adoption policy '{adoption_policy}'. Must be one of: "
            f"{', '.join(valid_adoption_policy)}"
        )

    if adoption_policy is None:
        adoption_policy = existedNamespace.properties.adoption_policy

    return adoption_policy


def updateDeletePolicy(raw_parameters, existedNamespace):
    delete_policy = raw_parameters.get("delete_policy")

    valid_delete_policy = {
        CONST_NAMESPACE_DELETE_POLICY_KEEP,
        CONST_NAMESPACE_DELETE_POLICY_DELETE
    }

    if delete_policy is not None and delete_policy not in valid_delete_policy:
        raise InvalidArgumentValueError(
            f"Invalid delete policy '{delete_policy}'. Must be one of: "
            f"{', '.join(valid_delete_policy)}"
        )

    if delete_policy is None:
        delete_policy = existedNamespace.properties.delete_policy

    return delete_policy
