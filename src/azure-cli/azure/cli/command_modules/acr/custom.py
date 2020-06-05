# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger

from ._constants import get_managed_sku, get_premium_sku
from ._utils import (
    get_registry_by_name,
    validate_managed_registry,
    validate_sku_update,
    get_resource_group_name_by_registry_name,
    user_confirmation
)
from ._docker_utils import get_login_credentials, EMPTY_GUID
from .network_rule import NETWORK_RULE_NOT_SUPPORTED

logger = get_logger(__name__)
DEF_DIAG_SETTINGS_NAME_TEMPLATE = '{}-diagnostic-settings'
SYSTEM_ASSIGNED_IDENTITY_ALIAS = '[system]'


def acr_check_name(client, registry_name):
    return client.check_name_availability(registry_name)


def acr_list(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def acr_create(cmd,
               client,
               registry_name,
               resource_group_name,
               sku,
               location=None,
               admin_enabled=False,
               default_action=None,
               tags=None,
               workspace=None,
               identity=None,
               key_encryption_key=None,
               public_network_enabled=None):

    if default_action and sku not in get_premium_sku(cmd):
        raise CLIError(NETWORK_RULE_NOT_SUPPORTED)

    if sku not in get_managed_sku(cmd):
        raise CLIError("Classic SKU is no longer supported. Please select a managed SKU.")

    Registry, Sku, NetworkRuleSet = cmd.get_models('Registry', 'Sku', 'NetworkRuleSet')
    registry = Registry(location=location, sku=Sku(name=sku), admin_user_enabled=admin_enabled, tags=tags)
    if default_action:
        registry.network_rule_set = NetworkRuleSet(default_action=default_action)

    if public_network_enabled is not None:
        _configure_public_network_access(cmd, registry, public_network_enabled)

    if identity or key_encryption_key:
        _configure_cmk(cmd, registry, resource_group_name, identity, key_encryption_key)

    lro_poller = client.create(resource_group_name, registry_name, registry)

    if workspace:
        from msrestazure.tools import is_valid_resource_id, resource_id
        from azure.cli.core.commands import LongRunningOperation
        from azure.cli.core.commands.client_factory import get_subscription_id
        acr = LongRunningOperation(cmd.cli_ctx)(lro_poller)
        if not is_valid_resource_id(workspace):
            workspace = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                    resource_group=resource_group_name,
                                    namespace='microsoft.OperationalInsights',
                                    type='workspaces',
                                    name=workspace)
        _create_diagnostic_settings(cmd.cli_ctx, acr, workspace)
        return acr

    return lro_poller


def acr_delete(cmd, client, registry_name, resource_group_name=None, yes=False):
    user_confirmation("Are you sure you want to delete the registry '{}'?".format(registry_name), yes)
    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    return client.delete(resource_group_name, registry_name)


def acr_show(cmd, client, registry_name, resource_group_name=None):
    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    return client.get(resource_group_name, registry_name)


def acr_update_custom(cmd,
                      instance,
                      sku=None,
                      admin_enabled=None,
                      default_action=None,
                      data_endpoint_enabled=None,
                      public_network_enabled=None,
                      tags=None):
    if sku is not None:
        Sku = cmd.get_models('Sku')
        instance.sku = Sku(name=sku)

    if admin_enabled is not None:
        instance.admin_user_enabled = admin_enabled

    if tags is not None:
        instance.tags = tags

    if default_action is not None:
        NetworkRuleSet = cmd.get_models('NetworkRuleSet')
        instance.network_rule_set = NetworkRuleSet(default_action=default_action)

    if data_endpoint_enabled is not None:
        instance.data_endpoint_enabled = data_endpoint_enabled

    if public_network_enabled is not None:
        _configure_public_network_access(cmd, instance, public_network_enabled)

    return instance


def _configure_public_network_access(cmd, registry, enabled):
    PublicNetworkAccess = cmd.get_models('PublicNetworkAccess')
    registry.public_network_access = (PublicNetworkAccess.enabled if enabled else PublicNetworkAccess.disabled)


