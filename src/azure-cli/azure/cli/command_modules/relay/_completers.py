# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
# pylint: disable=line-too-long
# pylint: disable=no-value-for-parameter

from azure.cli.core.decorators import Completer


@Completer
def get_wcfrelay_command_completion_list(cmd, prefix, namespace):
    from ._client_factory import wcfrelays_mgmt_client_factory
    resource_group_name = namespace.resource_group_name
    namespace_name = namespace.namespace_name
    result = wcfrelays_mgmt_client_factory(cmd.cli_ctx).list_by_namespace(resource_group_name, namespace_name)
    return [r.name for r in result]


@Completer
def get_hyco_command_completion_list(cmd, prefix, namespace):
    from ._client_factory import hycos_mgmt_client_factory
    resource_group_name = namespace.resource_group_name
    namespace_name = namespace.namespace_name
    result = hycos_mgmt_client_factory(cmd.cli_ctx).list_by_namespace(resource_group_name, namespace_name)
    return [r.name for r in result]
