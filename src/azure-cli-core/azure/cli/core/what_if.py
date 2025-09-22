# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Module for handling what-if functionality in Azure CLI.
This module provides the core logic for preview mode execution without actually running commands.

IMPORTANT: The what-if service requires client-side authentication to operate under the 
caller's subscription and permissions. Server-side authentication is not supported for 
what-if operations as it would not provide access to the caller's subscription.
"""
from typing import Dict, Any, Optional
from knack.log import get_logger

logger = get_logger(__name__)


def show_what_if(cli_ctx, azcli_script: str, subscription_id: Optional[str] = None, no_pretty_print: bool = False):
    from azure.cli.command_modules.resource._formatters import format_what_if_operation_result
    from azure.cli.core._profile import Profile
    import threading
    import time
    import sys
    import json
    from requests import Request, Session

    payload = {
        "azcli_script": azcli_script,
        "subscription_id": subscription_id
    }

    request_completed = threading.Event()

    def rotating_progress():
        """Simulate a rotating progress indicator, similar to the one displayed during long-running operations.
        """
        chars = ["|", "\\", "/", "-"]
        idx = 0
        while not request_completed.is_set():
            sys.stderr.write(f"\r{chars[idx % len(chars)]} Running")
            sys.stderr.flush()
            idx += 1
            time.sleep(0.2)
        sys.stderr.write("\r" + " " * 20 + "\r")
        sys.stderr.flush()

    try:
        FUNCTION_APP_URL = "https://azcli-script-insight.azurewebsites.net"
        resource = cli_ctx.cloud.endpoints.active_directory_resource_id
        profile = Profile(cli_ctx=cli_ctx)

        try:
            token_result = profile.get_raw_token(resource, subscription=subscription_id)
            token_info, _, _ = token_result
            token_type, token, _ = token_info
        except Exception as token_ex:
            request_completed.set()
            raise CLIError(f"Failed to get authentication token: {token_ex}")

        headers_dict = {}
        headers_dict['Authorization'] = '{} {}'.format(token_type, token)
        headers_dict['Content-Type'] = 'application/json'

        progress_thread = threading.Thread(target=rotating_progress)
        progress_thread.daemon = True
        progress_thread.start()

        session = Session()
        req = Request(method="POST", url=f"{FUNCTION_APP_URL}/api/what_if_preview",
                      headers=headers_dict, data=json.dumps(payload))
        prepared = session.prepare_request(req)
        response = session.send(prepared)
        request_completed.set()

        progress_thread.join(timeout=0.5)

    except Exception as ex:
        request_completed.set()
        if 'progress_thread' in locals():
            progress_thread.join(timeout=0.5)
        raise CLIError(f"Failed to connect to the what-if service: {ex}")

    try:
        raw_results = response.json()
    except ValueError as ex:
        raise CLIError(f"Failed to parse response from what-if service: {ex}")

    success = raw_results.get('success')
    if success is False:
        return raw_results
    elif success is True:
        what_if_result = raw_results.get('what_if_result', {})
        what_if_operation_result = _convert_json_to_what_if_result(what_if_result)
        if no_pretty_print:
            return what_if_result
        print(format_what_if_operation_result(what_if_operation_result, cli_ctx.enable_color))
        return what_if_result
    else:
        raise CLIError(f"Unexpected response from what-if service, got: {raw_results}")


def _convert_json_to_what_if_result(what_if_json_result):
    from azure.cli.command_modules.resource._formatters import _change_type_to_weight, _property_change_type_to_weight

    enum_keys = list(_change_type_to_weight.keys())
    enum_mapping = {}
    for enum_obj in enum_keys:
        str_repr = str(enum_obj).lower()
        if 'create' in str_repr:
            enum_mapping['Create'] = enum_obj
        elif 'delete' in str_repr:
            enum_mapping['Delete'] = enum_obj
        elif 'modify' in str_repr:
            enum_mapping['Modify'] = enum_obj
        elif 'deploy' in str_repr:
            enum_mapping['Deploy'] = enum_obj
        elif 'no_change' in str_repr or 'nochange' in str_repr:
            enum_mapping['NoChange'] = enum_obj
        elif 'ignore' in str_repr:
            enum_mapping['Ignore'] = enum_obj
        elif 'unsupported' in str_repr:
            enum_mapping['Unsupported'] = enum_obj
        elif 'no_effect' in str_repr or 'noeffect' in str_repr:
            enum_mapping['NoEffect'] = enum_obj

    property_enum_keys = list(_property_change_type_to_weight.keys())
    property_enum_mapping = {}
    for enum_obj in property_enum_keys:
        str_repr = str(enum_obj).lower()
        if 'create' in str_repr:
            property_enum_mapping['Create'] = enum_obj
        elif 'delete' in str_repr:
            property_enum_mapping['Delete'] = enum_obj
        elif 'modify' in str_repr:
            property_enum_mapping['Modify'] = enum_obj
        elif 'array' in str_repr:
            property_enum_mapping['Array'] = enum_obj
        elif 'no_effect' in str_repr or 'noeffect' in str_repr:
            property_enum_mapping['NoEffect'] = enum_obj

    class WhatIfOperationResult:
        def __init__(self):
            self.changes = []
            self.potential_changes = []
            self.diagnostics = []

    class ResourceChange:
        def __init__(self, change_data):
            self.change_type = _map_change_type_string(change_data.get('changeType', 'Unknown'))
            self.resource_id = change_data.get('resourceId', '')
            self.before = change_data.get('before')
            self.after = change_data.get('after')
            self.delta = []

            delta_data = change_data.get('delta', [])
            for property_data in delta_data:
                property_change = PropertyChange(property_data)
                self.delta.append(property_change)

    class PropertyChange:
        def __init__(self, change_data):
            self.property_change_type = _map_property_change_type_string(
                change_data.get('propertyChangeType', 'NoEffect'))
            self.path = change_data.get('path', '')
            self.before = change_data.get('before')
            self.after = change_data.get('after')
            self.children = []

            children_data = change_data.get('children', [])
            for child_data in children_data:
                child_property_change = PropertyChange(child_data)
                self.children.append(child_property_change)

    def _map_change_type_string(change_type_str):
        result = enum_mapping.get(change_type_str)
        return result

    def _map_property_change_type_string(property_change_type_str):
        result = property_enum_mapping.get(property_change_type_str)
        return result

    result = WhatIfOperationResult()

    changes = what_if_json_result.get('changes', [])
    for change_data in changes:
        resource_change = ResourceChange(change_data)
        result.changes.append(resource_change)

    potential_changes = what_if_json_result.get('potential_changes', [])
    for change_data in potential_changes:
        resource_change = ResourceChange(change_data)
        result.potential_changes.append(resource_change)

    return result