def acr_update_get(cmd):
    """Returns an empty RegistryUpdateParameters object.
    """
    RegistryUpdateParameters = cmd.get_models('RegistryUpdateParameters')
    return RegistryUpdateParameters()


def acr_update_set(cmd,
                   client,
                   registry_name,
                   resource_group_name=None,
                   parameters=None):
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name, resource_group_name)

    if parameters.network_rule_set and registry.sku.name not in get_premium_sku(cmd):
        raise CLIError(NETWORK_RULE_NOT_SUPPORTED)

    if parameters.data_endpoint_enabled is not None:
        # TODO remove the validation after service side blocking is available
        from ._utils import validate_premium_registry
        _, _ = validate_premium_registry(
            cmd, registry_name, resource_group_name,
            'Dadicated data endpoints are only supported for managed registries in Premium SKU')

    validate_sku_update(cmd, registry.sku.name, parameters.sku)

    return client.update(resource_group_name, registry_name, parameters)


def acr_show_endpoints(cmd,
                       registry_name,
                       resource_group_name=None):
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name, resource_group_name)
    info = {
        'loginServer': registry.login_server,
        'dataEndpoints': []
    }
    if registry.data_endpoint_enabled:
        for host in registry.data_endpoint_host_names:
            info['dataEndpoints'].append({
                'region': host.split('.')[1],
                'endpoint': host,
            })
    else:
        logger.warning('To configure client firewall w/o using wildcard storage blob urls, '
                       'use "az acr update --name %s --data-endpoint-enabled" to enable dedicated '
                       'data endpoints.', registry_name)
        from ._client_factory import cf_acr_replications
        replicate_client = cf_acr_replications(cmd.cli_ctx)
        replicates = list(replicate_client.list(resource_group_name, registry_name))
        for r in replicates:
            info['dataEndpoints'].append({
                'region': r.location,
                'endpoint': '*.blob.' + cmd.cli_ctx.cloud.suffixes.storage_endpoint,
            })
        if not replicates:
            info['dataEndpoints'].append({
                'region': registry.location,
                'endpoint': '*.blob.' + cmd.cli_ctx.cloud.suffixes.storage_endpoint,
            })

    return info


def acr_login(cmd,
              registry_name,
              resource_group_name=None,  # pylint: disable=unused-argument
              tenant_suffix=None,
              username=None,
              password=None,
              expose_token=False):
    if expose_token:
        login_server, _, password = get_login_credentials(
            cmd=cmd,
            registry_name=registry_name,
            tenant_suffix=tenant_suffix,
            username=username,
            password=password)

        logger.warning("You can perform manual login using the provided access token below, "
                       "for example: 'docker login loginServer -u %s -p accessToken'", EMPTY_GUID)

        token_info = {
            "loginServer": login_server,
            "accessToken": password
        }

        return token_info

    tips = "You may want to use 'az acr login -n {} --expose-token' to get an access token, " \
           "which does not require Docker to be installed.".format(registry_name)

    from azure.cli.core.util import in_cloud_console
    if in_cloud_console():
        raise CLIError("This command requires running the docker daemon, "
                       "which is not supported in Azure Cloud Shell. " + tips)

    try:
        docker_command, _ = get_docker_command()
    except CLIError as e:
        logger.warning(tips)
        raise e

    login_server, username, password = get_login_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password)

    # warn casing difference caused by ACR normalizing to lower on login_server
    parts = login_server.split('.')
    if registry_name != parts[0] and registry_name.lower() == parts[0]:
        logger.warning('Uppercase characters are detected in the registry name. When using its server url in '
                       'docker commands, to avoid authentication errors, use all lowercase.')

    from subprocess import PIPE, Popen
    p = Popen([docker_command, "login",
               "--username", username,
               "--password", password,
               login_server], stderr=PIPE)
    _, stderr = p.communicate()
    return_code = p.returncode

    if stderr:
        if b'error storing credentials' in stderr and b'stub received bad data' in stderr \
           and _check_wincred(login_server):
            # Retry once after disabling wincred
            p = Popen([docker_command, "login",
                       "--username", username,
                       "--password", password,
                       login_server])
            p.wait()
        else:
            stderr_messages = stderr.decode()
            # Dismiss the '--password-stdin' warning
            if b'--password-stdin' in stderr:
                errors = [err for err in stderr_messages.split('\n') if err and '--password-stdin' not in err]
                # Will not raise CLIError if there is no error other than '--password-stdin'
                if not errors:
                    return None
                stderr_messages = '\n'.join(errors)
            logger.warning(stderr_messages)

            # Raise error only if docker returns non-zero
            if return_code != 0:
                raise CLIError('Login failed.')

    return None


