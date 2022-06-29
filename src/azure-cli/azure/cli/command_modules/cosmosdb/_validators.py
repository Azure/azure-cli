# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ipaddress
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.commands.client_factory import get_subscription_id
from knack.util import CLIError


def validate_failover_policies(ns):
    """ Extracts multiple space-separated failoverPolicies in regionName=failoverPriority format """
    from azure.mgmt.cosmosdb.models import FailoverPolicies, FailoverPolicy
    fp_dict = []
    for item in ns.failover_parameters:
        comps = item.split('=', 1)
        fp_dict.append(FailoverPolicy(location_name=comps[0], failover_priority=int(comps[1])))
    ns.failover_parameters = FailoverPolicies(failover_policies=fp_dict)


def validate_ip_range_filter(ns):
    """ Extracts multiple comma-separated ip rules """
    from azure.mgmt.cosmosdb.models import IpAddressOrRange
    if ns.ip_range_filter is not None:
        ip_rules_list = []
        for item in ns.ip_range_filter:
            for i in item.split(","):
                if i:
                    ip_rules_list.append(IpAddressOrRange(ip_address_or_range=i))
                    ns.ip_range_filter = ip_rules_list
        ns.ip_range_filter = ip_rules_list


def validate_private_endpoint_connection_id(ns):
    if ns.connection_id:
        from azure.cli.core.util import parse_proxy_resource_id
        result = parse_proxy_resource_id(ns.connection_id)
        ns.resource_group_name = result['resource_group']
        ns.account_name = result['name']
        ns.private_endpoint_connection_name = result['child_name_1']

    if not all([ns.account_name, ns.resource_group_name, ns.private_endpoint_connection_name]):
        raise CLIError(None, 'incorrect usage: [--id ID | --name NAME --account-name NAME --resource-group NAME]')

    del ns.connection_id


def validate_capabilities(ns):
    """ Extracts multiple space-separated capabilities """
    from azure.mgmt.cosmosdb.models import Capability
    if ns.capabilities is not None:
        capabilties_list = []
        for item in ns.capabilities:
            capabilties_list.append(Capability(name=item))
        ns.capabilities = capabilties_list


def validate_virtual_network_rules(ns):
    """ Extracts multiple space-separated virtual network rules """
    from azure.mgmt.cosmosdb.models import VirtualNetworkRule
    if ns.virtual_network_rules is not None:
        virtual_network_rules_list = []
        for item in ns.virtual_network_rules:
            virtual_network_rules_list.append(VirtualNetworkRule(id=item))
        ns.virtual_network_rules = virtual_network_rules_list


def validate_role_definition_body(cmd, ns):
    """ Extracts role definition body """
    import os

    from azure.cli.core.util import get_file_json, shell_safe_json_parse
    from azure.mgmt.cosmosdb.models import Permission, RoleDefinitionType
    if ns.role_definition_body is not None:
        if os.path.exists(ns.role_definition_body):
            role_definition = get_file_json(ns.role_definition_body)
        else:
            role_definition = shell_safe_json_parse(ns.role_definition_body)

        if not isinstance(role_definition, dict):
            raise InvalidArgumentValueError(
                'Invalid role definition. A valid dictionary JSON representation is expected.')

        if 'Id' in role_definition:
            role_definition['Id'] = _parse_resource_path(
                resource=role_definition['Id'],
                to_fully_qualified=False,
                resource_type="sqlRoleDefinitions")
        else:
            role_definition['Id'] = _gen_guid()

        if 'DataActions' in role_definition:
            role_definition['Permissions'] = [Permission(data_actions=role_definition['DataActions'])]
        else:
            role_definition['Permissions'] = [Permission(data_actions=p['DataActions'])
                                              for p in role_definition['Permissions']]

        if 'Type' not in role_definition:
            role_definition['Type'] = RoleDefinitionType.custom_role

        role_definition['AssignableScopes'] = [_parse_resource_path(
            resource=scope,
            to_fully_qualified=True,
            resource_type=None,
            subscription_id=get_subscription_id(cmd.cli_ctx),
            resource_group_name=ns.resource_group_name,
            account_name=ns.account_name) for scope in role_definition['AssignableScopes']]

        ns.role_definition_body = role_definition


def validate_role_definition_id(ns):
    """ Extracts Guid role definition Id """
    if ns.role_definition_id is not None:
        ns.role_definition_id = _parse_resource_path(
            resource=ns.role_definition_id,
            to_fully_qualified=False,
            resource_type="sqlRoleDefinitions")


def validate_fully_qualified_role_definition_id(cmd, ns):
    """ Extracts fully qualified role definition Id """
    if ns.role_definition_id is not None:
        ns.role_definition_id = _parse_resource_path(
            resource=ns.role_definition_id,
            to_fully_qualified=True,
            resource_type="sqlRoleDefinitions",
            subscription_id=get_subscription_id(cmd.cli_ctx),
            resource_group_name=ns.resource_group_name,
            account_name=ns.account_name)


