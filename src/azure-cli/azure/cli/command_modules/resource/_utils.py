# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re

_subscription_pattern = r"^\/?subscriptions\/(?P<subscription_id>[a-f0-9-]+)"
_resource_group_pattern = r"^\/resourceGroups\/(?P<resource_group_name>[-\w\._\(\)]+)"
_relative_resource_id_pattern = r"^\/providers/(?P<relative_resource_id>.+$)"


def parse_resource_id(resource_id):
    if not resource_id:
        return None, None

    remaining = resource_id

    # Parse subscription_id.
    subscription_match = re.match(_subscription_pattern, remaining, flags=re.IGNORECASE)
    subscription_id = subscription_match.group("subscription_id") if subscription_match else ""
    remaining = remaining[len(subscription_match.group(0)) if subscription_match else 0:]

    # Parse resource_group_name.
    resource_group_match = re.match(_resource_group_pattern, remaining)
    resource_group_name = (
        resource_group_match.group("resource_group_name") if resource_group_match else ""
    )
    remaining = remaining[len(resource_group_match.group(0)) if resource_group_match else 0:]

    # Parse relateive_path.
    relative_resource_id_match = re.match(_relative_resource_id_pattern, remaining)
    relative_resource_id = (
        relative_resource_id_match.group("relative_resource_id")
        if relative_resource_id_match
        else ""
    )

    # The resourceId represents a resource group as a resource with
    # the format /subscription/{subscriptionId}/resourceGroups/{resourceGroupName},
    # which is a subscription-level resource ID. The resourceGroupName should belong to
    # the relative_resource_id but not the scope.
    if subscription_match and resource_group_match and not relative_resource_id_match:
        relative_resource_id = f"resourceGroups/{resource_group_name}"
        resource_group_name = None

    scope = f"/subscriptions/{subscription_id.lower()}"
    if resource_group_name:
        scope += f"/resourceGroups/{resource_group_name}"

    return scope, relative_resource_id
