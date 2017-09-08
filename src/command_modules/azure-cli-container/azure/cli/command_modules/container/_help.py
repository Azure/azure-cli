# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['container'] = """
    type: group
    short-summary: (PREVIEW) Manage Azure Container Instances.
"""

helps['container create'] = """
    type: command
    short-summary: Create a container group.
    examples:
        - name: Create a container group with 1 core and 1Gb of memory.
          text: az container create -g MyResourceGroup --name myalpine --image alpine:latest --cpu 1 --memory 1
        - name: Create a container group that runs Windows, with 2 cores and 3.5Gb of memory.
          text: az container create -g MyResourceGroup --name mywinapp --image winappimage:latest --os-type Windows --cpu 2 --memory 3.5
        - name: Create a container group with public IP address.
          text: az container create -g MyResourceGroup --name myalpine --image alpine:latest --ip-address public
        - name: Create a container group that invokes a script upon start.
          text: az container create -g MyResourceGroup --name myalpine --image alpine:latest --command-line "/bin/sh -c '/path to/myscript.sh'"
        - name: Create a container group with environment variables.
          text: az container create -g MyResourceGroup --name myalpine --image alpine:latest -e key1=value1 key2=value2
        - name: Create a container group using container image from Azure Container Registry.
          text: az container create -g MyResourceGroup --name myalpine --image myAcrRegistry.azurecr.io/alpine:latest --registry-password password
        - name: Create a container group using container image from another private container image registry.
          text: az container create -g MyResourceGroup --name myapp --image myimage:latest --cpu 1 --memory 1.5 --registry-login-server myregistry.com --registry-username username --registry-password password
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
    short-summary: Get the details of a container group.
"""

helps['container logs'] = """
    type: command
    short-summary: Examine the logs for a container group.
"""
