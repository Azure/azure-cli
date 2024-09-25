# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
This file contains util tools for working with ARM resources.

Initially, they were from msrestazure.tools. Now we import them from azure.mgmt.core.tools.

In the future, we many consider vendoring them or providing our own implementations.
"""

# ATTENTION: Importing from azure.mgmt.core is time-consuming. Only import this file when necessary.

from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id, resource_id
