# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-lines
# pylint: disable=inconsistent-return-statements
# pylint: disable=unused-variable
# pylint: disable=too-many-locals
# pylint: disable=too-many-return-statements
import re
from azure.cli.core.profiles import ResourceType


# Namespace Region
def cli_namespace_create(cmd, client, resource_group_name, namespace_name, location=None, tags=None, sku='Standard',
                         capacity=None, zone_redundant=None, mi_system_assigned=None,
                         mi_user_assigned=None, encryption_config=None, minimum_tls_version=None):

    SBSku = cmd.get_models('SBSku', resource_type=ResourceType.MGMT_SERVICEBUS)
    SBNamespace = cmd.get_models('SBNamespace', resource_type=ResourceType.MGMT_SERVICEBUS)
    Identity = cmd.get_models('Identity', resource_type=ResourceType.MGMT_SERVICEBUS)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_SERVICEBUS)
    UserAssignedIdentity = cmd.get_models('UserAssignedIdentity', resource_type=ResourceType.MGMT_SERVICEBUS)
    Encryption = cmd.get_models('Encryption', resource_type=ResourceType.MGMT_SERVICEBUS)

    parameter = SBNamespace(location=location)

    parameter.tags = tags
    parameter.sku = SBSku(name=sku, tier=sku, capacity=capacity)

    if zone_redundant is not None:
        parameter.zone_redundant = zone_redundant

    if mi_system_assigned:
        parameter.identity = Identity(type=IdentityType.SYSTEM_ASSIGNED)

    if mi_user_assigned:
        if parameter.identity:
            if parameter.identity.type == IdentityType.SYSTEM_ASSIGNED:
                parameter.identity.type = IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED
            else:
                parameter.identity.type = IdentityType.USER_ASSIGNED
        else:
            parameter.identity = Identity(type=IdentityType.USER_ASSIGNED)

        default_user_identity = UserAssignedIdentity()
        parameter.identity.user_assigned_identities = dict.fromkeys(mi_user_assigned, default_user_identity)

    if encryption_config:
        parameter.encryption = Encryption()
        parameter.encryption.key_vault_properties = encryption_config

    if minimum_tls_version:
        parameter.minimum_tls_version = minimum_tls_version

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=parameter
    ).result()

    return client.get(resource_group_name, namespace_name)


def cli_namespace_update(instance, tags=None, sku=None, capacity=None, minimum_tls_version=None):
    if tags is not None:
        instance.tags = tags

    if sku is not None:
        instance.sku.name = sku
        instance.sku.tier = sku

    if capacity is not None:
        instance.sku.capacity = capacity

    if minimum_tls_version:
        instance.minimum_tls_version = minimum_tls_version

    return instance


def cli_namespace_list(cmd, client, resource_group_name=None):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_SERVICEBUS, min_api='2021-06-01-preview'):
        if resource_group_name:
            return client.list_by_resource_group(resource_group_name=resource_group_name)

        return client.list()


def cli_namespace_exists(cmd, client, name):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_SERVICEBUS, min_api='2021-06-01-preview'):
        return client.check_name_availability(parameters={'name': name})


# Namespace Authorization rule:
def cli_namespaceautho_create(cmd, client, resource_group_name, namespace_name, name, rights=None):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_SERVICEBUS, min_api='2021-06-01-preview'):
        from azure.cli.command_modules.servicebus._utils import accessrights_converter
        return client.create_or_update_authorization_rule(
            resource_group_name=resource_group_name,
            namespace_name=namespace_name,
            authorization_rule_name=name,
            parameters={'rights': accessrights_converter(rights)})


# Namespace Authorization rule:
def cli_namespaceautho_update(cmd, instance, rights):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_SERVICEBUS, min_api='2021-06-01-preview'):
        from azure.cli.command_modules.servicebus._utils import accessrights_converter
        instance.rights = accessrights_converter(rights)
        return instance


def cli_keys_renew(client, resource_group_name, namespace_name, name, key_type, key=None):
    return client.regenerate_keys(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        authorization_rule_name=name,
        parameters={'key_type': key_type, 'key': key}
    )

