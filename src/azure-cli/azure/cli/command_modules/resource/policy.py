# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import shlex
import json
from io import StringIO

from azure.cli.command_modules.resource.aaz.latest.policy.assignment._create import Create as AssignmentCreate
from azure.cli.command_modules.resource.aaz.latest.policy.assignment._delete import Delete as AssignmentDelete
from azure.cli.command_modules.resource.aaz.latest.policy.assignment._list import List as AssignmentList
from azure.cli.command_modules.resource.aaz.latest.policy.assignment._show import Show as AssignmentShow
from azure.cli.command_modules.resource.aaz.latest.policy.assignment._update import Update as AssignmentUpdate

from azure.cli.command_modules.resource.aaz.latest.policy.assignment.identity._assign \
    import Assign as AssignmentIdentityAssign
from azure.cli.command_modules.resource.aaz.latest.policy.assignment.identity._remove \
    import Remove as AssignmentIdentityRemove
from azure.cli.command_modules.resource.aaz.latest.policy.assignment.identity._show \
    import Show as AssignmentIdentityShow

from azure.cli.command_modules.resource.aaz.latest.policy.assignment.non_compliance_message._create \
    import Create as NonComplianceMessageCreate
from azure.cli.command_modules.resource.aaz.latest.policy.assignment.non_compliance_message._delete \
    import Delete as NonComplianceMessageDelete
from azure.cli.command_modules.resource.aaz.latest.policy.assignment.non_compliance_message._list \
    import List as NonComplianceMessageList
from azure.cli.command_modules.resource.aaz.latest.policy.assignment.non_compliance_message._show \
    import Show as NonComplianceMessageShow
from azure.cli.command_modules.resource.aaz.latest.policy.assignment.non_compliance_message._update \
    import Update as NonComplianceMessageUpdate

from azure.cli.command_modules.resource.aaz.latest.policy.definition._create import Create as DefinitionCreate
from azure.cli.command_modules.resource.aaz.latest.policy.definition._delete import Delete as DefinitionDelete
from azure.cli.command_modules.resource.aaz.latest.policy.definition._list import List as DefinitionList
from azure.cli.command_modules.resource.aaz.latest.policy.definition._show import Show as DefinitionShow
from azure.cli.command_modules.resource.aaz.latest.policy.definition._update import Update as DefinitionUpdate

from azure.cli.command_modules.resource.aaz.latest.policy.definition.version._create import Create as DefinitionVersionCreate
from azure.cli.command_modules.resource.aaz.latest.policy.definition.version._delete import Delete as DefinitionVersionDelete
from azure.cli.command_modules.resource.aaz.latest.policy.definition.version._list import List as DefinitionVersionList
from azure.cli.command_modules.resource.aaz.latest.policy.definition.version._show import Show as DefinitionVersionShow
from azure.cli.command_modules.resource.aaz.latest.policy.definition.version._update import Update as DefinitionVersionUpdate

from azure.cli.command_modules.resource.aaz.latest.policy.enrollment._create import Create as EnrollmentCreate
from azure.cli.command_modules.resource.aaz.latest.policy.enrollment._delete import Delete as EnrollmentDelete
from azure.cli.command_modules.resource.aaz.latest.policy.enrollment._list import List as EnrollmentList
from azure.cli.command_modules.resource.aaz.latest.policy.enrollment._show import Show as EnrollmentShow
from azure.cli.command_modules.resource.aaz.latest.policy.enrollment._update import Update as EnrollmentUpdate

from azure.cli.command_modules.resource.aaz.latest.policy.exemption._create import Create as ExemptionCreate
from azure.cli.command_modules.resource.aaz.latest.policy.exemption._delete import Delete as ExemptionDelete
from azure.cli.command_modules.resource.aaz.latest.policy.exemption._list import List as ExemptionList
from azure.cli.command_modules.resource.aaz.latest.policy.exemption._show import Show as ExemptionShow
from azure.cli.command_modules.resource.aaz.latest.policy.exemption._update import Update as ExemptionUpdate

from azure.cli.command_modules.resource.aaz.latest.policy.set_definition._create import Create as SetDefinitionCreate
from azure.cli.command_modules.resource.aaz.latest.policy.set_definition._delete import Delete as SetDefinitionDelete
from azure.cli.command_modules.resource.aaz.latest.policy.set_definition._list import List as SetDefinitionList
from azure.cli.command_modules.resource.aaz.latest.policy.set_definition._show import Show as SetDefinitionShow
from azure.cli.command_modules.resource.aaz.latest.policy.set_definition._update import Update as SetDefinitionUpdate

from azure.cli.command_modules.resource.aaz.latest.policy.set_definition.version._create import Create as SetDefinitionVersionCreate
from azure.cli.command_modules.resource.aaz.latest.policy.set_definition.version._delete import Delete as SetDefinitionVersionDelete
from azure.cli.command_modules.resource.aaz.latest.policy.set_definition.version._list import List as SetDefinitionVersionList
from azure.cli.command_modules.resource.aaz.latest.policy.set_definition.version._show import Show as SetDefinitionVersionShow
from azure.cli.command_modules.resource.aaz.latest.policy.set_definition.version._update import Update as SetDefinitionVersionUpdate

from azure.cli.command_modules.resource._client_factory import _resource_policy_client_factory
from azure.cli.core.aaz import AAZAnyTypeArg, has_value, AAZResourceGroupNameArg, AAZStrArg, AAZBoolArg, AAZDictArg
from azure.cli.core.azclierror import InvalidArgumentValueError, ArgumentUsageError
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.decorators import Completer
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id

# --------------------------------------------------------------------------------------------
# Customization for auto-generated Azure Policy CLI commands (cstack: 5/9/2025)
#
# Notes on auto-generation
#  - The behavior of the auto-generated command code required significant customization to
#    work around differences from previous custom code. All customization is performed by
#    overriding generated code. No modification of generated code is present.
#  - The Common class is used for shard methods needed by the customization code.
#  - The Completers class hosts command line completers that were previously registered in
#    the custom commands.
#  - The other classes in this file override generated classes to evoke the correct behavior
#    matching the fully custom commands previously shipped.
# --------------------------------------------------------------------------------------------


