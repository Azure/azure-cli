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
    parser = cmd.cli_ctx.invocation.parser.subparser_map[cmd.name]
    specified = set(parser.specified_arguments)
    # Knack omits private destinations; argparse has already disambiguated accepted long-option prefixes.
    if any(option.startswith('--') and '--subscription'.startswith(option)
           for option in cmd.cli_ctx.data.get('safe_params', [])):
        specified.add('_subscription')
    if specified.intersection({'name', 'resource_group_name', 'silo', '_subscription'}):
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

ARGUMENT_HELP = {
    'addon_name': 'Name of the installed premium add-on.',
    'base_address': 'Module base address returned by the process module list.',
    'body': 'API request envelope as JSON or @file. Prefer named request options when available.',
    'container_name': 'Name of the container within the silo app.',
    'content_type': 'Content-Type header for the extension request body, such as application/json.',
    'delete_infected_files': 'Whether an antivirus scan may delete infected files. Specify true or false.',
    'deployment_id': 'Deployment identifier returned by deployment list.',
    'details': 'Include detailed metric values in the service response.',
    'dns_name': 'DNS name to resolve from the silo worker, such as example.com.',
    'duration': 'Network capture duration in seconds.',
    'end_time': 'End of the metrics window in UTC ISO 8601 format, such as 2026-10-20T01:00:00Z.',
    'endpoint_status': 'Enable or disable this silo as a managed-traffic endpoint.',
    'endpoints': 'JSON array or @file of region-keyed weight or priority overrides, each from 1 to 1000.',
    'expand_endpoints': 'Include persisted endpoint details in the managed-traffic collection.',
    'extension_name': 'Identifier of the installed site extension.',
    'file': 'Destination file for response bytes. Existing files require --overwrite.',
    'filename': 'Startup-log filename returned by startup list.',
    'filter_string': 'API OData metric filter. Do not combine with time, grain or metric-name options.',
    'follow_last_known_good': 'Whether the silo follows Last Known Good instead of newer ordinary revisions.',
    'force_restart': 'Whether the service may restart the silo when refreshing Key Vault references.',
    'format': 'Container-log download format: raw content or a ZIP archive.',
    'host': 'Destination hostname or IP address to test from the silo worker.',
    'include_file_paths': 'Include scanned file paths. The output may contain sensitive paths.',
    'include_secrets': 'Include private configuration values. Protect the command output.',
    'instance': 'Worker instance identifier returned by instance list.',
    'key': 'Connection-string name for a private-value point read. Omit to use the collection metadata route.',
    'latest': 'Return the latest startup-log metadata instead of the startup file list.',
    'legacy': 'Use the legacy service endpoint for this operation.',
    'location': 'Target silo region. Required on create; preserved from the existing silo on update.',
    'log_type': 'Startup-log type filter accepted by the service.',
    'max_frame_length': 'Maximum captured network-frame length in bytes.',
    'metadata_only': 'Read authentication metadata without requesting the full private settings.',
    'method': 'HTTP method used for the instance-qualified extension request.',
    'names': 'One or more metric names to include in the response.',
    'number_of_workers': 'Silo worker-count override, from 1 to 30. Omit to preserve inheritance.',
    'operation_id': 'Operation identifier returned by the corresponding accepted operation.',
    'overwrite': 'Replace the destination file if it already exists.',
    'path': 'Relative extension API path, without a leading slash, query string or fragment.',
    'port': 'Destination TCP port, from 1 to 65535.',
    'primary_location': 'Primary region. On create, resolved from the primary resource when omitted.',
    'process_id': 'Process identifier on the selected silo worker.',
    'run_id': 'Triggered WebJob run identifier returned by history list.',
    'sas_url': 'SAS URL for the trace destination. Treat this URL as a credential.',
    'scan_id': 'Antivirus scan identifier returned by antivirus log list.',
    'slot_view': 'Request the service slot view for the returned metrics.',
    'snapshot_id': 'Configuration snapshot identifier returned by config snapshot list.',
    'soft_restart': 'Whether to request the service soft-restart behavior.',
    'start_time': 'Start of the metrics window in UTC ISO 8601 format, such as 2026-10-20T00:00:00Z.',
    'subnet': 'Full subnet ARM resource ID for the silo VNet integration.',
    'synchronous': 'Whether the service should finish the restart before responding.',
    'thread_id': 'Thread identifier returned by process thread list.',
    'time_grain': 'Metrics interval as an ISO 8601 duration, such as PT1M or PT1H.',
    'timeout': 'Maximum API-operation wait in seconds. Expiry does not cancel the service operation.',
    'traffic_mode': 'Managed regional traffic mode: Active weights or Passive priorities.',
    'uri_parameters': 'Extension query parameters as KEY=VALUE pairs. Repeat keys when needed.',
    'webjob_name': 'Name of the WebJob installed in the silo app.',
    'zone_redundant': 'Silo zone-redundancy override. Specify true or false; omit to preserve inheritance.',
}