# Rule Region
def cli_rules_create(cmd, client, resource_group_name, namespace_name, topic_name, subscription_name, rule_name,
                     action_sql_expression=None, action_compatibility_level=None, action_requires_preprocessing=None,
                     filter_sql_expression=None, filter_requires_preprocessing=None, correlation_id=None,
                     message_id=None, to=None, reply_to=None, label=None, session_id=None, reply_to_session_id=None,
                     content_type=None, requires_preprocessing=None, filter_type=None, tags=None):

    Rule = cmd.get_models('Rule', resource_type=ResourceType.MGMT_SERVICEBUS)
    Action = cmd.get_models('Action', resource_type=ResourceType.MGMT_SERVICEBUS)
    SqlFilter = cmd.get_models('SqlFilter', resource_type=ResourceType.MGMT_SERVICEBUS)
    CorrelationFilter = cmd.get_models('CorrelationFilter', resource_type=ResourceType.MGMT_SERVICEBUS)
    parameters = Rule()

    if filter_type:
        parameters.filter_type = filter_type

    if filter_type == 'SqlFilter' or filter_type is None:
        parameters.sql_filter = SqlFilter(
            sql_expression=filter_sql_expression,
            requires_preprocessing=filter_requires_preprocessing)

    if filter_type == 'CorrelationFilter':
        parameters.correlation_filter = CorrelationFilter(
            properties=tags,
            correlation_id=correlation_id,
            to=to,
            message_id=message_id,
            reply_to=reply_to,
            label=label,
            session_id=session_id,
            reply_to_session_id=reply_to_session_id,
            content_type=content_type,
            requires_preprocessing=requires_preprocessing)

    if action_sql_expression or action_compatibility_level or action_requires_preprocessing:
        parameters.action = Action(
            sql_expression=action_sql_expression,
            compatibility_level=action_compatibility_level,
            requires_preprocessing=action_requires_preprocessing
        )
    return client.create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        topic_name=topic_name,
        subscription_name=subscription_name,
        rule_name=rule_name,
        parameters=parameters)


# Rule Region
def cli_rules_update(cmd, instance,
                     action_sql_expression=None, action_compatibility_level=None, action_requires_preprocessing=None,
                     filter_sql_expression=None, filter_requires_preprocessing=None, correlation_id=None,
                     message_id=None, to=None, reply_to=None, label=None, session_id=None, reply_to_session_id=None,
                     content_type=None, requires_preprocessing=None, tags=None):

    if cmd.supported_api_version(resource_type=ResourceType.MGMT_SERVICEBUS, min_api='2021-06-01-preview'):
        if action_sql_expression:
            instance.action.sql_expression = action_sql_expression

        if action_compatibility_level:
            instance.action.compatibility_level = action_compatibility_level

    if action_requires_preprocessing is not None:
        instance.action.requires_preprocessing = action_requires_preprocessing

    if filter_sql_expression:
        instance.sql_filter.sql_expression = filter_sql_expression

    if filter_requires_preprocessing is not None:
        instance.sql_filter.requires_preprocessing = filter_requires_preprocessing

    if correlation_id:
        instance.correlation_filter.correlation_id = correlation_id

    if tags:
        instance.correlation_filter.properties = tags

    if to:
        instance.correlation_filter.to = to

    if message_id:
        instance.correlation_filter.message_id = message_id

    if reply_to:
        instance.correlation_filter.reply_to = reply_to

    if label:
        instance.correlation_filter.label = label

    if session_id:
        instance.correlation_filter.session_id = session_id

    if reply_to_session_id:
        instance.correlation_filter.reply_to_session_id = reply_to_session_id

    if content_type:
        instance.correlation_filter.content_type = content_type

    if requires_preprocessing is not None:
        instance.correlation_filter.requires_preprocessing = requires_preprocessing

    return instance


# DisasterRecoveryConfigs Region
def cli_georecovery_alias_create(cmd, client, resource_group_name, namespace_name, alias,
                                 partner_namespace, alternate_name=None):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_SERVICEBUS, min_api='2021-06-01-preview'):
        parameters = {
            'partner_namespace': partner_namespace,
            'alternate_name': alternate_name,
        }
        return client.create_or_update(resource_group_name=resource_group_name, namespace_name=namespace_name,
                                       alias=alias, parameters=parameters)


