# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
# pylint: disable=inconsistent-return-statements
# pylint: disable=unused-variable


# Namespace Region
def cli_namespace_create(client, resource_group_name, namespace_name, location=None, tags=None):
    from azure.mgmt.relay.models import RelayNamespace
    return client.create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=RelayNamespace(
            location,
            tags)
    )


def cli_namespace_update(instance, tags=None):

    if tags is not None:
        instance.tags = tags

    return instance


def cli_namespace_list(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name=resource_group_name)

    return client.list()


# Namespace Authorization rule:
def cli_namespaceautho_create(client, resource_group_name, namespace_name, name, access_rights=None):
    from azure.cli.command_modules.relay._utils import accessrights_converter
    return client.create_or_update_authorization_rule(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        authorization_rule_name=name,
        rights=accessrights_converter(access_rights)
    )


# Namespace Authorization rule:
def cli_namespaceautho_update(instance, rights):
    from azure.cli.command_modules.relay._utils import accessrights_converter
    instance.rights = accessrights_converter(rights)
    return instance


# WCF Relay Region
def cli_wcfrelay_create(client, resource_group_name, namespace_name, relay_name, relay_type,
                        requires_client_authorization=None, user_metadata=None):

    from azure.mgmt.relay.models import WcfRelay, Relaytype

    if relay_type is None:
        set_relay_type = Relaytype.net_tcp
    elif relay_type == "Http":
        set_relay_type = Relaytype.http
    else:
        set_relay_type = Relaytype.net_tcp

    wcfrelay_params = WcfRelay(
        relay_type=set_relay_type,
        requires_client_authorization=requires_client_authorization,
        user_metadata=user_metadata
    )

    return client.create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        relay_name=relay_name,
        parameters=wcfrelay_params)


def cli_wcfrelay_update(instance, relay_type=None,
                        requires_client_authorization=None, user_metadata=None, status=None):

    from azure.mgmt.relay.models import WcfRelay
    returnobj = WcfRelay(relay_type=instance.relay_type,
                         requires_client_authorization=instance.requires_client_authorization,
                         user_metadata=instance.user_metadata)

    if relay_type:
        returnobj.relay_type = relay_type

    if requires_client_authorization:
        returnobj.requires_client_authorization = requires_client_authorization

    if user_metadata:
        returnobj.user_metadata = user_metadata

    if status:
        returnobj.status = status

    return returnobj


# Hybrid Connection Region
def cli_hyco_create(client, resource_group_name, namespace_name, hybrid_connection_name,
                    requires_client_authorization=None, user_metadata=None):
    from azure.mgmt.relay.models import HybridConnection
    hyco_params = HybridConnection(
        requires_client_authorization=requires_client_authorization,
        user_metadata=user_metadata
    )
    return client.create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        hybrid_connection_name=hybrid_connection_name,
        parameters=hyco_params)


def cli_hyco_update(instance, requires_client_authorization=None, status=None, user_metadata=None):

    from azure.mgmt.relay.models import HybridConnection
    hyco_params = HybridConnection(requires_client_authorization=instance.requires_client_authorization,
                                   user_metadata=instance.user_metadata)

    if requires_client_authorization:
        hyco_params.requires_client_authorization = requires_client_authorization

    if status:
        hyco_params.status = status

    if user_metadata:
        hyco_params.user_metadata = user_metadata

    return hyco_params


def empty_on_404(ex):
    from azure.mgmt.relay.models import ErrorResponseException
    if isinstance(ex, ErrorResponseException) and ex.response.status_code == 404:
        return None
    raise ex