def acr_show_usage(cmd, client, registry_name, resource_group_name=None):
    _, resource_group_name = validate_managed_registry(cmd,
                                                       registry_name,
                                                       resource_group_name,
                                                       "Usage is only supported for managed registries.")
    return client.list_usages(resource_group_name, registry_name)


def get_docker_command(is_diagnostics_context=False):
    from ._errors import DOCKER_COMMAND_ERROR, DOCKER_DAEMON_ERROR
    docker_command = 'docker'

    from subprocess import PIPE, Popen, CalledProcessError
    try:
        p = Popen([docker_command, "ps"], stdout=PIPE, stderr=PIPE)
        _, stderr = p.communicate()
    except OSError as e:
        logger.debug("Could not run '%s' command. Exception: %s", docker_command, str(e))
        # The executable may not be discoverable in WSL so retry *.exe once
        try:
            docker_command = 'docker.exe'
            p = Popen([docker_command, "ps"], stdout=PIPE, stderr=PIPE)
            _, stderr = p.communicate()
        except OSError as inner:
            logger.debug("Could not run '%s' command. Exception: %s", docker_command, str(inner))
            if is_diagnostics_context:
                return None, DOCKER_COMMAND_ERROR
            raise CLIError(DOCKER_COMMAND_ERROR.get_error_message())
        except CalledProcessError as inner:
            logger.debug("Could not run '%s' command. Exception: %s", docker_command, str(inner))
            if is_diagnostics_context:
                return docker_command, DOCKER_DAEMON_ERROR
            raise CLIError(DOCKER_DAEMON_ERROR.get_error_message())
    except CalledProcessError as e:
        logger.debug("Could not run '%s' command. Exception: %s", docker_command, str(e))
        if is_diagnostics_context:
            return docker_command, DOCKER_DAEMON_ERROR
        raise CLIError(DOCKER_DAEMON_ERROR.get_error_message())

    if stderr:
        if is_diagnostics_context:
            return None, DOCKER_COMMAND_ERROR.set_error_message(stderr.decode())
        raise CLIError(DOCKER_COMMAND_ERROR.set_error_message(stderr.decode()).get_error_message())

    return docker_command, None


def _check_wincred(login_server):
    import platform
    if platform.system() == 'Windows':
        import json
        from os.path import expanduser, isfile, join
        docker_directory = join(expanduser('~'), '.docker')
        config_path = join(docker_directory, 'config.json')
        logger.debug("Docker config file path %s", config_path)
        if isfile(config_path):
            with open(config_path) as input_file:
                content = json.load(input_file)
                input_file.close()
            wincred = content.pop('credsStore', None)
            if wincred and wincred.lower() == 'wincred':
                # Ask for confirmation
                from knack.prompting import prompt_y_n, NoTTYException
                message = "This operation will disable wincred and use file system to store docker credentials." \
                          " All registries that are currently logged in will be logged out." \
                          "\nAre you sure you want to continue?"
                try:
                    if prompt_y_n(message):
                        with open(config_path, 'w') as output_file:
                            json.dump(content, output_file, indent=4)
                            output_file.close()
                        return True
                    return False
                except NoTTYException:
                    return False
            # Don't update config file or retry as this doesn't seem to be a wincred issue
            return False

        import os
        content = {
            "auths": {
                login_server: {}
            }
        }
        try:
            os.makedirs(docker_directory)
        except OSError as e:
            logger.debug("Could not create docker directory '%s'. Exception: %s", docker_directory, str(e))
        with open(config_path, 'w') as output_file:
            json.dump(content, output_file, indent=4)
            output_file.close()
        return True

    return False


