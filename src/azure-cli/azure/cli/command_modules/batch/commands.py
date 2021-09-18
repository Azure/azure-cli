# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

from azure.cli.command_modules.batch import _client_factory as factories
from azure.cli.command_modules.batch._validators import (
    validate_pool_settings, validate_cert_settings)
from azure.cli.command_modules.batch._exception_handler import batch_exception_handler
from azure.cli.command_modules.batch._format import (
    job_list_table_format,
    task_create_table_format,
    account_keys_list_table_format,
    account_list_table_format,
    application_list_table_format,
    account_keys_renew_table_format)


def _operation(name):
    return "".join(x.title() for x in name.split('_')) + "Operations"


# pylint: disable=too-many-locals, too-many-statements, line-too-long
def load_command_table(self, _):

    data_path = 'azure.batch.operations._{}_operations#{}.'
    mgmt_path = 'azure.mgmt.batch.operations._{}_operations#{}.'

    def get_data_type(name):
        return CliCommandType(
            operations_tmpl=data_path.format(name, _operation(name)) + "{}",
            client_factory=get_data_factory(name),
            exception_handler=batch_exception_handler
        )

    def get_mgmt_type(name):
        return CliCommandType(
            operations_tmpl=mgmt_path.format(name, _operation(name)) + "{}",
            client_factory=get_mgmt_factory(name),
            exception_handler=batch_exception_handler
        )

    def get_mgmt_factory(name):
        return getattr(factories, "mgmt_{}_client_factory".format(name))

    def get_data_factory(name):
        return getattr(factories, "{}_client_factory".format(name))

    # Mgmt Account Operations
    with self.command_group('batch account', get_mgmt_type('batch_account'), client_factory=get_mgmt_factory('batch_account')) as g:
        g.custom_command('list', 'list_accounts', table_transformer=account_list_table_format)
        g.custom_show_command('show', 'get_account')
        g.custom_command('create', 'create_account', supports_no_wait=True)
        g.custom_command('set', 'update_account')
        g.command('delete', 'begin_delete', supports_no_wait=True, confirmation=True)
        g.custom_command('login', 'login_account')
        g.command('autostorage-keys sync', 'synchronize_auto_storage_keys')
        g.command('keys list', 'get_keys', table_transformer=account_keys_list_table_format)
        # g.command('keys renew', 'regenerate_key', table_transformer=account_keys_renew_table_format)
        g.custom_command('keys renew', 'renew_accounts_keys', table_transformer=account_keys_renew_table_format)
        g.command('outbound-endpoints', 'list_outbound_network_dependencies_endpoints')

    with self.command_group('batch application', get_mgmt_type('application'), client_factory=get_mgmt_factory('application')) as g:
        g.command('list', 'list', table_transformer=application_list_table_format)
        g.show_command('show', 'get')
        g.command('create', 'create')
        g.custom_command('set', 'update_application')
        g.command('delete', 'delete', confirmation=True)

    with self.command_group('batch application package', get_mgmt_type('application_package'), client_factory=get_mgmt_factory('application_package'))as g:
        g.custom_command('create', 'create_application_package')
        g.command('delete', 'delete', confirmation=True)
        g.show_command('show', 'get')
        # g.command('activate', 'activate')
        g.custom_command('activate', 'activate_application_package')
        g.command('list', 'list')

    with self.command_group('batch location quotas', get_mgmt_type('location')) as g:
        g.show_command('show', 'get_quotas')

    with self.command_group('batch location', get_mgmt_type('location')) as g:
        g.show_command('list-skus', 'list_supported_virtual_machine_skus')

    # Data Plane Commands
    with self.command_group('batch application summary', get_data_type('application')) as g:
        g.batch_command('list', 'list')
        g.batch_command('show', 'get')

    with self.command_group('batch pool supported-images', get_data_type('account')) as g:
        g.batch_command('list', 'list_supported_images')

    with self.command_group('batch pool node-counts', get_data_type('account')) as g:
        g.batch_command('list', 'list_pool_node_counts')

    with self.command_group('batch certificate', get_data_type('certificate'), client_factory=get_data_factory('certificate')) as g:
        g.custom_command('create', 'create_certificate')
        g.custom_command('delete', 'delete_certificate', confirmation=True)
        g.batch_command('show', 'get', validator=validate_cert_settings)
        g.batch_command('list', 'list')

    pool_type = get_data_type('pool')
    with self.command_group('batch pool', pool_type, client_factory=get_data_factory('pool')) as g:
        g.batch_command('usage-metrics list', 'list_usage_metrics')
        g.batch_command('all-statistics show', 'get_all_lifetime_statistics')
        g.batch_command('create', 'add', validator=validate_pool_settings, flatten=10)
        g.batch_command('list', 'list')
        g.batch_command('delete', 'delete')
        g.batch_command('show', 'get')
        g.batch_command('set', 'patch')
        g.custom_command('reset', 'update_pool')
        g.batch_command('autoscale disable', 'disable_auto_scale')
        g.batch_command('autoscale enable', 'enable_auto_scale')
        g.batch_command('autoscale evaluate', 'evaluate_auto_scale')
        g.custom_command('resize', 'resize_pool')

    with self.command_group('batch node', pool_type) as g:
        g.batch_command('delete', 'remove_nodes')

    with self.command_group('batch job', get_data_type('job'), client_factory=get_data_factory('job')) as g:
        g.batch_command('all-statistics show', 'get_all_lifetime_statistics')
        g.batch_command('create', 'add')
        g.batch_command('delete', 'delete')
        g.batch_command('show', 'get')
        g.batch_command('set', 'patch', flatten=2)
        g.batch_command('reset', 'update', flatten=2)
        g.custom_command('list', 'list_job', table_transformer=job_list_table_format)
        g.batch_command('disable', 'disable')
        g.batch_command('enable', 'enable')
        g.batch_command('stop', 'terminate')
        g.batch_command('prep-release-status list', 'list_preparation_and_release_task_status')
        g.batch_command('task-counts show', 'get_task_counts')

    with self.command_group('batch job-schedule', get_data_type('job_schedule')) as g:
        g.batch_command('create', 'add')
        g.batch_command('delete', 'delete')
        g.batch_command('show', 'get')
        g.batch_command('set', 'patch')
        g.batch_command('reset', 'update')
        g.batch_command('disable', 'disable')
        g.batch_command('enable', 'enable')
        g.batch_command('stop', 'terminate')
        g.batch_command('list', 'list')

    with self.command_group('batch task', get_data_type('task'), client_factory=get_data_factory('task')) as g:
        g.custom_command('create', 'create_task', table_transformer=task_create_table_format)
        g.batch_command('list', 'list')
        g.batch_command('delete', 'delete')
        g.batch_command('show', 'get')
        g.batch_command('reset', 'update')
        g.batch_command('reactivate', 'reactivate')
        g.batch_command('stop', 'terminate')
        g.batch_command('subtask list', 'list_subtasks')

    file_type = get_data_type('file')
    with self.command_group('batch task file', file_type) as g:
        g.batch_command('delete', 'delete_from_task')
        g.batch_command('download', 'get_from_task')
        g.batch_command('show', 'get_properties_from_task')
        g.batch_command('list', 'list_from_task')

    with self.command_group('batch node file', file_type) as g:
        g.batch_command('delete', 'delete_from_compute_node')
        g.batch_command('download', 'get_from_compute_node')
        g.batch_command('show', 'get_properties_from_compute_node')
        g.batch_command('list', 'list_from_compute_node')

    with self.command_group('batch node', get_data_type('compute_node')) as g:
        g.batch_command('user create', 'add_user')
        g.batch_command('user delete', 'delete_user')
        g.batch_command('user reset', 'update_user')
        g.batch_command('show', 'get')
        g.batch_command('list', 'list')
        g.batch_command('reboot', 'reboot')
        g.batch_command('reimage', 'reimage')
        g.batch_command('scheduling disable', 'disable_scheduling')
        g.batch_command('scheduling enable', 'enable_scheduling')
        g.batch_command('remote-login-settings show', 'get_remote_login_settings')
        g.batch_command('remote-desktop download', 'get_remote_desktop')
        g.batch_command('service-logs upload', 'upload_batch_service_logs')
