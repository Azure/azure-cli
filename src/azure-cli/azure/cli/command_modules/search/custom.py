# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.log import get_logger
from azure.cli.core.util import sdk_no_wait
from azure.cli.core.azclierror import UnrecognizedArgumentError

logger = get_logger(__name__)


def _get_resource_group_location(cli_ctx, resource_group_name):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    # pylint: disable=no-member
    return client.resource_groups.get(resource_group_name).location


def create_search_service(cmd, resource_group_name, search_service_name, sku, location=None, partition_count=0,
                          replica_count=0, public_network_access="enabled", ip_rules=None, identity_type=None,
                          hosting_mode="default", no_wait=False):
    """
    Creates a Search service in the given resource group.

    :param resource_group_name: Name of resource group.
    :param search_service_name: Name of the search service.
    :param sku: The SKU of the search service, which determines price tier and capacity limits.
    :param location: Geographic location of the resource.
    :param partition_count: Number of partitions in the search service.
    :param replica_count: Number of replicas in the search service.
    :param public_network_access: Public accessibility to the search service;
                                  allowed values are "enabled" or "disabled".
    :param ip_rules: Public IP(v4) addresses or CIDR ranges to the search service, separated by comma or semicolon;
                     these IP rules are applicable only when --public-network-access is "enabled".
    :param identity_type: The identity type; possible values include: "None", "SystemAssigned".
    :param hosting_mode: The hosting mode; possible values include: "default", "highDensity";
                     Note that "highDensity" is only applicable to the standard3 SKU.
    """
    from azure.mgmt.search.models import SearchService, Sku, NetworkRuleSet, IpRule, Identity
    from azure.cli.command_modules.search._client_factory import cf_search_services
    import re

    _client = cf_search_services(cmd.cli_ctx, None)
    if location is None:
        location = _get_resource_group_location(cmd.cli_ctx, resource_group_name)

    _search = SearchService(location=location, sku=Sku(name=sku.lower()))

    replica_count = int(replica_count)
    partition_count = int(partition_count)
    if replica_count > 0:
        _search.replica_count = replica_count
    if partition_count > 0:
        _search.partition_count = partition_count
    if (public_network_access.lower() not in ["enabled", "disabled"]):
        raise UnrecognizedArgumentError("SearchService.PublicNetworkAccess: only [""enabled"", ""disabled""] are allowed")
    if (hosting_mode not in ["default", "highDensity"]):
        raise UnrecognizedArgumentError("SearchService.HostingMode: only [""default"", ""highDensity""] are allowed")
    if (hosting_mode == "highDensity" and sku.lower() != "standard3"):
        raise UnrecognizedArgumentError("SearchService.HostingMode: ""highDensity"" is only allowed when sku is ""standard3""")
    _search.public_network_access = public_network_access
    _search.hosting_mode = hosting_mode

    if ip_rules:
        _ip_rules = []
        _ip_rules_array = re.split(';|,', ip_rules)
        for _ip_rule in _ip_rules_array:
            if _ip_rule:
                _ip_rules.append(IpRule(value=_ip_rule))
        _search.network_rule_set = NetworkRuleSet(ip_rules=_ip_rules)
    if identity_type:
        _identity = Identity(type=identity_type)
        _search.identity = _identity

    return sdk_no_wait(no_wait, _client.begin_create_or_update, resource_group_name, search_service_name, _search)


def update_search_service(instance, partition_count=0, replica_count=0, public_network_access=None,
                          ip_rules=None, identity_type=None):
    """
    Update partition and replica of the given search service.

    :param partition_count: Number of partitions in the search service.
    :param replica_count: Number of replicas in the search service.
    :param public_network_access: Public accessibility to the search service;
                                  allowed values are "enabled" or "disabled".
    :param ip_rules: Public IP(v4) addresses or CIDR ranges to the search service, seperated by comma(',') or
                     semicolon(';'); If spaces (' '), ',' or ';' is provided, any existing IP rule will be
                     nullified and no public IP rule is applied. These IP rules are applicable only when
                     public_network_access is "enabled".
    :param identity_type: The identity type; possible values include: "None", "SystemAssigned".
    """
    from azure.mgmt.search.models import NetworkRuleSet, IpRule, Identity
    import re

    replica_count = int(replica_count)
    partition_count = int(partition_count)
    if replica_count > 0:
        instance.replica_count = replica_count
    if partition_count > 0:
        instance.partition_count = partition_count
    if public_network_access:
        if (public_network_access.lower() not in ["enabled", "disabled"]):
            raise UnrecognizedArgumentError("SearchService.PublicNetworkAccess: only [""enabled"", ""disabled""] are allowed")
        instance.public_network_access = public_network_access
    if ip_rules:
        _ip_rules = []
        _ip_rules_array = re.split(';|,', ip_rules)
        for _ip_rule in _ip_rules_array:
            if _ip_rule:
                _ip_rules.append(IpRule(value=_ip_rule))
        instance.network_rule_set = NetworkRuleSet(ip_rules=_ip_rules)
    if identity_type:
        _identity = Identity(type=identity_type)
        instance.identity = _identity

    return instance


