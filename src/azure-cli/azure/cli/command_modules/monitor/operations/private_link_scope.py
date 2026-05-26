# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, protected-access
# Classes moved to operations/latest/monitor/private_link_scope/
# Helper function remains here and is imported by the tree files.


def validate_private_endpoint_connection_id(args):
    from azure.cli.core.aaz import has_value
    from azure.cli.core.azclierror import ArgumentUsageError
    from azure.cli.core.util import parse_proxy_resource_id

    if has_value(args.id):
        data = parse_proxy_resource_id(args.id.to_serialized_data())
        args.name = data["child_name_1"]
        args.resource_group = data["resource_group"]
        args.scope_name = data["name"]

    if not all([has_value(args.name), has_value(args.resource_group), has_value(args.scope_name)]):
        err_msg = "Incorrect usage. Please provide [--id ID] or [--n NAME -g NAME --scope-name NAME]."
        raise ArgumentUsageError(error_msg=err_msg)
