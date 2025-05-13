# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from azure.cli.core.aaz import register_command, has_value, AAZBoolArg, AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
from ..aaz.latest.disk_encryption_set import Update as _DiskEncryptionSetUpdate

logger = get_logger(__name__)


@register_command(
    "disk-encryption-set identity assign",
)
class DiskEncryptionSetIdentityAssign(_DiskEncryptionSetUpdate):
    """Add managed identities to an existing disk encryption set.

    :example: Add a system assigned managed identity to an existing disk encryption set.
        az disk-encryption-set identity assign --name MyDiskEncryptionSet --resource-group MyResourceGroup --system-assigned

    :example: Add a user assigned managed identity to an existing disk encryption set.
        az disk-encryption-set identity assign --name MyDiskEncryptionSet --resource-group MyResourceGroup --user-assigned MyAssignedId

    :example: Add system assigned identity and a user assigned managed identity to an existing disk encryption set.
        az disk-encryption-set identity assign --name MyDiskEncryptionSet --resource-group MyResourceGroup --system-assigned --user-assigned MyAssignedId
    """

    AZ_SUPPORT_GENERIC_UPDATE = False

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.system_assigned = AAZBoolArg(
            options=["--system-assigned"],
            help="Provide this flag to use system assigned identity.",
            arg_group="Managed Identity",
            blank=True
        )
        args_schema.user_assigned = AAZListArg(
            options=["--user-assigned"],
            help="User Assigned Identity ids to be used for disk encryption set. Accepts using the argument without any value.",
            arg_group="Managed Identity",
            blank=[]
        )
        args_schema.user_assigned.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(template="/subscriptions/{subscription}/resourceGroups/{resource_group}"
                                                "/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{}")
        )
        args_schema.no_wait._registered = False
        args_schema.identity._registered = False
        args_schema.enable_auto_key_rotation._registered = False
        args_schema.federated_client_id._registered = False
        args_schema.key_url._registered = False
        args_schema.source_vault._registered = False
        return args_schema

    def pre_instance_update(self, instance):
        existing_system_identity = False
        existing_user_identity = set()
        if instance.to_serialized_data().get('identity', None):
            existing_system_identity = instance.identity.type in ['SystemAssigned', 'SystemAssigned, UserAssigned']
            existing_user_identity = {x.lower() for x in list(getattr(instance.identity, 'user_assigned_identities', {}).keys())}

        add_system_assigned = self.ctx.args.system_assigned.to_serialized_data()
        add_user_assigned = {x.lower() for x in self.ctx.args.user_assigned.to_serialized_data() or []}

        updated_system_assigned = existing_system_identity or add_system_assigned
        updated_user_assigned = list(existing_user_identity.union(add_user_assigned))

        instance.identity.type = 'SystemAssigned'
        if updated_user_assigned:
            instance.identity.type = 'SystemAssigned, UserAssigned' if updated_system_assigned else 'UserAssigned'
            instance.identity.user_assigned_identities = dict.fromkeys(updated_user_assigned, {})

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result.get('identity', None)


@register_command(
    "disk-encryption-set identity remove",
    confirmation="Are you sure you want to perform this operation?"
)
class DiskEncryptionSetIdentityRemove(_DiskEncryptionSetUpdate):
    """Remove managed identities from an existing disk encryption set.

    :example: Remove a system assigned managed identity from an existing disk encryption set.
        az disk-encryption-set identity remove --name MyDiskEncryptionSet --resource-group MyResourceGroup --system-assigned

    :example: Remove a user assigned managed identity from an existing disk encryption set.
        az disk-encryption-set identity remove --name MyDiskEncryptionSet --resource-group MyResourceGroup --user-assigned MyAssignedId

    :example: Remove all user assigned managed identities from an existing disk encryption set.
        az disk-encryption-set identity remove --name MyDiskEncryptionSet --resource-group MyResourceGroup --user-assigned
    """

    AZ_SUPPORT_GENERIC_UPDATE = False

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.system_assigned = AAZBoolArg(
            options=["--system-assigned"],
            help="Provide this flag to use system assigned identity.",
            arg_group="Managed Identity",
            blank=True
        )
        args_schema.user_assigned = AAZListArg(
            options=["--user-assigned"],
            help="User Assigned Identity ids to be used for disk encryption set. Accepts using the argument without any value.",
            arg_group="Managed Identity",
            blank=[]
        )
        args_schema.user_assigned.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(template="/subscriptions/{subscription}/resourceGroups/{resource_group}"
                                                "/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{}")
        )
        args_schema.no_wait._registered = False
        args_schema.identity._registered = False
        args_schema.enable_auto_key_rotation._registered = False
        args_schema.federated_client_id._registered = False
        args_schema.key_url._registered = False
        args_schema.source_vault._registered = False
        return args_schema

    def _execute_operations(self):
        self.pre_operations()
        self.DiskEncryptionSetsGet(ctx=self.ctx)()
        if self.pre_instance_update(self.ctx.vars.instance):
            return
        self.InstanceUpdateByJson(ctx=self.ctx)()
        self.InstanceUpdateByGeneric(ctx=self.ctx)()
        self.post_instance_update(self.ctx.vars.instance)
        yield self.DiskEncryptionSetsCreateOrUpdate(ctx=self.ctx)()
        self.post_operations()

    def pre_instance_update(self, instance):
        identity = instance.to_serialized_data().get('identity', None)
        if identity is None:
            from types import MethodType

            def _output(self, *args, **kwargs):
                return None
            self._output = MethodType(_output, self)

            # skip the update operation if the identity is not present
            return True

        user_identities_to_remove = []
        if has_value(self.ctx.args.user_assigned):
            existing_user_identities = {x.lower() for x in list(getattr(instance.identity, 'user_assigned_identities', {}).keys())}

            # all user assigned identities will be removed if the length of mi_user_assigned is 0,
            # otherwise the specified identity
            for x in self.ctx.args.user_assigned:
                pass
            user_identities_to_remove = {str(x).lower() for x in self.ctx.args.user_assigned} \
                if len(self.ctx.args.user_assigned) > 0 else existing_user_identities
            non_existing = user_identities_to_remove.difference(existing_user_identities)
            if non_existing:
                from azure.cli.core.azclierror import InvalidArgumentValueError
                raise InvalidArgumentValueError("'{}' are not associated with '{}', please provide existing user managed "
                                                "identities".format(','.join(non_existing), instance.name))
            if not list(existing_user_identities - user_identities_to_remove):
                if hasattr(instance.identity, 'user_assigned_identities'):
                    del instance.identity.user_assigned_identities
                if instance.identity.type == 'UserAssigned':
                    instance.identity.type = 'None'
                elif instance.identity.type == 'SystemAssigned, UserAssigned':
                    instance.identity.type = 'SystemAssigned'

        if self.ctx.args.system_assigned:
            instance.identity.type = 'None' if instance.identity.type == 'SystemAssigned' else 'UserAssigned'

        if user_identities_to_remove:
            if instance.identity.type not in ['None', 'SystemAssigned']:
                for _id in user_identities_to_remove:
                    if hasattr(instance.identity.user_assigned_identities, _id):
                        del instance.identity.user_assigned_identities[_id]

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result.get('identity', None)
