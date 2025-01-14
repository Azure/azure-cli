# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import get_default_admin_username
from azure.cli.core.aaz import has_value, register_command
from .aaz.latest.lab import Get as _LabGet, Delete as _LabDelete, CreateEnvironment as _LabVmCreate
from .aaz.latest.lab.vm import (List as _LabVmList, Show as _LabVmShow, Delete as _LabVmDelete, Start as _LabVmStart,
                                Stop as _LabVmStop, ApplyArtifacts as _LabVmApplyArtifacts, Claim as LabVmClaim,
                                Hibernate as _LabVmHibernate)
from .aaz.latest.lab.custom_image import (Show as _CustomImageShow, Delete as _CustomImageDelete,
                                          Create as _CustomImageCreate)
from .aaz.latest.lab.artifact_source import Show as _ArtifactSourceShow
from .aaz.latest.lab.vnet import Get as _LabVnetGet
from .aaz.latest.lab.formula import Show as _FormulaShow, Delete as _FormulaDelete
from .aaz.latest.lab.secret import Set as _SecretSet, List as _SecretList, Show as _SecretShow, Delete as _SecretDelete
from .aaz.latest.lab.environment import (Create as _EnvironmentCreate, List as _EnvironmentList,
                                         Show as _EnvironmentShow, Delete as _EnvironmentDelete)
from .aaz.latest.lab.arm_template import Show as _ArmTemplateShow

# pylint: disable=too-many-locals, unused-argument, too-many-statements, protected-access


@register_command(
    "lab vm create",
    is_preview=True,
)
class LabVmCreate(_LabVmCreate):
    """Create a VM in a lab.
    """
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZBoolArg, AAZFileArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.artifacts = AAZFileArg(
            options=["--artifacts"],
            help="Path to the JSON encoded array of artifacts to be applied. JSON encoded list of parameters."
        )
        args_schema.disk_type = AAZBoolArg(
            options=["--disk-type"],
            help="Storage type to use for virtual machine.",
            enum={'Premium': 'Premium', 'Standard': 'Standard', 'StandardSSD': 'StandardSSD'}
        )
        args_schema.os_type = AAZStrArg(
            options=["--os-type"],
            help="Type of the OS on which the custom image is based.",
            enum={"Windows": "Windows", "Linux": "Linux"},
        )
        args_schema.formula = AAZStrArg(
            options=["--formula"],
            help="Name of the formula. Use `az lab formula list` for available formulas. "
                 "Use `az lab formula` with the `--export-artifacts` flag to export and update artifacts, "
                 "then pass the results via the `--artifacts` argument."
        )
        args_schema.generate_ssh_keys = AAZBoolArg(
            options=["--generate-ssh-keys"],
            help="Generate SSH public and private key files if missing."
        )
        args_schema.image = AAZStrArg(
            options=["--image"],
            help="The name of the operating system image (gallery image name or custom image name/ID)."
                 " Use `az lab gallery-image list` for available gallery images or "
                 "`az lab custom-image list` for available custom images."
        )
        args_schema.image_type = AAZStrArg(
            options=["--image-type"],
            help="Type of the image.",
            enum={'gallery': 'gallery', 'custom': 'custom'}
        )
        args_schema.admin_username = AAZStrArg(
            options=["--admin-username"],
            help="Username for the VM admin.",
            arg_group="Authentication",
            default=get_default_admin_username()
        )
        args_schema.admin_password = AAZStrArg(
            options=["--admin-password"],
            help="Password for the VM admin.",
            arg_group="Authentication"
        )
        args_schema.authentication_type = AAZStrArg(
            options=["--authentication-type"],
            help="Type of authentication allowed for the VM.",
            enum={'password': 'password', 'ssh': 'ssh'},
            arg_group="Authentication",
            default="password"
        )
        args_schema.saved_secret = AAZStrArg(
            options=["--saved-secret"],
            help="Name of the saved secret to be used for authentication. When this value is provided, "
                 "it is used in the place of other authentication methods.",
            arg_group="Authentication"
        )
        args_schema.ip_configuration = AAZStrArg(
            options=["--ip-configuration"],
            help="Type of IP configuration to use for the VM.",
            enum={'shared': 'shared', 'public': 'public', 'private': 'private'},
            arg_group="Network"
        )
        args_schema.subnet = AAZStrArg(
            options=["--subnet"],
            help="Name of the subnet to add the VM to.",
            arg_group="Network"
        )
        args_schema.vnet_name = AAZStrArg(
            options=["--vnet-name"],
            help="Name of the virtual network to add the VM to.",
            arg_group="Network"
        )
        args_schema.name._required = True
        args_schema.location._registered = False
        args_schema.artifacts_org._registered = False
        args_schema.ssh_key._arg_group = 'Authentication'
        args_schema.os_type._registered = False
        args_schema.environment_id._registered = False
        args_schema.bulk_creation_parameters ._registered = False
        args_schema.created_date._registered = False
        args_schema.custom_image_id ._registered = False
        args_schema.data_disk_parameters._registered = False
        args_schema.gallery_image_reference._registered = False
        args_schema.disallow_public_ip_address._registered = False
        args_schema.is_authentication_with_ssh_key._registered = False
        args_schema.user_name._registered = False
        args_schema.password._registered = False
        args_schema.lab_subnet_name._registered = False
        args_schema.lab_virtual_network_id._registered = False
        args_schema.network_interface._registered = False
        args_schema.owner_object_id._registered = False
        args_schema.owner_user_principal_name._registered = False
        args_schema.plan_id._registered = False
        args_schema.schedule_parameters._registered = False
        args_schema.storage_type._registered = False
        return args_schema

    def pre_operations(self):
        import json
        from .validators import validate_lab_vm_create
        args = self.ctx.args

        if has_value(args.artifacts):
            args.artifacts_org = json.loads(args.artifacts.to_serialized_data())

        if has_value(args.disk_type):
            args.storage_type = args.disk_type

        if has_value(args.admin_password):
            args.password = args.admin_password

        if has_value(args.subnet):
            args.lab_subnet_name = args.subnet

        args.user_name = args.admin_username
        validate_lab_vm_create(self, args)

        is_ssh_authentication = args.authentication_type.to_serialized_data() == 'ssh'
        args.is_authentication_with_ssh_key = is_ssh_authentication