def cli_georecovery_alias_exists(cmd, client, resource_group_name, namespace_name, name):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_SERVICEBUS, min_api='2021-06-01-preview'):
        return client.check_name_availability(resource_group_name=resource_group_name,
                                              namespace_name=namespace_name,
                                              parameters={'name': name})


# MigrationConfigs Region
def cli_migration_start(cmd, client, resource_group_name, namespace_name,
                        target_namespace, post_migration_name, config_name="$default"):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_SERVICEBUS, min_api='2021-06-01-preview'):
        import time
        parameters = {
            'target_namespace': target_namespace,
            'post_migration_name': post_migration_name
        }
        client.begin_create_and_start_migration(resource_group_name, namespace_name, config_name, parameters)
        getresponse = client.get(resource_group_name, namespace_name, config_name)

        # pool till Provisioning state is succeeded
        while getresponse.provisioning_state != 'Succeeded':
            time.sleep(30)
            getresponse = client.get(resource_group_name, namespace_name, config_name)

        # poll on the 'pendingReplicationOperationsCount' to be 0 or none
        while getresponse.pending_replication_operations_count != 0 and getresponse.pending_replication_operations_count is not None:
            time.sleep(30)
            getresponse = client.get(resource_group_name, namespace_name, config_name)

        return client.get(resource_group_name, namespace_name, config_name)


def cli_migration_show(cmd, client, resource_group_name, namespace_name, config_name="$default"):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_SERVICEBUS, min_api='2021-06-01-preview'):
        return client.get(resource_group_name, namespace_name, config_name)


def cli_migration_complete(client, resource_group_name, namespace_name, config_name="$default"):
    return client.complete_migration(resource_group_name, namespace_name, config_name)


iso8601pattern = re.compile("^P(?!$)(\\d+Y)?(\\d+M)?(\\d+W)?(\\d+D)?(T(?=\\d)(\\d+H)?(\\d+M)?(\\d+.)?(\\d+S)?)?$")
timedeltapattern = re.compile("^\\d+:\\d+:\\d+$")


def return_valid_duration(update_value, current_value=None):
    from datetime import timedelta
    from isodate import parse_duration
    from isodate import Duration
    from azure.cli.core.azclierror import InvalidArgumentValueError
    from azure.cli.command_modules.servicebus.constants import DURATION_SECS, DURATION_MIN, DURATION_DAYS
    if update_value is not None:
        value_toreturn = update_value
    else:
        return current_value

    if iso8601pattern.match(value_toreturn):
        try:
            time_duration = parse_duration(value_toreturn)
        except:
            raise InvalidArgumentValueError("Unable to parse provided ISO 8601 format duration %r" % value_toreturn)

        if isinstance(time_duration, timedelta):
            if time_duration <= timedelta(days=DURATION_DAYS, minutes=DURATION_MIN, seconds=DURATION_SECS):
                return time_duration
            return timedelta(days=DURATION_DAYS, minutes=DURATION_MIN, seconds=DURATION_SECS)

        if isinstance(time_duration, Duration):
            # for some reason 2 duration objects cannot be compared, must find a fix
            return time_duration

        return value_toreturn

    if timedeltapattern.match(value_toreturn):
        day, minute, seconds = value_toreturn.split(":")
        if timedelta(days=int(day), minutes=int(minute), seconds=int(seconds)) <= timedelta(days=DURATION_DAYS,
                                                                                            minutes=DURATION_MIN,
                                                                                            seconds=DURATION_SECS):
            return timedelta(days=int(day), minutes=int(minute), seconds=int(seconds))
        return timedelta(days=DURATION_DAYS, minutes=DURATION_MIN, seconds=DURATION_SECS)

    return update_value


