# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import uuid
from knack.log import get_logger
from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id
from azure.cli.core.aaz import has_value
from .aaz.latest.managedservices.definition import (
    Create as _DefinitionCreate, Delete as _DefinitionDelete, List as _DefinitionList, Show as _DefinitionShow)
from .aaz.latest.managedservices.assignment import (
    Create as _AssignmentCreate, Delete as _AssignmentDelete, List as _AssignmentList, Show as _AssignmentShow)

logger = get_logger(__name__)

# region Definitions Custom Commands


# pylint: disable=unused-argument, protected-access
class DefinitionCreate(_DefinitionCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.auth_principal_id = AAZStrArg(
            options=["--principal-id"],
            help="The principal id.",
            required=True
        )
        args_schema.auth_role_definition_id = AAZStrArg(
            options=["--role-definition-id "],
            help="The role definition id.",
            required=True
        )
        args_schema.scope._registered = False
        args_schema.authorizations._registered = False
        args_schema.name._required = True
        args_schema.tenant_id._required = True
        args_schema.definition_id._required = False
        args_schema.scope._required = False
        return args_schema

    def pre_operations(self):
        from azure.cli.core.commands.client_factory import get_subscription_id
        args = self.ctx.args
        if not args.definition_id:
            args.definition_id = str(uuid.uuid4())

        subscription = get_subscription_id(self.cli_ctx)
        scope = _get_scope(subscription)
        args.scope = scope
        authorizations = {}
        if has_value(args.auth_principal_id):
            authorizations.update({
                'principalId': args.auth_principal_id.to_serialized_data()
            })
        if has_value(args.auth_role_definition_id):
            authorizations.update({
                'roleDefinitionId': args.auth_role_definition_id.to_serialized_data()
            })
        if authorizations:
            args.authorizations = [authorizations]
        if not has_value(args.plan_name) or not has_value(args.plan_product) \
                or not has_value(args.plan_publisher) or not has_value(args.plan_product):
            args.plan_name = None
            args.plan_product = None
            args.plan_publisher = None
            args.plan_version = None


class DefinitionShow(_DefinitionShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope._registered = False
        args_schema.scope._required = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        subscription = _get_subscription_id_from_cmd(self.cli_ctx)
        definition_id, sub_id, rg_name = _get_resource_id_parts(self.cli_ctx,
                                                                args.definition.to_serialized_data(), subscription)
        scope = _get_scope(sub_id, rg_name)
        args.scope = scope
        args.definition = definition_id


class DefinitionList(_DefinitionList):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope._registered = False
        args_schema.scope._required = False
        return args_schema

    def pre_operations(self):
        from azure.cli.core.commands.client_factory import get_subscription_id
        args = self.ctx.args
        subscription = get_subscription_id(self.cli_ctx)
        scope = _get_scope(subscription)
        args.scope = scope


class DefinitionDelete(_DefinitionDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.scope._registered = False
        args_schema.scope._required = False
        args_schema.definition._required = True
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        subscription = _get_subscription_id_from_cmd(self.cli_ctx)
        definition_id, sub_id, rg_name = _get_resource_id_parts(self.cli_ctx,
                                                                args.definition.to_serialized_data(), subscription)
        scope = _get_scope(sub_id, rg_name)
        args.scope = scope
        args.definition = definition_id


# endregion

# region Assignments Custom Commands

# pylint: disable=unused-argument

class AssignmentCreate(_AssignmentCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.resource_group_name = AAZStrArg(
            options=["--resource-group", "-g"],
            help="Name of resource group."
                 " You can configure the default group using `az configure --defaults group=<name>`",
        )
        args_schema.assignment_id._required = False
        args_schema.scope._registered = False
        args_schema.definition._required = True
        args_schema.scope._required = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        resource_group_name = args.resource_group_name if has_value(args.resource_group_name) else None
        if not is_valid_resource_id(args.definition.to_serialized_data()):
            from azure.cli.core.azclierror import InvalidArgumentValueError
            raise InvalidArgumentValueError(
                "definition should be a valid resource id. For example, "
                "/subscriptions/id/providers/Microsoft.ManagedServices/registrationDefinitions/id")
        if not args.assignment_id:
            args.assignment_id = str(uuid.uuid4())

        subscription = _get_subscription_id_from_cmd(self.cli_ctx)
        scope = _get_scope(subscription, resource_group_name)
        args.scope = scope


class AssignmentShow(_AssignmentShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.resource_group_name = AAZStrArg(
            options=["--resource-group", "-g"],
            help="Name of resource group."
                 " You can configure the default group using `az configure --defaults group=<name>`",
        )
        args_schema.scope._registered = False
        args_schema.scope._required = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        resource_group_name = args.resource_group_name if has_value(args.resource_group_name) else None
        subscription = _get_subscription_id_from_cmd(self.cli_ctx)
        assignment_id, sub_id, rg_name = _get_resource_id_parts(self.cli_ctx, args.assignment.to_serialized_data(),
                                                                subscription, resource_group_name)
        scope = _get_scope(sub_id, rg_name)
        args.scope = scope
        args.assignment = assignment_id


class AssignmentDelete(_AssignmentDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.resource_group_name = AAZStrArg(
            options=["--resource-group", "-g"],
            help="Name of resource group."
                 " You can configure the default group using `az configure --defaults group=<name>`",
        )
        args_schema.scope._registered = False
        args_schema.scope._required = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        rg_name = args.resource_group_name.to_serialized_data() if has_value(args.resource_group_name) else None
        subscription = _get_subscription_id_from_cmd(self.cli_ctx)
        assignment_id, sub_id, rg_name = _get_resource_id_parts(self.cli_ctx, args.assignment.to_serialized_data(),
                                                                subscription, rg_name)
        scope = _get_scope(sub_id, rg_name)
        args.scope = scope
        args.assignment = assignment_id


class AssignmentList(_AssignmentList):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.resource_group_name = AAZStrArg(
            options=["--resource-group", "-g"],
            help="Name of resource group."
                 " You can configure the default group using `az configure --defaults group=<name>`",
        )
        args_schema.scope._registered = False
        args_schema.scope._required = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        resource_group_name = args.resource_group_name if has_value(args.resource_group_name) else None
        sub_id = _get_subscription_id_from_cmd(self.cli_ctx)
        scope = _get_scope(sub_id, resource_group_name)
        args.scope = scope


# endregion

# region private methods


def _get_subscription_id_from_cmd(cli_ctx):
    from azure.cli.core.commands.client_factory import get_subscription_id
    subscription = get_subscription_id(cli_ctx)
    return subscription


def _get_resource_id_parts(cli_ctx, name_or_id, subscription=None, resource_group_name=None):
    rg_name = None
    if is_valid_resource_id(name_or_id):
        id_parts = parse_resource_id(name_or_id)
        sub_id = id_parts['subscription']
        name = id_parts['name']
        if 'resource_group' in id_parts:
            rg_name = id_parts['resource_group']
    else:
        rg_name = resource_group_name
        name = name_or_id
        sub_id = _get_subscription_id_from_cmd(cli_ctx)
    return name, sub_id, rg_name


def _get_scope(subscription_id, resource_group_name=None):
    if not resource_group_name:
        scope = "/subscriptions/" + subscription_id
    else:
        scope = "/subscriptions/" + subscription_id + "/resourceGroups/" + resource_group_name

    return scope
# endregion