# Shared code for policy command customization
class Common:

    @staticmethod
    # Ensure that both --policy and -policy-set-definition are not specified, or that one of them is specified
    def ValidatePolicyDefinitionId(ctx):
        if bool(has_value(ctx.args.policy)) == bool(has_value(ctx.args.policy_set_definition)):
            raise ArgumentUsageError('usage error: --policy NAME_OR_ID | --policy-set-definition NAME_OR_ID')

    # Ensure that --scope is not used with other scoping parameters
    @staticmethod
    def ValidateScope(ctx):
        if has_value(ctx.args.scope) and has_value(ctx.args.resource_group):
            raise ArgumentUsageError('usage error: --scope SCOPE | --resource-group NAME')
        # Should also validate that both --scope and --subscription are not specified together. Unfortunately
        # it's not possible to make this check since there is no way to determine whether the user entered
        # --subscription on the command line. Current behavior is to ignore --subscription if both are provided.

    # If --scope is not provided, set it by subscription or resource group scope
    @staticmethod
    def PopulateScopeFromContext(ctx, cli_ctx):
        if not has_value(ctx.args.scope):
            subscription_id = get_subscription_id(cli_ctx)
            if has_value(ctx.args.resource_group):
                ctx.args.scope = f"/subscriptions/{subscription_id}/resourceGroups/{ctx.args.resource_group}"
            else:
                ctx.args.scope = f"/subscriptions/{subscription_id}"

    # Create role assignment for the system assigned identity of the policy assignment
    # pylint: disable=protected-access
    @staticmethod
    def CreateRoleAssignment(ctx, cli_ctx, assignment):
        from azure.cli.core.commands.arm import assign_identity
        if has_value(ctx.args.identity_scope):
            identity_role = None
            if has_value(ctx.args.role):
                identity_role = ctx.args.role
            assign_identity(
                cli_ctx, lambda: assignment, lambda resource: assignment,
                identity_role._data, ctx.args.identity_scope._data)

    # Implement default identity type behavior for policy assignment create
    @staticmethod
    def ResolveCreateIdentityType(ctx):
        if has_value(ctx.args.identity_scope) or has_value(ctx.args.location) or has_value(ctx.args.role):
            Common.ResolveIdentityType(ctx)

    # Set identity type to system assigned if not specified
    @staticmethod
    def ResolveIdentityType(ctx):
        if not has_value(ctx.args.mi_system_assigned) and not has_value(ctx.args.mi_user_assigned):
            ctx.args.mi_system_assigned = 'True'

    # Implement default scope behavior for policy assignment and exemption list commands
    # pylint: disable=protected-access
    # pylint: disable=attribute-defined-outside-init
    def ResolveScopeForList(self):
        ctx = self.ctx
        if has_value(ctx.args.scope):
            scope_parts = ctx.args.scope._data.split('/')
            if scope_parts[1] == 'providers' and len(scope_parts) > 4:
                ctx.args.management_group = scope_parts[4]
                ctx.args.resource_group = None
            elif scope_parts[1] == 'subscriptions':
                # store subscription from scope for later use
                self.subscription_from_scope = scope_parts[2]
                if len(scope_parts) > 3:
                    ctx.args.resource_group = scope_parts[4]
                else:
                    ctx.args.resource_group = None
            else:
                raise InvalidArgumentValueError("Invalid value in --scope: '%s'" % ctx.args.scope._data)

    # Implement default name behavior for policy assignment and exemption create commands
    @staticmethod
    def GenerateNameIfNone(ctx):
        if not has_value(ctx.args.name):
            import base64
            import uuid
            ctx.args.name = (base64.urlsafe_b64encode(uuid.uuid4().bytes).decode())[:-2]

    # Get policy definition ID from policy name if not specified
    # pylint: disable=protected-access
    @staticmethod
    def ResolvePolicyId(ctx):
        policy_id = ctx.args.policy._data or ctx.args.policy_set_definition._data
        if not is_valid_resource_id(policy_id):
            definition = None
            name = policy_id.split('/')[-1]
            command_string = None
            if has_value(ctx.args.policy):
                command_string = f"policy definition show --name {name}"
            else:
                command_string = f"policy set-definition show --name {name}"

            if policy_id.startswith('/providers'):
                management_group_name = policy_id.split('/')[4]
                command_string = command_string + f" --management-group {management_group_name}"

            try:
                definition = Common.run_cli_deserialize(command_string)
            except Exception as ex:
                raise InvalidArgumentValueError(
                    f"Invalid value in --policy or --policy-set-definition: '{policy_id}'") from ex

            policy_id = definition.get('id')

        ctx.args.policy_set_definition = policy_id

    # Get user assigned identity IDs from names if not specified
    # pylint: disable=protected-access
    # pylint: disable=consider-using-enumerate
    @staticmethod
    def ResolveUserAssignedIdentityId(ctx, cli_ctx):
        from azure.cli.command_modules.resource.custom import _get_resource_id
        if has_value(ctx.args.mi_user_assigned):
            resource_group = ctx.args.resource_group._data if has_value(ctx.args.resource_group) else None
            user_assigned_identities = ctx.args.mi_user_assigned
            for i in range(len(user_assigned_identities)):
                user_assigned_identity = user_assigned_identities[i]._data
                if not is_valid_resource_id(user_assigned_identity):
                    user_assigned_identities[i] = _get_resource_id(
                        cli_ctx, user_assigned_identity, resource_group,
                        'userAssignedIdentities', 'Microsoft.ManagedIdentity')

    # Helper function to check whether a scope is a management group scope
    @staticmethod
    def _is_management_group_scope(scope):
        return scope is not None and scope.lower().startswith("/providers/microsoft.management/managementgroups")

    # Validate that not_scopes are valid subscription or management group scopes
    # pylint: disable=protected-access
    @staticmethod
    def ValidateNotScopes(ctx):
        not_scopes = ctx.args.not_scopes
        if has_value(not_scopes):
            for not_scope in not_scopes:
                id_arg = not_scope._data
                id_parts = parse_resource_id(id_arg)
                if not (id_parts.get('subscription') or Common._is_management_group_scope(id_arg)):
                    raise InvalidArgumentValueError("Invalid resource ID value in --not-scopes: '%s'" % id_arg)

    # Fix not_scopes output to be a list of strings instead of a single string
    def AdjustNotScopesOutput(self):
        notScopes = self.deserialize_output(self.ctx.vars.instance.properties.notScopes)
        if notScopes and len(notScopes) == 1:
            split = notScopes[0].split(' ')
            self.ctx.vars.instance.properties.notScopes = split

    # Change UTC format from Zulu to +00:00
    @staticmethod
    def AdjustUTCFormat(exemption):
        if exemption.properties.expires_on:
            exemption.properties.expires_on = exemption.properties.expires_on._data.replace('Z', '+00:00')

    # Apply filter to list commands based on --disable-scope-strict-match argument
    @staticmethod
    def ApplyListFilter(ctx):
        if not has_value(ctx.args.filter):
            if has_value(ctx.args.disable_scope_strict_match):
                ctx.args.filter = "atScopeAndBelow()"
            else:
                ctx.args.filter = "atExactScope()"

    # Helper to execute Azure CLI command and return the output as JSON
    @staticmethod
    def run_cli_deserialize(command):
        from azure.cli.core.util import run_az_cmd
        stdout_buf = StringIO()
        result = run_az_cmd(shlex.split(command), out_file=stdout_buf)
        exit_code = result.exit_code or 0
        output = stdout_buf.getvalue()

        # Deserialize if the command was successful
        if exit_code == 0:
            return json.loads(output)

        return None

    @staticmethod
    def SetSchemaNullable(obj, path=''):
        if hasattr(obj, '_fields'):
            for key, value in obj._fields.items():
                new_path = f"{path}._fields.{key}" if path else key
                Common.SetSchemaNullable(value, new_path)
        elif hasattr(obj, '_element'):
            if hasattr(obj._element, 'DataType'):
                if obj._element.DataType is None:
                    obj._element._nullable = True
            else:
                new_path = f"{path}._element"
                Common.SetSchemaNullable(obj._element, new_path)

    @staticmethod
    def SetUndefinedNone(value):
        from azure.cli.core.aaz import AAZUndefined
        if isinstance(value, dict):
            for _, item in value.items():
                Common.SetUndefinedNone(item)
        elif isinstance(value, list):
            for item in value:
                Common.SetUndefinedNone(item)
        elif hasattr(value, 'data'):
            if value.data == AAZUndefined:
                value.data = None
            else:
                Common.SetUndefinedNone(value.data)

    # Allow legacy 'key=value [key=value ...]' partial shorthand for an
    # AAZAnyTypeArg, in addition to its native JSON / full-shorthand / @file inputs.
    @staticmethod
    def AllowKeyValueShorthand(any_type_arg):
        # pylint: disable=protected-access
        from azure.cli.core.aaz._arg_action import AAZAnyTypeArgAction
        original_build = type(any_type_arg)._build_cmd_action

        def build():
            parent_action = original_build(any_type_arg)
            if not issubclass(parent_action, AAZAnyTypeArgAction):
                return parent_action

            class Action(parent_action):
                @classmethod
                def decode_str(cls, value):
                    if isinstance(value, str):
                        stripped = value.strip()
                        # Skip JSON / list / @file / quoted -- let AAZ handle.
                        if stripped and stripped[0] not in ('{', '[', '@', '"', "'"):
                            parts = stripped.split()
                            if parts and all(
                                    '=' in p and p.split('=', 1)[0] for p in parts):
                                return dict(p.split('=', 1) for p in parts)
                    return super().decode_str(value)

            return Action

        any_type_arg._build_cmd_action = build