# to check the timespan value
def return_valid_duration_create(update_value):
    from datetime import timedelta
    from isodate import parse_duration
    from knack.util import CLIError
    from azure.cli.command_modules.servicebus.constants import DURATION_SECS, DURATION_MIN, DURATION_DAYS
    if update_value is not None:
        if iso8601pattern.match(update_value):
            if parse_duration(update_value) > timedelta(days=DURATION_DAYS, minutes=DURATION_MIN, seconds=DURATION_SECS):
                raise CLIError(
                    'duration value should be less than (days:min:secs) 10675199:10085:477581')

        if timedeltapattern.match(update_value):
            day, minute, seconds = update_value.split(":")
            if timedelta(days=int(day), minutes=int(minute), seconds=int(seconds)) <= timedelta(days=DURATION_DAYS, minutes=DURATION_MIN, seconds=DURATION_SECS):
                update_value = timedelta(days=int(day), minutes=int(minute), seconds=int(seconds))
            else:
                raise CLIError(
                    'duration value should be less than timedelta(days=DURATION_DAYS, minutes=DURATION_MIN, seconds=DURATION_SECS)')

    return update_value


# NetwrokRuleSet Region
def cli_networkrule_createupdate(cmd, client, resource_group_name, namespace_name, subnet=None, ip_mask=None, ignore_missing_vnet_service_endpoint=False, action='Allow'):
    NWRuleSetVirtualNetworkRules = cmd.get_models('NWRuleSetVirtualNetworkRules', resource_type=ResourceType.MGMT_SERVICEBUS)
    Subnet = cmd.get_models('Subnet', resource_type=ResourceType.MGMT_SERVICEBUS)
    NWRuleSetIpRules = cmd.get_models('NWRuleSetIpRules', resource_type=ResourceType.MGMT_SERVICEBUS)
    netwrokruleset = client.get_network_rule_set(resource_group_name, namespace_name)

    if netwrokruleset.virtual_network_rules is None:
        netwrokruleset.virtual_network_rules = []

    if netwrokruleset.ip_rules is None:
        netwrokruleset.ip_rules = []

    if subnet:
        netwrokruleset.virtual_network_rules.append(NWRuleSetVirtualNetworkRules(subnet=Subnet(id=subnet),
                                                                                 ignore_missing_vnet_service_endpoint=ignore_missing_vnet_service_endpoint))

    if ip_mask:
        netwrokruleset.ip_rules.append(NWRuleSetIpRules(ip_mask=ip_mask, action=action))

    return client.create_or_update_network_rule_set(resource_group_name, namespace_name, netwrokruleset)


def cli_networkrule_update(client, resource_group_name, namespace_name, public_network_access=None, trusted_service_access_enabled=None,
                           default_action=None):
    networkruleset = client.get_network_rule_set(resource_group_name, namespace_name)

    if trusted_service_access_enabled is not None:
        networkruleset.trusted_service_access_enabled = trusted_service_access_enabled

    if public_network_access:
        networkruleset.public_network_access = public_network_access

    if default_action:
        networkruleset.default_action = default_action

    return client.create_or_update_network_rule_set(resource_group_name, namespace_name, networkruleset)


def cli_networkrule_delete(cmd, client, resource_group_name, namespace_name, subnet=None, ip_mask=None):
    NWRuleSetVirtualNetworkRules = cmd.get_models('NWRuleSetVirtualNetworkRules', resource_type=ResourceType.MGMT_SERVICEBUS)
    NWRuleSetIpRules = cmd.get_models('NWRuleSetIpRules', resource_type=ResourceType.MGMT_SERVICEBUS)

    netwrokruleset = client.get_network_rule_set(resource_group_name, namespace_name)

    if subnet:
        virtualnetworkrule = NWRuleSetVirtualNetworkRules()
        virtualnetworkrule.subnet = subnet

        for vnetruletodelete in netwrokruleset.virtual_network_rules:
            if vnetruletodelete.subnet.id.lower() == subnet.lower():
                virtualnetworkrule.ignore_missing_vnet_service_endpoint = vnetruletodelete.ignore_missing_vnet_service_endpoint
                netwrokruleset.virtual_network_rules.remove(vnetruletodelete)
                break

    if ip_mask:
        ipruletodelete = NWRuleSetIpRules()
        ipruletodelete.ip_mask = ip_mask
        ipruletodelete.action = "Allow"

        if ipruletodelete in netwrokruleset.ip_rules:
            netwrokruleset.ip_rules.remove(ipruletodelete)

    return client.create_or_update_network_rule_set(resource_group_name, namespace_name, netwrokruleset)


