# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["cdn profile"] = """
"type": |-
    group
"short-summary": |-
    Manage CDN profiles to define an edge network.
"""

helps["cdn endpoint start"] = """
"type": |-
    command
"short-summary": |-
    Start a CDN endpoint.
"""

helps["cdn custom-domain"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure CDN Custom Domains to provide custom host names for endpoints.
"""

helps["cdn endpoint purge"] = """
"type": |-
    command
"short-summary": |-
    Purge pre-loaded content for a CDN endpoint.
"""

helps["cdn profile list"] = """
"type": |-
    command
"short-summary": |-
    List CDN profiles.
"""

helps["cdn profile create"] = """
"type": |-
    command
"short-summary": |-
    Create a new CDN profile.
"parameters":
-   "name": |-
        --sku
    "type": |-
        string
    "short-summary": |
        The pricing tier (defines a CDN provider, feature list and rate) of the CDN profile. Defaults to Standard_Akamai.
"""

helps["cdn custom-domain create"] = """
"type": |-
    command
"short-summary": |-
    Create a new custom domain to provide a hostname for a CDN endpoint.
"long-summary": |
    Creates a new custom domain which must point to the hostname of the endpoint. For example, the custom domain hostname cdn.contoso.com would need to have a CNAME record pointing to the hostname of the endpoint related to this custom domain.
"parameters":
-   "name": |-
        --profile-name
    "type": |-
        string
    "short-summary": |-
        Name of the CDN profile which is unique within the resource group.
-   "name": |-
        --endpoint-name
    "type": |-
        string
    "short-summary": |-
        Name of the endpoint under the profile which is unique globally.
-   "name": |-
        --hostname
    "type": |-
        string
    "short-summary": |-
        The host name of the custom domain. Must be a domain name.
"""

helps["cdn custom-domain show"] = """
"type": |-
    command
"short-summary": |-
    Show details for the custom domain of a CDN.
"""

helps["cdn endpoint create"] = """
"type": |-
    command
"short-summary": |-
    Create a named endpoint to connect to a CDN.
"""

helps["cdn edge-node"] = """
"type": |-
    group
"short-summary": |-
    View all available CDN edge nodes.
"""

helps["cdn endpoint load"] = """
"type": |-
    command
"short-summary": |-
    Pre-load content for a CDN endpoint.
"""

helps["cdn custom-domain delete"] = """
"type": |-
    command
"short-summary": |-
    Delete the custom domain of a CDN.
"""

helps["cdn profile update"] = """
"type": |-
    command
"short-summary": |-
    Update a CDN profile.
"""

helps["cdn endpoint"] = """
"type": |-
    group
"short-summary": |-
    Manage CDN endpoints.
"""

helps["cdn endpoint list"] = """
"type": |-
    command
"short-summary": |-
    List available endpoints for a CDN.
"""

helps["cdn profile delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a CDN profile.
"""

helps["cdn"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Content Delivery Networks (CDNs).
"""

helps["cdn endpoint stop"] = """
"type": |-
    command
"short-summary": |-
    Stop a CDN endpoint.
"""

helps["cdn endpoint update"] = """
"type": |-
    command
"short-summary": |-
    Update a CDN endpoint to manage how content is delivered.
"""

helps["cdn origin"] = """
"type": |-
    group
"short-summary": |-
    List or show existing origins related to CDN endpoints.
"""

helps["cdn endpoint delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a CDN endpoint.
"""

