# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import todict
from azure.cli.core.util import sdk_no_wait
from azure.cli.core.azclierror import (
    RequiredArgumentMissingError,
    ValidationError,
    AzureResponseError
)
from ._resource_config import (
    SUPPORTED_AUTH_TYPE,
    SUPPORTED_CLIENT_TYPE,
    TARGET_RESOURCES
)
from ._validators import (
    get_source_resource_name,
    get_target_resource_name
)
from ._addon_factory import AddonFactory
# pylint: disable=unused-argument


logger = get_logger(__name__)
err_msg = 'Required argument is missing, please provide the arguments: {}'


def connection_list(client,
                    source_resource_group=None,
                    source_id=None,
                    site=None,
                    spring=None, app=None, deployment=None):
    if not source_id:
        raise RequiredArgumentMissingError(err_msg.format('--source-id'))
    return client.list(resource_uri=source_id)


def connection_list_support_types(cmd, client,
                                  target_resource_type=None):
    results = []
    source = get_source_resource_name(cmd)

    targets = SUPPORTED_AUTH_TYPE.get(source).keys()
    if target_resource_type is not None:
        targets = []
        for resource in TARGET_RESOURCES:
            if target_resource_type == resource.value:
                targets.append(resource)
                break

    for target in targets:
        auth_types = SUPPORTED_AUTH_TYPE.get(source).get(target)
        client_types = SUPPORTED_CLIENT_TYPE.get(source).get(target)
        auth_types = [item.value for item in auth_types]
        client_types = [item.value for item in client_types]
        results.append({
            'source': source.value,
            'target': target.value,
            'auth_types': auth_types,
            'client_types': client_types
        })

    return results


def connection_show(client,
                    connection_name=None,
                    source_resource_group=None,
                    source_id=None,
                    indentifier=None,
                    site=None,
                    spring=None, app=None, deployment=None):
    if not source_id or not connection_name:
        raise RequiredArgumentMissingError(err_msg.format('--source-id, --connection-name'))
    return client.get(resource_uri=source_id,
                      linker_name=connection_name)


def connection_delete(client,
                      connection_name=None,
                      source_resource_group=None,
                      source_id=None,
                      indentifier=None,
                      site=None,
                      spring=None, app=None, deployment=None,
                      no_wait=False):
    if not source_id or not connection_name:
        raise RequiredArgumentMissingError(err_msg.format('--source-id, --connection-name'))

    return sdk_no_wait(no_wait,
                       client.begin_delete,
                       resource_uri=source_id,
                       linker_name=connection_name)


def connection_list_configuration(client,
                                  connection_name=None,
                                  source_resource_group=None,
                                  source_id=None,
                                  indentifier=None,
                                  site=None,
                                  spring=None, app=None, deployment=None):
    if not source_id or not connection_name:
        raise RequiredArgumentMissingError(err_msg.format('--source-id, --connection-name'))
    return client.list_configurations(resource_uri=source_id,
                                      linker_name=connection_name)


def connection_validate(client,
                        connection_name=None,
                        source_resource_group=None,
                        source_id=None,
                        indentifier=None,
                        site=None,
                        spring=None, app=None, deployment=None):
    if not source_id or not connection_name:
        raise RequiredArgumentMissingError(err_msg.format('--source-id, --connection-name'))
    return client.begin_validate(resource_uri=source_id,
                                 linker_name=connection_name)