def cli_returnnsdetails(cmd, resource_group_name, namespace_name, max_size_in_megabytes):
    from knack.util import CLIError
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    nsclient = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_SERVICEBUS).namespaces
    getnamespace = nsclient.get(resource_group_name=resource_group_name, namespace_name=namespace_name)
    if getnamespace.sku.name == 'Standard' and max_size_in_megabytes not in [1024, 2048, 3072, 4096, 5120]:
        raise CLIError('--max-size on Standard sku namespace only supports upto [1024, 2048, 3072, 4096, 5120] GB')

    if getnamespace.sku.name == 'Premium' and max_size_in_megabytes not in [1024, 2048, 3072, 4096, 5120, 10240, 20480,
                                                                            40960, 81920]:
        raise CLIError(
            '--max-size on Premium sku namespace only supports upto [1024, 2048, 3072, 4096, 5120, 10240, 20480, 40960, 81920] GB')


# Private Endpoint
def _update_private_endpoint_connection_status(cmd, client, resource_group_name, namespace_name,
                                               private_endpoint_connection_name, is_approved=True, description=None):
    from azure.core.exceptions import HttpResponseError
    import time

    PrivateEndpointServiceConnectionStatus = cmd.get_models('PrivateLinkConnectionStatus')

    private_endpoint_connection = client.get(resource_group_name=resource_group_name, namespace_name=namespace_name,
                                             private_endpoint_connection_name=private_endpoint_connection_name)

    old_status = private_endpoint_connection.private_link_service_connection_state.status
    if description:
        private_endpoint_connection.private_link_service_connection_state.description = description

    if old_status != "Approved" or not is_approved:
        private_endpoint_connection.private_link_service_connection_state.status = PrivateEndpointServiceConnectionStatus.APPROVED\
            if is_approved else PrivateEndpointServiceConnectionStatus.REJECTED
        try:
            private_endpoint_connection = client.create_or_update(resource_group_name=resource_group_name,
                                                                  namespace_name=namespace_name,
                                                                  private_endpoint_connection_name=private_endpoint_connection_name,
                                                                  parameters=private_endpoint_connection)
        except HttpResponseError as ex:
            if 'Operation returned an invalid status ''Accepted''' in ex.message:
                time.sleep(30)
                private_endpoint_connection = client.get(resource_group_name=resource_group_name,
                                                         namespace_name=namespace_name,
                                                         private_endpoint_connection_name=private_endpoint_connection_name)

    return private_endpoint_connection


def approve_private_endpoint_connection(cmd, client, resource_group_name, namespace_name,
                                        private_endpoint_connection_name, description=None):

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name=resource_group_name, namespace_name=namespace_name, is_approved=True,
        private_endpoint_connection_name=private_endpoint_connection_name, description=description
    )


def reject_private_endpoint_connection(cmd, client, resource_group_name, namespace_name, private_endpoint_connection_name,
                                       description=None):
    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name=resource_group_name, namespace_name=namespace_name, is_approved=False,
        private_endpoint_connection_name=private_endpoint_connection_name, description=description
    )