def _create_diagnostic_settings(cli_ctx, acr, workspace):
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.mgmt.monitor.models import (DiagnosticSettingsResource, RetentionPolicy,
                                           LogSettings, MetricSettings)
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    client = get_mgmt_service_client(cli_ctx, MonitorManagementClient)
    def_retention_policy = RetentionPolicy(enabled=True, days=0)
    logs = [
        LogSettings(enabled=True, category="ContainerRegistryRepositoryEvents", retention_policy=def_retention_policy),
        LogSettings(enabled=True, category="ContainerRegistryLoginEvents", retention_policy=def_retention_policy)
    ]
    metrics = [MetricSettings(enabled=True, category="AllMetrics", retention_policy=def_retention_policy)]
    parameters = DiagnosticSettingsResource(workspace_id=workspace, metrics=metrics, logs=logs)

    client.diagnostic_settings.create_or_update(resource_uri=acr.id, parameters=parameters,
                                                name=DEF_DIAG_SETTINGS_NAME_TEMPLATE.format(acr.name))


def _configure_cmk(cmd, registry, resource_group_name, identity, key_encryption_key):
    from azure.cli.core.commands.client_factory import get_subscription_id

    if bool(identity) != bool(key_encryption_key):
        raise CLIError("Usage error: --identity and --key-encryption-key must be both supplied")

    identity = _ensure_identity_resource_id(subscription_id=get_subscription_id(cmd.cli_ctx),
                                            resource_group=resource_group_name,
                                            resource=identity)

    identity_client_id = _resolve_identity_client_id(cmd.cli_ctx, identity)

    KeyVaultProperties, EncryptionProperty = cmd.get_models('KeyVaultProperties', 'EncryptionProperty')
    registry.encryption = EncryptionProperty(status='enabled', key_vault_properties=KeyVaultProperties(
        key_identifier=key_encryption_key, identity=identity_client_id))

    ResourceIdentityType, IdentityProperties = cmd.get_models('ResourceIdentityType', 'IdentityProperties')
    registry.identity = IdentityProperties(type=ResourceIdentityType.user_assigned,
                                           user_assigned_identities={identity: {}})


def assign_identity(cmd, client, registry_name, identities, resource_group_name=None):
    from azure.cli.core.commands.client_factory import get_subscription_id
    assign_system_identity, assign_user_identities = _analyze_identities(identities)
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name, resource_group_name)

    IdentityProperties, ResourceIdentityType = cmd.get_models('IdentityProperties', 'ResourceIdentityType')

    # ensure registry.identity is set and is of type IdentityProperties
    registry.identity = registry.identity or IdentityProperties(type=ResourceIdentityType.none)

    if assign_system_identity and registry.identity.type != ResourceIdentityType.system_assigned:
        registry.identity.type = (ResourceIdentityType.system_assigned
                                  if registry.identity.type == ResourceIdentityType.none
                                  else ResourceIdentityType.system_assigned_user_assigned)
    if assign_user_identities and registry.identity.type != ResourceIdentityType.user_assigned:
        registry.identity.type = (ResourceIdentityType.user_assigned
                                  if registry.identity.type == ResourceIdentityType.none
                                  else ResourceIdentityType.system_assigned_user_assigned)

    if assign_user_identities:
        subscription_id = get_subscription_id(cmd.cli_ctx)
        registry.identity.user_assigned_identities = registry.identity.user_assigned_identities or {}

        for r in assign_user_identities:
            r = _ensure_identity_resource_id(subscription_id, resource_group_name, r)
            registry.identity.user_assigned_identities[r] = {}

    return client.update(resource_group_name, registry_name, registry)


def show_identity(cmd, client, registry_name, resource_group_name=None):
    return acr_show(cmd, client, registry_name, resource_group_name).identity


