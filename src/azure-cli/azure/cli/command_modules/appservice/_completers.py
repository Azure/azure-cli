# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer
from ._appservice_utils import _generic_site_operation


@Completer
def get_hostname_completion_list(cmd, prefix, namespace):  # pylint: disable=unused-argument, inconsistent-return-statements
    if namespace.resource_group_name and namespace.webapp:
        rg = namespace.resource_group_name
        webapp = namespace.webapp
        slot = getattr(namespace, 'slot', None)
        result = _generic_site_operation(cmd.cli_ctx, rg, webapp, 'get_site_host_name_bindings', slot)
        # workaround an api defect, that 'name' is '<webapp>/<hostname>'
        return [r.name.split('/', 1)[1] for r in result]
