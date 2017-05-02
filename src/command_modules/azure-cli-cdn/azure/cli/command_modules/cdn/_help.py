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

helps['cdn endpoint delete'] = """
    type: command
    examples:
        - name: Delete a CDN endpoint
          text: >
            az cdn endpoint delete -g group -n endpoint --profile-name profile-name
"""

helps['cdn endpoint start'] = """
    type: command
    examples:
        - name: Start a CDN endpoint
          text: >
            az cdn endpoint start -g group -n endpoint --profile-name profile-name
"""

helps['cdn endpoint stop'] = """
    type: command
    examples:
        - name: Stop a CDN endpoint
          text: >
            az cdn endpoint stop -g group -n endpoint --profile-name profile-name
"""

helps['cdn endpoint load'] = """
    type: command
    examples:
        - name: Pre-load content for Javascript and CSS styles
          text: >
            az cdn endpoint load -g group -n endpoint --profile-name profile-name --content-paths \\
                '/scripts/app.js' '/styles/main.css'
"""

helps['cdn endpoint purge'] = """
    type: command
    examples:
        - name: Purge content for Javascript and CSS styles
          text: >
            az cdn endpoint load -g group -n endpoint --profile-name profile-name --content-paths \\
                '/scripts/app.js' '/styles/*'
"""

helps['cdn endpoint list'] = """
    type: command
    examples:
        - name: List all endpoints within a given CDN profile
          text: >
            az cdn endpoint list -g group --profile-name profile-name
"""

helps['cdn endpoint load'] = """
    type: command
    examples:
        - name: Stop a CDN endpoint
          text: >
            az cdn endpoint load -g group -n endpoint --profile-name profile-name --content-paths \\
                '/index.html' '/scripts/app.js' '/styles/main.css'
"""

helps['cdn custom-domain create'] = """
    type: command
    examples:
        - name: Create a custom domain within an endpoint and profile
          text: >
            az cdn custom-domain create -g group --endpoint-name endpoint --profile-name profile \\
                -n domain-name --host-name www.example.com
"""

helps['cdn custom-domain delete'] = """
    type: command
    examples:
        - name: Delete a custom domain within an endpoint and profile
          text: >
            az cdn custom-domain delete -g group --endpoint-name endpoint --profile-name profile \\
                -n domain-name
"""

helps['cdn custom-domain show'] = """
    type: command
    examples:
        - name: Show details of a custom domain within an endpoint and profile
          text: >
            az cdn custom-domain show -g group --endpoint-name endpoint --profile-name profile \\
                -n domain-name
"""