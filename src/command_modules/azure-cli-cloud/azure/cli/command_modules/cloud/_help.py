# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["cloud"] = """
"type": |-
    group
"short-summary": |-
    Manage registered Azure clouds.
"""

helps["cloud list"] = """
"type": |-
    command
"short-summary": |-
    List registered clouds.
"examples":
-   "name": |-
        List registered clouds.
    "text": |-
        az cloud list --output json
    "crafted": |-
        True
"""

helps["cloud list-profiles"] = """
"type": |-
    command
"short-summary": |-
    List the supported profiles for a cloud.
"""

helps["cloud register"] = """
"type": |-
    command
"short-summary": |-
    Register a cloud.
"long-summary": |-
    When registering a cloud, specify only the resource manager endpoint for the autodetection of other endpoints.
"""

helps["cloud set"] = """
"type": |-
    command
"short-summary": |-
    Set the active cloud.
"examples":
-   "name": |-
        Set the active cloud.
    "text": |-
        az cloud set --name MyRegisteredCloud
    "crafted": |-
        True
"""

helps["cloud show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a registered cloud.
"examples":
-   "name": |-
        Get the details of a registered cloud.
    "text": |-
        az cloud show --output json --query [0]
    "crafted": |-
        True
"""

helps["cloud unregister"] = """
"type": |-
    command
"short-summary": |-
    Unregister a cloud.
"""

helps["cloud update"] = """
"type": |-
    command
"short-summary": |-
    Update the configuration of a cloud.
"""

