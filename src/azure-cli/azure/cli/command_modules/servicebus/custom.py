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
from knack.log import get_logger
from azure.cli.core.profiles import ResourceType

logger = get_logger(__name__)


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


# DisasterRecoveryConfigs Region
def cli_georecovery_alias_create(cmd, client, resource_group_name, namespace_name, alias,
                                 partner_namespace, alternate_name=None):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_SERVICEBUS, min_api='2021-06-01-preview'):
        parameters = {
            'partner_namespace': partner_namespace,
            'alternate_name': alternate_name,
        }
        logger.warning(
            'the argument parameters from georecovery-alias fail-over cmdlets will be remove in future release.')
        return client.create_or_update(resource_group_name=resource_group_name, namespace_name=namespace_name,
                                       alias=alias, parameters=parameters)


def cli_georecovery_alias_exists(cmd, client, resource_group_name, namespace_name, name):
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_SERVICEBUS, min_api='2021-06-01-preview'):
        return client.check_name_availability(resource_group_name=resource_group_name,
                                              namespace_name=namespace_name,
                                              parameters={'name': name})


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
        logger.warning('Please use ISO8601 duration for timespan inputs. Timespan inputs of format (days:min:seconds) would be deprecated from version 2.49.0.')
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
            logger.warning('Please use ISO8601 duration for timespan inputs. Timespan inputs of format (days:min:seconds) would be deprecated from version 2.49.0.')
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

    logger.warning('This version will be depracated & latest version will release in breaking change release.')
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
