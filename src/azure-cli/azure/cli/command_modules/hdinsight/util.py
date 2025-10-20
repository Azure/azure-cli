# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


AUTOSCALE_TIMEZONES = ["Dateline Standard Time",
                       "UTC-11",
                       "Hawaiian Standard Time",
                       "Alaskan Standard Time",
                       "Pacific Standard Time (Mexico)",
                       "Pacific Standard Time",
                       "US Mountain Standard Time",
                       "Mountain Standard Time (Mexico)",
                       "Mountain Standard Time",
                       "Central America Standard Time",
                       "Central Standard Time",
                       "Central Standard Time (Mexico)",
                       "Canada Central Standard Time",
                       "SA Pacific Standard Time",
                       "Eastern Standard Time",
                       "USEasternStandardTime",
                       "Venezuela Standard Time",
                       "Paraguay Standard Time",
                       "Atlantic Standard Time",
                       "Central Brazilian Standard Time",
                       "SA Western Standard Time",
                       "Pacific SA Standard Time",
                       "Newfoundland Standard Time",
                       "E. South America Standard Time",
                       "Argentina Standard Time",
                       "SA Eastern Standard Time",
                       "Greenland Standard Time",
                       "Montevideo Standard Time",
                       "Bahia Standard Time",
                       "UTC-02",
                       "Mid-Atlantic Standard Time",
                       "Azores Standard Time",
                       "Cape Verde Standard Time",
                       "Morocco Standard Time",
                       "UTC",
                       "GMT Standard Time",
                       "Greenwich Standard Time",
                       "W. Europe Standard Time",
                       "Central Europe Standard Time",
                       "Romance Standard Time",
                       "Central European Standard Time",
                       "W. Central Africa Standard Time",
                       "Namibia Standard Time",
                       "Jordan Standard Time",
                       "GTB Standard Time",
                       "Middle East Standard Time",
                       "Egypt Standard Time",
                       "Syria Standard Time",
                       "E. Europe Standard Time",
                       "South Africa Standard Time",
                       "FLE Standard Time",
                       "Israel Standard Time",
                       "Kaliningrad Standard Time",
                       "Libya Standard Time",
                       "Arabic Standard Time",
                       "Turkey Standard Time",
                       "Arab Standard Time",
                       "Belarus Standard Time",
                       "Russian Standard Time",
                       "E. Africa Standard Time",
                       "Iran Standard Time",
                       "Arabian Standard Time",
                       "Azerbaijan Standard Time",
                       "Russia Time Zone 3",
                       "Mauritius Standard Time",
                       "Georgian Standard Time",
                       "Caucasus Standard Time",
                       "Afghanistan Standard Time",
                       "West Asia Standard Time",
                       "Ekaterinburg Standard Time",
                       "Pakistan Standard Time",
                       "India Standard Time",
                       "Sri Lanka Standard Time",
                       "Nepal Standard Time",
                       "Central Asia Standard Time",
                       "Bangladesh Standard Time",
                       "N. Central Asia Standard Time",
                       "Myanmar Standard Time",
                       "SE Asia Standard Time",
                       "North Asia Standard Time",
                       "China Standard Time",
                       "North Asia East Standard Time",
                       "Singapore Standard Time",
                       "W. Australia Standard Time",
                       "Taipei Standard Time",
                       "Ulaanbaatar Standard Time",
                       "Tokyo Standard Time",
                       "Korea Standard Time",
                       "Yakutsk Standard Time",
                       "Cen. Australia Standard Time",
                       "AUS Central Standard Time",
                       "E. Australia Standard Time",
                       "AUS Eastern Standard Time",
                       "West Pacific Standard Time",
                       "Tasmania Standard Time",
                       "Vladivostok Standard Time",
                       "Russia Time Zone 10",
                       "Magadan Standard Time",
                       "Central Pacific Standard Time",
                       "Russia Time Zone 11",
                       "New Zealand Standard Time",
                       "UTC+12",
                       "Fiji Standard Time",
                       "Kamchatka Standard Time",
                       "Tonga Standard Time",
                       "Samoa Standard Time",
                       "Line Islands Standard Time"
                       ]


