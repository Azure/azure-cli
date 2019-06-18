# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_key_for_storage_account(cmd, storage_account):  # pylint: disable=unused-argument
    from ._client_factory import cf_storage
    from msrestazure.tools import parse_resource_id, is_valid_resource_id
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
    from msrestazure.tools import parse_resource_id, is_valid_resource_id
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


def build_identities_info(identities):
    from azure.mgmt.hdinsight.models import ClusterIdentity, ResourceIdentityType
    identity = None
    if identities:
        identity_type = ResourceIdentityType.user_assigned
        identity = ClusterIdentity(type=identity_type)
        identity.user_assigned_identities = {e: {} for e in identities}

    return identity


def build_virtual_network_profile(subnet):
    from msrestazure.tools import resource_id, parse_resource_id, is_valid_resource_id
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
    from msrestazure.tools import parse_resource_id, is_valid_resource_id
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
