# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=too-many-locals, too-many-statements, line-too-long
def load_arguments(self, _):
    from argcomplete.completers import FilesCompleter

    from azure.mgmt.resource.locks.models import LockLevel
    from azure.mgmt.resource.managedapplications.models import ApplicationLockLevel

    from azure.cli.core.api import get_subscription_id_list
    from azure.cli.core.commands.parameters import (
        resource_group_name_type, get_location_type, tag_type, tags_type, get_resource_group_completion_list, no_wait_type, file_type,
        get_enum_type, get_three_state_flag)
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction, ALL

    from knack.arguments import ignore_type, CLIArgumentType

    from azure.cli.command_modules.resource._completers import (
        get_policy_completion_list, get_policy_set_completion_list, get_policy_assignment_completion_list,
        get_resource_types_completion_list, get_providers_completion_list)
    from azure.cli.command_modules.resource._validators import (
        validate_lock_parameters, validate_resource_lock, validate_group_lock, validate_subscription_lock, validate_metadata, RollbackAction,
        validate_msi)

    DeploymentMode, WhatIfResultFormat = self.get_models('DeploymentMode', 'WhatIfResultFormat', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)

    # BASIC PARAMETER CONFIGURATION

    resource_name_type = CLIArgumentType(options_list=['--name', '-n'], help='The resource name. (Ex: myC)')
    resource_type_type = CLIArgumentType(help="The resource type (Ex: 'resC'). Can also accept namespace/type format (Ex: 'Microsoft.Provider/resC')")
    resource_namespace_type = CLIArgumentType(options_list='--namespace', completer=get_providers_completion_list, help="Provider namespace (Ex: 'Microsoft.Provider')")
    resource_parent_type = CLIArgumentType(required=False, options_list=['--parent'], help="The parent path (Ex: 'resA/myA/resB/myB')")
    existing_policy_definition_name_type = CLIArgumentType(options_list=['--name', '-n'], completer=get_policy_completion_list, help='The policy definition name.')
    existing_policy_set_definition_name_type = CLIArgumentType(options_list=['--name', '-n'], completer=get_policy_set_completion_list, help='The policy set definition name.')
    subscription_type = CLIArgumentType(options_list='--subscription', FilesCompleter=get_subscription_id_list, help='The subscription id of the policy [set] definition.')
    management_group_name_type = CLIArgumentType(options_list='--management-group', help='The name of the management group of the policy [set] definition.')
    identity_scope_type = CLIArgumentType(help="Scope that the system assigned identity can access")
    identity_role_type = CLIArgumentType(options_list=['--role'], help="Role name or id that will be assigned to the managed identity")
    extended_json_format_type = CLIArgumentType(options_list=['--handle-extended-json-format', '-j'], action='store_true',
                                                help='Support to handle extended template content including multiline and comments in deployment')
    deployment_name_type = CLIArgumentType(options_list=['--name', '-n'], required=True, help='The deployment name.')
    deployment_create_name_type = CLIArgumentType(options_list=['--name', '-n'], required=False, help='The deployment name. Default to template file base name')
    management_group_id_type = CLIArgumentType(options_list=['--management-group-id', '-m'], required=True, help='The management group id.')
    deployment_template_file_type = CLIArgumentType(options_list=['--template-file', '-f'], completer=FilesCompleter(), type=file_type,
                                                    help="a template file path in the file system")
    deployment_template_uri_type = CLIArgumentType(options_list=['--template-uri', '-u'], help='a uri to a remote template file')
    deployment_parameters_type = CLIArgumentType(options_list=['--parameters', '-p'], action='append', nargs='+', completer=FilesCompleter(), help='the deployment parameters')
    filter_type = CLIArgumentType(options_list=['--filter'], is_preview=True,
                                  help='Filter expression using OData notation. You can use --filter "provisioningState eq \'{state}\'" to filter provisioningState. '
                                       'To get more information, please visit https://docs.microsoft.com/en-us/rest/api/resources/deployments/listatsubscriptionscope#uri-parameters')
    no_prompt = CLIArgumentType(arg_type=get_three_state_flag(), help='The option to disable the prompt of missing parameters for ARM template. '
                                'When the value is true, the prompt requiring users to provide missing parameter will be ignored. The default value is false.')

    deployment_what_if_result_format_type = CLIArgumentType(options_list=['--result-format', '-r'],
                                                            arg_type=get_enum_type(WhatIfResultFormat, "FullResourcePayloads"),
                                                            is_preview=True, min_api='2019-07-01')
    deployment_what_if_no_pretty_print_type = CLIArgumentType(options_list=['--no-pretty-print'], action='store_true',
                                                              help='Disable pretty-print for What-If results. When set, the output format type will be used.')
    deployment_what_if_confirmation_type = CLIArgumentType(options_list=['--confirm-with-what-if', '-c'], action='store_true',
                                                           help='Instruct the command to run deployment What-If before executing the deployment. It then prompts you to acknowledge resource changes before it continues.',
                                                           is_preview=True, min_api='2019-07-01')

    _PROVIDER_HELP_TEXT = 'the resource namespace, aka \'provider\''

    with self.argument_context('resource') as c:
        c.argument('no_wait', no_wait_type)
        c.argument('resource_group_name', resource_group_name_type, arg_group='Resource Id')
        c.ignore('resource_id')
        c.argument('resource_name', resource_name_type, arg_group='Resource Id')
        c.argument('api_version', help='The api version of the resource (omit for latest)', required=False, arg_group='Resource Id')
        c.argument('resource_provider_namespace', resource_namespace_type, arg_group='Resource Id')
        c.argument('resource_type', arg_type=resource_type_type, completer=get_resource_types_completion_list, arg_group='Resource Id')
        c.argument('parent_resource_path', resource_parent_type, arg_group='Resource Id')
        c.argument('tag', tag_type)
        c.argument('tags', tags_type)
        c.argument('resource_ids', nargs='+', options_list=['--ids'], help='One or more resource IDs (space-delimited). If provided, no other "Resource Id" arguments should be specified.', arg_group='Resource Id')
        c.argument('include_response_body', arg_type=get_three_state_flag(), help='Use if the default command output doesn\'t capture all of the property data.')

    with self.argument_context('resource list') as c:
        c.argument('name', resource_name_type)

    with self.argument_context('resource move') as c:
        c.argument('ids', nargs='+')

    with self.argument_context('resource invoke-action') as c:
        c.argument('action', help='The action that will be invoked on the specified resource')
        c.argument('request_body', help='JSON encoded parameter arguments for the action that will be passed along in the post request body. Use @{file} to load from a file.')

    with self.argument_context('resource create') as c:
        c.argument('resource_id', options_list=['--id'], help='Resource ID.', action=None)
        c.argument('properties', options_list=['--properties', '-p'], help='a JSON-formatted string containing resource properties')
        c.argument('is_full_object', action='store_true', help='Indicates that the properties object includes other options such as location, tags, sku, and/or plan.')

    with self.argument_context('resource link') as c:
        c.argument('target_id', options_list=['--target', c.deprecate(target='--target-id', redirect='--target', hide=True)], help='Fully-qualified resource ID of the resource link target.')
        c.argument('link_id', options_list=['--link', c.deprecate(target='--link-id', redirect='--link', hide=True)], help='Fully-qualified resource ID of the resource link.')
        c.argument('notes', help='Notes for the link.')
        c.argument('scope', help='Fully-qualified scope for retrieving links.')
        c.argument('filter_string', options_list=['--filter', c.deprecate(target='--filter-string', redirect='--filter', hide=True)], help='Filter string for limiting results.')

    with self.argument_context('resource tag') as c:
        c.argument('is_incremental', action='store_true', options_list=['--is-incremental', '-i'],
                   help='The option to add tags incrementally without deleting the original tags. If the key of new tag and original tag are duplicated, the original value will be overwritten.')

    with self.argument_context('provider') as c:
        c.ignore('top')
        c.argument('resource_provider_namespace', options_list=['--namespace', '-n'], completer=get_providers_completion_list, help=_PROVIDER_HELP_TEXT)

    with self.argument_context('provider register') as c:
        c.argument('wait', action='store_true', help='wait for the registration to finish')

    with self.argument_context('provider unregister') as c:
        c.argument('wait', action='store_true', help='wait for unregistration to finish')

    with self.argument_context('provider operation') as c:
        c.argument('api_version', help="The api version of the 'Microsoft.Authorization/providerOperations' resource (omit for latest)")

    with self.argument_context('feature') as c:
        c.argument('resource_provider_namespace', options_list='--namespace', required=True, help=_PROVIDER_HELP_TEXT)
        c.argument('feature_name', options_list=['--name', '-n'], help='the feature name')

    with self.argument_context('feature list') as c:
        c.argument('resource_provider_namespace', options_list='--namespace', required=False, help=_PROVIDER_HELP_TEXT)

    with self.argument_context('policy') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, help='the resource group where the policy will be applied')

    with self.argument_context('policy definition', resource_type=ResourceType.MGMT_RESOURCE_POLICY) as c:
        c.argument('policy_definition_name', arg_type=existing_policy_definition_name_type)
        c.argument('rules', help='JSON formatted string or a path to a file with such content', type=file_type, completer=FilesCompleter())
        c.argument('display_name', help='Display name of policy definition.')
        c.argument('description', help='Description of policy definition.')
        c.argument('params', help='JSON formatted string or a path to a file or uri with parameter definitions.', type=file_type, completer=FilesCompleter(), min_api='2016-12-01')
        c.argument('metadata', min_api='2017-06-01-preview', nargs='+', validator=validate_metadata, help='Metadata in space-separated key=value pairs.')
        c.argument('management_group', arg_type=management_group_name_type)
        c.argument('mode', options_list=['--mode', '-m'], help='Mode of the policy definition, e.g. All, Indexed. Please visit https://aka.ms/azure-policy-mode for more information.', min_api='2016-12-01')
        c.argument('subscription', arg_type=subscription_type)
        c.ignore('_subscription')  # disable global subscription

    with self.argument_context('policy definition create', resource_type=ResourceType.MGMT_RESOURCE_POLICY) as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the new policy definition.')

    with self.argument_context('policy assignment', resource_type=ResourceType.MGMT_RESOURCE_POLICY) as c:
        c.ignore('_subscription')
        c.argument('name', options_list=['--name', '-n'], completer=get_policy_assignment_completion_list, help='Name of the policy assignment.')
        c.argument('scope', help='Scope to which this policy assignment applies.')
        c.argument('disable_scope_strict_match', action='store_true', help='Include policy assignments either inherited from parent scope or at child scope.')
        c.argument('display_name', help='Display name of the policy assignment.')
        c.argument('policy', help='Name or id of the policy definition.', completer=get_policy_completion_list)

    with self.argument_context('policy assignment create', resource_type=ResourceType.MGMT_RESOURCE_POLICY) as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the new policy assignment.')
        c.argument('params', options_list=['--params', '-p'], help='JSON formatted string or a path to a file or uri with parameter values of the policy rule.', type=file_type, completer=FilesCompleter(), min_api='2016-12-01')

    with self.argument_context('policy assignment create', resource_type=ResourceType.MGMT_RESOURCE_POLICY, min_api='2017-06-01-preview') as c:
        c.argument('policy_set_definition', options_list=['--policy-set-definition', '-d'], help='Name or id of the policy set definition.')
        c.argument('sku', options_list=['--sku', '-s'], help='policy sku.', arg_type=get_enum_type(['free', 'standard']))
        c.argument('notscopes', options_list='--not-scopes', nargs='+')

    with self.argument_context('policy assignment create', resource_type=ResourceType.MGMT_RESOURCE_POLICY, min_api='2018-05-01') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), help='The location of the policy assignment. Only required when utilizing managed identity.')

    with self.argument_context('policy assignment create', resource_type=ResourceType.MGMT_RESOURCE_POLICY, arg_group='Managed Identity', min_api='2018-05-01') as c:
        c.argument('assign_identity', nargs='*', validator=validate_msi, help="Assigns a system assigned identity to the policy assignment.")
        c.argument('identity_scope', arg_type=identity_scope_type)
        c.argument('identity_role', arg_type=identity_role_type)

    with self.argument_context('policy assignment create', resource_type=ResourceType.MGMT_RESOURCE_POLICY, min_api='2019-06-01') as c:
        c.argument('enforcement_mode', options_list=['--enforcement-mode', '-e'], help='Enforcement mode of the policy assignment, e.g. Default, DoNotEnforce. Please visit https://aka.ms/azure-policyAssignment-enforcement-mode for more information.', arg_type=get_enum_type(['Default', 'DoNotEnforce']))

    with self.argument_context('policy assignment identity', resource_type=ResourceType.MGMT_RESOURCE_POLICY, min_api='2018-05-01') as c:
        c.argument('identity_scope', arg_type=identity_scope_type)
        c.argument('identity_role', arg_type=identity_role_type)

    with self.argument_context('policy set-definition', min_api='2017-06-01-preview', resource_type=ResourceType.MGMT_RESOURCE_POLICY) as c:
        c.argument('policy_set_definition_name', arg_type=existing_policy_set_definition_name_type)
        c.argument('display_name', help='Display name of policy set definition.')
        c.argument('description', help='Description of policy set definition.')
        c.argument('params', help='JSON formatted string or a path to a file or uri with parameter definitions.', type=file_type, completer=FilesCompleter())
        c.argument('definitions', help='JSON formatted string or a path to a file or uri containing definitions.', type=file_type, completer=FilesCompleter())
        c.argument('definition_groups', min_api='2019-09-01', help='JSON formatted string or a path to a file or uri containing policy definition groups. Groups are used to organize policy definitions within a policy set.', type=file_type, completer=FilesCompleter())
        c.argument('metadata', nargs='+', validator=validate_metadata, help='Metadata in space-separated key=value pairs.')
        c.argument('management_group', arg_type=management_group_name_type)
        c.argument('subscription', arg_type=subscription_type)
        c.ignore('_subscription')  # disable global subscription

    with self.argument_context('policy set-definition create', min_api='2017-06-01-preview', resource_type=ResourceType.MGMT_RESOURCE_POLICY) as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the new policy set definition.')

    with self.argument_context('group') as c:
        c.argument('tag', tag_type)
        c.argument('tags', tags_type)
        c.argument('resource_group_name', resource_group_name_type, options_list=['--name', '-n', '--resource-group', '-g'])

    with self.argument_context('group deployment') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, completer=get_resource_group_completion_list)
        c.argument('deployment_name', arg_type=deployment_name_type)
        c.argument('template_file', arg_type=deployment_template_file_type)
        c.argument('template_uri', arg_type=deployment_template_uri_type)
        c.argument('mode', arg_type=get_enum_type(DeploymentMode, default='incremental'),
                   help='Incremental (only add resources to resource group) or Complete (remove extra resources from resource group)')
        c.argument('parameters', arg_type=deployment_parameters_type)
        c.argument('rollback_on_error', nargs='?', action=RollbackAction,
                   help='The name of a deployment to roll back to on error, or use as a flag to roll back to the last successful deployment.')

    with self.argument_context('group deployment create') as c:
        c.argument('deployment_name', arg_type=deployment_create_name_type)
        c.argument('handle_extended_json_format', arg_type=extended_json_format_type,
                   deprecate_info=c.deprecate(target='--handle-extended-json-format/-j'))
        c.argument('aux_subscriptions', nargs='+', options_list=['--aux-subs'],
                   help='Auxiliary subscriptions which will be used during deployment across tenants.',
                   deprecate_info=c.deprecate(target='--aux-subs', redirect='--aux-tenants'))
        c.argument('aux_tenants', nargs='+', options_list=['--aux-tenants'],
                   help='Auxiliary tenants which will be used during deployment across tenants.')
        c.argument('no_prompt', arg_type=no_prompt)

    with self.argument_context('group deployment validate') as c:
        c.argument('handle_extended_json_format', arg_type=extended_json_format_type,
                   deprecate_info=c.deprecate(target='--handle-extended-json-format/-j'))
        c.argument('no_prompt', arg_type=no_prompt)

    with self.argument_context('group deployment list') as c:
        c.argument('filter_string', arg_type=filter_type)

    with self.argument_context('group deployment operation show') as c:
        c.argument('operation_ids', nargs='+', help='A list of operation ids to show')

    with self.argument_context('deployment') as c:
        c.argument('deployment_name', arg_type=deployment_name_type)
        c.argument('deployment_location', arg_type=get_location_type(self.cli_ctx), required=True)
        c.argument('template_file', arg_type=deployment_template_file_type)
        c.argument('template_uri', arg_type=deployment_template_uri_type)
        c.argument('parameters', arg_type=deployment_parameters_type)

    with self.argument_context('deployment create') as c:
        c.argument('deployment_name', arg_type=deployment_create_name_type)
        c.argument('handle_extended_json_format', arg_type=extended_json_format_type,
                   deprecate_info=c.deprecate(target='--handle-extended-json-format/-j'))
        c.argument('no_prompt', arg_type=no_prompt)
        c.argument('confirm_with_what_if', arg_type=deployment_what_if_confirmation_type)
        c.argument('what_if_result_format', options_list=['--what-if-result-format', '-r'],
                   arg_type=deployment_what_if_result_format_type)

    with self.argument_context('deployment validate') as c:
        c.argument('deployment_name', arg_type=deployment_create_name_type)
        c.argument('handle_extended_json_format', arg_type=extended_json_format_type,
                   deprecate_info=c.deprecate(target='--handle-extended-json-format/-j'))
        c.argument('no_prompt', arg_type=no_prompt)

    with self.argument_context('deployment operation') as c:
        c.argument('operation_ids', nargs='+', help='A list of operation ids to show')

    with self.argument_context('deployment list') as c:
        c.argument('filter_string', arg_type=filter_type)

    with self.argument_context('deployment sub') as c:
        c.argument('deployment_location', arg_type=get_location_type(self.cli_ctx), required=True)

    with self.argument_context('deployment sub create') as c:
        c.argument('deployment_name', arg_type=deployment_create_name_type)
        c.argument('handle_extended_json_format', arg_type=extended_json_format_type,
                   deprecate_info=c.deprecate(target='--handle-extended-json-format/-j'))
        c.argument('no_prompt', arg_type=no_prompt)
        c.argument('confirm_with_what_if', arg_type=deployment_what_if_confirmation_type)
        c.argument('what_if_result_format', options_list=['--what-if-result-format', '-r'],
                   arg_type=deployment_what_if_result_format_type)

    with self.argument_context('deployment sub what-if') as c:
        c.argument('deployment_name', arg_type=deployment_create_name_type)
        c.argument('no_prompt', arg_type=no_prompt)
        c.argument('result_format', arg_type=deployment_what_if_result_format_type)
        c.argument('no_pretty_print', arg_type=deployment_what_if_no_pretty_print_type)

    with self.argument_context('deployment sub validate') as c:
        c.argument('deployment_name', arg_type=deployment_create_name_type)
        c.argument('handle_extended_json_format', arg_type=extended_json_format_type,
                   deprecate_info=c.deprecate(target='--handle-extended-json-format/-j'))
        c.argument('no_prompt', arg_type=no_prompt)

    with self.argument_context('deployment sub list') as c:
        c.argument('filter_string', arg_type=filter_type)

    with self.argument_context('deployment group') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, completer=get_resource_group_completion_list, required=True)
        c.argument('mode', arg_type=get_enum_type(DeploymentMode, default='incremental'), help='Incremental (only add resources to resource group) or Complete (remove extra resources from resource group)')
        c.argument('rollback_on_error', nargs='?', action=RollbackAction,
                   help='The name of a deployment to roll back to on error, or use as a flag to roll back to the last successful deployment.')

    with self.argument_context('deployment group create') as c:
        c.argument('deployment_name', arg_type=deployment_create_name_type)
        c.argument('handle_extended_json_format', arg_type=extended_json_format_type,
                   deprecate_info=c.deprecate(target='--handle-extended-json-format/-j'))
        c.argument('aux_subscriptions', nargs='+', options_list=['--aux-subs'],
                   help='Auxiliary subscriptions which will be used during deployment across tenants.',
                   deprecate_info=c.deprecate(target='--aux-subs', redirect='--aux-tenants'))
        c.argument('aux_tenants', nargs='+', options_list=['--aux-tenants'],
                   help='Auxiliary tenants which will be used during deployment across tenants.')
        c.argument('no_prompt', arg_type=no_prompt)
        c.argument('confirm_with_what_if', arg_type=deployment_what_if_confirmation_type)
        c.argument('what_if_result_format', options_list=['--what-if-result-format', '-r'], arg_type=deployment_what_if_result_format_type)

    with self.argument_context('deployment group what-if') as c:
        c.argument('deployment_name', arg_type=deployment_create_name_type)
        c.argument('aux_tenants', nargs='+', options_list=['--aux-tenants'],
                   help='Auxiliary tenants which will be used during deployment across tenants.')
        c.argument('no_prompt', arg_type=no_prompt)
        c.argument('result_format', arg_type=deployment_what_if_result_format_type)
        c.argument('no_pretty_print', arg_type=deployment_what_if_no_pretty_print_type)
        c.ignore("rollback_on_error")

    with self.argument_context('deployment group validate') as c:
        c.argument('deployment_name', arg_type=deployment_create_name_type)
        c.argument('handle_extended_json_format', arg_type=extended_json_format_type,
                   deprecate_info=c.deprecate(target='--handle-extended-json-format/-j'))
        c.argument('no_prompt', arg_type=no_prompt)

    with self.argument_context('deployment group list') as c:
        c.argument('filter_string', arg_type=filter_type)

    with self.argument_context('deployment mg') as c:
        c.argument('management_group_id', arg_type=management_group_id_type)
        c.argument('deployment_location', arg_type=get_location_type(self.cli_ctx), required=True)

    with self.argument_context('deployment mg create') as c:
        c.argument('deployment_name', arg_type=deployment_create_name_type)
        c.argument('handle_extended_json_format', arg_type=extended_json_format_type,
                   deprecate_info=c.deprecate(target='--handle-extended-json-format/-j'))
        c.argument('no_prompt', arg_type=no_prompt)

    with self.argument_context('deployment mg validate') as c:
        c.argument('deployment_name', arg_type=deployment_create_name_type)
        c.argument('handle_extended_json_format', arg_type=extended_json_format_type,
                   deprecate_info=c.deprecate(target='--handle-extended-json-format/-j'))
        c.argument('no_prompt', arg_type=no_prompt)

    with self.argument_context('deployment mg list') as c:
        c.argument('filter_string', arg_type=filter_type)

    with self.argument_context('deployment operation mg') as c:
        c.argument('management_group_id', arg_type=management_group_id_type)

    with self.argument_context('deployment tenant') as c:
        c.argument('deployment_location', arg_type=get_location_type(self.cli_ctx), required=True)

    with self.argument_context('deployment tenant create') as c:
        c.argument('deployment_name', arg_type=deployment_create_name_type)
        c.argument('handle_extended_json_format', arg_type=extended_json_format_type,
                   deprecate_info=c.deprecate(target='--handle-extended-json-format/-j'))
        c.argument('no_prompt', arg_type=no_prompt)

    with self.argument_context('deployment tenant validate') as c:
        c.argument('deployment_name', arg_type=deployment_create_name_type)
        c.argument('handle_extended_json_format', arg_type=extended_json_format_type,
                   deprecate_info=c.deprecate(target='--handle-extended-json-format/-j'))
        c.argument('no_prompt', arg_type=no_prompt)

    with self.argument_context('deployment tenant list') as c:
        c.argument('filter_string', arg_type=filter_type)

    with self.argument_context('group export') as c:
        c.argument('include_comments', action='store_true')
        c.argument('include_parameter_default_value', action='store_true')

    with self.argument_context('group create') as c:
        c.argument('rg_name', options_list=['--name', '--resource-group', '-n', '-g'],
                   help='name of the new resource group', completer=None,
                   local_context_attribute=LocalContextAttribute(
                       name='resource_group_name', actions=[LocalContextAction.SET], scopes=[ALL]))
        c.argument('managed_by', min_api='2016-09-01', help='The ID of the resource that manages this resource group.')

    with self.argument_context('group delete') as c:
        c.argument('resource_group_name', resource_group_name_type,
                   options_list=['--name', '-n', '--resource-group', '-g'], local_context_attribute=None)

    with self.argument_context('tag') as c:
        c.argument('tag_name', options_list=['--name', '-n'])
        c.argument('tag_value', options_list='--value')

    with self.argument_context('lock') as c:
        c.argument('lock_name', options_list=['--name', '-n'], validator=validate_lock_parameters)
        c.argument('level', arg_type=get_enum_type(LockLevel), options_list=['--lock-type', '-t'], help='The type of lock restriction.')
        c.argument('parent_resource_path', resource_parent_type)
        c.argument('resource_provider_namespace', resource_namespace_type)
        c.argument('resource_type', arg_type=resource_type_type, completer=get_resource_types_completion_list)
        c.argument('resource_name', options_list=['--resource', '--resource-name'], help='Name or ID of the resource being locked. If an ID is given, other resource arguments should not be given.')
        c.argument('ids', nargs='+', options_list='--ids', help='One or more resource IDs (space-delimited). If provided, no other "Resource Id" arguments should be specified.')
        c.argument('resource_group', resource_group_name_type, validator=validate_lock_parameters)

    with self.argument_context('resource lock') as c:
        c.argument('resource_group', resource_group_name_type)
        c.argument('resource_name', options_list=['--resource', '--resource-name'], help='If an ID is given, other resource arguments should not be given.', validator=validate_resource_lock)

    with self.argument_context('group lock') as c:
        c.argument('resource_group', resource_group_name_type, validator=validate_group_lock, id_part=None)

    with self.argument_context('group lock create') as c:
        c.argument('resource_group', required=True)

    with self.argument_context('account lock') as c:
        c.argument('resource_group', ignore_type, validator=validate_subscription_lock)

    for scope in ['account', 'group']:
        with self.argument_context('{} lock'.format(scope)) as c:
            c.ignore('resource_provider_namespace', 'parent_resource_path', 'resource_type', 'resource_name')

    for scope in ['lock', 'account lock', 'group lock', 'resource lock']:
        with self.argument_context(scope) as c:
            c.argument('lock_name', options_list=['--name', '-n'], help='Name of the lock')
            c.argument('level', options_list=['--lock-type', '-t'], arg_type=get_enum_type([LockLevel.can_not_delete, LockLevel.read_only]), help='The type of lock restriction.')
            c.argument('ids', nargs='+', options_list='--ids', help='One or more resource IDs (space-delimited). If provided, no other "Resource Id" arguments should be specified.')
            c.argument('notes', help='Notes about this lock.')

    with self.argument_context('managedapp') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, help='the resource group of the managed application', id_part='resource_group')
        c.argument('application_name', options_list=['--name', '-n'], id_part='name')

    with self.argument_context('managedapp definition') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, help='the resource group of the managed application definition', id_part='resource_group')
        c.argument('application_definition_name', options_list=['--name', '-n'], id_part='name')

    with self.argument_context('managedapp create') as c:
        c.argument('name', options_list=['--name', '-n'], help='name of the new managed application', completer=None)
        c.argument('location', help='the managed application location')
        c.argument('managedapp_definition_id', options_list=['--managedapp-definition-id', '-d'], help='the full qualified managed application definition id')
        c.argument('managedby_resource_group_id', options_list=['--managed-rg-id', '-m'], help='the resource group managed by the managed application')
        c.argument('parameters', help='JSON formatted string or a path to a file with such content', type=file_type)

    with self.argument_context('managedapp definition create') as c:
        c.argument('lock_level', arg_type=get_enum_type(ApplicationLockLevel), help='The type of lock restriction.')
        c.argument('authorizations', options_list=['--authorizations', '-a'], nargs='+', help="space-separated authorization pairs in a format of `<principalId>:<roleDefinitionId>`")
        c.argument('createUiDefinition', options_list=['--create-ui-definition', '-c'], help='JSON formatted string or a path to a file with such content', type=file_type)
        c.argument('mainTemplate', options_list=['--main-template', '-t'], help='JSON formatted string or a path to a file with such content', type=file_type)

    with self.argument_context('account') as c:
        c.argument('subscription', options_list=['--subscription', '-s'], help='Name or ID of subscription.', completer=get_subscription_id_list)
        c.ignore('_subscription')  # hide global subscription parameter

    with self.argument_context('account management-group') as c:
        c.argument('group_name', options_list=['--name', '-n'])

    with self.argument_context('account management-group show') as c:
        c.argument('expand', options_list=['--expand', '-e'], action='store_true')
        c.argument('recurse', options_list=['--recurse', '-r'], action='store_true')

    with self.argument_context('account management-group create') as c:
        c.argument('display_name', options_list=['--display-name', '-d'])
        c.argument('parent', options_list=['--parent', '-p'])

    with self.argument_context('account management-group update') as c:
        c.argument('display_name', options_list=['--display-name', '-d'])
        c.argument('parent_id', options_list=['--parent', '-p'])

    with self.argument_context('rest') as c:
        c.argument('method', options_list=['--method', '-m'], arg_type=get_enum_type(['head', 'get', 'put', 'post', 'delete', 'options', 'patch'], default='get'),
                   help='HTTP request method')
        c.argument('uri', options_list=['--url', '--uri', '-u'], help='Request URL. If it doesn\'t start with a host, '
                   'CLI assumes it as an Azure resource ID and prefixes it with the ARM endpoint of the current '
                   'cloud shown by `az cloud show --query endpoints.resourceManager`. Common token {subscriptionId} '
                   'will be replaced with the current subscription ID specified by `az account set`')
        c.argument('headers', nargs='+', help="Space-separated headers in KEY=VALUE format or JSON string. Use @{file} to load from a file")
        c.argument('uri_parameters', nargs='+', help='Space-separated queries in KEY=VALUE format or JSON string. Use @{file} to load from a file')
        c.argument('skip_authorization_header', action='store_true', help='Do not auto-append Authorization header')
        c.argument('body', options_list=['--body', '-b'], help='Request body. Use @{file} to load from a file. For quoting issues in different terminals, see https://github.com/Azure/azure-cli/blob/dev/doc/use_cli_effectively.md#quoting-issues')
        c.argument('output_file', help='save response payload to a file')
        c.argument('resource', help='Resource url for which CLI should acquire a token from AAD in order to access '
                   'the service. The token will be placed in the Authorization header. By default, '
                   'CLI can figure this out based on --url argument, unless you use ones not in the list '
                   'of "az cloud show --query endpoints"')