COMMAND_SUMMARIES = {
    'create_plan_silo': 'Create a regional Active Backup silo for an existing App Service plan.',
    'update_plan_silo': 'Update worker-count or zone-redundancy overrides for a plan silo.',
    'show_plan_silo': 'Show a plan silo, including its provisioning state and overrides.',
    'list_plan_silos': 'List all silos associated with an App Service plan.',
    'delete_plan_silo': 'Delete a plan silo after its dependent site silos have been removed.',
    'wait_plan_silo': 'Wait for a plan-silo API operation to complete.',
    'show_plan_silo_operation': 'Inspect the current status of a plan-silo API operation.',
    'list_plan_silo_vnet_integrations': 'List the VNet integrations associated with a plan silo.',
    'create_site_silo': 'Create a web app silo in a region with an existing plan silo.',
    'update_site_silo': 'Update a silo endpoint, revision policy or networking override.',
    'show_site_silo': 'Show a web app silo, its current revision and service error details.',
    'list_site_silos': 'List a web app origin and its regional silos.',
    'delete_site_silo': 'Delete a web app silo without deleting the primary app.',
    'wait_site_silo': 'Wait for a web app silo API operation to complete.',
    'show_site_silo_operation': 'Inspect the current status of a web app silo API operation.',
    'refresh_site_silos': 'Request a fresh revision and asynchronous propagation to the app silos.',
    'start_site_silo': 'Start the selected web app silo.',
    'stop_site_silo': 'Stop the selected web app silo.',
    'restart_site_silo': 'Restart the selected web app silo.',
    'show_silo_vnet_integration': 'Show the selected silo VNet integration.',
    'add_silo_vnet_integration': 'Connect a web app silo to a delegated VNet subnet.',
    'update_silo_vnet_integration': 'Update a web app silo VNet integration.',
    'remove_silo_vnet_integration': 'Disconnect a web app silo from its VNet subnet.',
    'list_managed_traffic': 'List the app managed-traffic configuration, with optional endpoint expansion.',
    'show_managed_traffic': 'Show the app regional traffic mode and endpoint overrides.',
    'update_managed_traffic': 'Update the app regional traffic mode or selected endpoint overrides.',
    'list_managed_traffic_metrics': 'Read health metrics for the app managed regional traffic.',
    'list_last_known_good': 'List the app Last Known Good revision metadata.',
    'show_last_known_good': 'Show the app current Last Known Good revision.',
    'mark_last_known_good': 'Mark the app latest ready revision as Last Known Good.',
    'show_silo_php_logging': 'Read the silo PHP error-logging setting.',
    'list_silo_deployments': 'List deployment history recorded for the selected silo.',
    'show_silo_deployment': 'Show one deployment from the silo deployment history.',
    'list_silo_deployment_logs': 'List log entries for one silo deployment.',
    'show_silo_msdeploy_log': 'Read the selected silo MSDeploy log.',
    'show_silo_onedeploy_status': 'Show the selected silo OneDeploy status.',
    'list_silo_deployment_statuses': 'List deployment-status records for the selected silo.',
    'show_silo_process': 'Show one process on a silo worker.',
    'stop_silo_process': 'Stop one process on a silo worker.',
    'delete_silo_process': 'Delete one process on a silo worker.',
    'dump_silo_process': 'Save a silo worker process dump to a local file.',
    'list_silo_process_threads': 'List threads belonging to a silo worker process.',
    'show_silo_process_thread': 'Show one thread belonging to a silo worker process.',
    'list_silo_process_modules': 'List modules loaded by a silo worker process.',
    'show_silo_process_module': 'Show one module loaded by a silo worker process.',
    'restart_silo_container': 'Restart a named container in the selected silo.',
    'download_silo_container_logs': 'Download raw or ZIP container logs to a local file.',
    'list_silo_startup_logs': 'List container startup-log files or request the latest-log metadata.',
    'show_silo_startup_summary': 'Show per-instance container startup success and failure summaries.',
    'show_silo_startup_log': 'Read one container startup-log file.',
    'list_silo_logs': 'List available instance logs for the selected silo.',
    'tail_silo_logs': 'Stream live silo logs to the console or a local file.',
    'show_silo_log_config': 'Show the silo diagnostic logging configuration.',
    'list_silo_webjobs': 'List WebJobs installed in the selected silo.',
    'show_silo_webjob': 'Show one WebJob installed in the selected silo.',
    'list_silo_continuous_webjobs': 'List continuous WebJobs in the selected silo.',
    'show_silo_continuous_webjob': 'Show a continuous WebJob in the selected silo.',
    'start_silo_continuous_webjob': 'Start a continuous WebJob in the selected silo.',
    'stop_silo_continuous_webjob': 'Stop a continuous WebJob in the selected silo.',
    'list_silo_triggered_webjobs': 'List triggered WebJobs in the selected silo.',
    'show_silo_triggered_webjob': 'Show a triggered WebJob in the selected silo.',
    'run_silo_triggered_webjob': 'Start a new run of a triggered WebJob.',
    'list_silo_webjob_history': 'List previous runs of a triggered WebJob.',
    'show_silo_webjob_history': 'Show one previous run of a triggered WebJob.',
    'list_silo_site_extensions': 'List site extensions installed in the selected silo.',
    'show_silo_site_extension': 'Show one site extension installed in the selected silo.',
    'invoke_silo_extension': 'Send a request to an instance-qualified silo extension API.',
    'check_silo_connectivity': 'Run a service connectivity check from the selected silo.',
    'check_silo_dns': 'Resolve a DNS name from the selected silo worker.',
    'check_silo_tcp': 'Test a TCP destination from the selected silo worker.',
    'list_silo_instances': 'List worker instances assigned to the selected silo.',
    'show_silo_instance': 'Show one worker instance assigned to the selected silo.',
    'show_silo_config': 'Read the selected silo web configuration.',
    'list_silo_config': 'List web-configuration resources for the selected silo.',
    'list_silo_config_snapshots': 'List configuration snapshots available for the selected silo.',
    'show_silo_config_snapshot': 'Read a configuration snapshot, optionally including private values.',
    'list_silo_keyvault_references': 'List connection-string Key Vault reference status for the silo.',
    'refresh_silo_keyvault_references': 'Request refresh of the silo app-setting Key Vault references.',
    'list_silo_detected_stacks': 'List runtime stacks detected in the selected silo.',
    'list_silo_appsettings': 'Read the selected silo app-setting values.',
    'list_silo_storage_accounts': 'Read storage-account mount settings for the selected silo.',
    'list_silo_connection_strings': 'Read connection-string values for the selected silo.',
    'show_silo_connection_strings': 'Read connection-string metadata or one named private value.',
    'show_silo_auth': 'Read the silo authentication settings or their metadata.',
    'show_silo_auth_v2': 'Read the silo version 2 authentication settings.',
    'show_silo_push_settings': 'Read the silo push-notification settings.',
    'list_silo_metadata': 'Read the selected silo metadata properties.',
    'list_silo_premier_addons': 'List premium add-ons associated with the selected silo.',
    'show_silo_premier_addon': 'Show a premium add-on associated with the selected silo.',
    'list_silo_metrics': 'Read metric values for the selected silo and requested time window.',
    'list_silo_metric_definitions': 'List metric names and definitions available for the selected silo.',
    'list_silo_perf_counters': 'Read performance-counter values for the selected silo.',
    'start_silo_network_trace': 'Start a network capture for the selected silo.',
    'stop_silo_network_trace': 'Stop the selected silo network capture.',
    'show_silo_network_trace': 'Read the results of a completed silo network capture.',
    'show_silo_network_trace_operation': 'Inspect a silo network-capture operation.',
    'show_silo_runtime_operation': 'Inspect an app-runtime operation on the selected silo.',
    'scan_silo_antivirus': 'Queue an on-demand antivirus scan of the selected silo.',
    'show_silo_antivirus_config': 'Read the selected silo antivirus scan configuration.',
    'update_silo_antivirus_config': 'Update whether silo antivirus scans may delete infected files.',
    'list_silo_antivirus_logs': 'List antivirus scan records for the selected silo.',
    'show_silo_antivirus_log': 'Read an antivirus scan record, optionally including file paths.',
    'list_silo_sitecontainers': 'List site-container definitions for the selected silo.',
    'show_silo_sitecontainer': 'Show one site-container definition for the selected silo.',
}

