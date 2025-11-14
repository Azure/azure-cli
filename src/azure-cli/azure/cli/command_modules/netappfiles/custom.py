# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=protected-access
from enum import Enum

from knack.log import get_logger
from azure.cli.core.azclierror import ValidationError
from azure.cli.core.aaz import has_value, AAZJsonSelector
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
from .aaz.latest.netappfiles import UpdateNetworkSiblingSet as _UpdateNetworkSiblingSet
# from .aaz.latest.netappfiles.account import Create as _AccountCreate, Update as _AccountUpdate
from .aaz.latest.netappfiles.account.ad import Add as _ActiveDirectoryAdd, List as _ActiveDirectoryList, Update as _ActiveDirectoryUpdate
from .aaz.latest.netappfiles.volume import Create as _VolumeCreate, Update as _VolumeUpdate, BreakFileLocks as _BreakFileLocks
from .aaz.latest.netappfiles.volume_group import Create as _VolumeGroupCreate
from .aaz.latest.netappfiles.volume.export_policy import List as _ExportPolicyList, Add as _ExportPolicyAdd, Remove as _ExportPolicyRemove
from .aaz.latest.netappfiles.volume.replication import Resume as _ReplicationResume
from .aaz.latest.netappfiles.pool import Create as _PoolCreate, Update as _PoolUpdate

logger = get_logger(__name__)

# RP expted bytes but CLI allows integer TiBs for ease of use
gib_scale = 1024 * 1024 * 1024
tib_scale = gib_scale * 1024


def _get_location_from_resource_group(cli_ctx, resource_group_name):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    group = client.resource_groups.get(resource_group_name)
    return group.location


def _update_mapper(existing, new, keys):
    for key in keys:
        existing_value = getattr(existing, key)
        new_value = getattr(new, key)
        logger.debug("ANF LOG: update mapper => setting:%s old:%s new:%s", key, existing_value, new_value)
        setattr(new, key, new_value if new_value is not None else existing_value)
    logger.debug("mapping done new is now: %s", new)


# region NetworkSiblingset
class UpdateNetworkSiblingSet(_UpdateNetworkSiblingSet):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZArgEnum
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        # # The API does only support setting Basic and Standard
        args_schema.network_features.enum = AAZArgEnum({"Basic": "Basic", "Standard": "Standard"}, case_sensitive=False)
        return args_schema
# endregion


# region account
# class AccountCreate(_AccountCreate):
#     @classmethod
#     def _build_arguments_schema(cls, *args, **kwargs):
#         from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat
#         args_schema = super()._build_arguments_schema(*args, **kwargs)
#         # args_schema.user_assigned_identity = AAZStrArg(
#         #     options=["--user-assigned-identity u"],
#         #     arg_group="Identity",
#         #     help="The ARM resource identifier of the user assigned identity used to authenticate with key vault. Applicable if identity.type has UserAssigned. It should match key of identity.userAssignedIdentities.",
#         #     required=False
#         # )

#         args_schema.user_assigned_identity = AAZResourceIdArg(
#             options=["--user-assigned-identity", "-u"],
#             help="The ARM resource identifier of the user assigned identity used to authenticate with key vault. Applicable if identity.type has UserAssigned. It should match key of identity.userAssignedIdentities.",
#             required=False,
#             fmt=AAZResourceIdArgFormat(
#                 template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.ManagedIdentity"
#                          "/userAssignedIdentities/{}",
#             ),
#         )

#         args_schema.user_assigned_identities._registered = False
#         args_schema.encryption_identity._registered = False
#         return args_schema

#     def pre_operations(self):
#         args = self.ctx.args
#         logger.debug("ANF log: AccountCreate.pre_operations user_assigned_identity: %s", args.user_assigned_identity)
#         if has_value(args.user_assigned_identity):
#             # args.user_assigned_identities[args.user_assigned_identity.to_serialized_data()] = "None"
#             args.user_assigned_identities = {args.user_assigned_identity.to_serialized_data(): {}}
#             logger.debug("ANF log: AccountCreate.pre_operations setting user_assigned_identities: %s", args.user_assigned_identities.to_serialized_data())
#             args.encryption_identity.user_assigned_identity = args.user_assigned_identity.to_serialized_data()


# class AccountUpdate(_AccountUpdate):
#     @classmethod
#     def _build_arguments_schema(cls, *args, **kwargs):
#         from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat
#         args_schema = super()._build_arguments_schema(*args, **kwargs)

#         args_schema.user_assigned_identity = AAZResourceIdArg(
#             options=["--user-assigned-identity", "-u"],
#             help="The ARM resource identifier of the user assigned identity used to authenticate with key vault. Applicable if identity.type has UserAssigned. It should match key of identity.userAssignedIdentities.",
#             required=False,
#             fmt=AAZResourceIdArgFormat(
#                 template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.ManagedIdentity"
#                          "/userAssignedIdentities/{}",
#             ),
#         )

#         args_schema.user_assigned_identities._registered = False
#         args_schema.encryption_identity._registered = False
#         return args_schema

#     def pre_operations(self):
#         args = self.ctx.args
#         logger.debug("ANF log: AccountCreate.pre_operations user_assigned_identity: %s", args.user_assigned_identity)
#         if has_value(args.user_assigned_identity):
#             # args.user_assigned_identities[args.user_assigned_identity.to_serialized_data()] = "None"
#             args.user_assigned_identities = {args.user_assigned_identity.to_serialized_data(): {}}
#             logger.debug("ANF log: AccountCreate.pre_operations setting user_assigned_identities: %s", args.user_assigned_identities.to_serialized_data())
#             args.encryption_identity.user_assigned_identity = args.user_assigned_identity.to_serialized_data()
# endregion


