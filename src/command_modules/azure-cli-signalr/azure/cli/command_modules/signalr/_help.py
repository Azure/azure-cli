# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["signalr list"] = """
"type": |-
    command
"short-summary": |-
    Lists all the SignalR Service under the current subscription.
"""

helps["signalr key list"] = """
"type": |-
    command
"short-summary": |-
    List the access keys for a SignalR Service.
"""

helps["signalr"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure SignalR Service.
"""

helps["signalr show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a SignalR Service.
"""

helps["signalr create"] = """
"type": |-
    command
"short-summary": |-
    Creates a SignalR Service.
"""

helps["signalr delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes a SignalR Service.
"""

helps["signalr key"] = """
"type": |-
    group
"short-summary": |-
    Manage keys for Azure SignalR Service.
"""

helps["signalr key renew"] = """
"type": |-
    command
"short-summary": |-
    Regenerate the access key for a SignalR Service.
"""