def update_private_endpoint_connection(cmd, resource_group_name, search_service_name, private_endpoint_connection_name,
                                       private_link_service_connection_status,
                                       private_link_service_connection_description,
                                       private_link_service_connection_actions_required):
    """
    Update an existing private endpoint connection in a Search service in the given resource group.

    :param resource_group_name: Name of resource group.
    :param search_service_name: Name of the search service.
    :param private_endpoint_connection_name: Name of the private endpoint connection resource;
        for example: {the name of the private endpoint resource}.{guid}.
    :param private_link_service_connection_status: The updated status of the private endpoint connection resource.
        Possible values include: "Pending", "Approved", "Rejected", "Disconnected".
    :param private_link_service_connection_description: Custom description when updating
        the private endpoint connection resource.
    :param private_link_service_connection_actions_required: Custom 'actions required' message when updating
        the private endpoint connection resource.
    """

    from azure.mgmt.search.models import PrivateEndpointConnection, PrivateEndpointConnectionProperties,\
        PrivateEndpointConnectionPropertiesPrivateLinkServiceConnectionState
    from azure.cli.command_modules.search._client_factory import cf_search_private_endpoint_connections

    _client = cf_search_private_endpoint_connections(cmd.cli_ctx, None)
    _private_endpoint_connection = PrivateEndpointConnection()
    _private_link_service_connection_state = PrivateEndpointConnectionPropertiesPrivateLinkServiceConnectionState(
        status=private_link_service_connection_status,
        description=private_link_service_connection_description,
        actions_required=private_link_service_connection_actions_required
    )
    _private_endpoint_connection_properties = PrivateEndpointConnectionProperties(
        private_link_service_connection_state=_private_link_service_connection_state)
    _private_endpoint_connection.id = private_endpoint_connection_name
    _private_endpoint_connection.properties = _private_endpoint_connection_properties

    return _client.update(resource_group_name, search_service_name, private_endpoint_connection_name,
                          _private_endpoint_connection)


def create_shared_private_link_resource(cmd, resource_group_name, search_service_name,
                                        shared_private_link_resource_name, shared_private_link_resource_id,
                                        shared_private_link_resource_group_id,
                                        shared_private_link_resource_request_message="Please approve",
                                        no_wait=False):
    """
    Create shared privatelink resources in a Search service in the given resource group.

    :param resource_group_name: Name of resource group.
    :param search_service_name: Name of the search service.
    :param shared_private_link_resource_name: Name of the shared private link resource.
    :param shared_private_link_resource_id: Fully qualified resource ID for the resource.
        for example: /subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/
        {resourceProviderNamespace}/{resourceType}/{resourceName}.
    :param shared_private_link_resource_group_id: The group id of the resource; for example: blob, sql or vault.
    :param shared_private_link_resource_request_message: Custom request message when creating or updating the shared
        privatelink resources.
    """
    from azure.mgmt.search.models import SharedPrivateLinkResource, SharedPrivateLinkResourceProperties
    from azure.cli.command_modules.search._client_factory import cf_search_shared_private_link_resources

    _client = cf_search_shared_private_link_resources(cmd.cli_ctx, None)
    _shared_private_link_resource = SharedPrivateLinkResource()
    _shared_private_link_resource.name = shared_private_link_resource_name
    _shared_private_link_resource.properties = SharedPrivateLinkResourceProperties(
        private_link_resource_id=shared_private_link_resource_id,
        group_id=shared_private_link_resource_group_id,
        request_message=shared_private_link_resource_request_message
    )

    return sdk_no_wait(no_wait, _client.begin_create_or_update, resource_group_name,
                       search_service_name, shared_private_link_resource_name, _shared_private_link_resource)


def update_shared_private_link_resource(cmd, resource_group_name, search_service_name,
                                        shared_private_link_resource_name, shared_private_link_resource_id,
                                        shared_private_link_resource_group_id,
                                        shared_private_link_resource_request_message,
                                        no_wait=False):
    """
    Update shared privatelink resources in a Search service in the given resource group.

    :param resource_group_name: Name of resource group.
    :param search_service_name: Name of the search service.
    :param shared_private_link_resource_name: Name of the shared private link resource.
    :param shared_private_link_resource_id: Fully qualified resource ID for the resource;
        for example: /subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/
        {resourceProviderNamespace}/{resourceType}/{resourceName}.
    :param shared_private_link_resource_group_id: The group id of the resource; for example: blob, sql or vault.
    :param shared_private_link_resource_request_message: Custom request message when creating or updating the shared
        privatelink resources.
    """
    from azure.mgmt.search.models import SharedPrivateLinkResource, SharedPrivateLinkResourceProperties
    from azure.cli.command_modules.search._client_factory import cf_search_shared_private_link_resources

    _client = cf_search_shared_private_link_resources(cmd.cli_ctx, None)
    _shared_private_link_resource = SharedPrivateLinkResource()
    _shared_private_link_resource.name = shared_private_link_resource_name
    _shared_private_link_resource.properties = SharedPrivateLinkResourceProperties(
        private_link_resource_id=shared_private_link_resource_id,
        group_id=shared_private_link_resource_group_id,
        request_message=shared_private_link_resource_request_message
    )

    return sdk_no_wait(no_wait, _client.begin_create_or_update, resource_group_name,
                       search_service_name, shared_private_link_resource_name, _shared_private_link_resource)
