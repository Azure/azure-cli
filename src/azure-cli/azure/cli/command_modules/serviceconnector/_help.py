# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps
from ._resource_config import (
    AUTH_TYPE,
    RESOURCE,
    SOURCE_RESOURCES,
    SOURCE_RESOURCES_PARAMS,
    TARGET_RESOURCES,
    TARGET_RESOURCES_PARAMS,
    SUPPORTED_AUTH_TYPE
)

from ._utils import should_load_source
from ._addon_factory import AddonFactory


def get_source_resource_params(resource):
    params = SOURCE_RESOURCES_PARAMS.get(resource).values()

    param_str = ''
    for param in params:
        option = param.get('options')[-1]
        placeholder = param.get('placeholder')
        param_str += '{} {} '.format(option, placeholder)

    return param_str.strip()


def get_target_resource_params(resource):
    params = TARGET_RESOURCES_PARAMS.get(resource).values()

    param_str = ''
    for param in params:
        option = param.get('options')[-1]
        placeholder = param.get('placeholder')
        param_str += '{} {} '.format(option, placeholder)

    return param_str.strip()


def get_auth_info_params(auth_type):
    auth_params_map = {
        AUTH_TYPE.Secret: '--secret name=XX secret=XX',
        AUTH_TYPE.SecretAuto: '--secret',
        AUTH_TYPE.SystemIdentity: '--system-identity',
        AUTH_TYPE.ServicePrincipalSecret: '--service-principal client-id=XX object-id=XX secret=XX',
        AUTH_TYPE.UserIdentity: '--user-identity client-id=XX subs-id=XX'
    }

    return auth_params_map.get(auth_type)


def get_source_display_name(sourcename):
    display_name = sourcename
    if sourcename == RESOURCE.SpringCloud.value:
        display_name = 'spring app'
    return display_name