EXAMPLE_ARGUMENTS = {
    'create_plan_silo': '--number-of-workers 2 --timeout 7200',
    'create_site_silo': '--endpoint-status Enabled --follow-last-known-good false --timeout 7200',
    'update_plan_silo': '--number-of-workers 2 --zone-redundant false --timeout 7200',
    'update_site_silo': '--endpoint-status Enabled --follow-last-known-good false --timeout 7200',
    'delete_plan_silo': '--yes --timeout 7200',
    'delete_site_silo': '--yes --timeout 7200',
    'wait_plan_silo': '--timeout 7200',
    'wait_site_silo': '--timeout 7200',
    'restart_site_silo': '--soft-restart true --synchronous true --timeout 7200',
    'start_site_silo': '--timeout 7200',
    'stop_site_silo': '--timeout 7200',
    'list_managed_traffic': '--expand-endpoints',
    'update_managed_traffic': '--traffic-mode Passive',
    'show_silo_process': '--instance MyInstance',
    'list_silo_process_threads': '--instance MyInstance',
    'list_silo_process_modules': '--instance MyInstance',
    'delete_silo_process': '--yes',
    'download_silo_container_logs': '--format zip',
    'list_silo_startup_logs': '--latest true --instance MyInstance',
    'show_silo_startup_summary': '--duration 1.5 --instance MyInstance',
    'tail_silo_logs': '--instance MyInstance',
    'invoke_silo_extension': '--method POST --body @request.json',
    'check_silo_dns': '--dns-name example.com',
    'check_silo_tcp': '--host example.com --port 443',
    'show_silo_config_snapshot': '--include-secrets',
    'refresh_silo_keyvault_references': '--force-restart false',
    'show_silo_connection_strings': '--key MyConnection',
    'show_silo_auth': '--metadata-only',
    'show_silo_auth_v2': '--legacy',
    'list_silo_metrics': (
        '--names Requests --details true --time-grain PT1H '
        '--start-time 2026-10-20T00:00:00Z --end-time 2026-10-20T01:00:00Z'),
    'list_silo_perf_counters': (
        '--names Requests --time-grain PT1H '
        '--start-time 2026-10-20T00:00:00Z --end-time 2026-10-20T01:00:00Z'),
    'start_silo_network_trace': '--duration 60 --max-frame-length 128 --timeout 7200',
    'update_silo_antivirus_config': '--delete-infected-files false',
    'show_silo_antivirus_log': '--include-file-paths',
}