def cli_add_identity(cmd, client, resource_group_name, namespace_name, system_assigned=None, user_assigned=None):
    namespace = client.get(resource_group_name, namespace_name)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_SERVICEBUS)
    Identity = cmd.get_models('Identity', resource_type=ResourceType.MGMT_SERVICEBUS)
    UserAssignedIdentity = cmd.get_models('UserAssignedIdentity', resource_type=ResourceType.MGMT_SERVICEBUS)

    identity_id = {}

    if namespace.identity is None:
        namespace.identity = Identity()

    if system_assigned:
        if namespace.identity.type == IdentityType.USER_ASSIGNED:
            namespace.identity.type = IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED

        elif namespace.identity.type == IdentityType.NONE or namespace.identity.type is None:
            namespace.identity.type = IdentityType.SYSTEM_ASSIGNED

    if user_assigned:
        default_user_identity = UserAssignedIdentity()
        identity_id.update(dict.fromkeys(user_assigned, default_user_identity))

        if namespace.identity.user_assigned_identities is None:
            namespace.identity.user_assigned_identities = identity_id
        else:
            namespace.identity.user_assigned_identities.update(identity_id)

        if namespace.identity.type == IdentityType.SYSTEM_ASSIGNED:
            namespace.identity.type = IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED

        elif namespace.identity.type == IdentityType.NONE or namespace.identity.type is None:
            namespace.identity.type = IdentityType.USER_ASSIGNED

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=namespace).result()

    get_namespace = client.get(resource_group_name, namespace_name)

    return get_namespace


def cli_remove_identity(cmd, client, resource_group_name, namespace_name, system_assigned=None, user_assigned=None):
    namespace = client.get(resource_group_name, namespace_name)
    IdentityType = cmd.get_models('ManagedServiceIdentityType', resource_type=ResourceType.MGMT_SERVICEBUS)

    from azure.cli.core import CLIError

    if namespace.identity is None:
        raise CLIError('The namespace does not have identity enabled')

    if system_assigned:
        if namespace.identity.type == IdentityType.SYSTEM_ASSIGNED:
            namespace.identity.type = IdentityType.NONE

        if namespace.identity.type == IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED:
            namespace.identity.type = IdentityType.USER_ASSIGNED

    if user_assigned:
        if namespace.identity.type == IdentityType.USER_ASSIGNED:
            if namespace.identity.user_assigned_identities:
                for x in user_assigned:
                    namespace.identity.user_assigned_identities.pop(x)
                # if all identities are popped off of the dictionary, we disable user assigned identity
                if len(namespace.identity.user_assigned_identities) == 0:
                    namespace.identity.type = IdentityType.NONE
                    namespace.identity.user_assigned_identities = None

        if namespace.identity.type == IdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED:
            if namespace.identity.user_assigned_identities:
                for x in user_assigned:
                    namespace.identity.user_assigned_identities.pop(x)
                # if all identities are popped off of the dictionary, we disable user assigned identity
                if len(namespace.identity.user_assigned_identities) == 0:
                    namespace.identity.type = IdentityType.SYSTEM_ASSIGNED
                    namespace.identity.user_assigned_identities = None

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=namespace).result()

    get_namespace = client.get(resource_group_name, namespace_name)

    return get_namespace


def cli_add_encryption(cmd, client, resource_group_name, namespace_name, encryption_config):
    namespace = client.get(resource_group_name, namespace_name)
    Encryption = cmd.get_models('Encryption', resource_type=ResourceType.MGMT_SERVICEBUS)

    if namespace.encryption:
        if namespace.encryption.key_vault_properties:
            namespace.encryption.key_vault_properties.extend(encryption_config)
        else:
            namespace.encryption.key_vault_properties = encryption_config

    else:
        namespace.encryption = Encryption()
        namespace.encryption.key_vault_properties = encryption_config

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=namespace).result()

    get_namespace = client.get(resource_group_name, namespace_name)

    return get_namespace


def revert(client, resource_group_name, namespace_name, config_name="$default"):
    return client.revert(resource_group_name, namespace_name, config_name)


def cli_remove_encryption(client, resource_group_name, namespace_name, encryption_config):
    namespace = client.get(resource_group_name, namespace_name)

    from azure.cli.core import CLIError

    if namespace.encryption is None:
        raise CLIError('The namespace does not have encryption enabled')

    if namespace.encryption.key_vault_properties:
        for encryption_property in encryption_config:
            if encryption_property in namespace.encryption.key_vault_properties:
                namespace.encryption.key_vault_properties.remove(encryption_property)

    client.begin_create_or_update(
        resource_group_name=resource_group_name,
        namespace_name=namespace_name,
        parameters=namespace).result()

    get_namespace = client.get(resource_group_name, namespace_name)

    return get_namespace
