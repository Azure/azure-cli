# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument, too-many-branches
from knack.log import get_logger

from azure.cli.core.aaz import (has_value, register_command_group, register_command, AAZCommandGroup,
                                AAZCommand, AAZDictArg, AAZListArg, AAZStrArg, AAZResourceGroupNameArg)
from ..aaz.latest.sig.in_vm_access_control_profile_version import Update as _Update

logger = get_logger(__name__)


@register_command_group(
    "sig in-vm-access-control-profile-version config",
)
class __ConfigCMDGroup(AAZCommandGroup):
    """Manage the access control rules specification for an in VM access control profile version.
    """
    pass


@register_command_group(
    "sig in-vm-access-control-profile-version config privilege",
)
class __ConfigPrivilegeCMDGroup(AAZCommandGroup):
    """Manage privileges for an in VM access control profile version.
    """
    pass


@register_command_group(
    "sig in-vm-access-control-profile-version config role",
)
class __ConfigRoleCMDGroup(AAZCommandGroup):
    """Manage roles for an in VM access control profile version.
    """
    pass


@register_command_group(
    "sig in-vm-access-control-profile-version config identity",
)
class __ConfigIdentityCMDGroup(AAZCommandGroup):
    """Manage identities for an in VM access control profile version.
    """
    pass


@register_command_group(
    "sig in-vm-access-control-profile-version config role-assignment",
)
class __ConfigRoleAssignmentCMDGroup(AAZCommandGroup):
    """Manage role assignments for an in VM access control profile version.
    """
    pass


