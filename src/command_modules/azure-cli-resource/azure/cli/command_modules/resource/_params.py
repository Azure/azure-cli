# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=too-many-locals, too-many-statements, line-too-long
def load_arguments(self, _):
    from argcomplete.completers import FilesCompleter

    from azure.mgmt.resource.resources.models import DeploymentMode
    from azure.mgmt.resource.locks.models import LockLevel
    from azure.mgmt.resource.managedapplications.models import ApplicationLockLevel

    from azure.cli.core.api import get_subscription_id_list
    from azure.cli.core.commands.parameters import (
        resource_group_name_type, get_location_type, tag_type, tags_type, get_resource_group_completion_list, no_wait_type, file_type,
        get_enum_type, get_three_state_flag)
    from azure.cli.core.profiles import ResourceType

    from knack.arguments import ignore_type, CLIArgumentType

    from azure.cli.command_modules.resource._completers import (
        get_policy_completion_list, get_policy_set_completion_list, get_policy_assignment_completion_list,
        get_resource_types_completion_list, get_providers_completion_list)
    from azure.cli.command_modules.resource._validators import (
        validate_lock_parameters, validate_resource_lock, validate_group_lock, validate_subscription_lock, validate_metadata, RollbackAction)

    # BASIC PARAMETER CONFIGURATION

    resource_name_type = CLIArgumentType(options_list=('--name', '-n'), help='The resource name. (Ex: myC)')
    resource_type_type = CLIArgumentType(help="The resource type (Ex: 'resC'). Can also accept namespace/type format (Ex: 'Microsoft.Provider/resC')")
    resource_namespace_type = CLIArgumentType(options_list=('--namespace',), completer=get_providers_completion_list, help="Provider namespace (Ex: 'Microsoft.Provider')")
    resource_parent_type = CLIArgumentType(required=False, options_list=['--parent'], help="The parent path (Ex: 'resA/myA/resB/myB')")
    existing_policy_definition_name_type = CLIArgumentType(options_list=('--name', '-n'), completer=get_policy_completion_list, help='The policy definition name')
    existing_policy_set_definition_name_type = CLIArgumentType(options_list=('--name', '-n'), completer=get_policy_set_completion_list, help='The policy set definition name')
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
        c.argument('properties', options_list=('--properties', '-p'), help='a JSON-formatted string containing resource properties')
        c.argument('is_full_object', action='store_true', help='Indicates that the properties object includes other options such as location, tags, sku, and/or plan.')

    with self.argument_context('provider') as c:
        c.ignore('top')
        c.argument('resource_provider_namespace', options_list=('--namespace', '-n'), completer=get_providers_completion_list, help=_PROVIDER_HELP_TEXT)

    with self.argument_context('provider register') as c:
        c.argument('wait', action='store_true', help='wait for the registration to finish')

    with self.argument_context('provider unregister') as c:
        c.argument('wait', action='store_true', help='wait for unregistration to finish')

    with self.argument_context('provider operation') as c:
        c.argument('api_version', help="The api version of the 'Microsoft.Authorization/providerOperations' resource (omit for latest)")

    with self.argument_context('feature') as c:
        c.argument('resource_provider_namespace', options_list=('--namespace',), required=True, help=_PROVIDER_HELP_TEXT)
        c.argument('feature_name', options_list=('--name', '-n'), help='the feature name')

    with self.argument_context('feature list') as c:
        c.argument('resource_provider_namespace', options_list=('--namespace',), required=False, help=_PROVIDER_HELP_TEXT)

    with self.argument_context('policy') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, help='the resource group where the policy will be applied')

    with self.argument_context('policy definition', resource_type=ResourceType.MGMT_RESOURCE_POLICY) as c:
        c.argument('policy_definition_name', arg_type=existing_policy_definition_name_type)
        c.argument('rules', help='JSON formatted string or a path to a file with such content', type=file_type, completer=FilesCompleter())
        c.argument('display_name', help='display name of policy definition')
        c.argument('description', help='description of policy definition')
        c.argument('params', help='JSON formatted string or a path to a file or uri with parameter definitions', type=file_type, completer=FilesCompleter(), min_api='2016-12-01')
        c.argument('metadata', min_api='2017-06-01-preview', nargs='+', validator=validate_metadata, help='Metadata in space-separated key=value pairs.')

    with self.argument_context('policy definition create', resource_type=ResourceType.MGMT_RESOURCE_POLICY) as c:
        from azure.mgmt.resource.policy.models import PolicyMode
        c.argument('name', options_list=('--name', '-n'), help='name of the new policy definition')
        c.argument('mode', arg_type=get_enum_type(PolicyMode), options_list=('--mode', '-m'), help='mode of the new policy definition.', min_api='2016-12-01')

    with self.argument_context('policy assignment', resource_type=ResourceType.MGMT_RESOURCE_POLICY) as c:
        c.argument('name', options_list=('--name', '-n'), completer=get_policy_assignment_completion_list, help='name of the assignment')
        c.argument('scope', help='scope at which this policy assignment applies to, e.g., /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333, /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup, or /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup/providers/Microsoft.Compute/virtualMachines/myVM')
        c.argument('disable_scope_strict_match', action='store_true', help='include assignment either inherited from parent scope or at child scope')
        c.argument('display_name', help='display name of the assignment')
        c.argument('policy', help='name or id of the policy definition.', completer=get_policy_completion_list)

    with self.argument_context('policy assignment create', resource_type=ResourceType.MGMT_RESOURCE_POLICY) as c:
        c.argument('name', options_list=('--name', '-n'), help='name of the new assignment')
        c.argument('params', options_list=('--params', '-p'), help='JSON formatted string or path to file with parameter values of policy rule', min_api='2016-12-01')

    with self.argument_context('policy assignment create', resource_type=ResourceType.MGMT_RESOURCE_POLICY, min_api='2017-06-01-preview') as c:
        c.argument('policy_set_definition', options_list=('--policy-set-definition', '-d'), help='name or id of the policy set definition.')
        c.argument('sku', options_list=('--sku', '-s'), help='policy sku.', arg_type=get_enum_type(['free', 'standard']))
        c.argument('notscopes', options_list=('--not-scopes'), nargs='+')

    with self.argument_context('policy set-definition', min_api='2017-06-01-preview', resource_type=ResourceType.MGMT_RESOURCE_POLICY) as c:
        c.argument('policy_set_definition_name', arg_type=existing_policy_set_definition_name_type)
        c.argument('name', options_list=('--name', '-n'), help='name of the new policy set definition')
        c.argument('display_name', help='display name of policy set definition')
        c.argument('description', help='description of policy set definition')
        c.argument('params', help='JSON formatted string or a path to a file or uri with parameter definitions', type=file_type, completer=FilesCompleter())
        c.argument('definitions', help='JSON formatted string or a path to a file or uri with such content', type=file_type, completer=FilesCompleter())

    with self.argument_context('group') as c:
        c.argument('tag', tag_type)
        c.argument('tags', tags_type)
        c.argument('resource_group_name', resource_group_name_type, options_list=['--name', '-n', '--resource-group', '-g'])

    with self.argument_context('group deployment') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, completer=get_resource_group_completion_list)
        c.argument('deployment_name', options_list=('--name', '-n'), required=True, help='The deployment name.')
        c.argument('template_file', completer=FilesCompleter(), type=file_type, help="a template file path in the file system")
        c.argument('template_uri', help='a uri to a remote template file')
        c.argument('mode', arg_type=get_enum_type(DeploymentMode, default='incremental'), help='Incremental (only add resources to resource group) or Complete (remove extra resources from resource group)')
        c.argument('parameters', action='append', nargs='+', completer=FilesCompleter())
        c.argument('rollback_on_error', nargs='?', action=RollbackAction, help='The name of a deployment to roll back to on error, or use as a flag to roll back to the last successful deployment.')

    with self.argument_context('group deployment create') as c:
        c.argument('deployment_name', options_list=('--name', '-n'), required=False,
                   help='The deployment name. Default to template file base name')

    with self.argument_context('group deployment operation show') as c:
        c.argument('operation_ids', nargs='+', help='A list of operation ids to show')

    with self.argument_context('deployment') as c:
        c.argument('deployment_name', options_list=('--name', '-n'), required=True, help='The deployment name.')
        c.argument('deployment_location', arg_type=get_location_type(self.cli_ctx), required=True)
        c.argument('template_file', completer=FilesCompleter(), type=file_type, help="a template file path in the file system")
        c.argument('template_uri', help='a uri to a remote template file')
        c.argument('parameters', action='append', nargs='+', completer=FilesCompleter())

    with self.argument_context('deployment create') as c:
        c.argument('deployment_name', options_list=('--name', '-n'), required=False,
                   help='The deployment name. Default to template file base name')

    with self.argument_context('deployment operation show') as c:
        c.argument('operation_ids', nargs='+', help='A list of operation ids to show')

    with self.argument_context('group export') as c:
        c.argument('include_comments', action='store_true')
        c.argument('include_parameter_default_value', action='store_true')

    with self.argument_context('group create') as c:
        c.argument('rg_name', options_list=['--name', '--resource-group', '-n', '-g'], help='name of the new resource group', completer=None)

    with self.argument_context('tag') as c:
        c.argument('tag_name', options_list=('--name', '-n'))
        c.argument('tag_value', options_list=('--value',))

    with self.argument_context('lock') as c:
        c.argument('lock_name', options_list=('--name', '-n'), validator=validate_lock_parameters)
        c.argument('level', arg_type=get_enum_type(LockLevel), options_list=('--lock-type', '-t'))
        c.argument('parent_resource_path', resource_parent_type)
        c.argument('resource_provider_namespace', resource_namespace_type)
        c.argument('resource_type', arg_type=resource_type_type, completer=get_resource_types_completion_list)
        c.argument('resource_name', options_list=['--resource', '--resource-name'], help='Name or ID of the resource being locked. If an ID is given, other resource arguments should not be given.')
        c.argument('ids', nargs='+', options_list=('--ids'), help='One or more resource IDs (space-delimited). If provided, no other "Resource Id" arguments should be specified.')
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
            c.argument('lock_name', options_list=('--name', '-n'), help='Name of the lock')
            c.argument('level', options_list=('--lock-type', '-t'), arg_type=get_enum_type([LockLevel.can_not_delete, LockLevel.read_only]))
            c.argument('ids', nargs='+', options_list=('--ids'), help='One or more resource IDs (space-delimited). If provided, no other "Resource Id" arguments should be specified.')
            c.argument('notes', help='Notes about this lock.')

    with self.argument_context('managedapp') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, help='the resource group of the managed application', id_part='resource_group')
        c.argument('application_name', options_list=('--name', '-n'), id_part='name')

    with self.argument_context('managedapp definition') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, help='the resource group of the managed application definition', id_part='resource_group')
        c.argument('application_definition_name', options_list=('--name', '-n'), id_part='name')

    with self.argument_context('managedapp create') as c:
        c.argument('name', options_list=('--name', '-n'), help='name of the new managed application', completer=None)
        c.argument('location', help='the managed application location')
        c.argument('managedapp_definition_id', options_list=('--managedapp-definition-id', '-d'), help='the full qualified managed application definition id')
        c.argument('managedby_resource_group_id', options_list=('--managed-rg-id', '-m'), help='the resource group managed by the managed application')
        c.argument('parameters', help='JSON formatted string or a path to a file with such content', type=file_type)

    with self.argument_context('managedapp definition create') as c:
        c.argument('lock_level', arg_type=get_enum_type(ApplicationLockLevel))
        c.argument('authorizations', options_list=('--authorizations', '-a'), nargs='+', help="space-separated authorization pairs in a format of <principalId>:<roleDefinitionId>")
        c.argument('createUiDefinition', options_list=('--create-ui-definition', '-c'), help='JSON formatted string or a path to a file with such content', type=file_type)
        c.argument('mainTemplate', options_list=('--main-template', '-t'), help='JSON formatted string or a path to a file with such content', type=file_type)

    with self.argument_context('account') as c:
        c.argument('subscription', options_list=['--subscription', '-s'], help='Name or ID of subscription.', completer=get_subscription_id_list)

    with self.argument_context('account management-group') as c:
        c.argument('group_name', options_list=['--name', '-n'])
        c.ignore('_subscription')  # hide global subscription parameter

    with self.argument_context('account management-group show') as c:
        c.argument('expand', options_list=['--expand', '-e'], action='store_true')
        c.argument('recurse', options_list=['--recurse', '-r'], action='store_true')

    with self.argument_context('account management-group create') as c:
        c.argument('display_name', options_list=['--display-name', '-d'])
        c.argument('parent', options_list=['--parent', '-p'])

    with self.argument_context('account management-group update') as c:
        c.argument('display_name', options_list=['--display-name', '-d'])
        c.argument('parent_id', options_list=['--parent', '-p'])