def validate_role_assignment_id(ns):
    """ Extracts Guid role assignment Id """
    if ns.role_assignment_id is not None:
        ns.role_assignment_id = _parse_resource_path(
            resource=ns.role_assignment_id,
            to_fully_qualified=False,
            resource_type="sqlRoleAssignments")
    else:
        ns.role_assignment_id = _gen_guid()


def validate_scope(cmd, ns):
    """ Extracts fully qualified scope """
    if ns.scope is not None:
        ns.scope = _parse_resource_path(
            resource=ns.scope,
            to_fully_qualified=True,
            resource_type=None,
            subscription_id=get_subscription_id(cmd.cli_ctx),
            resource_group_name=ns.resource_group_name,
            account_name=ns.account_name)


def _parse_resource_path(resource,
                         to_fully_qualified,
                         resource_type=None,
                         subscription_id=None,
                         resource_group_name=None,
                         account_name=None):
    """Returns a properly formatted role definition or assignment id or scope. If scope, type=None."""
    import re
    regex = "/subscriptions/(?P<subscription>.*)/resourceGroups/(?P<resource_group>.*)/providers/" \
            "Microsoft.DocumentDB/databaseAccounts/(?P<database_account>.*)"
    formatted = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.DocumentDB/databaseAccounts/{2}"

    if resource_type is not None:
        regex += "/" + resource_type + "/(?P<resource_id>.*)"
        formatted += "/" + resource_type + "/"

    formatted += "{3}"

    if to_fully_qualified:
        result = re.match(regex, resource)
        if result is not None:
            return resource

        return formatted.format(subscription_id, resource_group_name, account_name, resource)

    result = re.match(regex, resource)
    if result is None:
        return resource

    return result['resource_id']


def _gen_guid():
    import uuid
    return uuid.uuid4()


def validate_gossip_certificates(ns):
    """ Extracts multiple comma-separated certificates """
    if ns.external_gossip_certificates is not None:
        ns.external_gossip_certificates = get_certificates(ns.external_gossip_certificates)


def validate_client_certificates(ns):
    """ Extracts multiple comma-separated certificates """
    if ns.client_certificates is not None:
        ns.client_certificates = get_certificates(ns.client_certificates)


def get_certificates(input_certificates):
    from azure.mgmt.cosmosdb.models import Certificate
    certificates = []
    for item in input_certificates:
        certificate = get_certificate(item)
        certificates.append(Certificate(pem=certificate))
    return certificates


def get_certificate(cert):
    """ Extract certificate from file or from string """
    from azure.cli.core.util import read_file_content
    import os
    certificate = ''
    if cert is not None:
        if os.path.exists(cert):
            certificate = read_file_content(cert)
        else:
            certificate = cert
    else:
        raise InvalidArgumentValueError("""One of the value provided for the certificates is empty.
    Please verify there aren't any spaces.""")
    return certificate


def validate_seednodes(ns):
    """ Extracts multiple comma-separated ipaddresses """
    from azure.mgmt.cosmosdb.models import SeedNode
    if ns.external_seed_nodes is not None:
        seed_nodes = []
        for item in ns.external_seed_nodes:
            try:
                ipaddress.ip_address(item)
            except ValueError as e:
                raise InvalidArgumentValueError("""IP address provided is invalid.
            Please verify if there are any spaces or other invalid characters.""") from e
            seed_nodes.append(SeedNode(ip_address=item))
        ns.external_seed_nodes = seed_nodes


def validate_node_count(ns):
    """ Validate node count is greater than 3"""
    if ns.node_count is not None:
        if int(ns.node_count) < 3:
            raise InvalidArgumentValueError("""Node count cannot be less than 3.""")


def validate_client_encryption_policy(ns):
    """ Validate all the included paths in client encryption policy"""
    partition_key_path = [ns.partition_key_path]
    client_encryption_policy = ns.client_encryption_policy

    if client_encryption_policy is not None:
        if "includedPaths" in client_encryption_policy:
            includedPaths = client_encryption_policy['includedPaths']
        else:
            raise InvalidArgumentValueError("includedPaths missing in Client Encryption Policy. "
                                            "Please verify your Client Encryption Policy JSON string.")

        if includedPaths == "":
            raise InvalidArgumentValueError("includedPaths missing in Client Encryption Policy. "
                                            "includedPaths cannot be null or empty.")

        if "policyFormatVersion" in client_encryption_policy:
            policyFormatVersion = client_encryption_policy['policyFormatVersion']
        else:
            raise InvalidArgumentValueError("policyFormatVersion missing in Client Encryption Policy. "
                                            "Please verify your Client Encryption Policy JSON string.")

        if not isinstance(policyFormatVersion, int):
            raise InvalidArgumentValueError("Invalid policyFormatVersion type used in Client Encryption Policy. "
                                            "policyFormatVersion is an integer type. "
                                            "Supported versions are 1 and 2.")

        if(policyFormatVersion < 1 or policyFormatVersion > 2):
            raise InvalidArgumentValueError("Invalid policyFormatVersion used in Client Encryption Policy. "
                                            "Please verify your Client Encryption Policy JSON string. "
                                            "Supported versions are 1 and 2.")

        _validate_included_paths_in_cep(partition_key_path, includedPaths, policyFormatVersion)


