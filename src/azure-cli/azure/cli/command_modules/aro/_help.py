# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from knack.help_files import helps


helps['aro'] = """
    type: group
    short-summary: Manage Azure Red Hat OpenShift clusters.
"""

helps['aro create'] = """
    type: command
    short-summary: Create a cluster.
"""

helps['aro list'] = """
    type: command
    short-summary: List clusters.
"""

helps['aro delete'] = """
    type: command
    short-summary: Delete a cluster.
"""

helps['aro show'] = """
    type: command
    short-summary: Get the details of a cluster.
"""

helps['aro update'] = """
    type: command
    short-summary: Update a cluster.
"""

helps['aro list-credentials'] = """
    type: command
    short-summary: List credentials of a cluster.
"""
