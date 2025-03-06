# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger
from ._util import import_aaz_by_profile

from azure.mgmt.core.tools import is_valid_resource_id
from azure.cli.core.aaz import has_value, AAZBoolArg, AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat

logger = get_logger(__name__)

_DES = import_aaz_by_profile("disk_encryption_set")

KV_RID_TEMPLATE = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.KeyVault/vaults/{}"


class DiskEncryptionSetCreate(_DES.Create):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.mi_system_assigned = AAZBoolArg(
            options=["--mi-system-assigned"],
            help="Provide this flag to use system assigned identity.",
            arg_group="Managed Identity"
        )
        args_schema.mi_user_assigned = AAZListArg(
            options=["--mi-user-assigned"],
            help="Space separated resource IDs to add user-assigned identities.",
            arg_group="Managed Identity"
        )
        args_schema.mi_user_assigned.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(template="/subscriptions/{subscription}/resourceGroups/{resource_group}"
                                                "/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{}")
        )
        args_schema.key_url._required = True
        args_schema.identity._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.identity.type = "SystemAssigned"
        if has_value(args.mi_user_assigned):
            args.identity.type = "SystemAssigned, UserAssigned" if args.mi_system_assigned else "UserAssigned"
            user_assigned_identities = {}
            for identity in args.mi_user_assigned:
                user_assigned_identities.update({
                    identity.to_serialized_data(): {}
                })
            args.identity.user_assigned_identities = user_assigned_identities

        if has_value(args.source_vault):
            vault = args.source_vault.to_serialized_data()
            args.source_vault = vault if is_valid_resource_id(vault) else KV_RID_TEMPLATE.format(self.ctx.subscription_id, args.resource_group, vault)


class DiskEncryptionSetUpdate(_DES.Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.identity._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.source_vault):
            vault = args.source_vault.to_serialized_data()
            args.source_vault = vault if is_valid_resource_id(vault) else KV_RID_TEMPLATE.format(self.ctx.subscription_id, args.resource_group, vault)