class NodeRoleType:  # pylint: disable=too-few-public-methods
    HEADNODE = "HeadNodeRole"
    WORKERNODE = "WorkerNodeRole"
    ZOOKEEPERNODE = "ZookeeperRole"
    EDGENODE = "EdgeNodeRole"
    HIBNODE = "HIBRole"
    KAFKAMANAGEMENTNODE = "KafkaManagementNodeRole"


def get_key_for_storage_account(cmd, storage_account):  # pylint: disable=unused-argument
    from ._client_factory import cf_storage
    from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id
    from knack.util import CLIError

    storage_account_key = None
    if is_valid_resource_id(storage_account):
        parsed_storage_account = parse_resource_id(storage_account)
        resource_group_name = parsed_storage_account['resource_group']
        storage_account_name = parsed_storage_account['resource_name']

        storage_client = cf_storage(cmd.cli_ctx)
        keys = storage_client.storage_accounts.list_keys(resource_group_name, storage_account_name)
        storage_account_key = keys.keys[0].value  # pylint: disable=no-member
    elif storage_account:
        raise CLIError('Failed to get access key for storage account: {}'.format(storage_account))
    return storage_account_key


def get_storage_account_endpoint(cmd, storage_account, is_wasb):
    from ._client_factory import cf_storage
    from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id
    host = None
    if is_valid_resource_id(storage_account):
        parsed_storage_account = parse_resource_id(storage_account)
        resource_group_name = parsed_storage_account['resource_group']
        storage_account_name = parsed_storage_account['resource_name']

        storage_client = cf_storage(cmd.cli_ctx)
        storage_account = storage_client.storage_accounts.get_properties(
            resource_group_name=resource_group_name,
            account_name=storage_account_name)

        def extract_endpoint(storage_account, is_wasb):
            if not storage_account:
                return None
            return storage_account.primary_endpoints.dfs if not is_wasb else storage_account.primary_endpoints.blob

        def extract_host(uri):
            import re
            return uri and re.search('//(.*)/', uri).groups()[0]

        host = extract_host(extract_endpoint(storage_account, is_wasb))
    return host


def is_wasb_storage_account(cmd, storage_account):
    from ._client_factory import cf_storage
    from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id
    is_wasb = True
    if is_valid_resource_id(storage_account):
        parsed_storage_account = parse_resource_id(storage_account)
        resource_group_name = parsed_storage_account['resource_group']
        storage_account_name = parsed_storage_account['resource_name']
        storage_client = cf_storage(cmd.cli_ctx)
        properties = storage_client.storage_accounts.get_properties(resource_group_name, storage_account_name)
        is_wasb = not properties.is_hns_enabled
    return is_wasb


def build_identities_info(identities):
    from azure.mgmt.hdinsight.models import ClusterIdentity, ResourceIdentityType
    identity = None
    if identities:
        identity_type = ResourceIdentityType.user_assigned
        identity = ClusterIdentity(type=identity_type)
        identity.user_assigned_identities = {e: {} for e in identities}

    return identity


def build_update_identities_info(assign_identity_type, identities):
    from azure.mgmt.hdinsight.models import ClusterIdentity
    identity = ClusterIdentity(type=assign_identity_type)
    if identities:
        identity.user_assigned_identities = {str(e): {} for sublist in identities for e in sublist}
    return identity


def build_virtual_network_profile(subnet):
    from azure.mgmt.core.tools import resource_id, parse_resource_id, is_valid_resource_id
    from azure.mgmt.hdinsight.models import VirtualNetworkProfile
    from knack.util import CLIError

    vnet_profile = None
    if is_valid_resource_id(subnet):
        parsed_subnet_id = parse_resource_id(subnet)
        subscription_name = parsed_subnet_id['subscription']
        resource_group_name = parsed_subnet_id['resource_group']
        vnet_namespace = parsed_subnet_id['namespace']
        vnet_type = parsed_subnet_id['type']
        vnet_name = parsed_subnet_id['name']
        vnet_id = resource_id(
            subscription=subscription_name,
            resource_group=resource_group_name,
            namespace=vnet_namespace,
            type=vnet_type,
            name=vnet_name)
        vnet_profile = VirtualNetworkProfile(id=vnet_id, subnet=subnet)
    elif subnet:
        raise CLIError('Invalid subnet: {}'.format(subnet))
    return vnet_profile


