# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps
from ._resource_config import (
    AUTH_TYPE,
    SOURCE_RESOURCES,
    TARGET_RESOURCES,
    SUPPORTED_AUTH_TYPE
)


for source in SOURCE_RESOURCES:

    connection_id = ('/subscriptions/{subscription}/resourceGroups/{source_resource_group}/'
                     'providers/Microsoft.Web/sites/{site}/providers/Microsoft.ServiceLinker/linkers/{linker}')

    helps['{source} connection'.format(source=source.value)] = """
        type: group
        short-summary: Manage {source} connections
    """.format(source=source.value)

    helps['{source} connection list-support-types'.format(source=source.value)] = """
        type: command
        short-summary: List target resource types and auth types supported by {source} connections.
        examples:
          - name: List all {source} supported target resource types and auth types
            text: |-
                  az {source} connection list-support-types -o table
          - name: List {source} supported auth types for a specific target resource type
            text: |-
                  az {source} connection list list-support-types --target-type storage-blob -o table
    """.format(source=source.value)

    helps['{source} connection list'.format(source=source.value)] = """
      type: command
      short-summary: List connections of a {source}.
      examples:
        - name: List {source} connections interactively
          text: |-
                 az {source} connection list
        - name: List {source} connections by source resource id
          text: |-
                 az {source} connection list --source-id "ResourceId"
    """.format(source=source.value)

    helps['{source} connection delete'.format(source=source.value)] = """
      type: command
      short-summary: Delete a {source} connection.
      examples:
        - name: Delete a {source} connection interactively
          text: |-
                 az {source} connection delete
        - name: Delete a {source} connection by connection id
          text: |-
                 az {source} connection delete --id {connection_id}
    """.format(source=source.value, connection_id=connection_id)

    helps['{source} connection list-configuration'.format(source=source.value)] = """
      type: command
      short-summary: List source configurations of a {source} connection.
      examples:
        - name: List a connection's source configurations interactively
          text: |-
                 az {source} connection list-configuration
        - name: List a connection's source configurations by connection id
          text: |-
                 az {source} connection list-configuration --id {connection_id}
    """.format(source=source.value, connection_id=connection_id)

    helps['{source} connection validate'.format(source=source.value)] = """
      type: command
      short-summary: Validate a {source} connection.
      examples:
        - name: Validate a connection interactively
          text: |-
                 az {source} connection validate
        - name: Validate a connection by connection id
          text: |-
                 az {source} connection validate --id {connection_id}
    """.format(source=source.value, connection_id=connection_id)

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
      short-summary: Get the details of a {source} connection.
      examples:
          - name: Get a connection interactively
            text: |-
                   az {source} connection show
          - name: Get a connection by connection id
            text: |-
                   az {source} connection show --id {connection_id}
    """.format(source=source.value, connection_id=connection_id)

    helps['{source} connection create'.format(source=source.value)] = """
      type: group
      short-summary: Create a connection between a {source} and a target resource
    """.format(source=source.value)

    helps['{source} connection update'.format(source=source.value)] = """
      type: group
      short-summary: Update a {source} connection
    """.format(source=source.value)

    for target in TARGET_RESOURCES:
        # params in example
        auth_param_map = {
            AUTH_TYPE.Secret: '--secret name=XX secret=XX',
            AUTH_TYPE.SecretAuto: '--auto-secret',
            AUTH_TYPE.SystemIdentity: '--system-identity'
        }
        auth_types = SUPPORTED_AUTH_TYPE.get(source).get(target)
        auth_param = auth_param_map.get(auth_types[0])
        source_id = SOURCE_RESOURCES.get(source)
        target_id = TARGET_RESOURCES.get(target)

        # secet params in help message
        secret_param = '''
            - name: --secret
              short-summary: The secret auth info, no need to provide additional info
              long-summary: |
                Usage: --secret

        ''' if AUTH_TYPE.SecretAuto in auth_types else '''
            - name: --secret
              short-summary: The secret auth info
              long-summary: |
                Usage: --secret name=XX secret=XX

                name    : Required. Username or account name for secret auth.
                secret  : Required. Password or account key for secret auth.
        '''

        helps['{source} connection create {target}'.format(source=source.value, target=target.value)] = """
          type: command
          short-summary: Create a {source} connection to {target}.
          parameters:
            {secret_param}
            - name: --system-identity
              short-summary: The system assigned identity auth info
              long-summary: |
                Usage: --system-identity

            - name: --user-identity
              short-summary: The user assigned identity auth info
              long-summary: |
                Usage: --user-identity client-id=XX subs-id=XX

                client-id      : Required. Client id of the user assigned identity.
                subs-id        : Required. Subscription id of the user assigned identity.
            - name: --service-principal
              short-summary: The service principal auth info
              long-summary: |
                Usage: --service-principal client-id=XX object-id=XX secret=XX

                client-id      : Required. Client id of the service principal.
                object-id      : Required. Object id of the service principal.
                secret         : Required. Secret of the service principal.

          examples:
            - name: Create a connection between {source} and {target} interactively
              text: |-
                     az {source} connection create {target}
            - name: Create a connection between {source} and {target}
              text: |-
                     az {source} connection create {target} --name MyConn --client-type python --source-id {source_id} --target-id {target_id} {auth_param}
            - name: Create a new {target} and connect {source} to it interactively
              text: |-
                     az {source} connection create {target} --new
            - name: Create a new {target} and connect {source} to it
              text: |-
                     az {source} connection create {target} --source-id {source_id} --new
        """.format(
            source=source.value,
            target=target.value,
            secret_param=secret_param,
            source_id=source_id,
            target_id=target_id,
            auth_param=auth_param)

        helps['{source} connection update {target}'.format(source=source.value, target=target.value)] = """
          type: command
          short-summary: Update a {source} to {target} connection.
          parameters:
            {secret_param}
            - name: --system-identity
              short-summary: The system assigned identity auth info
              long-summary: |
                Usage: --system-identity

            - name: --user-identity
              short-summary: The user assigned identity auth info
              long-summary: |
                Usage: --user-identity client-id=XX subs-id=XX

                client-id      : Required. Client id of the user assigned identity.
                subs-id        : Required. Subscription id of the user assigned identity.
            - name: --service-principal
              short-summary: The service principal auth info
              long-summary: |
                Usage: --service-principal client-id=XX object-id=XX secret=XX

                client-id      : Required. Client id of the service principal.
                object-id      : Required. Object id of the service principal.
                secret         : Required. Secret of the service principal.

          examples:
            - name: Update a {source} to {target} connection interactively
              text: |-
                     az {source} connection update {target}
            - name: Update the client type and auth info of a connection
              text: |-
                     az {source} connection update {target} --id {connection_id} --client-type python {auth_param}
        """.format(
            source=source.value,
            target=target.value,
            secret_param=secret_param,
            auth_param=auth_param,
            connection_id=connection_id)