def remove_identity(cmd, client, registry_name, identities, resource_group_name=None):
    from azure.cli.core.commands.client_factory import get_subscription_id
    remove_system_identity, remove_user_identities = _analyze_identities(identities)
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name, resource_group_name)

    ResourceIdentityType = cmd.get_models('ResourceIdentityType')

    # if registry.identity is not set or is none, return the registry.
    if not registry.identity or registry.identity.type == ResourceIdentityType.none:
        raise CLIError("The registry {} has no system or user assigned identities.".format(registry_name))

    if remove_system_identity:
        if registry.identity.type == ResourceIdentityType.user_assigned:
            raise CLIError("The registry does not have a system identity assigned.")
        registry.identity.type = (ResourceIdentityType.none
                                  if registry.identity.type == ResourceIdentityType.system_assigned
                                  else ResourceIdentityType.user_assigned)

    if remove_user_identities:
        subscription_id = get_subscription_id(cmd.cli_ctx)
        registry.identity.user_assigned_identities = registry.identity.user_assigned_identities or {}

        for id_to_remove in remove_user_identities:
            original_identity = id_to_remove
            was_removed = False

            id_to_remove = _ensure_identity_resource_id(subscription_id, resource_group_name, id_to_remove)

            # remove identity if it exists even if case is different
            for existing_identity in registry.identity.user_assigned_identities.copy():
                if existing_identity.lower() == id_to_remove.lower():
                    registry.identity.user_assigned_identities.pop(existing_identity)
                    was_removed = True
                    break

            if not was_removed:
                raise CLIError("The registry does not have specified user identity '{}' assigned, "
                               "so it cannot be removed.".format(original_identity))

        # all user assigned identities are gone
        if not registry.identity.user_assigned_identities:
            registry.identity.user_assigned_identities = None  # required for put
            registry.identity.type = (ResourceIdentityType.none
                                      if registry.identity.type == ResourceIdentityType.user_assigned
                                      else ResourceIdentityType.system_assigned)

    # this method should be named create_or_update as it calls the PUT method
    return client.create(resource_group_name, registry_name, registry)


def show_encryption(cmd, client, registry_name, resource_group_name=None):
    return acr_show(cmd, client, registry_name, resource_group_name).encryption


def rotate_key(cmd, client, registry_name, identity=None, key_encryption_key=None, resource_group_name=None):
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name, resource_group_name)
    if key_encryption_key:
        registry.encryption.key_vault_properties.key_identifier = key_encryption_key
    if identity:
        try:
            import uuid
            uuid.UUID(identity)
            client_id = identity
        except ValueError:
            from azure.cli.core.commands.client_factory import get_subscription_id
            if identity == SYSTEM_ASSIGNED_IDENTITY_ALIAS:
                client_id = 'system'  # reserved word on ACR service
            else:
                identity = _ensure_identity_resource_id(subscription_id=get_subscription_id(cmd.cli_ctx),
                                                        resource_group=resource_group_name,
                                                        resource=identity)
                client_id = _resolve_identity_client_id(cmd.cli_ctx, identity)

        registry.encryption.key_vault_properties.identity = client_id

    return client.update(resource_group_name, registry_name, registry)


def _analyze_identities(identities):
    identities = identities or []
    return SYSTEM_ASSIGNED_IDENTITY_ALIAS in identities, [x for x in identities if x != SYSTEM_ASSIGNED_IDENTITY_ALIAS]


def _ensure_identity_resource_id(subscription_id, resource_group, resource):
    from msrestazure.tools import resource_id, is_valid_resource_id
    if is_valid_resource_id(resource):
        return resource
    return resource_id(subscription=subscription_id,
                       resource_group=resource_group,
                       namespace='Microsoft.ManagedIdentity',
                       type='userAssignedIdentities',
                       name=resource)


def _resolve_identity_client_id(cli_ctx, managed_identity_resource_id):
    from azure.mgmt.msi import ManagedServiceIdentityClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from msrestazure.tools import parse_resource_id

    res = parse_resource_id(managed_identity_resource_id)
    client = get_mgmt_service_client(cli_ctx, ManagedServiceIdentityClient, subscription_id=res['subscription'])
    return client.user_assigned_identities.get(res['resource_group'], res['name']).client_id


def list_private_link_resources(cmd, client, registry_name, resource_group_name=None):
    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    return client.list_private_link_resources(resource_group_name, registry_name)