def parse_domain_name(domain):
    from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id
    domain_name = None
    if is_valid_resource_id(domain):
        parsed_domain_id = parse_resource_id(domain)
        domain_name = parsed_domain_id['resource_name']
    return domain_name


# Validate ESP cluster creation required parameters
def validate_esp_cluster_create_params(esp,
                                       cluster_name,
                                       resource_group_name,
                                       cluster_type,
                                       subnet,
                                       domain,
                                       cluster_admin_account,
                                       assign_identity,
                                       ldaps_urls,
                                       cluster_admin_password,
                                       cluster_users_group_dns):
    from knack.util import CLIError
    if esp:
        missing_params = []
        if not cluster_name:
            missing_params.append("--name/-n")
        if not resource_group_name:
            missing_params.append("--resource-group/-g")
        if not cluster_type:
            missing_params.append("--type/-t")
        if not subnet:
            missing_params.append("--subnet")
        if not domain:
            missing_params.append("--domain")
        if not cluster_admin_account:
            missing_params.append("--cluster-admin-account")
        if not cluster_users_group_dns:
            missing_params.append("--cluster-users-group-dns")
        if not assign_identity:
            missing_params.append("--assign-identity")

        if missing_params:
            raise CLIError('the following params are required  '
                           'when --esp is specified: {}'.format(', '.join(missing_params)))
    else:
        esp_params = []
        if domain:
            esp_params.append("--domain")
        if cluster_admin_account:
            esp_params.append("--cluster-admin_account")
        if ldaps_urls:
            esp_params.append("--ldaps-urls")
        if cluster_admin_password:
            esp_params.append("--cluster-admin-password")
        if cluster_users_group_dns:
            esp_params.append("--cluster-users-group-dns")

        if esp_params:
            raise CLIError('the following params are required only '
                           'when --esp is specified: {}'.format(', '.join(esp_params)))


def get_resource_id_by_name(cli_ctx, resource_type, resource_name):
    from ._client_factory import cf_resources
    from knack.util import CLIError

    client = cf_resources(cli_ctx)
    filter_str = "resourceType eq '{}' and name eq '{}'".format(resource_type, resource_name) if resource_type else None
    resources = list(client.resources.list(filter=filter_str))
    if not resources:
        raise CLIError('Fails to retrieve any resource by name {}'.format(resource_name))
    if len(resources) > 1:
        raise CLIError('Found more than one resources by name {}. '
                       'Please specify one of the following resource IDs explicitly:\n{}'
                       .format(resource_name, '\n'.join([resource.id for resource in resources])))
    return resources[0].id


def get_default_vm_sizes_configurations(cli_ctx, location):
    from ._client_factory import cf_hdinsight_locations
    locations_client = cf_hdinsight_locations(cli_ctx)
    billing_response_result = locations_client.list_billing_specs(location)
    default_vm_sizes_configurations = {}
    for vm_filter in billing_response_result.vm_size_filters:
        if vm_filter.filter_mode == "Default":
            for node_type in vm_filter.node_types:
                cluster_type_vm_sizes_dict = default_vm_sizes_configurations.get(node_type.upper())
                if not cluster_type_vm_sizes_dict:
                    cluster_type_vm_sizes_dict = {}
                for cluster_type in vm_filter.cluster_flavors:
                    for vm_size in vm_filter.vm_sizes:
                        cluster_type_vm_sizes_dict[cluster_type.upper()] = vm_size
                default_vm_sizes_configurations[node_type.upper()] = cluster_type_vm_sizes_dict
    return default_vm_sizes_configurations


