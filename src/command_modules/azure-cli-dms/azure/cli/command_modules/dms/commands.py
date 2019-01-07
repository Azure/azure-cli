# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.command_modules.dms._client_factory import (dms_client_factory,
                                                           dms_cf_services,
                                                           dms_cf_skus,
                                                           dms_cf_projects,
                                                           dms_cf_tasks)

from azure.cli.core.commands import CliCommandType


def dms_api_exception_handler(ex):
    from knack.util import CLIError
    from azure.mgmt.datamigration.models import ApiErrorException

    if isinstance(ex, ApiErrorException):
        raise CLIError(ex)
    raise ex


def load_command_table(self, _):

    dms_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.datamigration.operations.services_operations#ServicesOperations.{}',
        client_factory=dms_client_factory,
        exception_handler=dms_api_exception_handler
    )

    dms_skus_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.datamigration.operations.resource_skus_operations#ResourceSkusOperations.{}',
        client_factory=dms_client_factory,
        exception_handler=dms_api_exception_handler
    )

    dms_projects_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.datamigration.operations.projects_operations#ProjectsOperations.{}',
        client_factory=dms_client_factory,
        exception_handler=dms_api_exception_handler
    )

    dms_tasks_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.datamigration.operations.tasks_operations#TasksOperations.{}',
        client_factory=dms_client_factory,
        exception_handler=dms_api_exception_handler
    )

    with self.command_group('dms', dms_sdk, client_factory=dms_cf_services) as g:
        g.custom_command('check-name', 'check_service_name_availability')
        g.command('check-status', 'check_status')
        g.custom_command('create', 'create_service', supports_no_wait=True)
        g.custom_command('delete', 'delete_service', supports_no_wait=True, confirmation=True)
        g.custom_command('list', 'list_services')
        g.show_command('show', 'get')
        g.custom_command('start', 'start_service', supports_no_wait=True)
        g.custom_command('stop', 'stop_service', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('dms', dms_skus_sdk, client_factory=dms_cf_skus) as g:
        g.command('list-skus', 'list_skus')

    with self.command_group('dms project', dms_projects_sdk, client_factory=dms_cf_projects) as g:
        g.custom_command('create', 'create_or_update_project')
        g.command('delete', 'delete', confirmation=True)
        g.command('list', 'list')
        g.show_command('show', 'get')

    with self.command_group('dms project', dms_sdk, client_factory=dms_cf_services) as g:
        g.custom_command('check-name', 'check_project_name_availability')

    with self.command_group('dms project task', dms_tasks_sdk, client_factory=dms_cf_tasks) as g:
        g.custom_command('create', 'create_task')
        g.command('delete', 'delete', confirmation=True)
        g.command('list', 'list')
        g.show_command('show', 'get')
        g.command('cancel', 'cancel')

    with self.command_group('dms project task', dms_sdk, client_factory=dms_cf_services) as g:
        g.custom_command('check-name', 'check_task_name_availability')