# region account ad
class ActiveDirectoryAdd(_ActiveDirectoryAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.active_directory_id._required = False
        return args_schema

    def _output(self, *args, **kwargs):
        logger.debug("ANF log: ActiveDirectoryAdd _output")
        # For backwards compatibility return the whole resource
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class ActiveDirectoryUpdate(_ActiveDirectoryUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema

    def _output(self, *args, **kwargs):
        logger.debug("ANF log: ActiveDirectoryUpdate _output")
        # For backwards compatibility return the whole resource
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class ActiveDirectoryList(_ActiveDirectoryList):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema

    def _output(self, *args, **kwargs):
        logger.debug("ANF log: ActiveDirectoryList _output")
        result = self.deserialize_output(self.ctx.selectors.subresource.required(), client_flatten=True)
        return result

    class SubresourceSelector(AAZJsonSelector):

        def _get(self):
            logger.debug("ANF log: SubresourceSelector _get")
            result = self.ctx.vars.instance
            # For backwards compatibility, avoids returning ResourceNotFoundError when the list is empty
            if has_value(result.properties.activeDirectories):
                return result.properties.activeDirectories

            return

        def _set(self, value):
            result = self.ctx.vars.instance
            result.properties.activeDirectories = value


# endregion


# region Pool
class PoolCreate(_PoolCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        # RP expects bytes but CLI allows integer TiBs for ease of use
        logger.debug("ANF log: PoolCreate: size: %s", args.size)
        if has_value(args.size):
            args.size = int(args.size.to_serialized_data()) * tib_scale


class PoolUpdate(_PoolUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        # RP expects bytes but CLI allows integer TiBs for ease of use
        logger.debug("ANF log: PoolUpdate: size: %s", args.size)
        if has_value(args.size):
            args.size = int(args.size.to_serialized_data()) * tib_scale

# endregion


# region volume
class VolumeCreate(_VolumeCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZIntArgFormat, AAZBoolArg, AAZArgEnum
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet = AAZStrArg(
            options=["--vnet"],
            arg_group="Properties",
            help="Name or Resource ID of the vnet. If you want to use a vnet in other resource group, please provide the Resource ID instead of the name of the vnet.",
            required=False
        )

        # old export policy params, for backwards compatibility
        args_schema.rule_index = AAZStrArg(
            options=["--rule-index"],
            arg_group="ExportPolicy backwards compatibility",
            help="Order index. Exists for backwards compatibility, please use --export-policy-rules --rules instead.",
            required=False
        )
        args_schema.unix_read_only = AAZBoolArg(
            options=["--unix-read-only"],
            arg_group="ExportPolicy backwards compatibility",
            help="Read only access. Exists for backwards compatibility, please use --export-policy-rules (--rules) instead.",
            required=False
        )
        args_schema.unix_read_write = AAZBoolArg(
            options=["--unix-read-write"],
            arg_group="ExportPolicy backwards compatibility",
            help="Read and write access. Exists for backwards compatibility, please use --export-policy-rules --rules instead.",
            required=False
        )
        args_schema.cifs = AAZBoolArg(
            options=["--cifs"],
            arg_group="ExportPolicy backwards compatibility",
            help="Allows CIFS protocol. Enable only for CIFS type volumes. Exists for backwards compatibility, please use --export-policy-rules --rules instead.",
            required=False
        )
        args_schema.allowed_clients = AAZStrArg(
            options=["--allowed-clients"],
            arg_group="ExportPolicy backwards compatibility",
            help="Client ingress specification as comma separated string with IPv4 CIDRs, IPv4 host addresses and host names. Exists for backwards compatibility, please use --export-policy-rules --rules instead.",
            required=False
        )
        args_schema.kerberos5_read_only = AAZBoolArg(
            options=["--kerberos5-r"],
            arg_group="ExportPolicy backwards compatibility",
            help="Kerberos5 Read only access. Exists for backwards compatibility, please use --export-policy-rules --rules instead.",
            required=False
        )
        args_schema.kerberos5_read_write = AAZBoolArg(
            options=["--kerberos5-rw"],
            arg_group="ExportPolicy backwards compatibility",
            help="Kerberos5 Read and write access. Exists for backwards compatibility, please use --export-policy-rules --rules instead.",
            required=False
        )
        args_schema.kerberos5_i_read_only = AAZBoolArg(
            options=["--kerberos5i-r"],
            arg_group="ExportPolicy backwards compatibility",
            help="Kerberos5i Readonly access. Exists for backwards compatibility, please use --export-policy-rules --rules instead.",
            required=False
        )
        args_schema.kerberos5_i_read_write = AAZBoolArg(
            options=["--kerberos5i-rw"],
            arg_group="ExportPolicy backwards compatibility",
            help="Kerberos5i Read and write access. Exists for backwards compatibility, please use --export-policy-rules --rules instead.",
            required=False
        )
        args_schema.kerberos5_p_read_only = AAZBoolArg(
            options=["--kerberos5p-r"],
            arg_group="ExportPolicy backwards compatibility",
            help="Kerberos5p Readonly access. Exists for backwards compatibility, please use --export-policy-rules --rules instead.",
            required=False
        )
        args_schema.kerberos5_p_read_write = AAZBoolArg(
            options=["--kerberos5p-rw"],
            arg_group="ExportPolicy backwards compatibility",
            help="Kerberos5p Read and write access. Exists for backwards compatibility, please use --export-policy-rules --rules instead.",
            required=False
        )
        args_schema.has_root_access = AAZBoolArg(
            options=["--has-root-access"],
            arg_group="ExportPolicy backwards compatibility",
            help="Has root access to volume. Exists for backwards compatibility, please use --export-policy-rules --rules instead.",
            required=False
        )
        args_schema.chown_mode = AAZBoolArg(
            options=["--chown-mode"],
            arg_group="ExportPolicy backwards compatibility",
            help="This parameter specifies who is authorized to change the ownership of a file. restricted - Only root user can change the ownership of the file. unrestricted - Non-root users can change ownership of files that they own. Possible values include- Restricted, Unrestricted. Exists for backwards compatibility, please use --export-policy-rules --rules instead.",
            required=False,
            enum={"Restricted": "Restricted", "Unrestricted": "Unrestricted"}
        )

        args_schema.usage_threshold._default = 100
        args_schema.usage_threshold._fmt = AAZIntArgFormat(
            maximum=2457600,
            minimum=50
        )

        # The API does only support setting Basic and Standard
        args_schema.network_features.enum = AAZArgEnum({"Basic": "Basic", "Standard": "Standard"}, case_sensitive=False)

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        # RP expects bytes but CLI allows integer TiBs for ease of use
        logger.debug("ANF log: VolumeCreate.pre_operations usage_threshold: %s", args.usage_threshold)
        if args.usage_threshold is not None:
            args.usage_threshold = int(args.usage_threshold.to_serialized_data()) * gib_scale

        # default the resource group of the subnet to the volume's rg unless the subnet is specified by id
        subnet = args.subnet_id
        subnet_rg = args.resource_group
        subs_id = self.ctx.subscription_id
        vnetArg = args.vnet.to_serialized_data()
        # determine subnet - supplied value can be name or ARM resource Id
        if not is_valid_resource_id(args.subnet_id.to_serialized_data()):
            if is_valid_resource_id(vnetArg):
                # determine vnet - supplied value can be name or ARM resource Id
                resource_parts = parse_resource_id(vnetArg)
                vnetArg = resource_parts['resource_name']
                subnet_rg = resource_parts['resource_group']
            args.subnet_id = f"/subscriptions/{subs_id}/resourceGroups/{subnet_rg}/providers/Microsoft.Network/virtualNetworks/{vnetArg}/subnets/{subnet}"

        # if NFSv4 is specified then the export policy must reflect this
        # the RP ordinarily only creates a default setting NFSv3.
        logger.debug("ANF log: ProtocolTypes rules len:%s", len(args.protocol_types))

        for protocol in args.protocol_types:
            logger.debug("ANF log: ProtocolType: %s", protocol)

        logger.debug("ANF log: exportPolicy rules len:%s", len(args.export_policy_rules))

        for rule in args.export_policy_rules:
            logger.debug("ANF log: rule: %s", rule)

        if (has_value(args.protocol_types) and any(x in ['NFSv3', 'NFSv4.1'] for x in args.protocol_types) and len(args.export_policy_rules) == 0) \
                and not ((len(args.protocol_types) == 1 and all(elem == "NFSv3" for elem in args.protocol_types) and not has_value(args.rule_index)) and len(args.export_policy_rules) == 0):
            isNfs41 = False
            isNfs3 = False
            cifs = False

            if not has_value(args.rule_index):
                rule_index = 1
            else:
                rule_index = int(args.rule_index.to_serialized_data()) or 1
            if "NFSv4.1" in args.protocol_types:
                isNfs41 = True
                if not has_value(args.allowed_clients):
                    raise ValidationError("Parameter allowed-clients needs to be set when protocol-type is NFSv4.1")
            if "NFSv3" in args.protocol_types:
                isNfs3 = True
            if "CIFS" in args.protocol_types:
                cifs = True

            logger.debug("ANF log: Setting exportPolicy rule index: %s, isNfs3: %s, isNfs4: %s, cifs: %s", rule_index, isNfs3, isNfs41, cifs)

            logger.debug("ANF log: Before exportPolicy rule => : rule_index: %s, nfsv3: %s, nfsv4: %s, cifs: %s", args.export_policy_rules[0]["rule_index"], args.export_policy_rules[0]["nfsv3"], args.export_policy_rules[0]["nfsv41"], args.export_policy_rules[0]["cifs"])
            logger.debug("ANF log: args.rule_index %s,  rule_index: %s", args.rule_index, rule_index)
            args.export_policy_rules[0]["rule_index"] = rule_index
            args.export_policy_rules[0]["nfsv3"] = isNfs3
            args.export_policy_rules[0]["nfsv41"] = isNfs41
            args.export_policy_rules[0]["cifs"] = cifs
            args.export_policy_rules[0]["allowed_clients"] = args.allowed_clients
            args.export_policy_rules[0]["unix_read_only"] = args.unix_read_only
            args.export_policy_rules[0]["unix_read_write"] = args.unix_read_write
            args.export_policy_rules[0]["cifs"] = args.cifs
            args.export_policy_rules[0]["kerberos5_read_only"] = args.kerberos5_read_only
            args.export_policy_rules[0]["kerberos5_read_write"] = args.kerberos5_read_write
            args.export_policy_rules[0]["kerberos5i_read_only"] = args.kerberos5_i_read_only
            args.export_policy_rules[0]["kerberos5i_read_write"] = args.kerberos5_i_read_write
            args.export_policy_rules[0]["kerberos5p_read_only"] = args.kerberos5_p_read_only
            args.export_policy_rules[0]["kerberos5p_read_write"] = args.kerberos5_p_read_write
            args.export_policy_rules[0]["has_root_access"] = args.has_root_access
            args.export_policy_rules[0]["chown_mode"] = args.chown_mode

            logger.debug("ANF log: after exportPolicy rule => : %s, %s, %s, %s", args.export_policy_rules[0]["rule_index"], args.export_policy_rules[0]["nfsv3"], args.export_policy_rules[0]["nfsv41"], args.export_policy_rules[0]["cifs"])
        else:
            logger.debug("ANF log: Don't create export policy")


# check if flattening dataprotection works
class VolumeUpdate(_VolumeUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZIntArgFormat, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet = AAZStrArg(
            options=["--vnet"],
            arg_group="Properties",
            help="Name or Resource ID of the vnet. If you want to use a vnet in other resource group or subscription, please provide the Resource ID instead of the name of the vnet.",
            required=False,
        )
        args_schema.remote_volume_resource_id = AAZStrArg(
            options=["--remote-volume-id", "--remote-volume-resource-id"],
            arg_group="Replication",
            help="The resource ID of the remote volume.",
            nullable=True,
        )
        args_schema.usage_threshold._fmt = AAZIntArgFormat(
            maximum=2457600,
            minimum=50
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        # RP expects bytes but CLI allows integer TiBs for ease of use
        logger.debug("ANF-Extension log: VolumeUpdate pre_operations")
        logger.debug("ANF-Extension log: usage_threshold: %s", args.usage_threshold)
        if has_value(args.usage_threshold) and args.usage_threshold.to_serialized_data() is not None:
            args.usage_threshold = int(args.usage_threshold.to_serialized_data()) * gib_scale


class VolumeBreakFileLocks(_BreakFileLocks):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.confirm_running_disruptive_operation.registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        # RP expects confirm_running_disruptive_operation but we use standard Azure CLI prompts, if we are here we are confirmed
        logger.debug("ANF-Extension log: VolumeBreakFileLocks pre_operations")
        args.confirm_running_disruptive_operation = True
# endregion


# region ExportPolicy
class ExportPolicyList(_ExportPolicyList):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        logger.debug("ANF log: ExportPolicyList _build_arguments_schema")
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema

    def _output(self, *args, **kwargs):
        logger.debug("ANF log: ExportPolicyList _output")
        result = self.deserialize_output(self.ctx.selectors.subresource.required(), client_flatten=True)
        return result

    class SubresourceSelector(AAZJsonSelector):
        def _get(self):
            result = self.ctx.vars.instance
            return result.properties.exportPolicy

        def _set(self, value):
            result = self.ctx.vars.instance
            result.properties.exportPolicy = value


class ExportPolicyAdd(_ExportPolicyAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        logger.debug("ANF log: ExportPolicyAdd _build_arguments_schema")
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.rule_index._required = False
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        # if rule_index is None:
        #     rule_index = 1 if len(instance.export_policy.rules) < 1 else max(rule.rule_index for rule in instance.export_policy.rules) + 1
        result = self.ctx.vars.instance
        if not has_value(args.rule_index):
            instance = result.properties
            rule_index = 1 if len(instance.export_policy.rules) < 1 else max(rule.rule_index.to_serialized_data() for rule in instance.export_policy.rules) + 1
            logger.debug("ANF log: No rule_index given, set to %s", rule_index)
            args.rule_index = rule_index

    def _output(self, *args, **kwargs):
        logger.debug("ANF log: ExportPolicyAdd _output")
        # For backwards compatibility return the whole resource
        result = self.deserialize_output(self.ctx.selectors.subresource.required(), client_flatten=True)
        return result

    class SubresourceSelector(AAZJsonSelector):
        def _get(self):
            result = self.ctx.vars.instance
            return result

        def _set(self, value):
            result = self.ctx.vars.instance
            result = result.properties.exportPolicy.rules
            filters = enumerate(result)
            filters = filter(
                lambda e: e[1].ruleIndex == self.ctx.args.rule_index,
                filters
            )
            idx = next(filters, [len(result)])[0]
            result[idx] = value


class ExportPolicyRemove(_ExportPolicyRemove):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        logger.debug("ANF log: ExportPolicyRemove _build_arguments_schema")
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema

    # def pre_operations(self):
    #     args = self.ctx.args

    def _output(self):
        logger.debug("ANF log: ExportPolicyRemove _output")
        # For backwards compatibility return the whole resource
        result = self.deserialize_output(self.ctx.selectors.subresource.required(), client_flatten=True)
        return result

    class SubresourceSelector(AAZJsonSelector):
        def _get(self):
            result = self.ctx.vars.instance
            return result
            # result = result.properties.exportPolicy.rules
            # filters = enumerate(result)
            # filters = filter(
            #     lambda e: e[1].ruleIndex == self.ctx.args.rule_index,
            #     filters
            # )
            # idx = next(filters)[0]
            # return result[idx]

        def _set(self, value):
            result = self.ctx.vars.instance
            result = result.properties.exportPolicy.rules
            filters = enumerate(result)
            filters = filter(
                lambda e: e[1].ruleIndex == self.ctx.args.rule_index,
                filters
            )
            idx = next(filters, [len(result)])[0]
            result[idx] = value

# endregion

# region volume replication custom


class ReplicationResume(_ReplicationResume):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        logger.debug("ANF log: ReplicationResume _build_arguments_schema")
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return args_schema

    def pre_operations(self):
        # RP expects bytes but CLI allows integer TiBs for ease of use
        logger.debug("ANF log: ReplicationResume pre_operations")
        logger.warning("\nIf any quota rules exists on destination volume they will be overwritten with source volume's quota rules.")

# endregion


# region VolumeGroup
class VolumeGroupCreate(_VolumeGroupCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZIntArg, AAZDictArg, AAZBoolArg, AAZListArg, AAZStrArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        logger.debug("ANF log: VolumeGroup _build_arguments_schema")

        args_schema.tags = AAZDictArg(
            options=["--tags"],
            arg_group="Body",
            help="Resource tags.",
        )
        args_schema.tags.Element = AAZStrArg(
            nullable=True,
        )
        args_schema.zones = AAZListArg(
            options=["--zones"],
            arg_group="Body",
            help="Availability Zone",
        )
        zones = cls._args_schema.zones
        zones.Element = AAZStrArg(
            fmt=AAZStrArgFormat(
                max_length=255,
                min_length=1,
            ),
        )
        args_schema.gp_rules = AAZDictArg(
            options=["--gp-rules"],
            arg_group="GroupMetaData",
            help="Application specific placement rules for the volume group.",
            nullable=True,
        )
        args_schema.gp_rules.Element = AAZStrArg(
            nullable=True,
        )
        args_schema.global_placement_rules._registered = False

        args_schema.pool_name = AAZStrArg(
            options=["--pool-name", "-p"],
            arg_group="Volumes",
            help="Name of the ANF capacity pool",
        )
        args_schema.proximity_placement_group = AAZStrArg(
            options=["--proximity-placement-group", "--ppg"],
            arg_group="Volumes",
            help="The resource id of the Proximity Placement Group for volume placement.",
            required=False
        )
        args_schema.vnet = AAZStrArg(
            options=["--vnet"],
            arg_group="Volumes",
            help="The ARM Id or name of the vnet for the volumes.",
            required=False
        )
        args_schema.add_snapshot_capacity = AAZIntArg(
            options=["--add-snapshot-capacity"],
            arg_group="Volumes",
            help="Additional memory to store snapshots, must be specified as % of RAM (range 0-200). This is used to auto compute storage size.  Default: 50.",
            required=False,
            default=50
        )
        args_schema.prefix = AAZStrArg(
            options=["--prefix"],
            arg_group="Volumes",
            help="All volume names will be prefixed with the given text. The default values for prefix text depends on system role. For PRIMARY it will be `\"\"` and HA it will be `\"HA-\"`.",
        )
        args_schema.smb_access = AAZStrArg(
            options=["--smb-access"],
            arg_group="Volumes",
            help="Enables access based enumeration share property for SMB Shares. Only applicable for SMB/DualProtocol volume.",
            required=False,
            enum={"Disabled": "Disabled", "Enabled": "Enabled"},
        )
        args_schema.smb_browsable = AAZStrArg(
            options=["--smb-browsable"],
            arg_group="Volumes",
            help="Enables non-browsable property for SMB Shares. Only applicable for SMB/DualProtocol volume",
            required=False,
            enum={"Disabled": "Disabled", "Enabled": "Enabled"},
        )
        args_schema.start_host_id = AAZIntArg(
            options=["--start-host-id"],
            arg_group="Volumes",
            help="Starting SAP-HANA Host ID. Host ID 1 indicates Master Host. Shared, Data Backup and Log Backup volumes are only provisioned for Master Host i.e. `HostID == 1`.",
            default=1
        )
        args_schema.subnet = AAZStrArg(
            options=["--subnet"],
            arg_group="Volumes",
            help="The delegated Subnet name.",
            default="Default"
        )
        args_schema.system_role = AAZStrArg(
            options=["--system-role"],
            arg_group="Volumes",
            help=" Type of role for the storage account. Primary indicates first of a SAP-HANA Replication (HSR) setup or No HSR. High Availability (HA) specifies local scenario. Default is PRIMARY.  Allowed values: DR, HA, PRIMARY.",
            enum={"DR": "DR", "HA": "HA", "PRIMARY": "PRIMARY"},
            default="PRIMARY"
        )

        # replication volume (backup volume) arguments
        args_schema.backup_nfsv3 = AAZBoolArg(
            options=["--backup-nfsv3"],
            arg_group="Backup Volume Properties",
            help="Indicates if NFS Protocol version 3 is preferred for data backup and log backup volumes. Default is False.",
            required=False,
            default=False,
        )
        args_schema.data_backup_replication_schedule = AAZStrArg(
            options=["--data-backup-repl-skd"],
            arg_group="Data Backup Volume",
            help="Replication Schedule for data backup volume.",
            enum={"_10minutely": "_10minutely", "daily": "daily", "hourly": "hourly"},
        )
        args_schema.data_backup_size = AAZIntArg(
            options=["--data-backup-size"],
            arg_group="Data Backup Volume",
            help="Capacity (in GiB) for data backup volumes. If not provided size will automatically be calculated.",
            required=False,
        )
        args_schema.data_backup_src_id = AAZStrArg(
            options=["--data-backup-src-id"],
            arg_group="Data Backup Volume",
            help="ResourceId of the data backup source volume.",
            required=False,
        )
        args_schema.data_backup_throughput = AAZIntArg(
            options=["--data-backup-throughput"],
            arg_group="Data Backup Volume",
            help="Throughput in MiB/s for data backup volumes. If not provided size will automatically be calculated.",
            required=False,
        )
        # data volume  arguments
        args_schema.data_repl_skd = AAZStrArg(
            options=["--data-repl-skd"],
            arg_group="Data Volume",
            help="Replication Schedule for data volume.",
            enum={"_10minutely": "_10minutely", "daily": "daily", "hourly": "hourly"},
        )
        args_schema.data_size = AAZIntArg(
            options=["--data-size"],
            arg_group="Data Volume",
            help="Capacity (in GiB) for data volumes. If not provided size will automatically be calculated.",
            required=False,
        )
        args_schema.data_src_id = AAZStrArg(
            options=["--data-src-id"],
            arg_group="Data Volume",
            help="ResourceId of the data source volume.",
            required=False,
        )
        args_schema.data_throughput = AAZIntArg(
            options=["--data-throughput"],
            arg_group="Data Volume",
            help="Throughput in MiB/s for data volumes. If not provided size will automatically be calculated.",
            required=False,
        )
        # log volume  arguments
        args_schema.log_size = AAZIntArg(
            options=["--log-size"],
            arg_group="Log Volume",
            help="Capacity (in GiB) for log volumes. If not provided size will automatically be calculated.",
            required=False,
        )
        args_schema.log_throughput = AAZIntArg(
            options=["--log-throughput"],
            arg_group="Log Volume",
            help="Throughput in MiB/s for log volumes. If not provided size will automatically be calculated.",
            required=False,
        )
        args_schema.log_backup_repl_skd = AAZStrArg(
            options=["--log-backup-repl-skd"],
            arg_group="Log Volume",
            help="Replication Schedule for Log backup volume.",
            enum={"_10minutely": "_10minutely", "daily": "daily", "hourly": "hourly"},
        )
        args_schema.log_backup_size = AAZIntArg(
            options=["--log-backup-size"],
            arg_group="Log Backup Volume",
            help="Capacity (in GiB) for log backup volumes. If not provided size will automatically be calculated.",
            required=False,
        )
        args_schema.log_backup_src_id = AAZStrArg(
            options=["--log-backup-src-id"],
            arg_group="Log Backup Volume",
            help="ResourceId of the log backup source volume.",
            required=False
        )
        args_schema.log_backup_throughput = AAZIntArg(
            options=["--log-backup-throughput"],
            arg_group="Log Backup Volume",
            help="Throughput in MiB/s for log backup volumes. If not provided size will automatically be calculated.",
            required=False,
        )
        # shared volume  arguments
        args_schema.shared_repl_skd = AAZStrArg(
            options=["--shared-repl-skd"],
            arg_group="Shared Volume",
            help="Replication Schedule for shared volume.",
            enum={"_10minutely": "_10minutely", "daily": "daily", "hourly": "hourly"},
        )
        args_schema.shared_size = AAZIntArg(
            options=["--shared-size"],
            arg_group="Shared Volume",
            help="Capacity (in GiB) for shared volumes. If not provided size will automatically be calculated.",
            required=False,
        )
        args_schema.shared_src_id = AAZStrArg(
            options=["--shared-src-id"],
            arg_group="Shared Volume",
            help="ResourceId of the shared source volume.",
            required=False
        )
        args_schema.shared_throughput = AAZIntArg(
            options=["--shared-throughput"],
            arg_group="Shared Volume",
            help="Throughput in MiB/s for shared volumes. If not provided size will automatically be calculated.",
            required=False,
        )
        args_schema.shared_network_features = AAZStrArg(
            options=["--shared-network-features", "--network-features"],
            arg_group="Shared Volume",
            help="Network features available to the volumes in the volume group.",
            default="Basic",
            enum={"Basic": "Basic", "Standard": "Standard"},
        )
        # cmk
        args_schema.key_vault_private_endpoint_resource_id = AAZStrArg(
            options=["--kv-private-endpoint-id", "--key-vault-private-endpoint-resource-id"],
            arg_group="CMK Encryption",
            help="The resource ID of private endpoint for KeyVault. It must reside in the same VNET as the volume. Only applicable if encryptionKeySource = 'Microsoft.KeyVault'.",
        )
        args_schema.encryption_key_source = AAZStrArg(
            options=["--encryption-key-source"],
            arg_group="CMK Encryption",
            help="Source of key used to encrypt data in volume. Applicable if NetApp account has encryption.keySource = 'Microsoft.KeyVault'.",
            default="Microsoft.NetApp",
            enum={"Microsoft.KeyVault": "Microsoft.KeyVault", "Microsoft.NetApp": "Microsoft.NetApp"},
        )
        args_schema.memory = AAZIntArg(
            options=["--memory"],
            arg_group="Volume Group SAP-HANA sizing",
            help="System (SAP-HANA) memory in GiB (max 12000 GiB), used to auto compute storage size and throughput.",
            default=100
        )
        args_schema.number_of_hosts = AAZIntArg(
            options=["--number-of-hosts", "--number-of-hots"],
            arg_group="Volume Group SAP-HANA sizing",
            help="Total Number of system (SAP-HANA) host in this deployment (currently max 3 nodes can be configured)",
            default=1,
        )
        args_schema.database_size = AAZIntArg(
            options=["--database-size"],
            arg_group="Volume Group Oracle sizing",
            help="Oracle database size in (TiB), used to auto compute storage size and throughput.",
            default=100
        )
        args_schema.number_of_oracle_volumes = AAZIntArg(
            options=["--number-of-volumes"],
            arg_group="Volume Group Oracle sizing",
            help="Total Number of Oracle data volumes (currently min 2 and max 8 nodes can be configured)"
        )
        args_schema.database_throughput = AAZIntArg(
            options=["--database-throughput"],
            arg_group="Volume Group Oracle sizing",
            help="Oracle database throughput in (MiB/s), used to auto compute storage size and throughput.",
            default=1,
        )
        args_schema.log_mirror_size = AAZIntArg(
            options=["--log-mirror-size"],
            arg_group="Oracle Volumes",
            help="Capacity (in GiB) for log mirror volume. If not provided size will automatically be calculated.",
            required=False,
        )
        # args_schema.log_backup_src_id = AAZStrArg(
        #     options=["--log-backup-src-id"],
        #     arg_group="Oracle Volumes",
        #     help="ResourceId of the log backup source volume.",
        #     required=False
        # )
        args_schema.log_mirror_throughput = AAZIntArg(
            options=["--log-mirror-throughput"],
            arg_group="Oracle Volumes",
            help="Throughput in MiB/s for log mirror volume. If not provided size will automatically be calculated.",
            required=False,
        )
        args_schema.binary_size = AAZIntArg(
            options=["--binary-size"],
            arg_group="Oracle Volumes",
            help="Capacity (in GiB) for binary volume. If not provided size will automatically be calculated.",
            required=False,
        )
        args_schema.binary_throughput = AAZIntArg(
            options=["--binary-throughput"],
            arg_group="Oracle Volumes",
            help="Throughput in MiB/s for log binary volume. If not provided size will automatically be calculated.",
            required=False,
        )
        return args_schema

# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
    def pre_operations(self):
        args = self.ctx.args
        account_name = args.account_name.to_serialized_data()
        application_type = args.application_type.to_serialized_data()
        number_of_hosts = args.number_of_hosts.to_serialized_data()
        number_of_volumes = args.number_of_oracle_volumes.to_serialized_data()
        memory = args.memory.to_serialized_data()
        add_snapshot_capacity = args.add_snapshot_capacity.to_serialized_data()
        system_role = args.system_role.to_serialized_data()
        pool_name = args.pool_name.to_serialized_data()

        if has_value(args.application_identifier):
            application_identifier = args.application_identifier.to_serialized_data()
        else:
            if application_type == "ORACLE":
                application_identifier = "ORA1"
            elif application_type == "SAP-HANA":
                application_identifier = "SH1"

        if has_value(args.data_size):
            data_size = args.data_size.to_serialized_data()
        else:
            data_size = None
        if has_value(args.data_throughput):
            data_throughput = args.data_throughput.to_serialized_data()
        else:
            data_throughput = None
        if has_value(args.database_throughput):
            database_throughput = args.database_throughput.to_serialized_data()

        data_repl_skd = args.data_repl_skd.to_serialized_data()
        data_src_id = args.data_src_id.to_serialized_data()
        if has_value(args.log_throughput):
            log_throughput = args.log_throughput.to_serialized_data()
        else:
            log_throughput = None
        if has_value(args.log_size):
            log_size = args.log_size.to_serialized_data()
        else:
            log_size = None

        if has_value(args.shared_size):
            shared_size = args.shared_size.to_serialized_data()
        else:
            shared_size = None
        if has_value(args.shared_throughput):
            shared_throughput = args.shared_throughput.to_serialized_data()
        else:
            shared_throughput = None
        if has_value(args.shared_network_features):
            shared_network_features = args.shared_network_features.to_serialized_data()
        else:
            shared_network_features = None

        shared_repl_skd = args.shared_repl_skd.to_serialized_data()
        shared_src_id = args.data_repl_skd.to_serialized_data()
        smb_access_based_enumeration = args.smb_access.to_serialized_data()
        smb_non_browsable = args.smb_browsable.to_serialized_data()

        if has_value(args.log_size):
            log_size = args.log_size.to_serialized_data()
        else:
            log_size = None
        if has_value(args.data_backup_throughput):
            data_backup_throughput = args.data_backup_throughput.to_serialized_data()
        else:
            data_backup_throughput = None

        backup_nfsv3 = args.backup_nfsv3.to_serialized_data()
        data_backup_repl_skd = args.data_backup_replication_schedule.to_serialized_data()
        data_backup_src_id = args.data_backup_src_id.to_serialized_data()

        if has_value(args.data_backup_size):
            data_backup_size = args.data_backup_size.to_serialized_data()
        else:
            data_backup_size = None

        if has_value(args.log_backup_throughput):
            log_backup_throughput = args.log_backup_throughput.to_serialized_data()
        else:
            log_backup_throughput = None
        log_backup_repl_skd = args.log_backup_repl_skd.to_serialized_data()
        log_backup_src_id = args.log_backup_src_id.to_serialized_data()
        if has_value(args.log_backup_size):
            log_backup_size = args.log_backup_size.to_serialized_data()
        else:
            log_backup_size = None

        kv_private_endpoint_id = args.key_vault_private_endpoint_resource_id.to_serialized_data()
        encryption_key_source = args.encryption_key_source.to_serialized_data()

        ppg = args.proximity_placement_group.to_serialized_data()

        if has_value(args.zones):
            zones = args.zones.to_serialized_data()
        else:
            zones = None

        logger.debug("ANF log: VolumeGroupCreate.pre_operations: Pool: %s, Hosts: %s, memory: %s, additional snapshot capacity: {add_snapshot_capacity}", {pool_name}, {number_of_hosts}, {memory})
        if application_type == "ORACLE":
            if has_value(args.number_of_oracle_volumes):
                if args.number_of_oracle_volumes < 2 or args.number_of_oracle_volumes > 8:
                    raise ValidationError("Number of volumes must be between 2 and 8")
            else:
                number_of_volumes = 2
        elif application_type == "SAP-HANA":
            if number_of_hosts < 1 or number_of_hosts > 3:
                raise ValidationError("Number of hosts must be between 1 and 3")
            if memory < 1 or memory > 12000:
                raise ValidationError("Memory must be between 1 and 12000")
            if system_role == "DR" and number_of_hosts != 1:
                raise ValidationError("Number of hosts must be 1 when creating a Disaster Recovery (DR) volume group")

        if add_snapshot_capacity < 0 or add_snapshot_capacity > 200:
            raise ValidationError("Additional capacity for snapshot must be between 0 and 200")

        if not has_value(args.prefix):
            prefix = ""
            if system_role == "HA":
                prefix = "HA-"
            if system_role == "DR":
                prefix = "DR-"
        else:
            prefix = str(prefix) + "-"
        logger.debug("gp rules count %s", len(args.gp_rules))
        if has_value(args.gp_rules):
            _gp_rules = []
            for key, value in args.gp_rules.items():
                _gp_rules.append({
                    "key": key,
                    "value": value,
                })
            args.global_placement_rules = _gp_rules
        if not has_value(args.group_description):
            args.group_description = f"Primary for {args.volume_group_name}"

        # default the resource group of the subnet to the volume's rg unless the subnet is specified by id
        subnet_rg = args.resource_group

        # determine vnet - supplied value can be name or ARM resource Id
        vnet = args.vnet.to_serialized_data()
        if is_valid_resource_id(vnet):
            resource_parts = parse_resource_id(vnet)
            vnet = resource_parts['resource_name']
            subnet_rg = resource_parts['resource_group']
        # determine subnet - supplied value can be name or ARM resource Id
        subnet = args.subnet.to_serialized_data()
        if is_valid_resource_id(subnet):
            resource_parts = parse_resource_id(subnet)
            subnet = resource_parts['resource_name']
            subnet_rg = resource_parts['resource_group']
        subscription_id = self.ctx.subscription_id

        subnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{subnet_rg}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}"

        pool_id = f"/subscriptions/{subscription_id}/resourceGroups/{subnet_rg}/providers/Microsoft.NetApp/netAppAccounts/{account_name}/capacityPools/{pool_name}"
        logger.debug("ANF LOG: VolumeGroupCreate.pre_operations()  => Received: %s volumes ", len(args.volumes))
        if not has_value(args.volumes) or len(args.volumes) == 0:
            # Create data volume(s)
            if application_type == "SAP-HANA":
                number_of_volumes = number_of_hosts

            data_volumes = []
            start_host_id = args.start_host_id.to_serialized_data()
            # args.volumes.append({"name":"testname"})
            for i in range(start_host_id, start_host_id + number_of_volumes):
                data_volumes.append(create_data_volume_properties(subnet_id, application_identifier, application_type, pool_id, ppg, memory,
                                                                  add_snapshot_capacity, str(i), data_size, data_throughput,
                                                                  prefix, data_repl_skd, data_src_id, kv_private_endpoint_id, encryption_key_source,
                                                                  smb_access_based_enumeration, smb_non_browsable, zones, database_throughput, number_of_volumes, shared_network_features))

            # Create log volume(s)
            log_volumes = []
            if application_type == "SAP-HANA":
                for i in range(start_host_id, start_host_id + number_of_hosts):
                    log_volumes.append(create_log_volume_properties(subnet_id, application_identifier, application_type, pool_id, ppg, memory, str(i), log_size,
                                                                    log_throughput, prefix, kv_private_endpoint_id, encryption_key_source,
                                                                    smb_access_based_enumeration, smb_non_browsable, zones, database_throughput, shared_network_features))
            elif application_type == "ORACLE":
                log_volumes.append(create_log_volume_properties(subnet_id, application_identifier, application_type, pool_id, ppg, memory, 1, log_size,
                                                                log_throughput, prefix, kv_private_endpoint_id, encryption_key_source,
                                                                smb_access_based_enumeration, smb_non_browsable, zones, database_throughput, number_of_volumes, shared_network_features))
            total_data_volume_size = sum(int(vol["usage_threshold"]) for vol in data_volumes)
            total_log_volume_size = sum(int(vol["usage_threshold"]) for vol in log_volumes)

            # # Combine volumes and create shared and backup volumes
            # volumes = []
            args.volumes.extend(data_volumes)
            args.volumes.extend(log_volumes)

            args.volumes.append(create_shared_volume_properties(subnet_id, application_identifier, application_type, pool_id, ppg, memory, shared_size,
                                                                shared_throughput, number_of_hosts, prefix, shared_repl_skd, shared_src_id, kv_private_endpoint_id, encryption_key_source,
                                                                smb_access_based_enumeration, smb_non_browsable, zones, database_throughput, number_of_volumes, shared_network_features))
            args.volumes.append(create_data_backup_volume_properties(subnet_id, application_identifier, application_type, pool_id, ppg, memory, data_backup_size,
                                                                     data_backup_throughput, total_data_volume_size,
                                                                     total_log_volume_size, prefix, backup_nfsv3,
                                                                     data_backup_repl_skd, data_backup_src_id, kv_private_endpoint_id, encryption_key_source,
                                                                     smb_access_based_enumeration,
                                                                     smb_non_browsable, zones, database_throughput, number_of_volumes, shared_network_features))
            args.volumes.append(create_log_backup_volume_properties(subnet_id, application_identifier, application_type, pool_id, ppg, memory, log_backup_size,
                                                                    log_backup_throughput, prefix, backup_nfsv3, log_backup_repl_skd,
                                                                    log_backup_src_id, kv_private_endpoint_id, encryption_key_source,
                                                                    smb_access_based_enumeration,
                                                                    smb_non_browsable, zones, database_throughput, number_of_volumes, shared_network_features))


# pylint: disable=too-many-locals
def create_data_volume_properties(subnet_id, application_identifier, application_type, pool_id, ppg, memory, add_snap_capacity, host_id,
                                  data_size, data_throughput, prefix, data_repl_skd=None, data_src_id=None, kv_private_endpoint_id=None,
                                  encryption_key_source=None, smb_access_based_enumeration=None, smb_non_browsable=None, zones=None, database_throughput=None, number_of_volumes=1, network_features=None):

    throughput = data_throughput
    if application_type == "SAP-HANA":
        name = prefix + application_identifier + "-" + VolumeType.DATA.value + "-mnt" + (host_id.rjust(5, '0'))
        volume_spec = VolumeType.DATA.value
        if data_size is None:
            size = calculate_usage_threshold(memory, VolumeType.DATA, add_snap_capacity=add_snap_capacity)
        else:
            size = data_size * gib_scale
        if throughput is None:
            throughput = calculate_throughput(memory, VolumeType.DATA)
    elif application_type == "ORACLE":
        name = prefix + application_identifier + "-" + OracleVolumeType.DATA.value + (host_id)
        volume_spec = OracleVolumeType.DATA.value + host_id
        if data_size is None:
            size = calculate_oracle_usage_threshold(memory, OracleVolumeType.DATA, add_snap_capacity=add_snap_capacity)
        else:
            size = data_size * gib_scale
        if throughput is None:
            if data_throughput is not None:
                throughput = calculate_oracle_throughput(databaseThroughput=data_throughput, numberOfDataVolumes=number_of_volumes, volume_type=OracleVolumeType.DATA)
            else:
                throughput = calculate_oracle_throughput(databaseThroughput=database_throughput, numberOfDataVolumes=number_of_volumes, volume_type=OracleVolumeType.DATA)

    data_protection = None
    if data_repl_skd is not None and data_src_id is not None:
        replication = ({"replication_schedule": data_repl_skd,
                        "remote_volume_resource_id": data_src_id})
        data_protection = {"replication": replication}

    data_volume = {
        "subnet_id": subnet_id,
        "creation_token": name,
        "capacity_pool_resource_id": pool_id,
        "proximity_placement_group": ppg,
        "volume_spec_name": volume_spec,
        "protocol_types": ["NFSv4.1"],
        "name": name,
        "usage_threshold": size,
        "throughput_mibps": throughput,
        "export_policy": create_default_export_policy_for_vg(),
        "data_protection": data_protection,
        "key_vault_private_endpoint_resource_id": kv_private_endpoint_id,
        "encryption_key_source": encryption_key_source,
        "smb_access_based_enumeration": smb_access_based_enumeration,
        "smb_non_browsable": smb_non_browsable,
        "zones": zones,
        "network_features": network_features
    }

    return data_volume


def create_log_volume_properties(subnet_id, application_identifier, application_type, pool_id, ppg, memory, host_id, log_size,
                                 log_throughput, prefix, kv_private_endpoint_id=None, encryption_key_source=None,
                                 smb_access_based_enumeration=None, smb_non_browsable=None, zones=None, database_throughput=None, number_of_volumes=1, network_features=None):
    throughput = log_throughput
    if application_type == "SAP-HANA":
        name = prefix + application_identifier + "-" + VolumeType.LOG.value + "-mnt" + (host_id.rjust(5, '0'))
        volume_spec = VolumeType.LOG.value
        if log_size is None:
            size = calculate_usage_threshold(memory, VolumeType.LOG)
        else:
            size = log_size * gib_scale
        if log_throughput is None:
            throughput = calculate_throughput(memory, VolumeType.LOG)
        else:
            throughput = log_throughput

    if application_type == "ORACLE":
        name = prefix + application_identifier + "-" + OracleVolumeType.LOG.value
        volume_spec = OracleVolumeType.LOG.value
        if log_size is None:
            size = calculate_oracle_usage_threshold(memory, OracleVolumeType.LOG)
        else:
            size = log_size * gib_scale
        if log_throughput is not None:
            throughput = calculate_oracle_throughput(databaseThroughput=log_throughput, numberOfDataVolumes=number_of_volumes, volume_type=OracleVolumeType.LOG)
        else:
            throughput = calculate_oracle_throughput(databaseThroughput=database_throughput, numberOfDataVolumes=number_of_volumes, volume_type=OracleVolumeType.LOG)

    log_volume = {
        "subnet_id": subnet_id,
        "creation_token": name,
        "capacity_pool_resource_id": pool_id,
        "proximity_placement_group": ppg,
        "volume_spec_name": volume_spec,
        "protocol_types": ["NFSv4.1"],
        "name": name,
        "usage_threshold": size,
        "throughput_mibps": throughput,
        "export_policy": create_default_export_policy_for_vg(),
        "key_vault_private_endpoint_resource_id": kv_private_endpoint_id,
        "encryption_key_source": encryption_key_source,
        "smb_access_based_enumeration": smb_access_based_enumeration,
        "smb_non_browsable": smb_non_browsable,
        "zones": zones,
        "network_features": network_features
    }

    return log_volume


# pylint: disable=too-many-locals
def create_shared_volume_properties(subnet_id, application_identifier, application_type, pool_id, ppg, memory, shared_size,
                                    shared_throughput, number_of_hosts, prefix, shared_repl_skd=None,
                                    shared_src_id=None, kv_private_endpoint_id=None, encryption_key_source=None, smb_access_based_enumeration=None,
                                    smb_non_browsable=None, zones=None, database_throughput=None, number_of_volumes=1, network_features=None):
    throughput = shared_throughput
    if application_type == "SAP-HANA":
        name = prefix + application_identifier + "-" + VolumeType.SHARED.value
        volume_spec = VolumeType.SHARED.value
        if has_value(shared_size):
            size = calculate_usage_threshold(memory, VolumeType.SHARED, total_host_count=number_of_hosts)
        else:
            size = shared_size * gib_scale

        if shared_throughput is None:
            throughput = calculate_throughput(memory, VolumeType.SHARED)
        else:
            throughput = shared_throughput

    if application_type == "ORACLE":
        name = prefix + application_identifier + "-" + OracleVolumeType.BINARY.value
        volume_spec = OracleVolumeType.BINARY.value
        if shared_size is None:
            size = calculate_oracle_usage_threshold(memory, OracleVolumeType.BINARY)
        else:
            size = shared_size * gib_scale
        if shared_throughput is not None:
            throughput = calculate_oracle_throughput(databaseThroughput=shared_throughput, numberOfDataVolumes=number_of_volumes, volume_type=OracleVolumeType.BINARY)
        else:
            throughput = calculate_oracle_throughput(databaseThroughput=database_throughput, numberOfDataVolumes=number_of_volumes, volume_type=OracleVolumeType.BINARY)

    data_protection = None
    if shared_repl_skd is not None and shared_src_id is not None:
        replication = {"replication_schedule": shared_repl_skd,
                       "remote_volume_resource_id": shared_src_id}
        data_protection = {"replication": replication}

    shared_volume = {
        "subnet_id": subnet_id,
        "creation_token": name,
        "capacity_pool_resource_id": pool_id,
        "proximity_placement_group": ppg,
        "volume_spec_name": volume_spec,
        "protocol_types": ["NFSv4.1"],
        "name": name,
        "usage_threshold": size,
        "throughput_mibps": throughput,
        "export_policy": create_default_export_policy_for_vg(),
        "data_protection": data_protection,
        "key_vault_private_endpoint_resource_id": kv_private_endpoint_id,
        "encryption_key_source": encryption_key_source,
        "smb_access_based_enumeration": smb_access_based_enumeration,
        "smb_non_browsable": smb_non_browsable,
        "zones": zones,
        "network_features": network_features
    }

    return shared_volume


# pylint: disable=too-many-locals
def create_data_backup_volume_properties(subnet_id, application_identifier, application_type, pool_id, ppg, memory, data_backup_size,
                                         data_backup_throughput, total_data_volume_size, total_log_volume_size,
                                         prefix, backup_nfsv3, data_backup_repl_skd, data_backup_src_id,
                                         kv_private_endpoint_id=None, encryption_key_source=None, smb_access_based_enumeration=None,
                                         smb_non_browsable=None, zones=None, database_throughput=None, number_of_volumes=1, network_features=None):
    logger.debug("ANF LOG: create_data_backup_volume_properties  => data_backup_size: %s * %s ", data_backup_size, gib_scale,)
    throughput = data_backup_throughput
    if application_type == "SAP-HANA":
        name = prefix + application_identifier + "-" + VolumeType.DATA_BACKUP.value
        volume_spec = VolumeType.DATA_BACKUP.value
        if data_backup_size is None:
            size = calculate_usage_threshold(memory, VolumeType.DATA_BACKUP, data_size=total_data_volume_size,
                                             log_size=total_log_volume_size)
        else:
            size = data_backup_size * gib_scale
        if data_backup_throughput is None:
            throughput = calculate_throughput(memory, VolumeType.DATA_BACKUP)
        else:
            throughput = data_backup_throughput

    elif application_type == "ORACLE":
        name = prefix + application_identifier + "-" + OracleVolumeType.BACKUP.value
        volume_spec = OracleVolumeType.BACKUP.value
        if data_backup_size is None:
            size = calculate_oracle_usage_threshold(memory, OracleVolumeType.BACKUP)
        else:
            size = data_backup_size * gib_scale
        if data_backup_throughput is not None:
            throughput = calculate_oracle_throughput(databaseThroughput=data_backup_throughput, numberOfDataVolumes=number_of_volumes, volume_type=OracleVolumeType.BACKUP)
        else:
            throughput = calculate_oracle_throughput(databaseThroughput=database_throughput, numberOfDataVolumes=number_of_volumes, volume_type=OracleVolumeType.BACKUP)

    data_protection = None
    if data_backup_repl_skd is not None and data_backup_src_id is not None:
        replication = {"replication_schedule": data_backup_repl_skd,
                       "remote_volume_resource_id": data_backup_src_id}
        data_protection = {"replication": replication}

    data_backup_volume = {
        "subnet_id": subnet_id,
        "creation_token": name,
        "capacity_pool_resource_id": pool_id,
        "proximity_placement_group": ppg,
        "volume_spec_name": volume_spec,
        "protocol_types": ['NFSv4.1'] if not backup_nfsv3 else ['NFSv3'],
        "name": name,
        "usage_threshold": size,
        "throughput_mibps": throughput,
        "export_policy": create_default_export_policy_for_vg(backup_nfsv3),
        "data_protection": data_protection,
        "key_vault_private_endpoint_resource_id": kv_private_endpoint_id,
        "encryption_key_source": encryption_key_source,
        "smb_access_based_enumeration": smb_access_based_enumeration,
        "smb_non_browsable": smb_non_browsable,
        "zones": zones,
        "network_features": network_features
    }

    return data_backup_volume


def create_log_backup_volume_properties(subnet_id, application_identifier, application_type, pool_id, ppg, memory, log_backup_size,
                                        log_backup_throughput, prefix, backup_nfsv3, log_backup_repl_skd,
                                        log_backup_src_id, kv_private_endpoint_id=None, encryption_key_source=None, smb_access_based_enumeration=None,
                                        smb_non_browsable=None, zones=None, database_throughput=None, number_of_volumes=1, network_features=None):

    throughput = log_backup_throughput
    if application_type == "SAP-HANA":
        name = prefix + application_identifier + "-" + VolumeType.LOG_BACKUP.value
        volume_spec = VolumeType.LOG_BACKUP.value
        if log_backup_size is None:
            size = calculate_usage_threshold(memory, VolumeType.LOG_BACKUP)
        else:
            size = log_backup_size * gib_scale
        if log_backup_throughput is None:
            throughput = calculate_throughput(memory, VolumeType.LOG_BACKUP)
        else:
            throughput = log_backup_throughput

    if application_type == "ORACLE":
        name = prefix + application_identifier + "-" + OracleVolumeType.LOG_MIRROR.value
        volume_spec = OracleVolumeType.LOG_MIRROR.value
        if log_backup_size is None:
            size = calculate_oracle_usage_threshold(memory, OracleVolumeType.LOG_MIRROR)
        else:
            size = log_backup_size * gib_scale
        if log_backup_throughput is not None:
            throughput = calculate_oracle_throughput(databaseThroughput=log_backup_throughput, numberOfDataVolumes=number_of_volumes, volume_type=OracleVolumeType.LOG_MIRROR)
        else:
            throughput = calculate_oracle_throughput(databaseThroughput=database_throughput, numberOfDataVolumes=number_of_volumes, volume_type=OracleVolumeType.BACKUP)

    data_protection = None
    if log_backup_repl_skd is not None and log_backup_src_id is not None:
        replication = {"replication_schedule": log_backup_repl_skd,
                       "remote_volume_resource_id": log_backup_src_id}
        data_protection = {"replication": replication}

    log_backup = {
        "subnet_id": subnet_id,
        "creation_token": name,
        "capacity_pool_resource_id": pool_id,
        "proximity_placement_group": ppg,
        "volume_spec_name": volume_spec,
        "protocol_types": ['NFSv4.1'] if not backup_nfsv3 else ['NFSv3'],
        "name": name,
        "usage_threshold": size,
        "throughput_mibps": throughput,
        "export_policy": create_default_export_policy_for_vg(backup_nfsv3),
        "data_protection": data_protection,
        "key_vault_private_endpoint_resource_id": kv_private_endpoint_id,
        "encryption_key_source": encryption_key_source,
        "smb_access_based_enumeration": smb_access_based_enumeration,
        "smb_non_browsable": smb_non_browsable,
        "zones": zones,
        "network_features": network_features
    }

    return log_backup


# Memory should be sent in as GiB and additional snapshot capacity as percentage (0-200). Usage is returned in bytes.
def calculate_usage_threshold(memory, volume_type, add_snap_capacity=50, total_host_count=1, data_size=50, log_size=50):
    if volume_type == VolumeType.DATA:
        usage = (add_snap_capacity / 100) * memory + memory
        return int(usage) * gib_scale if usage > 100 else 100 * gib_scale  # MIN 100 GiB
    if volume_type == VolumeType.LOG:
        if memory < 512:
            usage = memory * 0.5  # 50%
            return int(usage) * gib_scale if usage > 100 else 100 * gib_scale  # MIN 100 GiB
        return 512 * gib_scale
    if volume_type == VolumeType.SHARED:
        usage = ((total_host_count + 3) / 4) * memory
        return int(usage) * gib_scale if usage > 1024 else 1024 * gib_scale  # MIN 1 TiB
    if volume_type == VolumeType.DATA_BACKUP:
        usage = (data_size / gib_scale) + (log_size / gib_scale)
        return int(usage) * gib_scale if usage > 100 else 100 * gib_scale  # MIN 100 GiB
    if volume_type == VolumeType.LOG_BACKUP:
        return 512 * gib_scale


# Memory should be sent in in GiB. Returns throughput in MiB/s.
# pylint: disable=too-many-return-statements
def calculate_throughput(memory, volume_type):
    if volume_type == VolumeType.DATA:
        if memory <= 1024:
            return 400
        if memory <= 2048:
            return 600
        if memory <= 4096:
            return 800
        if memory <= 6144:
            return 1000
        if memory <= 8192:
            return 1200
        if memory <= 10248:
            return 1400
        return 1500
    if volume_type == VolumeType.LOG:
        if memory <= 4096:
            return 250
        return 500
    if volume_type == VolumeType.SHARED:
        return 64
    if volume_type == VolumeType.DATA_BACKUP:
        return 128
    if volume_type == VolumeType.LOG_BACKUP:
        return 250


# Usage is returned in bytes
def calculate_oracle_usage_threshold(databaseSize, volume_type, add_snap_capacity=50, total_volume_count=1):
    if volume_type == OracleVolumeType.DATA:
        sizeFactor = databaseSize / total_volume_count
        capacityFactor = (add_snap_capacity / 100) * sizeFactor
        usage = sizeFactor + capacityFactor
        return int(usage) * gib_scale if usage > 100 else 100 * gib_scale  # MIN 100 GiB
    return 100 * gib_scale


# pylint: disable=too-many-return-statements
def calculate_oracle_throughput(databaseThroughput, numberOfDataVolumes, volume_type):
    oracle_throughput = 150
    if volume_type == OracleVolumeType.DATA:
        oracle_throughput = max(100, databaseThroughput / numberOfDataVolumes)
    elif volume_type == OracleVolumeType.BINARY:
        oracle_throughput = 64
    return oracle_throughput


def create_default_export_policy_for_vg(nfsv3=False):
    rules = []
    export_policy = ({"rule_index": 1,
                      "unix_read_only": False,
                      "unix_read_write": True,
                      "nfsv3": nfsv3,
                      "nfsv41": not nfsv3,
                      "kerberos5_read_only": False,
                      "kerberos5_read_write": False,
                      "kerberos5i_read_only": False,
                      "kerberos5i_read_write": False,
                      "kerberos5p_read_only": False,
                      "kerberos5p_read_write": False,
                      "allowed_clients": "0.0.0.0/0"})
    rules.append(export_policy)
    volume_export_policy = {"rules": rules}
    return volume_export_policy


class VolumeType(Enum):
    DATA = "data"
    LOG = "log"
    SHARED = "shared"
    DATA_BACKUP = "data-backup"
    LOG_BACKUP = "log-backup"


class OracleVolumeType(Enum):
    DATA = "ora-data"
    LOG = "ora-log"
    BINARY = "ora-binary"
    BACKUP = "ora-backup"
    LOG_MIRROR = "ora-log-mirror"

# endregion
