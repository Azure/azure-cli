# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading
import time
import sys
import json
from requests import Request, Session
from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)

def read_script_file(script_path):
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise CLIError(f"Script file not found: {script_path}")
    except Exception as ex:
        raise CLIError(f"Error reading script file: {ex}")


def _get_auth_headers(cli_ctx, subscription_id):
    from azure.cli.core._profile import Profile

    resource = cli_ctx.cloud.endpoints.active_directory_resource_id
    profile = Profile(cli_ctx=cli_ctx)

    try:
        token_result = profile.get_raw_token(resource, subscription=subscription_id)
        token_info, _, _ = token_result
        token_type, token, _ = token_info
    except Exception as token_ex:
        raise CLIError(f"Failed to get authentication token: {token_ex}")

    return {
        'Authorization': f'{token_type} {token}',
        'Content-Type': 'application/json'
    }


def _make_what_if_request(payload, headers_dict, cli_ctx=None):
    request_completed = threading.Event()

    def _rotating_progress():
        """Simulate a rotating progress indicator."""
        spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        fallback_chars = ["|", "\\", "/", "-"]

        try:
            "⠋".encode(sys.stderr.encoding or 'utf-8')
            chars = spinner_chars
        except (UnicodeEncodeError, UnicodeDecodeError, LookupError):
            chars = fallback_chars

        use_color = cli_ctx and getattr(cli_ctx, 'enable_color', False)
        if use_color:
            try:
                CYAN = '\033[36m'
                GREEN = '\033[32m'
                YELLOW = '\033[33m'
                BLUE = '\033[34m'
                RESET = '\033[0m'
                BOLD = '\033[1m'
            except (UnicodeError, AttributeError):
                use_color = False

        if not use_color:
            CYAN = GREEN = YELLOW = BLUE = RESET = BOLD = ''

        idx = 0
        start_time = time.time()

        # Simulate different stages, can be improved with real stages if available
        while not request_completed.is_set():
            elapsed = time.time() - start_time
            if elapsed < 10:
                status = f"{CYAN}Connecting to what-if service{RESET}"
                spinner_color = CYAN
            elif elapsed < 30:
                status = f"{BLUE}Analyzing Azure CLI script{RESET}"
                spinner_color = BLUE
            elif elapsed < 60:
                status = f"{YELLOW}Processing what-if analysis{RESET}"
                spinner_color = YELLOW
            else:
                status = f"{GREEN}Finalizing results{RESET}"
                spinner_color = GREEN
            elapsed_str = f"{BOLD}({elapsed:.0f}s){RESET}"
            spinner = f"{spinner_color}{chars[idx % len(chars)]}{RESET}"
            progress_line = f"{spinner} {status}... {elapsed_str}"
            visible_length = len(progress_line) - (progress_line.count('\033[') * 5)
            max_width = 100
            if visible_length > max_width:
                truncated_status = status[:max_width - 30] + "..."
                progress_line = f"{spinner} {truncated_status} {elapsed_str}"
            sys.stderr.write(f"\r{' ' * 120}\r{progress_line}")
            sys.stderr.flush()
            idx += 1
            time.sleep(0.12)
        clear_line = f"\r{' ' * 120}\r"
        sys.stderr.write(clear_line)
        sys.stderr.flush()

    try:
        function_app_url = "https://azcli-script-insight.azurewebsites.net"

        progress_thread = threading.Thread(target=_rotating_progress)
        progress_thread.daemon = True
        progress_thread.start()

        session = Session()
        logger.debug("url: %s/api/what_if_cli_preview; payload: %s", function_app_url, payload)
        req = Request(method="POST", url=f"{function_app_url}/api/what_if_cli_preview",
                      headers=headers_dict, data=json.dumps(payload))
        prepared = session.prepare_request(req)
        response = session.send(prepared)
        logger.debug("response: %s", response)
        request_completed.set()
        progress_thread.join(timeout=0.5)

        return response

    except Exception as ex:
        request_completed.set()
        if 'progress_thread' in locals():
            progress_thread.join(timeout=0.5)
        raise CLIError(f"Failed to connect to the what-if service: {ex}")


