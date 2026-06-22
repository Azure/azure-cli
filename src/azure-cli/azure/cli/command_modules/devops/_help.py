# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import

helps['artifacts'] = """
type: group
short-summary: Commands for working with Azure Artifacts.
"""

helps['artifacts universal'] = """
type: group
short-summary: Manage Universal Packages.
"""

helps['artifacts universal download'] = """
type: command
short-summary: Download a Universal Package.
examples:
  - name: Download a Universal Package to the current directory.
    text: |
        az artifacts universal download --organization https://dev.azure.com/MyOrg \\
            --project MyProject --scope project --feed MyFeed --name my-package \\
            --version 1.0.0 --path .
  - name: Download a Universal Package on a file system without hard link support.
    text: |
        az artifacts universal download --organization https://dev.azure.com/MyOrg \\
            --project MyProject --scope project --feed MyFeed --name my-package \\
            --version 1.0.0 --path . --no-hardlinks
"""

helps['artifacts universal publish'] = """
type: command
short-summary: Publish a Universal Package.
examples:
  - name: Publish a Universal Package from the current directory.
    text: |
        az artifacts universal publish --organization https://dev.azure.com/MyOrg \\
            --project MyProject --scope project --feed MyFeed --name my-package \\
            --version 1.0.0 --path .
"""
