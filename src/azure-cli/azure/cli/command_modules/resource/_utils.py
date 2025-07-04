# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import json

_management_group_pattern = (
    r"^\/?providers\/Microsoft.Management\/managementGroups\/(?P<management_group_id>[\w\d_\.\(\)-]+)"
)
_subscription_pattern = r"^\/?subscriptions\/(?P<subscription_id>[a-f0-9-]+)"
_resource_group_pattern = r"^\/resourceGroups\/(?P<resource_group_name>[-\w\._\(\)]+)"
_relative_resource_id_pattern = r"^\/providers/(?P<relative_resource_id>.+$)"


def split_resource_id(resource_id):
    """Splits a fully qualified resource ID into two parts.

    Returns the resource scope and the relative resource ID extracted from the given resource ID.

    Examples:

      - split_resource_id("/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myRG) returns
        "/subscriptions/00000000-0000-0000-0000-000000000000", "resourceGroups/myRG"
      - split_resource_id("/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myRG\
/providers/Microsoft.Storage/storageAccounts/myStorageAccount) returns
        "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myRG,
        "Microsoft.Storage/storageAccounts/myStorageAccount"

    """
    if not resource_id:
        return None, None

    remaining = resource_id

    management_group_match = re.match(_management_group_pattern, remaining, flags=re.IGNORECASE)
    management_group_id = management_group_match.group("management_group_id") if management_group_match else ""
    remaining = remaining[len(management_group_match.group(0)) if management_group_match else 0:]

    # Parse subscription_id.
    subscription_match = re.match(_subscription_pattern, remaining, flags=re.IGNORECASE)
    subscription_id = subscription_match.group("subscription_id") if subscription_match else ""
    remaining = remaining[len(subscription_match.group(0)) if subscription_match else 0:]

    # Parse resource_group_name.
    resource_group_match = re.match(_resource_group_pattern, remaining, flags=re.IGNORECASE)
    resource_group_name = resource_group_match.group("resource_group_name") if resource_group_match else ""
    remaining = remaining[len(resource_group_match.group(0)) if resource_group_match else 0:]

    # Parse relateive_path.
    relative_resource_id_match = re.match(_relative_resource_id_pattern, remaining, flags=re.IGNORECASE)
    relative_resource_id = (
        relative_resource_id_match.group("relative_resource_id") if relative_resource_id_match else ""
    )

    if management_group_match:
        management_group_relative_id = f"Microsoft.Management/ManagementGroups/{management_group_id}"

        return (
            (f"/providers/{management_group_relative_id}", relative_resource_id)
            if relative_resource_id
            else ("/", management_group_relative_id)
        )

    if subscription_match:
        subscription_scope = f"/subscriptions/{subscription_id.lower()}"

        if resource_group_match:
            resource_group_id = f"resourceGroups/{resource_group_name}"

            return (
                (f"{subscription_scope}/{resource_group_id}", relative_resource_id)
                if relative_resource_id_match
                else (subscription_scope, resource_group_id)
            )
        return subscription_scope, relative_resource_id

    return "/", relative_resource_id


def _build_preflight_error_message(preflight_error):
    err_messages = [f'{preflight_error.code} - {preflight_error.message}']
    for detail in preflight_error.details or []:
        err_messages.append(_build_preflight_error_message(detail))
    return '\n'.join(err_messages)


def _build_http_response_error_message(http_error):
    from azure.core.exceptions import StreamClosedError, StreamConsumedError
    try:
        error_txt = http_error.response.internal_response.text
        error_info = json.loads(error_txt)['error']
    except (StreamClosedError, StreamConsumedError):
        error_info = http_error.response.json()['error']
    error_details = error_info.pop('details') if 'details' in error_info else []
    err_messages = [f'{json.dumps(error_info)}']

    for detail in error_details:
        err_messages.append(_build_error_details(detail))

    return '\n\n'.join(err_messages)


def _build_error_details(error_detail):
    nested_error_details = error_detail.pop('details') if 'details' in error_detail else []
    err_messages = [f'Inner Errors: \n{json.dumps(error_detail)}']

    for detail in nested_error_details:
        err_messages.append(_build_error_details(detail))

    return '\n\n'.join(err_messages)