# Completers for policy command arguments
class Completers:

    @staticmethod
    @Completer
    def get_policy_definition_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        policy_client = _resource_policy_client_factory(cmd.cli_ctx)
        result = policy_client.policy_definitions.list(filter="policyType eq 'Custom'")
        return [i.name for i in result]

    @staticmethod
    @Completer
    def get_policy_set_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        policy_client = _resource_policy_client_factory(cmd.cli_ctx)
        result = policy_client.policy_set_definitions.list(filter="policyType eq 'Custom'")
        return [i.name for i in result]

    @staticmethod
    @Completer
    def get_policy_assignment_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        policy_client = _resource_policy_client_factory(cmd.cli_ctx)
        result = policy_client.policy_assignments.list()
        return [i.name for i in result]

    @staticmethod
    @Completer
    def get_policy_exemption_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        policy_client = _resource_policy_client_factory(cmd.cli_ctx)
        result = policy_client.policy_exemptions.list()
        return [i.name for i in result]

    @staticmethod
    @Completer
    def get_policy_enrollment_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        policy_client = _resource_policy_client_factory(cmd.cli_ctx)
        result = policy_client.policy_enrollments.list()
        return [i.name for i in result]

    @staticmethod
    @Completer
    def get_policy_definition_version_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        policy_client = _resource_policy_client_factory(cmd.cli_ctx)
        if hasattr(namespace, 'policy_definition_name') and namespace.policy_definition_name:
            result = policy_client.policy_definition_versions.list(namespace.policy_definition_name)
            return [i.name for i in result]
        return []

    @staticmethod
    @Completer
    def get_policy_set_definition_version_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        policy_client = _resource_policy_client_factory(cmd.cli_ctx)
        if hasattr(namespace, 'policy_set_definition_name') and namespace.policy_set_definition_name:
            result = policy_client.policy_set_definition_versions.list(namespace.policy_set_definition_name)
            return [i.name for i in result]
        return []


class PolicyAssignmentCreate(AssignmentCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._required = False                # pylint: disable=protected-access
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        args_schema.policy = AAZStrArg(
            options=['--policy'],
            help='The name or resource ID of the policy definition or policy set definition to be assigned.')
        args_schema.identity_scope = AAZStrArg(
            options=['--identity-scope'],
            help='Scope that the system assigned identity can access.')
        args_schema.role = AAZStrArg(
            options=['--role'],
            help='Role name or id that will be assigned to the managed identity.')
        return args_schema

    class PolicyAssignmentsCreate(AssignmentCreate.PolicyAssignmentsCreate):

        @staticmethod
        def serialize_content(value, required=False):
            # pylint: disable=protected-access
            Common.SetUndefinedNone(value._data)
            content = AssignmentCreate.PolicyAssignmentsCreate.serialize_content(value, required)
            return content

        @classmethod
        def _build_schema_on_201(cls):
            _schema = super()._build_schema_on_201()
            Common.SetSchemaNullable(_schema)
            return _schema

    def pre_operations(self):
        Common.ValidatePolicyDefinitionId(self.ctx)
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)
        Common.ValidateNotScopes(self.ctx)
        Common.GenerateNameIfNone(self.ctx)
        Common.ResolvePolicyId(self.ctx)
        Common.ResolveUserAssignedIdentityId(self.ctx, self.cli_ctx)
        Common.ResolveCreateIdentityType(self.ctx)

    def _execute_operations(self):
        self.pre_operations()
        self.PolicyAssignmentsCreate(ctx=self.ctx)()
        self.post_operations()

    def post_operations(self):
        Common.CreateRoleAssignment(self.ctx, self.cli_ctx, self.ctx.vars.instance)

    # pylint: disable=arguments-differ
    def _output(self):
        Common.AdjustNotScopesOutput(self)
        result = super()._output(self)
        return result


