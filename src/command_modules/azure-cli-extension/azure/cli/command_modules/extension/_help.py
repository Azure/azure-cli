# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["extension add"] = """
"type": |-
    command
"short-summary": |-
    Add an extension.
"examples":
-   "name": |-
        Add an extension.
    "text": |-
        az extension add --name anextension
"""

helps["extension list-available"] = """
"type": |-
    command
"short-summary": |-
    List publicly available extensions.
"""

helps["extension update"] = """
"type": |-
    command
"short-summary": |-
    Update an extension.
"examples":
-   "name": |-
        Update an extension.
    "text": |-
        az extension update --name anextension
"""

helps["extension list"] = """
"type": |-
    command
"short-summary": |-
    List the installed extensions.
"""

helps["extension"] = """
"type": |-
    group
"short-summary": |-
    Manage and update CLI extensions.
"""

helps["extension remove"] = """
"type": |-
    command
"short-summary": |-
    Remove an extension.
"examples":
-   "name": |-
        Remove an extension.
    "text": |-
        az extension remove --name MyExtension
"""

helps["extension show"] = """
"type": |-
    command
"short-summary": |-
    Show an extension.
"examples":
-   "name": |-
        Show an extension.
    "text": |-
        az extension show --name MyExtension
"""