def get_default_vm_size_per_node_cluster_type(cluster_type, node_type, default_vm_sizes_configurations):
    cluster_type_vm_size_dict = default_vm_sizes_configurations.get(node_type.upper())
    cluster_type = map_cluster_type(cluster_type)

    vm_size = None
    if cluster_type_vm_size_dict:
        vm_size = cluster_type_vm_size_dict.get(cluster_type.upper())
        if not vm_size:
            vm_size = cluster_type_vm_size_dict.get("*")
    return vm_size


def set_vm_size(cli_ctx, location, cluster_type, headnode_size, workernode_size):
    if not headnode_size or not workernode_size:
        default_vm_size_configurations = get_default_vm_sizes_configurations(cli_ctx, location)
        if not headnode_size:
            headnode_size = get_default_vm_size_per_node_cluster_type(cluster_type, NodeRoleType.HEADNODE,
                                                                      default_vm_size_configurations)
        if not workernode_size:
            workernode_size = get_default_vm_size_per_node_cluster_type(cluster_type, NodeRoleType.WORKERNODE,
                                                                        default_vm_size_configurations)

    return headnode_size, workernode_size


def map_cluster_type(cluster_type):
    # the cluster type is mlservice in the list billing spec response
    if cluster_type.lower() == 'mlservices' or cluster_type.lower() == 'rserver':
        cluster_type = 'mlservice'
    return cluster_type


def get_entra_user_info(cmd, entra_user_identity, entra_user_full_info, toJson=True):
    import json
    from ._client_factory import cf_graph
    from azure.cli.core.azclierror import ResourceNotFoundError, InvalidArgumentValueError, AzureResponseError

    def is_email(value):
        return "@" in value and "." in value

    def normalize_keys(d):
        return {k.lower(): v for k, v in d.items()}

    graph_client = cf_graph(cmd.cli_ctx)
    rest_auth_entra_users = []
    if entra_user_identity:
        user_data = []
        for item in entra_user_identity:
            if item:
                user_data.extend([s.strip() for s in item.split(',') if s.strip()])
        for data in user_data:
            try:
                user = graph_client.user_get(data)
                if user is None:
                    filter_expr = f"id eq '{data}'"
                    if is_email(data):
                        filter_expr = f"userPrincipalName eq '{data}' or mail eq '{data}'"
                    user = graph_client.user_list(filter=filter_expr)
                    user = user[0]
                if user is None:
                    raise ResourceNotFoundError(
                        error_msg=f'No Entra user found for input: "{data}"',
                        recommendation=[
                            'Verify the user exists in Microsoft Entra ID',
                            'Confirm the identifier (email, upn, or objectId) is correct',
                            'Try querying manually: az ad user show --id <identifier>'
                        ]
                    )
                rest_auth_entra_users.append({'ObjectId': user['id'],
                                              'DisplayName': user['displayName'],
                                              'Upn': user['userPrincipalName']})
            except ResourceNotFoundError:
                raise
            except Exception as ex:
                raise AzureResponseError(
                    error_msg=f'Error: {type(ex).__name__}: {str(ex)}',
                    recommendation=[
                        'Check network connectivity to Microsoft Graph API',
                        'Validate authentication permissions for directory queries',
                        'Retry operation with --debug to inspect detailed error',
                        'Alternatively, consider using --entra-user-full-info to provide user details directly',
                    ]
                )
    else:
        for user in entra_user_full_info:
            user_normalized = normalize_keys(user)
            allowed_keys = {'objectid', 'displayname', 'upn'}
            if invalid_keys := set(user_normalized.keys()) - allowed_keys:
                raise InvalidArgumentValueError(
                    error_msg=f'Invalid keys detected in user object: {", ".join(invalid_keys)}',
                    recommendation=[
                        'User objects must only contain: objectId, displayName, and upn',
                        f'Remove invalid keys: {", ".join(invalid_keys)}',
                        'Example valid format: [{"objectId": "...", "displayName": "...", "upn": "..."}]'
                    ]
                )
            rest_auth_entra_users.append({'ObjectId': user_normalized.get('objectid'),
                                          'DisplayName': user_normalized.get('displayname'),
                                          'Upn': user_normalized.get('upn')})
    return json.dumps(rest_auth_entra_users) if toJson else rest_auth_entra_users