class PolicyAssignmentDelete(AssignmentDelete):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_assignment_completion_list
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)


class PolicyAssignmentList(AssignmentList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope = AAZStrArg(
            options=['--scope'],
            help='Scope at which to list applicable policy assignments. '
                 'If scope is not provided, the scope will be the implied or specified subscription.')
        args_schema.disable_scope_strict_match = AAZBoolArg(
            options=['-d', '--disable-scope-strict-match'],
            help='Include policy assignments either inherited from parent scopes or at child scopes.')
        return args_schema

    # subscription provided by --scope argument (may be different from context subscription)
    def __init__(self, loader):
        super().__init__(loader)
        self.subscription_from_scope = None

    class PolicyAssignmentsListForManagementGroup(AssignmentList.PolicyAssignmentsListForManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicyAssignmentsListForResourceGroup(AssignmentList.PolicyAssignmentsListForResourceGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicyAssignmentsList(AssignmentList.PolicyAssignmentsList):

        def __init__(self, ctx, subscription_from_scope):
            super().__init__(ctx)
            self.subscription_from_scope = subscription_from_scope

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

        @property
        def url(self):
            if self.subscription_from_scope is not None:
                return self.client.format_url(
                    "/subscriptions/{subscriptionId}/providers/Microsoft.Authorization/policyAssignments",
                    subscriptionId=self.subscription_from_scope
                )

            return super().url

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.ResolveScopeForList(self)
        Common.ApplyListFilter(self.ctx)

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.management_group):
            self.PolicyAssignmentsListForManagementGroup(ctx=self.ctx)()
        elif has_value(self.ctx.args.resource_group):
            self.PolicyAssignmentsListForResourceGroup(ctx=self.ctx)()
        else:
            self.PolicyAssignmentsList(ctx=self.ctx, subscription_from_scope=self.subscription_from_scope)()

        self.post_operations()


class PolicyAssignmentShow(AssignmentShow):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_assignment_completion_list
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    @classmethod
    def _build_schema_on_200(cls):
        _schema = super()._build_schema_on_200()
        Common.SetSchemaNullable(_schema)
        return _schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)


class PolicyAssignmentUpdate(AssignmentUpdate):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_assignment_completion_list
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        args_schema.policy = AAZStrArg(
            options=['--policy'],
            help='The name or resource ID of the policy definition or policy set definition to be assigned.')
        return args_schema

    class PolicyAssignmentsCreate(AssignmentUpdate.PolicyAssignmentsCreate):

        @staticmethod
        def serialize_content(value, required=False):
            Common.SetUndefinedNone(value._data)
            content = AssignmentUpdate.PolicyAssignmentsCreate.serialize_content(value, required)
            return content

    class PolicyAssignmentsGet(AssignmentUpdate.PolicyAssignmentsGet):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)
        Common.ValidateNotScopes(self.ctx)

    def _execute_operations(self):
        self.pre_operations()
        self.PolicyAssignmentsGet(ctx=self.ctx)()
        self.pre_instance_update(self.ctx.vars.instance)
        self.InstanceUpdateByJson(ctx=self.ctx)()
        self.InstanceUpdateByGeneric(ctx=self.ctx)()
        self.post_instance_update(self.ctx.vars.instance)
        self.PolicyAssignmentsCreate(ctx=self.ctx)()
        self.post_operations()

    # pylint: disable=arguments-differ
    def _output(self):
        Common.AdjustNotScopesOutput(self)
        result = super()._output(self)
        return result


class PolicyAssignmentIdentityAssign(AssignmentIdentityAssign):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        args_schema.identity_scope = AAZStrArg(
            options=['--identity-scope'],
            help='Scope that the system assigned identity can access.')
        args_schema.role = AAZStrArg(
            options=['--role'],
            help='Role name or id that will be assigned to the managed identity.')
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)
        Common.ResolveIdentityType(self.ctx)

    def post_operations(self):
        Common.CreateRoleAssignment(self.ctx, self.cli_ctx, self.ctx.vars.instance)


class PolicyAssignmentIdentityRemove(AssignmentIdentityRemove):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)
        Common.ResolveIdentityType(self.ctx)


class PolicyAssignmentIdentityShow(AssignmentIdentityShow):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)


class PolicyAssignmentNonComplianceMessageCreate(NonComplianceMessageCreate):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope._required = False
        args_schema.policy_definition_reference_id._required = False
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)


class PolicyAssignmentNonComplianceMessageDelete(NonComplianceMessageDelete):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope._required = False
        args_schema.policy_definition_reference_id._required = False
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)


class PolicyAssignmentNonComplianceMessageList(NonComplianceMessageList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)

    # pylint: disable=arguments-differ
    def _output(self):
        value = self.ctx.selectors.subresource.get()
        if has_value(value):
            result = self.deserialize_output(value, client_flatten=True)
        else:
            result = None
        return result


class PolicyAssignmentNonComplianceMessageShow(NonComplianceMessageShow):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope._required = False
        args_schema.policy_definition_reference_id._required = False
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)


class PolicyAssignmentNonComplianceMessageUpdate(NonComplianceMessageUpdate):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.policy_definition_reference_id._required = False
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)


