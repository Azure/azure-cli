# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace.data_export._update \
    import Update as _WorkspaceDataExportUpdate


class WorkspaceDataExportUpdate(_WorkspaceDataExportUpdate):

    def pre_operations(self):
        args = self.ctx.args
        if args.destination:
            destination = str(args.destination)
            from azure.mgmt.core.tools import is_valid_resource_id, resource_id, parse_resource_id
            if not is_valid_resource_id(destination):
                raise InvalidArgumentValueError('usage error: --destination should be a storage account,'
                                                ' an evenhug namespace or an event hub resource id.')
            result = parse_resource_id(destination)
            if result['namespace'].lower() == 'microsoft.eventhub' and result['type'].lower() == 'namespaces':
                args.destination = resource_id(
                    subscription=result['subscription'],
                    resource_group=result['resource_group'],
                    namespace=result['namespace'],
                    type=result['type'],
                    name=result['name']
                )
                if 'child_type_1' in result and result['child_type_1'].lower() == 'eventhubs':
                    args.event_hub_name = result['child_name_1']
            elif result['namespace'].lower() == 'microsoft.storage' and result['type'].lower() == 'storageaccounts':
                pass
            else:
                raise InvalidArgumentValueError('usage error: --destination should be a storage account,'
                                                ' an evenhug namespace or an event hub resource id.')
