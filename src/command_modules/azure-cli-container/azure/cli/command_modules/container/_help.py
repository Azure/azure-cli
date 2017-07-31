# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['container'] = """
    type: group
    short-summary: (Preview) Manage Azure Container Instances.
"""

helps['container create'] = """
    type: command
    short-summary: Create a container group.
    examples:
        - name: Create a container group and specify resources required.
          text: az container create -g MyResourceGroup --name MyAlpine --image alpine:latest --cpu 1 --memory 1
        - name: Create a container group with OS type.
          text: az container create -g MyResourceGroup --name MyWinApp --image winappimage:latest --os-type Windows
        - name: Create a container group with public IP address.
          text: az container create -g MyResourceGroup --name MyAlpine --image alpine:latest --ip-address public
        - name: Create a container group with starting command line.
          text: az container create -g MyResourceGroup --name MyAlpine --image alpine:latest --command-line "/bin/sh -c '/path to/myscript.sh'"
        - name: Create a container group with envrionment variables.
          text: az contanier create -g MyResourceGroup --name MyAlpine --image alpine:latest -e key1=value1 key2=value2
        - name: Create a container group using container image from Azure Container Registry.
          text: az container create -g MyResourceGroup --name MyAlpine --image myAcrRegistry.azurecr.io/alpine:latest --registry-password password
        - name: Create a container group using container image from other private container image registry.
          text: az container create -g MyResourceGroup --name MyApp --image myimage:latest --cpu 1 --memory 1.5 --registry-server myregistry.com --registry-username username --registry-password password
"""

helps['container delete'] = """
    type: command
    short-summary: Delete a container group.
"""

helps['container list'] = """
    type: command
    short-summary: List container groups.
"""

helps['container show'] = """
    type: command
    short-summary: Show the details of a container group.
"""

helps['container logs'] = """
    type: command
    short-summary: Tail the log of a container group.
"""
