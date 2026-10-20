# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import inspect


def validate_identity(cmd, namespace):
    from azure.cli.core.azclierror import InvalidArgumentValueError, MutuallyExclusiveArgumentError
    from azure.mgmt.core.tools import parse_resource_id
    identifiers = getattr(namespace, '_ids', None)
    if not identifiers:
        return
    named_flags = {'--name', '-n', '--resource-group', '-g', '--silo', '--subscription'}
    if named_flags.intersection(cmd.cli_ctx.data.get('safe_params', [])):
        raise MutuallyExclusiveArgumentError('Use --ids or named resource arguments, not both.')
    expected_type = 'serverfarms' if cmd.name.startswith('appservice plan silo') else 'sites'
    child_required = hasattr(namespace, 'silo')
    for identifier in identifiers:
        parts = parse_resource_id(identifier)
        if (parts.get('namespace', '').lower() != 'microsoft.web' or
                parts.get('type', parts.get('resource_type', '')).lower() != expected_type or
                (child_required and parts.get('child_type_1', '').lower() != 'silos') or
                (not child_required and 'child_type_1' in parts) or 'child_type_2' in parts):
            raise InvalidArgumentValueError(
                'Provide a Microsoft.Web/{}{} resource ID.'.format(expected_type, '/silos' if child_required else ''))


