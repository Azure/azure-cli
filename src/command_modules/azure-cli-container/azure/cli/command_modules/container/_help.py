# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["container exec"] = """
"type": |-
    command
"short-summary": |-
    Execute a command from within a running container of a container group.
"long-summary": |-
    The most common use case is to open an interactive bash shell. See examples below. This command is currently not supported for Windows machines.
"examples":
-   "name": |-
        Execute a command from within a running container of a container group.
    "text": |-
        az container exec --name mynginx --exec-command "/bin/bash" --resource-group MyResourceGroup
"""

helps["container attach"] = """
"type": |-
    command
"short-summary": |-
    Attach local standard output and error streams to a container in a container group.
"examples":
-   "name": |-
        Attach local standard output and error streams to a container in a container group.
    "text": |-
        az container attach --name MyContainerGroup --resource-group MyResourceGroup
"""

helps["container"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Container Instances.
"""

helps["container list"] = """
"type": |-
    command
"short-summary": |-
    List container groups.
"""

helps["container export"] = """
"type": |-
    command
"short-summary": |-
    Export a container group in yaml format.
"""

helps["container delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a container group.
"examples":
-   "name": |-
        Delete a container group.
    "text": |-
        az container delete --name MyContainerGroup --yes  --resource-group MyResourceGroup
"""

helps["container show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a container group.
"examples":
-   "name": |-
        Get the details of a container group.
    "text": |-
        az container show --name MyContainerGroup --query [0] --resource-group MyResourceGroup
"""

helps["container create"] = """
"type": |-
    command
"short-summary": |-
    Create a container group.
"examples":
-   "name": |-
        Create a container group.
    "text": |-
        az container create --dns-name-label contoso --ports 8081 --registry-password password --registry-login-server <registry-login-server> --image myimage:latest --name myapp --registry-username <registry-username> --cpu 1 --resource-group MyResourceGroup --memory 1
"""

helps["container logs"] = """
"type": |-
    command
"short-summary": |-
    Examine the logs for a container in a container group.
"examples":
-   "name": |-
        Examine the logs for a container in a container group.
    "text": |-
        az container logs --name MyContainerGroup --resource-group MyResourceGroup
"""