def convert_json_to_what_if_result(what_if_json_result):
    from azure.cli.command_modules.resource._formatters import _change_type_to_weight, _property_change_type_to_weight
    from collections import namedtuple

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

    WhatIfOperationResult = namedtuple('WhatIfOperationResult', ['changes', 'potential_changes', 'diagnostics'])
    ResourceChange = namedtuple('ResourceChange', ['change_type', 'resource_id', 'before', 'after', 'delta'])
    PropertyChange = namedtuple('PropertyChange', ['property_change_type', 'path', 'before', 'after', 'children'])

    def _map_change_type_string(change_type_str):
        return enum_mapping.get(change_type_str)

    def _map_property_change_type_string(property_change_type_str):
        return property_enum_mapping.get(property_change_type_str)

    def _create_property_change(change_data):
        property_change_type = _map_property_change_type_string(
            change_data.get('propertyChangeType', 'NoEffect'))
        path = change_data.get('path', '')
        before = change_data.get('before')
        after = change_data.get('after')

        children = []
        children_data = change_data.get('children', [])
        for child_data in children_data:
            children.append(_create_property_change(child_data))

        return PropertyChange(property_change_type, path, before, after, children)

    def _create_resource_change(change_data):
        change_type = _map_change_type_string(change_data.get('changeType', 'Unknown'))
        resource_id = change_data.get('resourceId', '')
        before = change_data.get('before')
        after = change_data.get('after')

        delta = []
        delta_data = change_data.get('delta', [])
        for property_data in delta_data:
            delta.append(_create_property_change(property_data))

        return ResourceChange(change_type, resource_id, before, after, delta)

    changes = []
    for change_data in what_if_json_result.get('changes', []):
        changes.append(_create_resource_change(change_data))

    potential_changes = []
    for change_data in what_if_json_result.get('potential_changes', []):
        potential_changes.append(_create_resource_change(change_data))

    return WhatIfOperationResult(changes, potential_changes, [])


def show_what_if(cli_ctx, azcli_script: str, subscription_id: str = None, no_pretty_print=False, export_bicep=False):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from azure.cli.command_modules.resource._formatters import format_what_if_operation_result

    if not subscription_id:
        subscription_id = get_subscription_id(cli_ctx)

    payload = {
        "azcli_script": azcli_script,
        "export_bicep": export_bicep,
        "subscription_id": subscription_id
    }

    headers_dict = _get_auth_headers(cli_ctx, subscription_id)
    response = _make_what_if_request(payload, headers_dict, cli_ctx)

    try:
        raw_results = response.json()
        # Only print raw results in debug mode
        logger.debug("Raw what-if service response: %s", raw_results)
    except ValueError as ex:
        raise CLIError(f"Failed to parse response from what-if service: {ex}, raw response: {response.text}")

    success = raw_results.get('success')
    if success is False:
        raise CLIError(f"Errors from what-if service: {raw_results}")
    if success is True:
        what_if_result = raw_results.get('what_if_result', {})
        what_if_operation_result = convert_json_to_what_if_result(what_if_result)
        
        # If export_bicep is enabled and bicep_template exists, include it in the result
        result_data = what_if_result.copy()
        if export_bicep and 'bicep_template' in raw_results:
            result_data['bicep_template'] = raw_results['bicep_template']
            logger.debug("Bicep template included in result: %s", raw_results['bicep_template'])
        
        if no_pretty_print:
            return result_data
        
        # Print the formatted what-if result (but not bicep template unless in debug mode)
        print(format_what_if_operation_result(what_if_operation_result, cli_ctx.enable_color))
        
        return result_data
    raise CLIError(f"Unexpected response from what-if service, got: {raw_results}")
