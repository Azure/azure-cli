# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer

from azure.cli.command_modules.resource._client_factory import _resource_client_factory


@Completer
def get_providers_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    rcf = _resource_client_factory(cmd.cli_ctx)
    result = rcf.providers.list()
    return [r.namespace for r in result]


@Completer
def get_resource_types_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    rcf = _resource_client_factory(cmd.cli_ctx)
    result = rcf.providers.list()
    types = []
    for p in list(result):
        for r in p.resource_types:
            types.append(p.namespace + '/' + r.resource_type)
    return types