ADDITIONAL_EXAMPLES = {
    'create_plan_silo': (
        'Create a plan silo with explicit zone and worker overrides.',
        'az appservice plan silo create -g MyResourceGroup -n MyPrimary --silo MySilo '
        '--location westus2 --primary-location eastus --number-of-workers 2 --zone-redundant false'),
    'update_plan_silo': (
        'Update capacity while supplying the unchanged routing locations explicitly.',
        'az appservice plan silo update -g MyResourceGroup -n MyPrimary --silo MySilo '
        '--number-of-workers 2 --location westus2 --primary-location eastus'),
    'show_plan_silo': (
        'Read only the plan-silo provisioning state for a script.',
        'az appservice plan silo show -g MyResourceGroup -n MyPrimary --silo MySilo '
        '--query properties.provisioningState --output tsv'),
    'list_plan_silos': (
        'List the names of all plan silos for a script.',
        'az appservice plan silo list -g MyResourceGroup -n MyPrimary --query "[].name" --output tsv'),
    'delete_plan_silo': (
        'Request plan-silo deletion using its ARM ID after removing dependent site silos.',
        'az appservice plan silo delete --ids $PlanSiloResourceId --yes --no-wait'),
    'wait_plan_silo': (
        'Wait for a known plan-silo operation and return only its terminal status.',
        'az appservice plan silo wait --ids $PlanSiloResourceId '
        '--operation-id 00000000-0000-0000-0000-000000000001 --timeout 120 --query status --output tsv'),
    'show_plan_silo_operation': (
        'Inspect the status of an operation on a plan silo identified by ARM ID.',
        'az appservice plan silo operation show --ids $PlanSiloResourceId '
        '--operation-id 00000000-0000-0000-0000-000000000001 --query status --output tsv'),
    'list_plan_silo_vnet_integrations': (
        'Read integrations for a plan silo identified by ARM ID.',
        'az appservice plan silo vnet-integration list --ids $PlanSiloResourceId --output json'),
    'create_site_silo': (
        'Create a Passive-traffic silo with a delegated subnet override.',
        'az webapp silo create -g MyResourceGroup -n MyPrimary --silo MySilo '
        '--location westus2 --primary-location eastus --traffic-mode Passive '
        '--subnet /subscriptions/SUB/resourceGroups/NetworkGroup/providers/Microsoft.Network/'
        'virtualNetworks/WestNet/subnets/integration'),
    'update_site_silo': (
        'Set a subnet override while supplying the unchanged routing locations.',
        'az webapp silo update -g MyResourceGroup -n MyPrimary --silo MySilo '
        '--location westus2 --primary-location eastus '
        '--subnet /subscriptions/SUB/resourceGroups/NetworkGroup/providers/Microsoft.Network/'
        'virtualNetworks/WestNet/subnets/integration'),
    'show_site_silo': (
        'Read the current revision for a silo identified by ARM ID.',
        'az webapp silo show --ids $SiteSiloResourceId --query properties.revisionNumber --output tsv'),
    'list_site_silos': (
        'Show regional silo names and locations in a table.',
        'az webapp silo list -g MyResourceGroup -n MyPrimary '
        '--query "[].{Name:name,Region:location}" --output table'),
    'delete_site_silo': (
        'Request deletion by silo ARM ID without polling the accepted operation.',
        'az webapp silo delete --ids $SiteSiloResourceId --yes --no-wait'),
    'wait_site_silo': (
        'Wait for an operation on a silo identified by ARM ID and return its terminal status.',
        'az webapp silo wait --ids $SiteSiloResourceId '
        '--operation-id 00000000-0000-0000-0000-000000000001 --timeout 120 --query status --output tsv'),
    'show_site_silo_operation': (
        'Read only the current operation status.',
        'az webapp silo operation show --ids $SiteSiloResourceId '
        '--operation-id 00000000-0000-0000-0000-000000000001 --query status --output tsv'),
    'refresh_site_silos': (
        'Request asynchronous refresh for a primary app identified by ARM ID.',
        'az webapp silo refresh --ids $PrimaryAppResourceId'),
    'start_site_silo': (
        'Start a silo identified by ARM ID without polling the accepted operation.',
        'az webapp silo start --ids $SiteSiloResourceId --no-wait'),
    'stop_site_silo': (
        'Stop a silo identified by ARM ID without polling the accepted operation.',
        'az webapp silo stop --ids $SiteSiloResourceId --no-wait'),
    'restart_site_silo': (
        'Ask the service for an asynchronous restart and skip subsequent operation polling.',
        'az webapp silo restart --ids $SiteSiloResourceId --synchronous false --no-wait'),
    'show_silo_vnet_integration': (
        'Read the subnet ID from a silo VNet integration.',
        'az webapp silo vnet-integration show --ids $SiteSiloResourceId '
        '--query properties.subnetResourceId --output tsv'),
    'add_silo_vnet_integration': (
        'Connect using an advanced VNet connection envelope.',
        'az webapp silo vnet-integration add -g MyResourceGroup -n MyPrimary --silo MySilo --body @vnet.json'),
    'update_silo_vnet_integration': (
        'Patch advanced VNet connection properties from a file.',
        'az webapp silo vnet-integration update -g MyResourceGroup -n MyPrimary --silo MySilo --body @vnet.json'),
    'remove_silo_vnet_integration': (
        'Disconnect the integration on a silo identified by ARM ID.',
        'az webapp silo vnet-integration remove --ids $SiteSiloResourceId'),
    'list_managed_traffic': (
        'Read the expanded managed-traffic resource for a primary app identified by ARM ID.',
        'az webapp managed-traffic list --ids $PrimaryAppResourceId --expand-endpoints --output json'),
    'show_managed_traffic': (
        'Read only the configured regional traffic mode.',
        'az webapp managed-traffic show -g MyResourceGroup -n MyPrimary --query properties.trafficMode --output tsv'),
    'update_managed_traffic': (
        'Apply region-keyed weight overrides from a JSON array file.',
        'az webapp managed-traffic update -g MyResourceGroup -n MyPrimary '
        '--traffic-mode Active --endpoints @endpoints.json'),
    'list_managed_traffic_metrics': (
        'Read health metrics for a one-hour UTC window at one-minute intervals.',
        'az webapp managed-traffic metrics list -g MyResourceGroup -n MyPrimary '
        '--start-time 2026-10-20T00:00:00Z --end-time 2026-10-20T01:00:00Z --time-grain PT1M'),
    'list_last_known_good': (
        'Read Last Known Good metadata for a primary app identified by ARM ID.',
        'az webapp last-known-good list --ids $PrimaryAppResourceId --output json'),
    'show_last_known_good': (
        'Read only the Last Known Good revision number.',
        'az webapp last-known-good show -g MyResourceGroup -n MyPrimary '
        '--query properties.revisionNumber --output tsv'),
    'mark_last_known_good': (
        'Mark the latest ready revision using the primary app ARM ID.',
        'az webapp last-known-good mark --ids $PrimaryAppResourceId'),
    'show_silo_php_logging': (
        'Inspect the PHP logging response for a silo identified by ARM ID.',
        'az webapp silo log php show --ids $SiteSiloResourceId --output json'),
    'list_silo_deployments': (
        'List deployment identifiers for subsequent deployment-log reads.',
        'az webapp silo deployment list --ids $SiteSiloResourceId --query "[].id" --output tsv'),
    'show_silo_deployment': (
        'Read one deployment using the silo ARM ID.',
        'az webapp silo deployment show --ids $SiteSiloResourceId --deployment-id MyDeployment --output json'),
    'list_silo_deployment_logs': (
        'Read log entries for a deployment using the silo ARM ID.',
        'az webapp silo deployment log list --ids $SiteSiloResourceId --deployment-id MyDeployment --output json'),
    'show_silo_msdeploy_log': (
        'Read the MSDeploy log from one worker instance.',
        'az webapp silo deployment log show --ids $SiteSiloResourceId --instance MyInstance --output json'),
    'show_silo_onedeploy_status': (
        'Read OneDeploy status from one worker instance.',
        'az webapp silo deployment status show --ids $SiteSiloResourceId --instance MyInstance --output json'),
    'list_silo_deployment_statuses': (
        'Read deployment-status resources for a silo identified by ARM ID.',
        'az webapp silo deployment status list --ids $SiteSiloResourceId --output json'),
    'show_silo_process': (
        'Read one process using the silo ARM ID and a worker instance.',
        'az webapp silo process show --ids $SiteSiloResourceId --process-id 123 --instance MyInstance --output json'),
    'stop_silo_process': (
        'Stop a process on a specific worker instance.',
        'az webapp silo process stop --ids $SiteSiloResourceId --process-id 123 --instance MyInstance'),
    'delete_silo_process': (
        'Delete a process on a specific worker without prompting.',
        'az webapp silo process delete --ids $SiteSiloResourceId --process-id 123 --instance MyInstance --yes'),
    'dump_silo_process': (
        'Save a worker-qualified process dump and replace an existing local file.',
        'az webapp silo process dump --ids $SiteSiloResourceId --process-id 123 --instance MyInstance '
        '--file worker.dmp --overwrite'),
    'list_silo_process_threads': (
        'List thread identifiers for a process on a specific worker.',
        'az webapp silo process thread list --ids $SiteSiloResourceId --process-id 123 '
        '--instance MyInstance --query "[].id" --output tsv'),
    'show_silo_process_thread': (
        'Read one thread on a specific worker instance.',
        'az webapp silo process thread show --ids $SiteSiloResourceId --process-id 123 '
        '--thread-id 456 --instance MyInstance'),
    'list_silo_process_modules': (
        'List process module names on a specific worker.',
        'az webapp silo process module list --ids $SiteSiloResourceId --process-id 123 '
        '--instance MyInstance --query "[].name" --output tsv'),
    'show_silo_process_module': (
        'Read a module at a known base address on a specific worker.',
        'az webapp silo process module show --ids $SiteSiloResourceId --process-id 123 '
        '--base-address 0x1000 --instance MyInstance'),
    'restart_silo_container': (
        'Restart a named container on a specific worker.',
        'az webapp silo container restart --ids $SiteSiloResourceId '
        '--container-name MyContainer --instance MyInstance'),
    'download_silo_container_logs': (
        'Download raw container logs and replace an existing destination.',
        'az webapp silo log container download --ids $SiteSiloResourceId --format raw --file container.log --overwrite'),
    'list_silo_startup_logs': (
        'List startup files for a worker and a service-supported log type.',
        'az webapp silo log startup list --ids $SiteSiloResourceId '
        '--instance MyInstance --log-type $StartupLogType --latest false'),
    'show_silo_startup_summary': (
        'Read the last two hours of startup summaries for one worker.',
        'az webapp silo log startup show-summary --ids $SiteSiloResourceId --instance MyInstance --duration 2'),
    'show_silo_startup_log': (
        'Read a startup-log filename returned by startup list.',
        'az webapp silo log startup show --ids $SiteSiloResourceId --filename startup.log'),
    'list_silo_logs': (
        'List available logs from a specific worker.',
        'az webapp silo log list --ids $SiteSiloResourceId --instance MyInstance --output json'),
    'tail_silo_logs': (
        'Stream worker logs to a local file, replacing an existing destination.',
        'az webapp silo log tail --ids $SiteSiloResourceId --instance MyInstance --file live.log --overwrite'),
    'show_silo_log_config': (
        'Read only the diagnostic logging properties.',
        'az webapp silo log config show --ids $SiteSiloResourceId --query properties --output json'),
    'list_silo_webjobs': (
        'List installed WebJob names.',
        'az webapp silo webjob list --ids $SiteSiloResourceId --query "[].name" --output tsv'),
    'show_silo_webjob': (
        'Read one WebJob using the silo ARM ID.',
        'az webapp silo webjob show --ids $SiteSiloResourceId --webjob-name MyJob --output json'),
    'list_silo_continuous_webjobs': (
        'List continuous WebJob names for a script.',
        'az webapp silo webjob continuous list --ids $SiteSiloResourceId --query "[].name" --output tsv'),
    'show_silo_continuous_webjob': (
        'Inspect one continuous WebJob using the silo ARM ID.',
        'az webapp silo webjob continuous show --ids $SiteSiloResourceId --webjob-name MyJob --output json'),
    'start_silo_continuous_webjob': (
        'Start an installed continuous WebJob using the silo ARM ID.',
        'az webapp silo webjob continuous start --ids $SiteSiloResourceId --webjob-name MyJob'),
    'stop_silo_continuous_webjob': (
        'Stop an installed continuous WebJob using the silo ARM ID.',
        'az webapp silo webjob continuous stop --ids $SiteSiloResourceId --webjob-name MyJob'),
    'list_silo_triggered_webjobs': (
        'List triggered WebJob names for a script.',
        'az webapp silo webjob triggered list --ids $SiteSiloResourceId --query "[].name" --output tsv'),
    'show_silo_triggered_webjob': (
        'Inspect a triggered WebJob using the silo ARM ID.',
        'az webapp silo webjob triggered show --ids $SiteSiloResourceId --webjob-name MyJob --output json'),
    'run_silo_triggered_webjob': (
        'Queue a new run of an installed triggered WebJob.',
        'az webapp silo webjob triggered run --ids $SiteSiloResourceId --webjob-name MyJob'),
    'list_silo_webjob_history': (
        'List previous run identifiers for a triggered WebJob.',
        'az webapp silo webjob triggered history list --ids $SiteSiloResourceId '
        '--webjob-name MyJob --query "[].id" --output tsv'),
    'show_silo_webjob_history': (
        'Read a known triggered-WebJob run.',
        'az webapp silo webjob triggered history show --ids $SiteSiloResourceId '
        '--webjob-name MyJob --run-id MyRun --output json'),
    'list_silo_site_extensions': (
        'List installed extension names for a script.',
        'az webapp silo site-extension list --ids $SiteSiloResourceId --query "[].name" --output tsv'),
    'show_silo_site_extension': (
        'Inspect one installed site extension using the silo ARM ID.',
        'az webapp silo site-extension show --ids $SiteSiloResourceId --extension-name MyExtension --output json'),
    'invoke_silo_extension': (
        'Send a custom-content request with query parameters and save the response.',
        'az webapp silo extension invoke --ids $SiteSiloResourceId --instance MyInstance --path api/settings '
        '--method POST --content-type application/xml --body @request.xml '
        '--uri-parameters mode=inspect --file extension-response.bin --overwrite'),
    'check_silo_connectivity': (
        'Use a prepared connectivity-check request for a silo identified by ARM ID.',
        'az webapp silo network-check connectivity --ids $SiteSiloResourceId --body @connectivity-check.json'),
    'check_silo_dns': (
        'Use an advanced DNS-check request instead of named request fields.',
        'az webapp silo network-check dns --ids $SiteSiloResourceId --body @dns-check.json'),
    'check_silo_tcp': (
        'Use an advanced TCP-check request instead of host and port options.',
        'az webapp silo network-check tcp-ping --ids $SiteSiloResourceId --body @tcp-check.json'),
    'list_silo_instances': (
        'List worker instance names for later worker-qualified commands.',
        'az webapp silo instance list --ids $SiteSiloResourceId --query "[].name" --output tsv'),
    'show_silo_instance': (
        'Inspect one instance using the silo ARM ID.',
        'az webapp silo instance show --ids $SiteSiloResourceId --instance MyInstance --output json'),
    'show_silo_config': (
        'Read only the web-configuration properties.',
        'az webapp silo config show --ids $SiteSiloResourceId --query properties --output json'),
    'list_silo_config': (
        'List web-configuration resource names.',
        'az webapp silo config list --ids $SiteSiloResourceId --query "[].name" --output tsv'),
    'list_silo_config_snapshots': (
        'List configuration snapshot identifiers for point reads.',
        'az webapp silo config snapshot list --ids $SiteSiloResourceId --query "[].properties.snapshotId" --output tsv'),
    'show_silo_config_snapshot': (
        'Read a snapshot without including its private configuration values.',
        'az webapp silo config snapshot show --ids $SiteSiloResourceId --snapshot-id 1 --output json'),
    'list_silo_keyvault_references': (
        'Read connection-string Key Vault reference status for a silo identified by ARM ID.',
        'az webapp silo config keyvault-reference list --ids $SiteSiloResourceId --output json'),
    'refresh_silo_keyvault_references': (
        'Refresh app-setting Key Vault references and permit a service restart.',
        'az webapp silo config keyvault-reference refresh --ids $SiteSiloResourceId --force-restart true'),
    'list_silo_detected_stacks': (
        'Inspect detected runtime-stack records using the silo ARM ID.',
        'az webapp silo runtime list-detected --ids $SiteSiloResourceId --output json'),
    'list_silo_appsettings': (
        'Read one named app-setting value; protect the returned value.',
        'az webapp silo config appsettings list --ids $SiteSiloResourceId --query properties.MySetting --output tsv'),
    'list_silo_storage_accounts': (
        'Read storage-mount properties using the silo ARM ID; protect secret values.',
        'az webapp silo config storage-account list --ids $SiteSiloResourceId --query properties --output json'),
    'list_silo_connection_strings': (
        'Read one named connection string; protect the returned value.',
        'az webapp silo config connection-string list --ids $SiteSiloResourceId '
        '--query properties.MyConnection --output json'),
    'show_silo_connection_strings': (
        'Read connection-string metadata without selecting a private-value key.',
        'az webapp silo config connection-string show --ids $SiteSiloResourceId --output json'),
    'show_silo_auth': (
        'Read full authentication settings rather than metadata; protect secret values.',
        'az webapp silo auth show --ids $SiteSiloResourceId --output json'),
    'show_silo_auth_v2': (
        'Use the current authentication-v2 endpoint instead of the legacy list route.',
        'az webapp silo auth v2 show --ids $SiteSiloResourceId --output json'),
    'show_silo_push_settings': (
        'Read push-notification properties using the silo ARM ID; protect secret values.',
        'az webapp silo config push-settings show --ids $SiteSiloResourceId --query properties --output json'),
    'list_silo_metadata': (
        'Read one named metadata property.',
        'az webapp silo config metadata list --ids $SiteSiloResourceId --query properties.MyMetadata --output tsv'),
    'list_silo_premier_addons': (
        'List associated premium add-on names.',
        'az webapp silo premier-addon list --ids $SiteSiloResourceId --query "[].name" --output tsv'),
    'show_silo_premier_addon': (
        'Read one premium add-on using the silo ARM ID.',
        'az webapp silo premier-addon show --ids $SiteSiloResourceId --addon-name MyAddon --output json'),
    'list_silo_metrics': (
        'Use a service OData filter instead of named metric-window options.',
        'az webapp silo metrics list --ids $SiteSiloResourceId '
        '--filter "name.value eq \'Requests\'" --slot-view true --details false'),
    'list_silo_metric_definitions': (
        'Inspect metric definitions for a silo identified by ARM ID.',
        'az webapp silo metrics definition list --ids $SiteSiloResourceId --output json'),
    'list_silo_perf_counters': (
        'Use a service OData filter for performance counters.',
        'az webapp silo metrics perf-counter list --ids $SiteSiloResourceId '
        '--filter "name.value eq \'Requests\'" --output json'),
    'start_silo_network_trace': (
        'Use the legacy capture endpoint with a caller-provided trace destination.',
        'az webapp silo network-trace start --ids $SiteSiloResourceId --legacy '
        '--duration 60 --max-frame-length 128 --sas-url $TraceDestinationSas --timeout 7200'),
    'stop_silo_network_trace': (
        'Stop capture using the silo ARM ID.',
        'az webapp silo network-trace stop --ids $SiteSiloResourceId'),
    'show_silo_network_trace': (
        'Read results for a known capture using the silo ARM ID.',
        'az webapp silo network-trace show --ids $SiteSiloResourceId '
        '--operation-id 00000000-0000-0000-0000-000000000001 --output json'),
    'show_silo_network_trace_operation': (
        'Read only the status of a known capture operation.',
        'az webapp silo network-trace operation show --ids $SiteSiloResourceId '
        '--operation-id 00000000-0000-0000-0000-000000000001 --output json'),
    'show_silo_runtime_operation': (
        'Inspect an app-runtime operation using the silo ARM ID.',
        'az webapp silo runtime-operation show --ids $SiteSiloResourceId '
        '--operation-id 00000000-0000-0000-0000-000000000001 --output json'),
    'scan_silo_antivirus': (
        'Queue a scan using the silo ARM ID.',
        'az webapp silo antivirus scan --ids $SiteSiloResourceId'),
    'show_silo_antivirus_config': (
        'Read the antivirus scan configuration properties.',
        'az webapp silo antivirus config show --ids $SiteSiloResourceId --query properties --output json'),
    'update_silo_antivirus_config': (
        'Use an advanced antivirus configuration envelope instead of named options.',
        'az webapp silo antivirus config update --ids $SiteSiloResourceId --body @antivirus.json'),
    'list_silo_antivirus_logs': (
        'Read scan records for a silo identified by ARM ID.',
        'az webapp silo antivirus log list --ids $SiteSiloResourceId --output json'),
    'show_silo_antivirus_log': (
        'Read a scan record without including sensitive file paths.',
        'az webapp silo antivirus log show --ids $SiteSiloResourceId --scan-id MyScan --output json'),
    'list_silo_sitecontainers': (
        'List the names of site-container definitions.',
        'az webapp silo sitecontainers list --ids $SiteSiloResourceId --query "[].name" --output tsv'),
    'show_silo_sitecontainer': (
        'Read one site-container definition using the silo ARM ID.',
        'az webapp silo sitecontainers show --ids $SiteSiloResourceId --container-name MyContainer --output json'),
}