@register_command(
    "sig in-vm-access-control-profile-version config privilege add",
)
class SigInVMAccessControlProfileVersionConfigPrivilegeAdd(_Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        if cls._args_schema is not None:
            return cls._args_schema
        cls._args_schema = super(_Update, cls)._build_arguments_schema(*args, **kwargs)

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.gallery_name = AAZStrArg(
            options=["--gallery-name"],
            help="The name of the Shared Image Gallery in which the in VM access control profile resides.",
            required=True,
            id_part="name",
        )
        _args_schema.profile_name = AAZStrArg(
            options=["--profile-name"],
            help="The name of the gallery in VM access control profile in which the in VM access control profile version is to be created.",
            required=True,
            id_part="child_name_1",
        )
        _args_schema.profile_version = AAZStrArg(
            options=["--version-name", "--profile-version"],
            help="The name of the gallery in VM access control profile version to be created. Needs to follow semantic version name pattern: The allowed characters are digit and period. Digits must be within the range of a 32-bit integer. Format: MajorVersion.MinorVersion.Patch",
            required=True,
            id_part="child_name_2",
        )
        _args_schema.resource_group = AAZResourceGroupNameArg(
            required=True,
        )

        # define Arg Group "Properties"

        _args_schema.name = AAZStrArg(
            options=["--name"],
            arg_group="Properties",
            required=True,
            help="The name of the privilege.",
        )
        _args_schema.path = AAZStrArg(
            options=["--path"],
            arg_group="Properties",
            required=True,
            help="The HTTP path corresponding to the privilege.",
        )
        _args_schema.query_parameters = AAZDictArg(
            options=["--query-parameters"],
            arg_group="Properties",
            help="The query parameters to match in the path.",
        )

        return cls._args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args

        privilege = {
            "name": args.name,
            "path": args.path
        }
        if has_value(args.query_parameters):
            privilege["query_parameters"] = args.query_parameters

        if not instance.properties.rules.privileges:
            instance.properties.rules.privileges = [privilege]
        else:
            instance.properties.rules.privileges.append(privilege)


@register_command(
    "sig in-vm-access-control-profile-version config privilege remove",
)
class SigInVMAccessControlProfileVersionConfigPrivilegeRemove(_Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        if cls._args_schema is not None:
            return cls._args_schema
        cls._args_schema = super(_Update, cls)._build_arguments_schema(*args, **kwargs)

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.gallery_name = AAZStrArg(
            options=["--gallery-name"],
            help="The name of the Shared Image Gallery in which the in VM access control profile resides.",
            required=True,
            id_part="name",
        )
        _args_schema.profile_name = AAZStrArg(
            options=["--profile-name"],
            help="The name of the gallery in VM access control profile in which the in VM access control profile version is to be created.",
            required=True,
            id_part="child_name_1",
        )
        _args_schema.profile_version = AAZStrArg(
            options=["--version-name", "--profile-version"],
            help="The name of the gallery in VM access control profile version to be created. Needs to follow semantic version name pattern: The allowed characters are digit and period. Digits must be within the range of a 32-bit integer. Format: MajorVersion.MinorVersion.Patch",
            required=True,
            id_part="child_name_2",
        )
        _args_schema.resource_group = AAZResourceGroupNameArg(
            required=True,
        )

        # define Arg Group "Properties"

        _args_schema.name = AAZStrArg(
            options=["--name"],
            arg_group="Properties",
            required=True,
            help="The name of the privilege.",
        )

        return cls._args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args

        if instance.properties.rules.privileges:
            privileges = [privilege for privilege in instance.properties.rules.privileges if privilege.name != args.name]
            instance.properties.rules.privileges = privileges


@register_command(
    "sig in-vm-access-control-profile-version config role add",
)
class SigInVMAccessControlProfileVersionConfigRoleAdd(_Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        if cls._args_schema is not None:
            return cls._args_schema
        cls._args_schema = super(_Update, cls)._build_arguments_schema(*args, **kwargs)

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.gallery_name = AAZStrArg(
            options=["--gallery-name"],
            help="The name of the Shared Image Gallery in which the in VM access control profile resides.",
            required=True,
            id_part="name",
        )
        _args_schema.profile_name = AAZStrArg(
            options=["--profile-name"],
            help="The name of the gallery in VM access control profile in which the in VM access control profile version is to be created.",
            required=True,
            id_part="child_name_1",
        )
        _args_schema.profile_version = AAZStrArg(
            options=["--version-name", "--profile-version"],
            help="The name of the gallery in VM access control profile version to be created. Needs to follow semantic version name pattern: The allowed characters are digit and period. Digits must be within the range of a 32-bit integer. Format: MajorVersion.MinorVersion.Patch",
            required=True,
            id_part="child_name_2",
        )
        _args_schema.resource_group = AAZResourceGroupNameArg(
            required=True,
        )

        # define Arg Group "Properties"

        _args_schema.name = AAZStrArg(
            options=["--name"],
            arg_group="Properties",
            required=True,
            help="The name of the role.",
        )
        _args_schema.privileges = AAZListArg(
            options=["--privileges"],
            arg_group="Properties",
            required=True,
            help="A list of privileges needed by this role.",
        )
        privileges = args_schema.privileges
        privileges.Element = AAZStrArg()

        return cls._args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args

        role = {
            "name": args.name,
            "privileges": args.privileges
        }

        if not instance.properties.rules.roles:
            instance.properties.rules.roles = [role]
        else:
            instance.properties.rules.roles.append(role)


@register_command(
    "sig in-vm-access-control-profile-version config role remove",
)
class SigInVMAccessControlProfileVersionConfigRoleRemove(_Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        if cls._args_schema is not None:
            return cls._args_schema
        cls._args_schema = super(_Update, cls)._build_arguments_schema(*args, **kwargs)

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.gallery_name = AAZStrArg(
            options=["--gallery-name"],
            help="The name of the Shared Image Gallery in which the in VM access control profile resides.",
            required=True,
            id_part="name",
        )
        _args_schema.profile_name = AAZStrArg(
            options=["--profile-name"],
            help="The name of the gallery in VM access control profile in which the in VM access control profile version is to be created.",
            required=True,
            id_part="child_name_1",
        )
        _args_schema.profile_version = AAZStrArg(
            options=["--version-name", "--profile-version"],
            help="The name of the gallery in VM access control profile version to be created. Needs to follow semantic version name pattern: The allowed characters are digit and period. Digits must be within the range of a 32-bit integer. Format: MajorVersion.MinorVersion.Patch",
            required=True,
            id_part="child_name_2",
        )
        _args_schema.resource_group = AAZResourceGroupNameArg(
            required=True,
        )

        # define Arg Group "Properties"

        _args_schema.name = AAZStrArg(
            options=["--name"],
            arg_group="Properties",
            required=True,
            help="The name of the role.",
        )

        return cls._args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args

        if instance.properties.rules.roles:
            roles = [role for role in instance.properties.rules.roles if
                     role.name != args.name]
            instance.properties.rules.roles = roles


@register_command(
    "sig in-vm-access-control-profile-version config identity add",
)
class SigInVMAccessControlProfileVersionConfigIdentityAdd(_Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        if cls._args_schema is not None:
            return cls._args_schema
        cls._args_schema = super(_Update, cls)._build_arguments_schema(*args, **kwargs)

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.gallery_name = AAZStrArg(
            options=["--gallery-name"],
            help="The name of the Shared Image Gallery in which the in VM access control profile resides.",
            required=True,
            id_part="name",
        )
        _args_schema.profile_name = AAZStrArg(
            options=["--profile-name"],
            help="The name of the gallery in VM access control profile in which the in VM access control profile version is to be created.",
            required=True,
            id_part="child_name_1",
        )
        _args_schema.profile_version = AAZStrArg(
            options=["--version-name", "--profile-version"],
            help="The name of the gallery in VM access control profile version to be created. Needs to follow semantic version name pattern: The allowed characters are digit and period. Digits must be within the range of a 32-bit integer. Format: MajorVersion.MinorVersion.Patch",
            required=True,
            id_part="child_name_2",
        )
        _args_schema.resource_group = AAZResourceGroupNameArg(
            required=True,
        )

        # define Arg Group "Properties"

        _args_schema.name = AAZStrArg(
            options=["--name"],
            arg_group="Properties",
            required=True,
            help="The name of the identity.",
        )
        _args_schema.user_name = AAZStrArg(
            options=["--user-name"],
            arg_group="Properties",
            help="The username corresponding to this identity.",
        )
        _args_schema.group_name = AAZStrArg(
            options=["--group-name"],
            arg_group="Properties",
            help="The group name corresponding to this identity.",
        )
        _args_schema.exe_path = AAZStrArg(
            options=["--exe-path"],
            arg_group="Properties",
            help="The path to the executable.",
        )
        _args_schema.process_name = AAZStrArg(
            options=["--process-name"],
            arg_group="Properties",
            help="The process name of the executable.",
        )

        return cls._args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args

        identity = {
            "name": args.name,
        }
        if has_value(args.user_name):
            identity["user_name"] = args.user_name
        if has_value(args.group_name):
            identity["group_name"] = args.group_name
        if has_value(args.exe_path):
            identity["exe_path"] = args.exe_path
        if has_value(args.process_name):
            identity["process_name"] = args.process_name

        if not instance.properties.rules.identities:
            instance.properties.rules.identities = [identity]
        else:
            instance.properties.rules.identities.append(identity)


@register_command(
    "sig in-vm-access-control-profile-version config identity remove",
)
class SigInVMAccessControlProfileVersionConfigIdentityRemove(_Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        if cls._args_schema is not None:
            return cls._args_schema
        cls._args_schema = super(_Update, cls)._build_arguments_schema(*args, **kwargs)

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.gallery_name = AAZStrArg(
            options=["--gallery-name"],
            help="The name of the Shared Image Gallery in which the in VM access control profile resides.",
            required=True,
            id_part="name",
        )
        _args_schema.profile_name = AAZStrArg(
            options=["--profile-name"],
            help="The name of the gallery in VM access control profile in which the in VM access control profile version is to be created.",
            required=True,
            id_part="child_name_1",
        )
        _args_schema.profile_version = AAZStrArg(
            options=["--version-name", "--profile-version"],
            help="The name of the gallery in VM access control profile version to be created. Needs to follow semantic version name pattern: The allowed characters are digit and period. Digits must be within the range of a 32-bit integer. Format: MajorVersion.MinorVersion.Patch",
            required=True,
            id_part="child_name_2",
        )
        _args_schema.resource_group = AAZResourceGroupNameArg(
            required=True,
        )

        # define Arg Group "Properties"

        _args_schema.name = AAZStrArg(
            options=["--name"],
            arg_group="Properties",
            required=True,
            help="The name of the identity.",
        )

    def pre_instance_update(self, instance):
        args = self.ctx.args

        if instance.properties.rules.identities:
            identities = [identity for identity in instance.properties.rules.identities if
                          identity.name != args.name]
            instance.properties.rules.identities = identities


@register_command(
    "sig in-vm-access-control-profile-version config role-assignment add",
)
class SigInVMAccessControlProfileVersionConfigRoleAssignmentAdd(_Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        if cls._args_schema is not None:
            return cls._args_schema
        cls._args_schema = super(_Update, cls)._build_arguments_schema(*args, **kwargs)

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.gallery_name = AAZStrArg(
            options=["--gallery-name"],
            help="The name of the Shared Image Gallery in which the in VM access control profile resides.",
            required=True,
            id_part="name",
        )
        _args_schema.profile_name = AAZStrArg(
            options=["--profile-name"],
            help="The name of the gallery in VM access control profile in which the in VM access control profile version is to be created.",
            required=True,
            id_part="child_name_1",
        )
        _args_schema.profile_version = AAZStrArg(
            options=["--version-name", "--profile-version"],
            help="The name of the gallery in VM access control profile version to be created. Needs to follow semantic version name pattern: The allowed characters are digit and period. Digits must be within the range of a 32-bit integer. Format: MajorVersion.MinorVersion.Patch",
            required=True,
            id_part="child_name_2",
        )
        _args_schema.resource_group = AAZResourceGroupNameArg(
            required=True,
        )

        # define Arg Group "Properties"

        _args_schema.role = AAZStrArg(
            options=["--role"],
            arg_group="Properties",
            required=True,
            help="The name of the role.",
        )
        _args_schema.identities = AAZListArg(
            options=["--identities"],
            arg_group="Properties",
            required=True,
            help="A list of identities that can access the privileges defined by the role.",
        )
        identities = args_schema.identities
        identities.Element = AAZStrArg()

        return cls._args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args

        role_assignment = {
            "role": args.role,
            "identities": args.identities,
        }

        if not instance.properties.rules.role_assignments:
            instance.properties.rules.role_assignments = [role_assignment]
        else:
            instance.properties.rules.role_assignments.append(role_assignment)


@register_command(
    "sig in-vm-access-control-profile-version config role-assignment remove",
)
class SigInVMAccessControlProfileVersionConfigRoleAssignmentRemove(_Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        if cls._args_schema is not None:
            return cls._args_schema
        cls._args_schema = super(_Update, cls)._build_arguments_schema(*args, **kwargs)

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.gallery_name = AAZStrArg(
            options=["--gallery-name"],
            help="The name of the Shared Image Gallery in which the in VM access control profile resides.",
            required=True,
            id_part="name",
        )
        _args_schema.profile_name = AAZStrArg(
            options=["--profile-name"],
            help="The name of the gallery in VM access control profile in which the in VM access control profile version is to be created.",
            required=True,
            id_part="child_name_1",
        )
        _args_schema.profile_version = AAZStrArg(
            options=["--version-name", "--profile-version"],
            help="The name of the gallery in VM access control profile version to be created. Needs to follow semantic version name pattern: The allowed characters are digit and period. Digits must be within the range of a 32-bit integer. Format: MajorVersion.MinorVersion.Patch",
            required=True,
            id_part="child_name_2",
        )
        _args_schema.resource_group = AAZResourceGroupNameArg(
            required=True,
        )

        # define Arg Group "Properties"

        _args_schema.role = AAZStrArg(
            options=["--role"],
            arg_group="Properties",
            required=True,
            help="The name of the role.",
        )

        return cls._args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args

        if instance.properties.rules.role_assignments:
            role_assignments = [role_assignment for role_assignment in instance.properties.rules.role_assignments if
                          role_assignment.role != args.role]
            instance.properties.rules.role_assignments = role_assignments