for source in SOURCE_RESOURCES:
    if not should_load_source(source):
        continue

    source_id = SOURCE_RESOURCES.get(source)
    source_params = get_source_resource_params(source)
    connection_id = ('/subscriptions/{subscription}/resourceGroups/{source_resource_group}/providers/'
                     'Microsoft.Web/sites/{site}/providers/Microsoft.ServiceLinker/linkers/{linker}')
    source_display_name = get_source_display_name(source.value)

    helps['{source} connection'.format(source=source.value)] = """
        type: group
        short-summary: Commands to manage {source_display_name} connections
    """.format(source_display_name=source_display_name)

    helps['{source} connection list-support-types'.format(source=source.value)] = """
        type: command
        short-summary: List client types and auth types supported by {source_display_name} connections.
        examples:
          - name: List all {source_display_name} supported target resource types and auth types
            text: |-
                  az {source} connection list-support-types -o table
          - name: List {source_display_name} supported auth types for a specific target resource type
            text: |-
                  az {source} connection list-support-types --target-type storage-blob -o table
    """.format(source=source.value, source_display_name=source_display_name)

    helps['{source} connection list'.format(source=source.value)] = """
      type: command
      short-summary: List connections of a {source_display_name}.
      examples:
        - name: List {source_display_name} connections interactively
          text: |-
                 az {source} connection list
        - name: List {source_display_name} connections by source resource name
          text: |-
                 az {source} connection list {source_params}
        - name: List {source_display_name} connections by source resource id
          text: |-
                 az {source} connection list --source-id {source_id}
    """.format(
        source=source.value,
        source_params=source_params,
        source_id=source_id,
        source_display_name=source_display_name)

    helps['{source} connection delete'.format(source=source.value)] = """
      type: command
      short-summary: Delete a {source_display_name} connection.
      examples:
        - name: Delete a {source_display_name} connection interactively
          text: |-
                 az {source} connection delete
        - name: Delete a {source_display_name} connection by connection name
          text: |-
                 az {source} connection delete {source_params} --connection MyConnection
        - name: Delete a {source_display_name} connection by connection id
          text: |-
                 az {source} connection delete --id {connection_id}
    """.format(
        source=source.value,
        source_params=source_params,
        connection_id=connection_id,
        source_display_name=source_display_name)

    helps['{source} connection list-configuration'.format(source=source.value)] = """
      type: command
      short-summary: List source configurations of a {source_display_name} connection.
      examples:
        - name: List a connection's source configurations interactively
          text: |-
                 az {source} connection list-configuration
        - name: List a connection's source configurations by connection name
          text: |-
                 az {source} connection list-configuration {source_params} --connection MyConnection
        - name: List a connection's source configurations by connection id
          text: |-
                 az {source} connection list-configuration --id {connection_id}
    """.format(
        source=source.value,
        source_params=source_params,
        connection_id=connection_id,
        source_display_name=source_display_name)

    helps['{source} connection validate'.format(source=source.value)] = """
      type: command
      short-summary: Validate a {source_display_name} connection.
      examples:
        - name: Validate a connection interactively
          text: |-
                 az {source} connection validate
        - name: Validate a connection by connection name
          text: |-
                 az {source} connection validate {source_params} --connection MyConnection
        - name: Validate a connection by connection id
          text: |-
                 az {source} connection validate --id {connection_id}
    """.format(
        source=source.value,
        source_params=source_params,
        connection_id=connection_id,
        source_display_name=source_display_name)

    helps['{source} connection wait'.format(source=source.value)] = """
      type: command
      short-summary: Place the CLI in a waiting state until a condition of the connection is met.
      examples:
          - name: Wait until the connection is successfully created.
            text: |-
                   az {source} connection wait --id {connection_id} --created
    """.format(source=source.value, connection_id=connection_id)

    helps['{source} connection show'.format(source=source.value)] = """
      type: command
      short-summary: Get the details of a {source_display_name} connection.
      examples:
          - name: Get a connection interactively
            text: |-
                   az {source} connection show
          - name: Get a connection by connection name
            text: |-
                   az {source} connection show {source_params} --connection MyConnection
          - name: Get a connection by connection id
            text: |-
                   az {source} connection show --id {connection_id}
    """.format(
        source=source.value,
        source_params=source_params,
        connection_id=connection_id,
        source_display_name=source_display_name)

    helps['{source} connection create'.format(source=source.value)] = """
      type: group
      short-summary: Create a connection between a {source_display_name} and a target resource
    """.format(source_display_name=source_display_name)

    helps['{source} connection update'.format(source=source.value)] = """
      type: group
      short-summary: Update a {source_display_name} connection
    """.format(source_display_name=source_display_name)

    # use SUPPORTED_AUTH_TYPE to decide target resource, as some
    # target resources are not avialable for certain source resource
    supported_target_resources = list(SUPPORTED_AUTH_TYPE.get(source).keys())
    supported_target_resources.remove(RESOURCE.ConfluentKafka)
    for target in supported_target_resources:
        target_id = TARGET_RESOURCES.get(target)

        # target resource params
        target_params = get_target_resource_params(target)

        # auth info params
        auth_types = SUPPORTED_AUTH_TYPE.get(source).get(target)
        auth_params = get_auth_info_params(auth_types[0])

        # auth info params in help message
        secret_param = '''
            - name: --secret
              short-summary: The secret auth info
              long-summary: |
                Usage: --secret name=XX secret=XX
                       --secret name=XX secret-uri=XX
                       --secret name=XX secret-name=XX

                name    : Required. Username or account name for secret auth.
                secret  : One of <secret, secret-uri, secret-name> is required. Password or account key for secret auth.
                secret-uri  : One of <secret, secret-uri, secret-name> is required. Keyvault secret uri which stores password.
                secret-name : One of <secret, secret-uri, secret-name> is required. Keyvault secret name which stores password. It's for AKS only.
        ''' if AUTH_TYPE.Secret in auth_types else ''
        secret_auto_param = '''
            - name: --secret
              short-summary: The secret auth info
              long-summary: |
                Usage: --secret

        ''' if AUTH_TYPE.SecretAuto in auth_types else ''
        system_identity_param = ''
        if AUTH_TYPE.SystemIdentity in auth_types:
            if target in {RESOURCE.MysqlFlexible}:
                system_identity_param = '''
            - name: --system-identity
              short-summary: The system assigned identity auth info
              long-summary: |
                Usage: --system-identity mysql-identity-id=xx

                mysql-identity-id      : Optional. ID of identity used for MySQL flexible server AAD Authentication. Ignore it if you are the server AAD administrator.
            '''
            else:
                system_identity_param = '''
            - name: --system-identity
              short-summary: The system assigned identity auth info
              long-summary: |
                Usage: --system-identity

            '''
        user_identity_param = '''
            - name: --user-identity
              short-summary: The user assigned identity auth info
              long-summary: |
                Usage: --user-identity client-id=XX subs-id=XX

                client-id      : Required. Client id of the user assigned identity.
                subs-id        : Required. Subscription id of the user assigned identity.
        ''' if AUTH_TYPE.UserIdentity in auth_types else ''
        service_principal_param = '''
            - name: --service-principal
              short-summary: The service principal auth info
              long-summary: |
                Usage: --service-principal client-id=XX secret=XX

                client-id      : Required. Client id of the service principal.
                object-id      : Optional. Object id of the service principal (Enterprise Application).
                secret         : Required. Secret of the service principal.
        ''' if AUTH_TYPE.ServicePrincipalSecret in auth_types else ''

        # create with `--new` examples
        provision_example = '''
            - name: Create a new {target} and connect {source_display_name} to it interactively
              text: |-
                    az {source} connection create {target} --new
            - name: Create a new {target} and connect {source_display_name} to it
              text: |-
                    az {source} connection create {target} --source-id {source_id} --new
        '''.format(
            source=source.value,
            target=target.value,
            source_id=source_id,
            source_display_name=source_display_name) if target in AddonFactory else ''

        helps['{source} connection create {target}'.format(source=source.value, target=target.value)] = """
          type: command
          short-summary: Create a {source_display_name} connection to {target}.
          parameters:
            {secret_param}
            {secret_auto_param}
            {system_identity_param}
            {user_identity_param}
            {service_principal_param}
          examples:
            - name: Create a connection between {source_display_name} and {target} interactively
              text: |-
                     az {source} connection create {target}
            - name: Create a connection between {source_display_name} and {target} with resource name
              text: |-
                     az {source} connection create {target} {source_params} {target_params} {auth_params}
            - name: Create a connection between {source_display_name} and {target} with resource id
              text: |-
                     az {source} connection create {target} --source-id {source_id} --target-id {target_id} {auth_params}
            {provision_example}
        """.format(
            source=source.value,
            target=target.value,
            source_id=source_id,
            target_id=target_id,
            secret_param=secret_param,
            secret_auto_param=secret_auto_param,
            system_identity_param=system_identity_param,
            user_identity_param=user_identity_param,
            service_principal_param=service_principal_param,
            source_params=source_params,
            target_params=target_params,
            auth_params=auth_params,
            provision_example=provision_example,
            source_display_name=source_display_name)

        helps['{source} connection update {target}'.format(source=source.value, target=target.value)] = """
          type: command
          short-summary: Update a {source_display_name} to {target} connection.
          parameters:
            {secret_param}
            {secret_auto_param}
            {system_identity_param}
            {user_identity_param}
            {service_principal_param}
          examples:
            - name: Update the client type of a connection with resource name
              text: |-
                     az {source} connection update {target} {source_params} --connection MyConnection --client-type dotnet
            - name: Update the client type of a connection with resource id
              text: |-
                     az {source} connection update {target} --id {connection_id} --client-type dotnet
        """.format(
            source=source.value,
            target=target.value,
            secret_param=secret_param,
            secret_auto_param=secret_auto_param,
            system_identity_param=system_identity_param,
            user_identity_param=user_identity_param,
            service_principal_param=service_principal_param,
            source_params=source_params,
            connection_id=connection_id,
            source_display_name=source_display_name)

    # special target resource, independent implementation
    target = RESOURCE.ConfluentKafka
    server_params = ('--bootstrap-server xxx.eastus.azure.confluent.cloud:9092 '
                     '--kafka-key Name --kafka-secret Secret')
    registry_params = ('--schema-registry https://xxx.eastus.azure.confluent.cloud '
                       '--schema-key Name --schema-secret Secret')

    helps['{source} connection create {target}'.format(source=source.value, target=target.value)] = """
      type: command
      short-summary: Create a {source_display_name} connection to {target}.
      examples:
        - name: Create a connection between {source_display_name} and {target}
          text: |-
                  az {source} connection create {target} {source_params} {server_params} {registry_params}
    """.format(source=source.value,
               target=target.value,
               source_params=source_params,
               server_params=server_params,
               registry_params=registry_params,
               source_display_name=source_display_name)

    helps['{source} connection update {target}'.format(source=source.value, target=target.value)] = """
      type: command
      short-summary: Update a {source_display_name} to {target} connection.
      examples:
        - name: Update the client-type of a bootstrap server connection
          text: |-
                  az {source} connection update {target} {source_params} --connection MyConnection --client python
        - name: Update the auth configurations of a bootstrap server connection
          text: |-
                  az {source} connection update {target} {source_params} --connection MyConnection {server_params}
        - name: Update the client-type of a schema registry connection
          text: |-
                  az {source} connection update {target} {source_params} --connection MyConnection_schema --client python
        - name: Update the auth configurations of a schema registry connection
          text: |-
                  az {source} connection update {target} {source_params} --connection MyConnection_schema {registry_params}
    """.format(source=source.value,
               target=target.value,
               source_params=source_params,
               server_params=server_params,
               registry_params=registry_params,
               source_display_name=source_display_name)