class LabVmList(_LabVmList):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZBoolArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.claimable = AAZBoolArg(
            options=["--claimable"],
            help="List only claimable virtual machines in the lab. Cannot be used with `--filters`."
        )
        args_schema.all = AAZBoolArg(
            options=["--all"],
            help="List all virtual machines in the lab. Cannot be used with `--filters`."
        )
        args_schema.environment = AAZStrArg(
            options=["--environment"],
            help="Name or ID of the environment to list virtual machines in. Cannot be used with `--filters`.",
            arg_group="Filter"
        )
        args_schema.object_id = AAZStrArg(
            options=["--object-id"],
            help="Object ID of the owner to list VMs for."
        )
        args_schema.filters._arg_group = "Filter"
        return args_schema

    def pre_operations(self):
        from .validators import validate_lab_vm_list
        args = self.ctx.args
        validate_lab_vm_list(self, args)


class LabVmShow(_LabVmShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._id_part = None
        args_schema.lab_name._id_part = None
        return args_schema


class LabVmDelete(_LabVmDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._id_part = None
        args_schema.lab_name._id_part = None
        return args_schema


class LabVmStart(_LabVmStart):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._id_part = None
        args_schema.lab_name._id_part = None
        return args_schema


class LabVmStop(_LabVmStop):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._id_part = None
        args_schema.lab_name._id_part = None
        return args_schema


class LabVmHibernate(_LabVmHibernate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._id_part = None
        args_schema.lab_name._id_part = None
        return args_schema


class LabVmApplyArtifacts(_LabVmApplyArtifacts):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZFileArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.artifacts = AAZFileArg(
            options=["--artifacts"],
            help="Path to the JSON encoded array of artifacts to be applied. JSON encoded list of parameters."
        )
        args_schema.name._id_part = None
        args_schema.lab_name._id_part = None
        args_schema.artifacts_org._registered = False
        return args_schema

    def pre_operations(self):
        import json
        args = self.ctx.args
        if has_value(args.artifacts):
            args.artifacts_org = json.loads(args.artifacts.to_serialized_data())


def claim_vm(cmd, lab_name=None, name=None, resource_group_name=None):
    """ Command to claim a VM in the Azure DevTest Lab"""
    if name is None:
        from .aaz.latest.lab import ClaimAnyVm
        result = ClaimAnyVm(cli_ctx=cmd.cli_ctx)(command_args={
            "name": lab_name,
            "resource_group": resource_group_name
        })
        return result
    result = LabVmClaim(cli_ctx=cmd.cli_ctx)(command_args={
        "name": name,
        "lab_name": lab_name,
        "resource_group": resource_group_name
    })
    return result


def _export_parameters(arm_template):
    parameters = []
    if arm_template and arm_template.get('contents') and arm_template['contents'].get('parameters'):
        default_values = {}
        if arm_template.get('parametersValueFilesInfo'):
            for parameter_value_file_info in arm_template.get('parametersValueFilesInfo'):
                if isinstance(parameter_value_file_info['parametersValueInfo'], dict):
                    for k in parameter_value_file_info['parametersValueInfo']:
                        default_values[k] = parameter_value_file_info['parametersValueInfo'][k].get('value', "")

        if isinstance(arm_template['contents']['parameters'], dict):
            for k in arm_template['contents']['parameters']:
                param = {}
                param['name'] = k
                param['value'] = default_values.get(k, "")
                parameters.append(param)
    return parameters


class LabGet(_LabGet):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._id_part = None
        return args_schema


class LabDelete(_LabDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._id_part = None
        return args_schema


class CustomImageCreate(_CustomImageCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.source_vm_id = AAZResourceIdArg(
            options=["--source-vm-id"],
            help="The resource ID of a virtual machine in the provided lab.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{}/resourcegroups/{}/providers/microsoft.devtestlab/labs/{}/virtualmachines/{}"
            ),
            required=True
        )
        args_schema.os_type = AAZStrArg(
            options=["--os-type"],
            help="Type of the OS on which the custom image is based.",
            enum={"Windows": "Windows", "Linux": "Linux"},
            required=True
        )
        args_schema.os_state = AAZStrArg(
            options=["--os-state"],
            help="The current state of the virtual machine. "
                 "For Windows virtual machines: NonSysprepped, SysprepRequested, SysprepApplied. "
                 "For Linux virtual machines: NonDeprovisioned, DeprovisionRequested, DeprovisionApplied.",
            required=True
        )
        args_schema.vm._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.vm.source_vm_id = args.source_vm_id
        if args.os_type.to_serialized_data().lower() == "linux":
            args.vm.linux_os_info.linux_os_state = args.os_state
        if args.os_type.to_serialized_data().lower() == "windows":
            args.vm.windows_os_info.windows_os_state = args.os_state


class CustomImageShow(_CustomImageShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lab_name._id_part = None
        args_schema.name._id_part = None
        return args_schema


class CustomImageDelete(_CustomImageDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lab_name._id_part = None
        args_schema.name._id_part = None
        return args_schema


class ArtifactSourceShow(_ArtifactSourceShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lab_name._id_part = None
        args_schema.name._id_part = None
        return args_schema


class LabVnetGet(_LabVnetGet):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lab_name._id_part = None
        args_schema.name._id_part = None
        return args_schema


class FormulaShow(_FormulaShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lab_name._id_part = None
        args_schema.name._id_part = None
        return args_schema


@register_command(
    "lab formula export-artifacts",
    is_preview=True,
)
class FormulaExportArtifacts(_FormulaShow):
    """Export artifacts from a formula.
    """
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lab_name._id_part = None
        args_schema.name._id_part = None
        return args_schema


class FormulaDelete(_FormulaDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lab_name._id_part = None
        args_schema.name._id_part = None
        return args_schema


class SecretSet(_SecretSet):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lab_name._id_part = None
        args_schema.name._id_part = None
        args_schema.user_name._required = False
        args_schema.user_name._registered = False
        args_schema.value._required = True
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.user_name = "@me"


class SecretList(_SecretList):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.user_name._required = False
        args_schema.user_name._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.user_name = "@me"


class SecretShow(_SecretShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._id_part = None
        args_schema.lab_name._id_part = None
        args_schema.user_name._required = False
        args_schema.user_name._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.user_name = "@me"


class SecretDelete(_SecretDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._id_part = None
        args_schema.lab_name._id_part = None
        args_schema.user_name._required = False
        args_schema.user_name._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.user_name = "@me"


class EnvironmentCreate(_EnvironmentCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZFileArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.arm_template = AAZStrArg(
            options=["--arm-template"],
            help="Name or ID of the ARM template in the lab.",
            required=True
        )
        args_schema.artifact_source_name = AAZStrArg(
            options=["--artifact-source-name"],
            help="Name of the artifact source in the lab.  Values from: az lab artifact-source list."
        )
        args_schema.parameters = AAZFileArg(
            options=["--parameters"],
            help="Path to the parameters of the azure resource manager template. JSON encoded list of parameters."
        )
        args_schema.user_name._required = False
        args_schema.user_name._registered = False
        args_schema.deployment_properties._registered = False
        return args_schema

    def pre_operations(self):
        import json
        from azure.mgmt.core.tools import resource_id, is_valid_resource_id
        from azure.cli.core.azclierror import RequiredArgumentMissingError
        from azure.cli.core.commands.client_factory import get_subscription_id
        args = self.ctx.args
        args.user_name = "@me"

        if has_value(args.parameters):
            args.deployment_properties.parameters = json.loads(args.parameters.to_serialized_data())

        if not is_valid_resource_id(args.arm_template.to_serialized_data()):
            if not has_value(args.artifact_source_name):
                raise RequiredArgumentMissingError("--artifact-source-name is required "
                                                   "when name is provided for --arm-template")
            args.arm_template = resource_id(subscription=get_subscription_id(self.cli_ctx),
                                            resource_group=args.resource_group.to_serialized_data(),
                                            namespace='Microsoft.DevTestLab',
                                            type='labs',
                                            name=args.lab_name.to_serialized_data(),
                                            child_type_1='artifactSources',
                                            child_name_1=args.artifact_source_name.to_serialized_data(),
                                            child_type_2='armTemplates',
                                            child_name_2=args.arm_template.to_serialized_data())
        args.deployment_properties.arm_template_id = args.arm_template


class EnvironmentList(_EnvironmentList):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.user_name._required = False
        args_schema.user_name._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.user_name = "@me"


class EnvironmentShow(_EnvironmentShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._id_part = None
        args_schema.lab_name._id_part = None
        args_schema.user_name._required = False
        args_schema.user_name._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.user_name = "@me"


class EnvironmentDelete(_EnvironmentDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.name._id_part = None
        args_schema.lab_name._id_part = None
        args_schema.user_name._required = False
        args_schema.user_name._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.user_name = "@me"


class ArmTemplateShow(_ArmTemplateShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZBoolArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.export_parameters = AAZBoolArg(
            options=["--export-parameters"],
            help="Whether or not to export parameters template."
        )
        args_schema.name._id_part = None
        args_schema.lab_name._id_part = None
        return args_schema

    def _output(self, *args, **kwargs):
        args = self.ctx.args
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        if has_value(args.export_parameters) and args.export_parameters.to_serialized_data() is True:
            result = _export_parameters(result)
        return result