def _validate_included_paths_in_cep(partition_key_path, includedPaths, policyFormatVersion):
    listOfPaths = []
    for includedPath in includedPaths:
        if "encryptionType" in includedPath:
            encryptionType = includedPath['encryptionType']
        else:
            raise InvalidArgumentValueError("encryptionType missing in includedPaths. "
                                            "Please verify your Client Encryption Policy JSON string.")

        if encryptionType == "":
            raise InvalidArgumentValueError("Invalid encryptionType included in Client Encryption Policy. "
                                            "encryptionType cannot be null or empty.")

        if(encryptionType != "Deterministic" and encryptionType != "Randomized"):
            raise InvalidArgumentValueError(f"Invalid Encryption Type {encryptionType} used. "
                                            "Supported types are Deterministic or Randomized.")

        if "path" in includedPath:
            path = includedPath['path']
        else:
            raise InvalidArgumentValueError("path missing in includedPaths. "
                                            "Please verify your Client Encryption Policy JSON string.")

        if path == "":
            raise InvalidArgumentValueError("Invalid path included in Client Encryption Policy. "
                                            "Path cannot be null or empty.")

        if path in listOfPaths:
            raise InvalidArgumentValueError(f"Duplicate path:{path} found in Client Encryption Policy.")

        listOfPaths.append(path)

        if(path[0] != "/" or path.rfind('/') != 0):
            raise InvalidArgumentValueError("Invalid path included in Client Encryption Policy. "
                                            "Only top level paths supported. Paths should begin with /.")

        if path[1:] == "id":
            if policyFormatVersion < 2:
                raise InvalidArgumentValueError("id path which is part of Client Encryption policy is configured "
                                                f"with invalid policyFormatVersion: {policyFormatVersion}. "
                                                "Please use policyFormatVersion 2.")

            if encryptionType != "Deterministic":
                raise InvalidArgumentValueError("id path is part of Client Encryption policy "
                                                f"with invalid encryption type: {encryptionType}. "
                                                "Only deterministic encryption type is supported.")

        if "clientEncryptionKeyId" in includedPath:
            clientEncryptionKeyId = includedPath['clientEncryptionKeyId']
        else:
            raise InvalidArgumentValueError("clientEncryptionKeyId missing in includedPaths. "
                                            "Please verify your Client Encryption Policy JSON string.")

        if clientEncryptionKeyId == "":
            raise InvalidArgumentValueError("Invalid clientEncryptionKeyId included in Client Encryption Policy. "
                                            "clientEncryptionKeyId cannot be null or empty.")

        _validate_pk_paths_in_cep(path, partition_key_path, policyFormatVersion, encryptionType)

        if "encryptionAlgorithm" in includedPath:
            encryptionAlgorithm = includedPath['encryptionAlgorithm']
        else:
            raise InvalidArgumentValueError("encryptionAlgorithm missing in includedPaths. "
                                            "Please verify your Client Encryption Policy JSON string.")

        if encryptionAlgorithm == "":
            raise InvalidArgumentValueError("Invalid encryptionAlgorithm included in Client Encryption Policy. "
                                            "encryptionAlgorithm cannot be null or empty.")

        if encryptionAlgorithm != "AEAD_AES_256_CBC_HMAC_SHA256":
            raise InvalidArgumentValueError("Invalid encryptionAlgorithm included in Client Encryption Policy. "
                                            "encryptionAlgorithm should be 'AEAD_AES_256_CBC_HMAC_SHA256'.")


def _validate_pk_paths_in_cep(path, partition_key_path, policyFormatVersion, encryptionType):

    # for each partition key path verify if its part of client encryption policy
    # or if its stop level path is part of client encryption policy
    # eg: pk path is /a/b/c and /a is part of client encryption policy
    for pkPath in partition_key_path:
        if path[1:] == pkPath.split('/')[1]:
            if policyFormatVersion < 2:
                raise InvalidArgumentValueError(f"Partition key path:{pkPath} which is part of "
                                                "Client Encryption policy is configured "
                                                f"with invalid policyFormatVersion: {policyFormatVersion}. "
                                                "Please use policyFormatVersion 2.")
            if encryptionType != "Deterministic":
                raise InvalidArgumentValueError(f"Partition key path:{pkPath} is part of "
                                                "Client Encryption policy with invalid encryption type. "
                                                "Only deterministic encryption type is supported.")