def connection_create(cmd, client,  # pylint: disable=too-many-locals
                      connection_name=None, client_type=None,
                      source_resource_group=None, source_id=None,
                      target_resource_group=None, target_id=None,
                      secret_auth_info=None, secret_auth_info_auto=None,
                      user_identity_auth_info=None, system_identity_auth_info=None,
                      service_principal_auth_info_secret=None,
                      new_addon=False, no_wait=False,
                      site=None,                                             # Resource.WebApp
                      spring=None, app=None, deployment=None,                # Resource.SpringCloud
                      server=None, database=None,                            # Resource.*Postgres, Resource.*Sql*
                      vault=None,                                            # Resource.KeyVault
                      account=None, key_space=None, graph=None, table=None,  # Resource.Cosmos*, Resource.Storage*
                      config_store=None,                                     # Resource.AppConfig
                      namespace=None):                                       # Resource.EventHub

    if not source_id:
        raise RequiredArgumentMissingError(err_msg.format('--source-id'))
    if not new_addon and not target_id:
        raise RequiredArgumentMissingError(err_msg.format('--target-id'))

    all_auth_info = []
    if secret_auth_info is not None:
        all_auth_info.append(secret_auth_info)
    if secret_auth_info_auto is not None:
        all_auth_info.append(secret_auth_info_auto)
    if user_identity_auth_info is not None:
        all_auth_info.append(user_identity_auth_info)
    if system_identity_auth_info is not None:
        all_auth_info.append(system_identity_auth_info)
    if service_principal_auth_info_secret is not None:
        all_auth_info.append(service_principal_auth_info_secret)
    if not new_addon and len(all_auth_info) != 1:
        raise ValidationError('Only one auth info is needed')
    auth_info = all_auth_info[0] if len(all_auth_info) == 1 else None

    parameters = {
        'target_id': target_id,
        'auth_info': auth_info,
        'client_type': client_type
    }

    if new_addon:
        target_type = get_target_resource_name(cmd)
        addon = AddonFactory.get(target_type)(cmd, source_id)
        target_id, auth_info = addon.provision()
        parameters['target_id'] = target_id
        parameters['auth_info'] = auth_info
        logger.warning('Start creating the connection')

        try:
            linker = client.begin_create_or_update(resource_uri=source_id,
                                                   linker_name=connection_name,
                                                   parameters=parameters)
            return linker
        except Exception as e:
            logger.warning('Connection creation failed, start rolling back')
            addon.rollback()
            raise AzureResponseError('{}. Provision failed, please create the target resource '
                                     'manually and then create the connection.'.format(str(e)))

    return sdk_no_wait(no_wait,
                       client.begin_create_or_update,
                       resource_uri=source_id,
                       linker_name=connection_name,
                       parameters=parameters)


def connection_update(client,
                      connection_name=None, client_type=None,
                      source_resource_group=None, source_id=None, indentifier=None,
                      secret_auth_info=None, secret_auth_info_auto=None,
                      user_identity_auth_info=None, system_identity_auth_info=None,
                      service_principal_auth_info_secret=None,
                      no_wait=False,
                      site=None,                                              # Resource.WebApp
                      spring=None, app=None, deployment=None):                # Resource.SpringCloud

    linker = todict(client.get(resource_uri=source_id, linker_name=connection_name))

    all_auth_info = []
    if secret_auth_info is not None:
        all_auth_info.append(secret_auth_info)
    if secret_auth_info_auto is not None:
        all_auth_info.append(secret_auth_info_auto)
    if user_identity_auth_info is not None:
        all_auth_info.append(user_identity_auth_info)
    if system_identity_auth_info is not None:
        all_auth_info.append(system_identity_auth_info)
    if service_principal_auth_info_secret is not None:
        all_auth_info.append(service_principal_auth_info_secret)

    # validate auth info
    if len(all_auth_info) > 1:
        raise ValidationError('Only one auth info is needed')
    # when user provides auth info
    if len(all_auth_info) == 1:
        auth_info = all_auth_info[0]
    # when user doesn't provide auth info and linker is not secret-with-username type
    elif not all_auth_info and (linker.get('authInfo').get('authType') != 'secret' or
                                not linker.get('authInfo').get('name')):
        auth_info = linker.get('authInfo')
    else:
        raise ValidationError('Auth info argument should be provided when '
                              'updating the connection: {}'.format(linker.get('name')))
    # validate the properties to be updated
    if client_type is None and not all_auth_info:
        raise ValidationError('Either client type or auth info should be specified to update')

    parameters = {
        'target_id': linker.get('targetId'),
        'auth_info': auth_info,
        'client_type': client_type or linker.get('clienType'),
    }

    return sdk_no_wait(no_wait,
                       client.begin_create_or_update,
                       resource_uri=source_id,
                       linker_name=connection_name,
                       parameters=parameters)