COMMAND_GROUPS = {
    'appservice plan silo': (
        ('create', 'create_plan_silo'), ('update', 'update_plan_silo'),
        ('show', 'show_plan_silo'), ('list', 'list_plan_silos'), ('delete', 'delete_plan_silo'),
        ('wait', 'wait_plan_silo')),
    'appservice plan silo operation': (('show', 'show_plan_silo_operation'),),
    'appservice plan silo vnet-integration': (('list', 'list_plan_silo_vnet_integrations'),),
    'webapp silo': (
        ('create', 'create_site_silo'), ('update', 'update_site_silo'), ('show', 'show_site_silo'),
        ('list', 'list_site_silos'), ('delete', 'delete_site_silo'), ('wait', 'wait_site_silo'),
        ('refresh', 'refresh_site_silos'), ('start', 'start_site_silo'),
        ('stop', 'stop_site_silo'), ('restart', 'restart_site_silo')),
    'webapp silo operation': (('show', 'show_site_silo_operation'),),
    'webapp silo vnet-integration': (
        ('show', 'show_silo_vnet_integration'), ('add', 'add_silo_vnet_integration'),
        ('update', 'update_silo_vnet_integration'), ('remove', 'remove_silo_vnet_integration')),
    'webapp managed-traffic': (
        ('list', 'list_managed_traffic'), ('show', 'show_managed_traffic'), ('update', 'update_managed_traffic')),
    'webapp managed-traffic metrics': (('list', 'list_managed_traffic_metrics'),),
    'webapp last-known-good': (
        ('list', 'list_last_known_good'), ('show', 'show_last_known_good'), ('mark', 'mark_last_known_good')),
    'webapp silo log php': (('show', 'show_silo_php_logging'),),
    'webapp silo deployment': (('list', 'list_silo_deployments'), ('show', 'show_silo_deployment')),
    'webapp silo deployment log': (
        ('list', 'list_silo_deployment_logs'), ('show', 'show_silo_msdeploy_log')),
    'webapp silo deployment status': (
        ('show', 'show_silo_onedeploy_status'), ('list', 'list_silo_deployment_statuses')),
    'webapp silo process': (
        ('show', 'show_silo_process'), ('stop', 'stop_silo_process'), ('delete', 'delete_silo_process'),
        ('dump', 'dump_silo_process')),
    'webapp silo process thread': (
        ('list', 'list_silo_process_threads'), ('show', 'show_silo_process_thread')),
    'webapp silo process module': (
        ('list', 'list_silo_process_modules'), ('show', 'show_silo_process_module')),
    'webapp silo container': (('restart', 'restart_silo_container'),),
    'webapp silo log container': (('download', 'download_silo_container_logs'),),
    'webapp silo log startup': (
        ('list', 'list_silo_startup_logs'), ('show-summary', 'show_silo_startup_summary'),
        ('show', 'show_silo_startup_log')),
    'webapp silo log': (('list', 'list_silo_logs'), ('tail', 'tail_silo_logs')),
    'webapp silo log config': (('show', 'show_silo_log_config'),),
    'webapp silo webjob': (('list', 'list_silo_webjobs'), ('show', 'show_silo_webjob')),
    'webapp silo webjob continuous': (
        ('list', 'list_silo_continuous_webjobs'), ('show', 'show_silo_continuous_webjob'),
        ('start', 'start_silo_continuous_webjob'), ('stop', 'stop_silo_continuous_webjob')),
    'webapp silo webjob triggered': (
        ('list', 'list_silo_triggered_webjobs'), ('show', 'show_silo_triggered_webjob'),
        ('run', 'run_silo_triggered_webjob')),
    'webapp silo webjob triggered history': (
        ('list', 'list_silo_webjob_history'), ('show', 'show_silo_webjob_history')),
    'webapp silo site-extension': (
        ('list', 'list_silo_site_extensions'), ('show', 'show_silo_site_extension')),
    'webapp silo extension': (('invoke', 'invoke_silo_extension'),),
    'webapp silo network-check': (
        ('connectivity', 'check_silo_connectivity'), ('dns', 'check_silo_dns'), ('tcp-ping', 'check_silo_tcp')),
    'webapp silo instance': (('list', 'list_silo_instances'), ('show', 'show_silo_instance')),
    'webapp silo config': (('show', 'show_silo_config'), ('list', 'list_silo_config')),
    'webapp silo config snapshot': (
        ('list', 'list_silo_config_snapshots'), ('show', 'show_silo_config_snapshot')),
    'webapp silo config keyvault-reference': (
        ('list', 'list_silo_keyvault_references'), ('refresh', 'refresh_silo_keyvault_references')),
    'webapp silo runtime': (('list-detected', 'list_silo_detected_stacks'),),
    'webapp silo config appsettings': (('list', 'list_silo_appsettings'),),
    'webapp silo config storage-account': (('list', 'list_silo_storage_accounts'),),
    'webapp silo config connection-string': (
        ('list', 'list_silo_connection_strings'), ('show', 'show_silo_connection_strings')),
    'webapp silo auth': (('show', 'show_silo_auth'),),
    'webapp silo auth v2': (('show', 'show_silo_auth_v2'),),
    'webapp silo config push-settings': (('show', 'show_silo_push_settings'),),
    'webapp silo config metadata': (('list', 'list_silo_metadata'),),
    'webapp silo premier-addon': (('list', 'list_silo_premier_addons'), ('show', 'show_silo_premier_addon')),
    'webapp silo metrics': (('list', 'list_silo_metrics'),),
    'webapp silo metrics definition': (('list', 'list_silo_metric_definitions'),),
    'webapp silo metrics perf-counter': (('list', 'list_silo_perf_counters'),),
    'webapp silo network-trace': (
        ('start', 'start_silo_network_trace'), ('stop', 'stop_silo_network_trace'),
        ('show', 'show_silo_network_trace')),
    'webapp silo network-trace operation': (('show', 'show_silo_network_trace_operation'),),
    'webapp silo runtime-operation': (('show', 'show_silo_runtime_operation'),),
    'webapp silo antivirus': (('scan', 'scan_silo_antivirus'),),
    'webapp silo antivirus config': (
        ('show', 'show_silo_antivirus_config'), ('update', 'update_silo_antivirus_config')),
    'webapp silo antivirus log': (('list', 'list_silo_antivirus_logs'), ('show', 'show_silo_antivirus_log')),
    'webapp silo sitecontainers': (('list', 'list_silo_sitecontainers'), ('show', 'show_silo_sitecontainer')),
}


