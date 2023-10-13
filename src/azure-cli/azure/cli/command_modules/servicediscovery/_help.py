# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps['discovery'] = """
    type: group
    short-summary: Commands to manage service discovery namespaces, services and instances.
"""


for cmd_group_name in ['namespace', 'service', 'instance']:
    helps['discovery {}'.format(cmd_group_name)] = """
        type: group
        short-summary: Commands to manage service discovery {}.
    """.format(cmd_group_name)

helps['discovery namespace create'] = """
    type: command
    short-summary: Command to create service discovery namespace.
    examples:
        - name: Create a service discovery namespace
          text: |-
                az discovery namespace create --namespace MyNs
        - name: Create a service discovery namespace that will be automatically exported to app config
          text: |-
                az discovery namespace create --namespace MyNs --app-config MyAppConfig
"""

helps['discovery namespace show'] = """
    type: command
    short-summary: Command to show service discovery namespace.
    examples:
        - name: Show a service discovery namespace
          text: |-
                az discovery namespace show --namespace MyNs
"""

helps['discovery namespace export'] = """
    type: command
    short-summary: Command to export the instances under a namespace.
    examples:
        - name: Export the instances under a namespace to an Azure App Config service
          text: |-
                az discovery namespace export --namespace MyNs --app-config MyAppConfig
"""


helps['discovery namespace list'] = """
    type: command
    short-summary: Command to list service discovery namespaces.
    examples:
        - name: List service discovery namespaces
          text: |-
                az discovery namespace list
"""

helps['discovery namespace delete'] = """
    type: command
    short-summary: Command to delete service discovery namespace.
    examples:
        - name: Delete a service discovery namespace
          text: |-
                az discovery namespace delete --namespace MyNs
"""


helps['discovery service create'] = """
    type: command
    short-summary: Command to create service discovery service.
    examples:
        - name: Create a service discovery service
          text: |-
                az discovery service create --namespace MyNs --service MyService --description "My first discovery service"
        - name: Create a service discovery service with specified protocol
          text: |-
                az discovery service create --namespace MyNs --service MyService --protocol HTTP --description "My first discovery service"
"""

helps['discovery service show'] = """
    type: command
    short-summary: Command to show service discovery service.
    examples:
        - name: Show a service discovery service
          text: |-
                az discovery service show --namespace MyNs --service MyService
"""

helps['discovery service list'] = """
    type: command
    short-summary: Command to list service discovery service.
    examples:
        - name: List service discovery services
          text: |-
                az discovery service list --namespace MyNs
"""

helps['discovery service delete'] = """
    type: command
    short-summary: Command to delete service discovery service.
    examples:
        - name: Delete a service discovery service
          text: |-
                az discovery service delete --namespace MyNs --service MyService
"""



helps['discovery instance create'] = """
    type: command
    short-summary: Command to create service discovery instance.
    examples:
        - name: Create a service discovery instance target to localhost
          text: |-
                az discovery instance create --namespace MyNs --service MyService --instance MyInstance --address 127.0.0.1 --port 80
        - name: Create a service discovery instance with metadata
          text: |-
                az discovery instance create --namespace MyNs --service MyService --instance MyInstance --address <ServiceIP> --port <ServicePort> --metadata TTL=10
"""

helps['discovery instance show'] = """
    type: command
    short-summary: Command to show service discovery instance.
    examples:
        - name: Show a service discovery instance
          text: |-
                az discovery instance show --namespace MyNs --service MyService --instance MyInstance
"""

helps['discovery instance list'] = """
    type: command
    short-summary: Command to list service discovery instance.
    examples:
        - name: List service discovery instances
          text: |-
                az discovery instance list --namespace MyNs --service MyService
"""

helps['discovery instance delete'] = """
    type: command
    short-summary: Command to delete service discovery instance.
    examples:
        - name: Delete a service discovery instance
          text: |-
                az discovery instance delete --namespace MyNs --service MyService --instance MyInstance
"""