NO_WAIT_EXAMPLE_ARGUMENTS = {
    'create_plan_silo': '--number-of-workers 2',
    'update_plan_silo': '--number-of-workers 2',
    'delete_plan_silo': '--yes',
    'create_site_silo': '--endpoint-status Enabled',
    'update_site_silo': '--endpoint-status Enabled',
    'delete_site_silo': '--yes',
    'start_site_silo': '',
    'stop_site_silo': '',
    'restart_site_silo': '--soft-restart true --synchronous false',
    'start_silo_network_trace': '--duration 60 --max-frame-length 128',
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
                help='Skip polling accepted API operations. The initial service request must still complete.')
        for argument in parameters:
            if argument in ('cmd', 'name', 'resource_group_name', 'silo', 'no_wait'):
                continue
            settings = {'help': ARGUMENT_HELP[argument]}
            if argument in ('zone_redundant', 'follow_last_known_good', 'force_restart',
                            'soft_restart', 'synchronous', 'details', 'latest', 'slot_view', 'delete_infected_files'):
                settings['arg_type'] = get_three_state_flag()
            if argument in ('expand_endpoints', 'overwrite', 'include_secrets', 'metadata_only',
                            'legacy', 'include_file_paths'):
                settings['action'] = 'store_true'
            if argument in ('number_of_workers', 'timeout', 'duration', 'max_frame_length', 'port'):
                settings['type'] = int
            if argument == 'duration' and handler_name == 'show_silo_startup_summary':
                settings['type'] = float
                settings['help'] = 'Startup-summary look-back window in hours. Zero or omitted uses 24 hours.'
            if argument == 'legacy':
                settings['help'] = (
                    'Use the legacy trace-start endpoint instead of the asynchronous start-operation endpoint.'
                    if handler_name == 'start_silo_network_trace'
                    else 'Read authsettingsV2 through the legacy /list GET endpoint.')
            if argument == 'number_of_workers':
                settings.update(default=None, help='Silo worker-count override, from 1 to 30. Omit to preserve inheritance.')
            if argument == 'location':
                settings.update(
                    configured_default=None, local_context_attribute=None,
                    help='Target silo region. Required on create; preserved from the existing silo on update.')
            if argument == 'filter_string':
                settings['options_list'] = ['--filter']
            if argument == 'names':
                settings['nargs'] = '+'
            if argument == 'uri_parameters':
                settings['nargs'] = '+'
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
    sensitive_handlers = {
        'list_silo_appsettings', 'list_silo_storage_accounts', 'list_silo_connection_strings',
        'show_silo_connection_strings', 'show_silo_auth', 'show_silo_auth_v2',
        'show_silo_push_settings', 'show_silo_config_snapshot', 'show_silo_antivirus_log',
    }
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
            if handler_name in ('add_silo_vnet_integration', 'update_silo_vnet_integration'):
                example += (
                    ' --subnet /subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/MyNetworkGroup'
                    '/providers/Microsoft.Network/virtualNetworks/MyVnet/subnets/MySubnet')
            base_example = example
            if handler_name in EXAMPLE_ARGUMENTS:
                example += ' ' + EXAMPLE_ARGUMENTS[handler_name]
            description = COMMAND_SUMMARIES[handler_name]
            long_summary = 'Calls the public Active Backup API. Service eligibility and errors remain authoritative.'
            if handler_name == 'refresh_site_silos':
                long_summary += (
                    ' Returns on HTTP 204 acceptance without waiting for revision convergence or inventing a target revision.')
            if 'no_wait' in parameters:
                long_summary += (
                    ' No-wait skips subsequent operation polling, not the initial service request or synchronous service work.')
            if handler_name in sensitive_handlers:
                long_summary += ' Output can contain secrets or sensitive values; protect it.'
            if any(variable in ADDITIONAL_EXAMPLES[handler_name][1] for variable in (
                    '$SiteSiloResourceId', '$PlanSiloResourceId', '$PrimaryAppResourceId')):
                long_summary += ' ARM-ID variables in examples represent IDs returned by earlier show/list commands.'
            if handler_name == 'start_silo_network_trace':
                long_summary += ' Set TraceDestinationSas to your trace destination SAS URL; do not log or share it.'
            if handler_name == 'list_silo_startup_logs':
                long_summary += ' Set StartupLogType to the service-supported startup-log filter you need.'
            long_summary += (
                ' Origin point GET 404s can use the matching silo-list entry for metadata, with a warning. '
                'Origin writes and operation polling are unchanged.'
                if handler_name in ('show_site_silo', 'update_site_silo') else '')
            long_summary += ' See https://github.com/Azure/azure-cli/blob/dev/doc/active_backup_preview.md for details.'
            helps[command] = (
                'type: command\nshort-summary: {}\n'
                'long-summary: {}\n'
                'examples:\n  - name: {}\n    text: {}\n'
            ).format(description, long_summary, description, example)
            extra_name, extra_text = ADDITIONAL_EXAMPLES[handler_name]
            helps[command] += (
                '  - name: {}\n'
                '    text: {}\n'
            ).format(extra_name, extra_text)
            if 'no_wait' in parameters:
                options = NO_WAIT_EXAMPLE_ARGUMENTS[handler_name]
                no_wait_example = base_example + (' ' + options if options else '')
                helps[command] += (
                    '  - name: Skip operation polling after the initial service response.\n'
                    '    text: {} --no-wait\n'
                ).format(no_wait_example)
    for group in ('appservice plan silo', 'webapp silo'):
        helps[group] = (
            'type: group\nshort-summary: Manage App Service Active Backup silos.\n'
            'long-summary: >-\n'
            '  Preview creation targets Windows/Linux dedicated multitenant PremiumV3, PremiumMV3, '
            'PremiumV4 and PremiumMV4 plans. P0v3 is excluded. Regional subscription/flavor enablement, '
            'slot restrictions and dependency ordering are service-enforced. Creating the first silo '
            'can restart the primary app. Pass-through operations are not filtered by OS or SKU.\n')