class PolicyDefinitionCreate(DefinitionCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        Common.SetSchemaNullable(args_schema)
        Common.AllowKeyValueShorthand(args_schema.metadata)
        return args_schema

    class PolicyDefinitionsCreateOrUpdateAtManagementGroup(
            DefinitionCreate.PolicyDefinitionsCreateOrUpdateAtManagementGroup):

        @classmethod
        def _build_schema_on_201(cls):
            _schema = super()._build_schema_on_201()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            # pylint: disable=protected-access
            Common.SetUndefinedNone(value._data)
            content = DefinitionCreate.PolicyDefinitionsCreateOrUpdateAtManagementGroup.serialize_content(
                value, required)
            return content

    class PolicyDefinitionsCreateOrUpdate(DefinitionCreate.PolicyDefinitionsCreateOrUpdate):

        @classmethod
        def _build_schema_on_201(cls):
            _schema = super()._build_schema_on_201()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            # pylint: disable=protected-access
            Common.SetUndefinedNone(value._data)
            content = DefinitionCreate.PolicyDefinitionsCreateOrUpdate.serialize_content(value, required)
            return content

    def pre_operations(self):
        pass

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.name) and has_value(self.ctx.args.management_group):
            self.PolicyDefinitionsCreateOrUpdateAtManagementGroup(ctx=self.ctx)()
        else:
            self.PolicyDefinitionsCreateOrUpdate(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicyDefinitionDelete(DefinitionDelete):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_definition_completion_list
        return args_schema


class PolicyDefinitionList(DefinitionList):

    class PolicyDefinitionsListByManagementGroup(DefinitionList.PolicyDefinitionsListByManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicyDefinitionsList(DefinitionList.PolicyDefinitionsList):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    def pre_operations(self):
        pass

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.management_group):
            self.PolicyDefinitionsListByManagementGroup(ctx=self.ctx)()
        else:
            self.PolicyDefinitionsList(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicyDefinitionShow(DefinitionShow):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_definition_completion_list
        return args_schema

    class PolicyDefinitionsGetBuiltIn(DefinitionShow.PolicyDefinitionsGet):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

        @property
        def url(self):
            return self.client.format_url(
                "/providers/Microsoft.Authorization/policyDefinitions/{policyDefinitionName}",
                **self.url_parameters
            )

        @property
        def url_parameters(self):
            parameters = {
                **self.serialize_url_param(
                    'policyDefinitionName', self.ctx.args.name,
                    required=True,
                )
            }
            return parameters

    class PolicyDefinitionsGetAtManagementGroup(DefinitionShow.PolicyDefinitionsGetAtManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicyDefinitionsGet(DefinitionShow.PolicyDefinitionsGet):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    def pre_operations(self):
        pass

    def _execute_operations(self):

        self.pre_operations()
        done = False
        if has_value(self.ctx.args.name) and not has_value(self.ctx.args.management_group):
            try:
                self.PolicyDefinitionsGetBuiltIn(ctx=self.ctx)()
                done = True
            except ResourceNotFoundError:
                pass

        if not done and has_value(self.ctx.args.name) and has_value(self.ctx.args.management_group):
            self.PolicyDefinitionsGetAtManagementGroup(ctx=self.ctx)()
        elif not done:
            self.PolicyDefinitionsGet(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicyDefinitionUpdate(DefinitionUpdate):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_definition_completion_list
        Common.AllowKeyValueShorthand(args_schema.metadata)
        return args_schema

    class PolicyDefinitionsCreateOrUpdateAtManagementGroup(
            DefinitionUpdate.PolicyDefinitionsCreateOrUpdateAtManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            Common.SetUndefinedNone(value._data)
            content = DefinitionUpdate.PolicyDefinitionsCreateOrUpdateAtManagementGroup.serialize_content(
                value, required)
            return content

    class PolicyDefinitionsCreateOrUpdate(DefinitionUpdate.PolicyDefinitionsCreateOrUpdate):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            Common.SetUndefinedNone(value._data)
            content = DefinitionUpdate.PolicyDefinitionsCreateOrUpdate.serialize_content(value, required)
            return content

    class PolicyDefinitionsGetAtManagementGroup(DefinitionUpdate.PolicyDefinitionsGetAtManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicyDefinitionsGet(DefinitionUpdate.PolicyDefinitionsGet):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    # pylint: disable=too-few-public-methods
    class InstanceUpdateByJson(DefinitionUpdate.InstanceUpdateByJson):
        pass

    # pylint: disable=too-few-public-methods
    class InstanceUpdateByGeneric(DefinitionUpdate.InstanceUpdateByGeneric):
        pass

    def pre_operations(self):
        pass

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.name) and has_value(self.ctx.args.management_group):
            self.PolicyDefinitionsGetAtManagementGroup(ctx=self.ctx)()
            self.InstanceUpdateByJson(ctx=self.ctx)()
            self.InstanceUpdateByGeneric(ctx=self.ctx)()
            self.PolicyDefinitionsCreateOrUpdateAtManagementGroup(ctx=self.ctx)()
        else:
            self.PolicyDefinitionsGet(ctx=self.ctx)()
            self.InstanceUpdateByJson(ctx=self.ctx)()
            self.InstanceUpdateByGeneric(ctx=self.ctx)()
            self.PolicyDefinitionsCreateOrUpdate(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicyDefinitionVersionCreate(DefinitionVersionCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        Common.SetSchemaNullable(args_schema)
        return args_schema

    class PolicyDefinitionVersionsCreateOrUpdateAtManagementGroup(
            DefinitionVersionCreate.PolicyDefinitionVersionsCreateOrUpdateAtManagementGroup):

        @classmethod
        def _build_schema_on_201(cls):
            _schema = super()._build_schema_on_201()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            Common.SetUndefinedNone(value._data)
            content = DefinitionVersionCreate.PolicyDefinitionVersionsCreateOrUpdateAtManagementGroup.serialize_content(
                value, required)
            return content

    class PolicyDefinitionVersionsCreateOrUpdate(DefinitionVersionCreate.PolicyDefinitionVersionsCreateOrUpdate):

        @classmethod
        def _build_schema_on_201(cls):
            _schema = super()._build_schema_on_201()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            Common.SetUndefinedNone(value._data)
            content = DefinitionVersionCreate.PolicyDefinitionVersionsCreateOrUpdate.serialize_content(value, required)
            return content

    def pre_operations(self):
        # Set properties.version to match the version argument
        if has_value(self.ctx.args.version):
            self.ctx.args.properties.version = self.ctx.args.version

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.policy_definition_name) and has_value(self.ctx.args.management_group):
            self.PolicyDefinitionVersionsCreateOrUpdateAtManagementGroup(ctx=self.ctx)()
        else:
            self.PolicyDefinitionVersionsCreateOrUpdate(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicyDefinitionVersionDelete(DefinitionVersionDelete):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.version._completer = Completers.get_policy_definition_version_completion_list
        return args_schema


class PolicyDefinitionVersionList(DefinitionVersionList):

    class PolicyDefinitionVersionsListByManagementGroup(
            DefinitionVersionList.PolicyDefinitionVersionsListByManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicyDefinitionVersionsList(DefinitionVersionList.PolicyDefinitionVersionsList):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    def pre_operations(self):
        pass

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.management_group):
            self.PolicyDefinitionVersionsListByManagementGroup(ctx=self.ctx)()
        else:
            self.PolicyDefinitionVersionsList(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicyDefinitionVersionShow(DefinitionVersionShow):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.version._completer = Completers.get_policy_definition_version_completion_list
        return args_schema

    class PolicyDefinitionVersionsGetAtManagementGroup(
            DefinitionVersionShow.PolicyDefinitionVersionsGetAtManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicyDefinitionVersionsGet(DefinitionVersionShow.PolicyDefinitionVersionsGet):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    def pre_operations(self):
        pass

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.policy_definition_name) and has_value(self.ctx.args.management_group):
            self.PolicyDefinitionVersionsGetAtManagementGroup(ctx=self.ctx)()
        else:
            self.PolicyDefinitionVersionsGet(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicyDefinitionVersionUpdate(DefinitionVersionUpdate):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.version._completer = Completers.get_policy_definition_version_completion_list
        return args_schema

    class PolicyDefinitionVersionsCreateOrUpdateAtManagementGroup(
            DefinitionVersionUpdate.PolicyDefinitionVersionsCreateOrUpdateAtManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            Common.SetUndefinedNone(value._data)
            content = DefinitionVersionUpdate.PolicyDefinitionVersionsCreateOrUpdateAtManagementGroup.serialize_content(
                value, required)
            return content

    class PolicyDefinitionVersionsCreateOrUpdate(DefinitionVersionUpdate.PolicyDefinitionVersionsCreateOrUpdate):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            Common.SetUndefinedNone(value._data)
            content = DefinitionVersionUpdate.PolicyDefinitionVersionsCreateOrUpdate.serialize_content(value, required)
            return content

    class PolicyDefinitionVersionsGetAtManagementGroup(
            DefinitionVersionUpdate.PolicyDefinitionVersionsGetAtManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicyDefinitionVersionsGet(DefinitionVersionUpdate.PolicyDefinitionVersionsGet):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class InstanceUpdateByJson(DefinitionVersionUpdate.InstanceUpdateByJson):
        pass

    class InstanceUpdateByGeneric(DefinitionVersionUpdate.InstanceUpdateByGeneric):
        pass

    def pre_operations(self):
        pass

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.policy_definition_name) and has_value(self.ctx.args.management_group):
            self.PolicyDefinitionVersionsGetAtManagementGroup(ctx=self.ctx)()
            self.InstanceUpdateByJson(ctx=self.ctx)()
            self.InstanceUpdateByGeneric(ctx=self.ctx)()
            self.PolicyDefinitionVersionsCreateOrUpdateAtManagementGroup(ctx=self.ctx)()
        else:
            self.PolicyDefinitionVersionsGet(ctx=self.ctx)()
            self.InstanceUpdateByJson(ctx=self.ctx)()
            self.InstanceUpdateByGeneric(ctx=self.ctx)()
            self.PolicyDefinitionVersionsCreateOrUpdate(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicyEnrollmentCreate(EnrollmentCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._required = False            # pylint: disable=protected-access
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)
        Common.GenerateNameIfNone(self.ctx)

    def post_operations(self):
        Common.AdjustUTCFormat(self.ctx.vars.instance)


class PolicyEnrollmentDelete(EnrollmentDelete):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_enrollment_completion_list
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)


class PolicyEnrollmentList(EnrollmentList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope = AAZStrArg(
            options=['--scope'],
            help='Scope at which to list applicable policy enrollments. '
                 'If scope is not provided, the scope will be the implied or specified subscription.')
        args_schema.disable_scope_strict_match = AAZBoolArg(
            options=['-d', '--disable-scope-strict-match'],
            help='Include policy enrollments either inherited from parent scopes or at child scopes.')
        return args_schema

    # subscription provided by --scope argument (may be different from context subscription)
    def __init__(self, loader):
        super().__init__(loader)
        self.subscription_from_scope = None

    class PolicyEnrollmentsListForManagementGroup(EnrollmentList.PolicyEnrollmentsListForManagementGroup):
        pass

    class PolicyEnrollmentsListForResourceGroup(EnrollmentList.PolicyEnrollmentsListForResourceGroup):
        pass

    class PolicyEnrollmentsList(EnrollmentList.PolicyEnrollmentsList):
        def __init__(self, ctx, subscription_from_scope):
            super().__init__(ctx)
            self.subscription_from_scope = subscription_from_scope

        @property
        def url(self):
            if self.subscription_from_scope is not None:
                return self.client.format_url(
                    "/subscriptions/{subscriptionId}/providers/Microsoft.Authorization/policyEnrollments",
                    subscriptionId=self.subscription_from_scope
                )

            return super().url

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.ResolveScopeForList(self)
        Common.ApplyListFilter(self.ctx)

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.management_group):
            self.PolicyEnrollmentsListForManagementGroup(ctx=self.ctx)()
        elif has_value(self.ctx.args.resource_group):
            self.PolicyEnrollmentsListForResourceGroup(ctx=self.ctx)()
        else:
            self.PolicyEnrollmentsList(ctx=self.ctx, subscription_from_scope=self.subscription_from_scope)()

        self.post_operations()

    def post_operations(self):
        listing = self.ctx.vars.instance.value
        for item in listing:
            Common.AdjustUTCFormat(item)


class PolicyEnrollmentShow(EnrollmentShow):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_enrollment_completion_list
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)

    def post_operations(self):
        Common.AdjustUTCFormat(self.ctx.vars.instance)


class PolicyEnrollmentUpdate(EnrollmentUpdate):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_enrollment_completion_list
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)

    def post_operations(self):
        Common.AdjustUTCFormat(self.ctx.vars.instance)


class PolicyExemptionCreate(ExemptionCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._required = False            # pylint: disable=protected-access
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)
        Common.GenerateNameIfNone(self.ctx)

    def post_operations(self):
        Common.AdjustUTCFormat(self.ctx.vars.instance)


class PolicyExemptionDelete(ExemptionDelete):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_exemption_completion_list
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)


class PolicyExemptionList(ExemptionList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope = AAZStrArg(
            options=['--scope'],
            help='Scope at which to list applicable policy exemptions. '
                 'If scope is not provided, the scope will be the implied or specified subscription.')
        args_schema.disable_scope_strict_match = AAZBoolArg(
            options=['-d', '--disable-scope-strict-match'],
            help='Include policy exemptions either inherited from parent scopes or at child scopes.')
        return args_schema

    # subscription provided by --scope argument (may be different from context subscription)
    def __init__(self, loader):
        super().__init__(loader)
        self.subscription_from_scope = None

    class PolicyExemptionsListForManagementGroup(ExemptionList.PolicyExemptionsListForManagementGroup):
        pass

    class PolicyExemptionsListForResourceGroup(ExemptionList.PolicyExemptionsListForResourceGroup):
        pass

    class PolicyExemptionsList(ExemptionList.PolicyExemptionsList):
        def __init__(self, ctx, subscription_from_scope):
            super().__init__(ctx)
            self.subscription_from_scope = subscription_from_scope

        @property
        def url(self):
            if self.subscription_from_scope is not None:
                return self.client.format_url(
                    "/subscriptions/{subscriptionId}/providers/Microsoft.Authorization/policyExemptions",
                    subscriptionId=self.subscription_from_scope
                )

            return super().url

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.ResolveScopeForList(self)
        Common.ApplyListFilter(self.ctx)

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.management_group):
            self.PolicyExemptionsListForManagementGroup(ctx=self.ctx)()
        elif has_value(self.ctx.args.resource_group):
            self.PolicyExemptionsListForResourceGroup(ctx=self.ctx)()
        else:
            self.PolicyExemptionsList(ctx=self.ctx, subscription_from_scope=self.subscription_from_scope)()

        self.post_operations()

    def post_operations(self):
        listing = self.ctx.vars.instance.value
        for item in listing:
            Common.AdjustUTCFormat(item)


class PolicyExemptionShow(ExemptionShow):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_exemption_completion_list
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)

    def post_operations(self):
        Common.AdjustUTCFormat(self.ctx.vars.instance)


class PolicyExemptionUpdate(ExemptionUpdate):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_exemption_completion_list
        args_schema.scope._required = False               # pylint: disable=protected-access
        args_schema.resource_group = AAZResourceGroupNameArg()
        return args_schema

    def pre_operations(self):
        Common.ValidateScope(self.ctx)
        Common.PopulateScopeFromContext(self.ctx, self.cli_ctx)

    def post_operations(self):
        Common.AdjustUTCFormat(self.ctx.vars.instance)


class PolicySetDefinitionCreate(SetDefinitionCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        Common.SetSchemaNullable(args_schema)
        return args_schema

    class PolicySetDefinitionsCreateOrUpdateAtManagementGroup(
            SetDefinitionCreate.PolicySetDefinitionsCreateOrUpdateAtManagementGroup):

        @classmethod
        def _build_schema_on_201(cls):
            _schema = super()._build_schema_on_201()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            # pylint: disable=protected-access
            Common.SetUndefinedNone(value._data)
            content = SetDefinitionCreate.PolicySetDefinitionsCreateOrUpdateAtManagementGroup.serialize_content(
                value, required)
            return content

    class PolicySetDefinitionsCreateOrUpdate(SetDefinitionCreate.PolicySetDefinitionsCreateOrUpdate):

        @classmethod
        def _build_schema_on_201(cls):
            _schema = super()._build_schema_on_201()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            # pylint: disable=protected-access
            Common.SetUndefinedNone(value._data)
            content = SetDefinitionCreate.PolicySetDefinitionsCreateOrUpdate.serialize_content(value, required)
            return content

    def pre_operations(self):
        pass

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.name) and has_value(self.ctx.args.management_group):
            self.PolicySetDefinitionsCreateOrUpdateAtManagementGroup(ctx=self.ctx)()
        else:
            self.PolicySetDefinitionsCreateOrUpdate(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicySetDefinitionDelete(SetDefinitionDelete):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_set_completion_list
        return args_schema


class PolicySetDefinitionList(SetDefinitionList):

    class PolicySetDefinitionsListByManagementGroup(SetDefinitionList.PolicySetDefinitionsListByManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicySetDefinitionsList(SetDefinitionList.PolicySetDefinitionsList):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    def pre_operations(self):
        pass

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.management_group):
            self.PolicySetDefinitionsListByManagementGroup(ctx=self.ctx)()
        else:
            self.PolicySetDefinitionsList(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicySetDefinitionShow(SetDefinitionShow):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_set_completion_list
        return args_schema

    class PolicySetDefinitionsGetBuiltIn(SetDefinitionShow.PolicySetDefinitionsGet):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

        @property
        def url(self):
            return self.client.format_url(
                "/providers/Microsoft.Authorization/policySetDefinitions/{policySetDefinitionName}",
                **self.url_parameters
            )

        @property
        def url_parameters(self):
            parameters = {
                **self.serialize_url_param(
                    'policySetDefinitionName', self.ctx.args.name,
                    required=True,
                )
            }
            return parameters

    class PolicySetDefinitionsGetAtManagementGroup(SetDefinitionShow.PolicySetDefinitionsGetAtManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicySetDefinitionsGet(SetDefinitionShow.PolicySetDefinitionsGet):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    def pre_operations(self):
        pass

    def _execute_operations(self):
        self.pre_operations()
        done = False
        if has_value(self.ctx.args.name) and not has_value(self.ctx.args.management_group):
            try:
                self.PolicySetDefinitionsGetBuiltIn(ctx=self.ctx)()
                done = True
            except ResourceNotFoundError:
                pass

        if not done and has_value(self.ctx.args.name) and has_value(self.ctx.args.management_group):
            self.PolicySetDefinitionsGetAtManagementGroup(ctx=self.ctx)()
        elif not done:
            self.PolicySetDefinitionsGet(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicySetDefinitionUpdate(SetDefinitionUpdate):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._completer = Completers.get_policy_set_completion_list
        return args_schema

    class PolicySetDefinitionsCreateOrUpdateAtManagementGroup(
            SetDefinitionUpdate.PolicySetDefinitionsCreateOrUpdateAtManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            Common.SetUndefinedNone(value._data)
            content = SetDefinitionUpdate.PolicySetDefinitionsCreateOrUpdateAtManagementGroup.serialize_content(
                value, required)
            return content

    class PolicySetDefinitionsCreateOrUpdate(SetDefinitionUpdate.PolicySetDefinitionsCreateOrUpdate):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            Common.SetUndefinedNone(value._data)
            content = SetDefinitionUpdate.PolicySetDefinitionsCreateOrUpdate.serialize_content(value, required)
            return content

    class PolicySetDefinitionsGetAtManagementGroup(SetDefinitionUpdate.PolicySetDefinitionsGetAtManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicySetDefinitionsGet(SetDefinitionUpdate.PolicySetDefinitionsGet):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    # pylint: disable=too-few-public-methods
    class InstanceUpdateByJson(SetDefinitionUpdate.InstanceUpdateByJson):
        pass

    # pylint: disable=too-few-public-methods
    class InstanceUpdateByGeneric(SetDefinitionUpdate.InstanceUpdateByGeneric):
        pass

    def pre_operations(self):
        pass

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.name) and has_value(self.ctx.args.management_group):
            self.PolicySetDefinitionsGetAtManagementGroup(ctx=self.ctx)()
            self.InstanceUpdateByJson(ctx=self.ctx)()
            self.InstanceUpdateByGeneric(ctx=self.ctx)()
            self.PolicySetDefinitionsCreateOrUpdateAtManagementGroup(ctx=self.ctx)()
        else:
            self.PolicySetDefinitionsGet(ctx=self.ctx)()
            self.InstanceUpdateByJson(ctx=self.ctx)()
            self.InstanceUpdateByGeneric(ctx=self.ctx)()
            self.PolicySetDefinitionsCreateOrUpdate(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicySetDefinitionVersionCreate(SetDefinitionVersionCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        Common.SetSchemaNullable(args_schema)
        return args_schema

    class PolicySetDefinitionVersionsCreateOrUpdateAtManagementGroup(
            SetDefinitionVersionCreate.PolicySetDefinitionVersionsCreateOrUpdateAtManagementGroup):

        @classmethod
        def _build_schema_on_201(cls):
            _schema = super()._build_schema_on_201()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            Common.SetUndefinedNone(value._data)
            content = SetDefinitionVersionCreate.PolicySetDefinitionVersionsCreateOrUpdateAtManagementGroup.serialize_content(
                value, required)
            return content

    class PolicySetDefinitionVersionsCreateOrUpdate(SetDefinitionVersionCreate.PolicySetDefinitionVersionsCreateOrUpdate):

        @classmethod
        def _build_schema_on_201(cls):
            _schema = super()._build_schema_on_201()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            Common.SetUndefinedNone(value._data)
            content = SetDefinitionVersionCreate.PolicySetDefinitionVersionsCreateOrUpdate.serialize_content(value, required)
            return content

    def pre_operations(self):
        # Set properties.version to match the version argument
        if has_value(self.ctx.args.version):
            self.ctx.args.properties.version = self.ctx.args.version

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.policy_set_definition_name) and has_value(self.ctx.args.management_group):
            self.PolicySetDefinitionVersionsCreateOrUpdateAtManagementGroup(ctx=self.ctx)()
        else:
            self.PolicySetDefinitionVersionsCreateOrUpdate(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicySetDefinitionVersionDelete(SetDefinitionVersionDelete):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.version._completer = Completers.get_policy_set_definition_version_completion_list
        return args_schema


class PolicySetDefinitionVersionList(SetDefinitionVersionList):

    class PolicySetDefinitionVersionsListByManagementGroup(
            SetDefinitionVersionList.PolicySetDefinitionVersionsListByManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicySetDefinitionVersionsList(SetDefinitionVersionList.PolicySetDefinitionVersionsList):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    def pre_operations(self):
        pass

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.management_group):
            self.PolicySetDefinitionVersionsListByManagementGroup(ctx=self.ctx)()
        else:
            self.PolicySetDefinitionVersionsList(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicySetDefinitionVersionShow(SetDefinitionVersionShow):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.version._completer = Completers.get_policy_set_definition_version_completion_list
        return args_schema

    class PolicySetDefinitionVersionsGetAtManagementGroup(
            SetDefinitionVersionShow.PolicySetDefinitionVersionsGetAtManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicySetDefinitionVersionsGet(SetDefinitionVersionShow.PolicySetDefinitionVersionsGet):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    def pre_operations(self):
        pass

    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.policy_set_definition_name) and has_value(self.ctx.args.management_group):
            self.PolicySetDefinitionVersionsGetAtManagementGroup(ctx=self.ctx)()
        else:
            self.PolicySetDefinitionVersionsGet(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass


class PolicySetDefinitionVersionUpdate(SetDefinitionVersionUpdate):

    # pylint: disable=protected-access
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.version._completer = Completers.get_policy_set_definition_version_completion_list
        return args_schema

    class PolicySetDefinitionVersionsCreateOrUpdateAtManagementGroup(
            SetDefinitionVersionUpdate.PolicySetDefinitionVersionsCreateOrUpdateAtManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            Common.SetUndefinedNone(value._data)
            content = SetDefinitionVersionUpdate.PolicySetDefinitionVersionsCreateOrUpdateAtManagementGroup.serialize_content(
                value, required)
            return content

    class PolicySetDefinitionVersionsCreateOrUpdate(SetDefinitionVersionUpdate.PolicySetDefinitionVersionsCreateOrUpdate):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

        @staticmethod
        def serialize_content(value, required=False):
            Common.SetUndefinedNone(value._data)
            content = SetDefinitionVersionUpdate.PolicySetDefinitionVersionsCreateOrUpdate.serialize_content(value, required)
            return content

    class PolicySetDefinitionVersionsGetAtManagementGroup(
            SetDefinitionVersionUpdate.PolicySetDefinitionVersionsGetAtManagementGroup):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class PolicySetDefinitionVersionsGet(SetDefinitionVersionUpdate.PolicySetDefinitionVersionsGet):

        @classmethod
        def _build_schema_on_200(cls):
            _schema = super()._build_schema_on_200()
            Common.SetSchemaNullable(_schema)
            return _schema

    class InstanceUpdateByJson(SetDefinitionVersionUpdate.InstanceUpdateByJson):
        pass

    class InstanceUpdateByGeneric(SetDefinitionVersionUpdate.InstanceUpdateByGeneric):
        pass

    def pre_operations(self):
        pass
    
    def _execute_operations(self):
        self.pre_operations()

        if has_value(self.ctx.args.policy_set_definition_name) and has_value(self.ctx.args.management_group):
            self.PolicySetDefinitionVersionsGetAtManagementGroup(ctx=self.ctx)()
            self.InstanceUpdateByJson(ctx=self.ctx)()
            self.InstanceUpdateByGeneric(ctx=self.ctx)()
            self.PolicySetDefinitionVersionsCreateOrUpdateAtManagementGroup(ctx=self.ctx)()
        else:
            self.PolicySetDefinitionVersionsGet(ctx=self.ctx)()
            self.InstanceUpdateByJson(ctx=self.ctx)()
            self.InstanceUpdateByGeneric(ctx=self.ctx)()
            self.PolicySetDefinitionVersionsCreateOrUpdate(ctx=self.ctx)()

        self.post_operations()

    def post_operations(self):
        pass

