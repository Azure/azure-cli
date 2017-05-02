# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-import
from azure.cli.core.help_files import helps

# pylint: disable=line-too-long
helps['cdn'] = """
    type: group
    short-summary: Manage Azure Content Delivery Networks (CDN)
"""

helps['cdn endpoint create'] = """
    type: command
    examples:
        - name: Create an endpoint with a custom domain origin
          text: >
            az cdn endpoint create -g group -n endpoint --profile-name profile \\
                --origin www.example.com
        - name: Create an endpoint with a custom domain origin with HTTP and HTTPS ports
          text: >
            az cdn endpoint create -g group -n endpoint --profile-name profile \\
                --origin www.example.com 88 4444
        - name: Create an endpoint with a custom domain with compression and only HTTPS
          text: >
            az cdn endpoint create -g group -n endpoint --profile-name profile \\
                --origin www.example.com --no-http --enable-compression
"""