def load_command_table(loader):
    from azure.cli.core.commands import CliCommandType
    from . import active_backup
    command_type = CliCommandType(operations_tmpl='azure.cli.command_modules.appservice.active_backup#{}')
    for group, commands in COMMAND_GROUPS.items():
        with loader.command_group(group, custom_command_type=command_type, is_preview=True,
                                  validator=validate_identity) as context:
            for verb, handler_name in commands:
                options = {}
                if verb == 'delete':
                    options['confirmation'] = True
                if group in ('appservice plan silo', 'webapp silo') and verb in ('create', 'update', 'show', 'list'):
                    options['table_transformer'] = active_backup.silo_table
                register = context.custom_show_command if verb == 'show' else context.custom_command
                register(verb, handler_name, **options)


def load_arguments(loader, command):
    from azure.cli.core.commands.parameters import get_enum_type, get_three_state_flag, resource_group_name_type
    from . import active_backup
    handler_name = next((handler for group, entries in COMMAND_GROUPS.items() for verb, handler in entries
                         if group + ' ' + verb == command), None)
    if handler_name is None:
        return
    parameters = inspect.signature(getattr(active_backup, handler_name)).parameters
    with loader.argument_context(command) as context:
        context.argument('resource_group_name', arg_type=resource_group_name_type)
        context.argument('name', options_list=['--name', '-n'], id_part='name',
                         configured_default=None, local_context_attribute=None, completer=None,
                         help='Name of the primary App Service plan or app, not an internal silo resource.')
        context.argument('silo', id_part='child_name_1', help='Customer-facing silo name, including origin when supported.')
        if 'no_wait' in parameters:
            # Register the reserved flag locally; supports_no_wait would discard the receipt.
            context.extra(
                'no_wait', options_list=['--no-wait'], action='store_true', default=False,
                help='Return without waiting for the API operation, preserving its resource or accepted-operation receipt.')
        for argument in parameters:
            if argument in ('cmd', 'name', 'resource_group_name', 'silo', 'no_wait'):
                continue
            settings = {'help': argument.replace('_', ' ').capitalize() + '.'}
            if argument in ('zone_redundant', 'follow_last_known_good', 'force_restart',
                            'soft_restart', 'synchronous', 'details', 'latest', 'slot_view'):
                settings['arg_type'] = get_three_state_flag()
            if argument in ('expand_endpoints', 'overwrite', 'include_secrets', 'metadata_only',
                            'legacy', 'include_file_paths'):
                settings['action'] = 'store_true'
            if argument in ('number_of_workers', 'timeout', 'duration', 'max_frame_length'):
                settings['type'] = int
            if argument == 'duration' and handler_name == 'show_silo_startup_summary':
                settings['type'] = float
            if argument == 'number_of_workers':
                settings.update(default=None, help='Silo worker-count override, from 1 to 30. Omit to preserve inheritance.')
            if argument == 'location':
                settings['help'] = 'Target silo region. Required on create; never inferred from the resource group.'
            if argument == 'primary_location':
                settings['help'] = 'Primary region. On create, resolved from the primary resource when omitted.'
            if argument == 'timeout':
                settings['help'] = 'Maximum API-operation wait in seconds. Does not cancel the service operation.'
            if argument == 'body':
                settings['help'] = 'Request JSON or @file containing the API request envelope, including properties.'
            if argument == 'endpoints':
                settings['help'] = 'JSON array or @file with region and optional weight/priority values (1-1000).'
            if argument == 'subnet':
                settings['help'] = 'Full subnet ARM resource ID for the silo network integration.'
            if argument == 'file':
                settings['help'] = 'Destination file for response bytes. Existing files require --overwrite.'
            if argument == 'filter_string':
                settings.update(options_list=['--filter'], help='API OData metric filter; cannot combine with time/name filters.')
            if argument == 'names':
                settings['nargs'] = '+'
            if argument == 'uri_parameters':
                settings.update(nargs='+', help='Extension query parameters as KEY=VALUE pairs. May repeat keys.')
            enums = {'traffic_mode': ['Active', 'Passive'], 'endpoint_status': ['Enabled', 'Disabled'],
                     'format': ['raw', 'zip'], 'method': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD']}
            if argument in enums:
                settings['arg_type'] = get_enum_type(enums[argument])
            if argument == 'time_grain' and command.startswith('webapp managed-traffic'):
                settings['arg_type'] = get_enum_type(['PT1M', 'PT1H'])
            context.argument(argument, **settings)


def load_help():
    from knack.help_files import helps
    from . import active_backup
    for group, entries in COMMAND_GROUPS.items():
        root_length = 3 if group.startswith('appservice plan') else 2
        words = group.split()
        for length in range(root_length, len(words) + 1):
            subgroup = ' '.join(words[:length])
            helps[subgroup] = (
                'type: group\nshort-summary: Manage App Service Active Backup {}.\n'
                'long-summary: Operations use public ARM APIs. Service eligibility and not-found errors are preserved.\n'
            ).format(' '.join(words[root_length:length]) or 'silos')
        for verb, handler_name in entries:
            command = group + ' ' + verb
            parameters = inspect.signature(getattr(active_backup, handler_name)).parameters
            example = 'az ' + command + ' -g MyResourceGroup -n MyPrimary'
            if 'silo' in parameters:
                example += ' --silo MySilo'
            examples = {'location': 'westus2', 'operation_id': '00000000-0000-0000-0000-000000000001',
                        'file': 'silo-output.bin', 'body': '@request.json', 'path': 'api/settings',
                        'instance': 'MyInstance', 'process_id': '123', 'thread_id': '456',
                        'base_address': '0x1000', 'deployment_id': 'MyDeployment',
                        'filename': 'startup.log', 'webjob_name': 'MyJob', 'run_id': 'MyRun',
                        'extension_name': 'MyExtension', 'snapshot_id': '1', 'addon_name': 'MyAddon',
                        'scan_id': 'MyScan', 'container_name': 'MyContainer'}
            for argument, parameter in parameters.items():
                if argument not in ('cmd', 'resource_group_name', 'name', 'silo') and parameter.default is inspect.Parameter.empty:
                    example += ' --{} {}'.format(argument.replace('_', '-'), examples[argument])
            if verb == 'create':
                example += ' --primary-location eastus'
                if group == 'webapp silo':
                    example += ' --traffic-mode Active'
            if handler_name == 'update_managed_traffic':
                example += ' --traffic-mode Passive'
            if handler_name in ('add_silo_vnet_integration', 'update_silo_vnet_integration'):
                example += ' --body @request.json'
            description = handler_name.replace('_', ' ').capitalize() + '.'
            origin_help = (
                ' Origin point GET 404s can use the matching silo-list entry for metadata, with a warning. '
                'Origin writes and operation polling are unchanged.'
                if handler_name in ('show_site_silo', 'update_site_silo') else '')
            helps[command] = (
                'type: command\nshort-summary: {}\n'
                'long-summary: Calls the supported silo ARM API without client-side OS or SKU eligibility checks. '
                'Read operations can return sensitive configuration. File responses require --file. '
                'See https://github.com/Azure/azure-cli/blob/dev/doc/active_backup_preview.md '
                'for API bodies and service limitations.{}\n'
                'examples:\n  - name: {}\n    text: {}\n'
            ).format(description, origin_help, description, example)
    for group in ('appservice plan silo', 'webapp silo'):
        helps[group] = (
            'type: group\nshort-summary: Manage App Service Active Backup silos.\n'
            'long-summary: >-\n'
            '  Preview creation targets Windows/Linux dedicated multitenant PremiumV3, PremiumMV3, '
            'PremiumV4 and PremiumMV4 plans. P0v3 is excluded. Regional subscription/flavor enablement, '
            'slot restrictions and dependency ordering are service-enforced. Creating the first silo '
            'can restart the primary app. Pass-through operations are not filtered by OS or SKU.\n')
    helps['webapp silo refresh'] = """
type: command
short-summary: Request a fresh revision and asynchronous propagation to the app's silos.
long-summary: Returns successfully on HTTP 204 acceptance. Does not wait for revision convergence or invent a target revision.
examples:
  - name: Request refresh for all silos of a primary app.
    text: az webapp silo refresh -g MyResourceGroup -n MyPrimary
"""
