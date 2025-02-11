# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger
from knack.util import CLIError
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id, resource_id

from azure.cli.core.azclierror import ValidationError, RequiredArgumentMissingError, MutuallyExclusiveArgumentError
from azure.cli.core.commands.arm import get_arm_resource_by_id

from azure.cli.core.aaz import has_value, AAZResourceLocationArg, AAZResourceLocationArgFormat, AAZListArg, AAZStrArg, \
    AAZBoolArg, AAZFloatArg, AAZIntArg, AAZIntArgFormat, AAZDictArg, AAZResourceIdArg, AAZResourceIdArgFormat
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.validators import validate_tags
from azure.cli.command_modules.network._validators import validate_managed_identity_resource_id
from .._validators import _resolve_api_version

from ..aaz.latest.network.watcher import RunConfigurationDiagnostic as _RunConfigurationDiagnostic
from ..aaz.latest.network.watcher import ShowNextHop as _ShowNextHop, ShowSecurityGroupView as _ShowSecurityGroupView, \
    ShowTopology as _ShowTopology
from ..aaz.latest.network.watcher import TestConnectivity as _TestConnectivity, TestIpFlow as _TestIPFlow

from ..aaz.latest.network.watcher.flow_log import Create as _NwFlowLogCreate, Update as _NwFlowLogUpdate, \
    List as _NwFlowLogList, Delete as _NwFlowLogDelete
from ..aaz.latest.network.watcher.troubleshooting import Start as _NwTroubleshootingStart, \
    Show as _NwTroubleshootingShow
from ..aaz.latest.network.watcher.packet_capture import Create as _PacketCaptureCreate
from ..aaz.latest.network.watcher.packet_capture import Delete as _PacketCaptureDelete, List as _PacketCaptureList, \
    Show as _PacketCaptureShow, ShowStatus as _PacketCaptureShowStatus, Stop as _PacketCaptureStop

from ..aaz.latest.network.watcher.connection_monitor import Create as _WatcherConnectionMonitorCreate
from ..aaz.latest.network.watcher.connection_monitor import Start as _WatcherConnectionMonitorStart
from ..aaz.latest.network.watcher.connection_monitor import Stop as _WatcherConnectionMonitorStop
from ..aaz.latest.network.watcher.connection_monitor import Show as _WatcherConnectionMonitorShow
from ..aaz.latest.network.watcher.connection_monitor import List as _WatcherConnectionMonitorList
from ..aaz.latest.network.watcher.connection_monitor import Delete as _WatcherConnectionMonitorDelete
from ..aaz.latest.network.watcher.connection_monitor import Query as _WatcherConnectionMonitorQuery
from ..aaz.latest.network.watcher.connection_monitor import Update as _WatcherConnectionMonitorUpdate
from ..aaz.latest.network.watcher.connection_monitor.output import Add as _WatcherConnectionMonitorOutputAdd, \
    List as _WatcherConnectionMonitorOutputList
from ..aaz.latest.network.watcher.connection_monitor.endpoint import Show as _WatcherConnectionMonitorEndpointShow, \
    Remove as _WatcherConnectionMonitorEndpointRemove, List as _WatcherConnectionMonitorEndpointList, \
    Add as _WatcherConnectionMonitorEndpointAdd

from ..aaz.latest.network.watcher.connection_monitor.test_configuration import Add as _MonitorTestConfigurationAdd, \
    Show as _MonitorTestConfigurationShow, List as _MonitorTestConfigurationList, \
    Remove as _MonitorTestConfigurationRemove

from ..aaz.latest.network.watcher.connection_monitor.test_group import Add as _WatcherConnectionMonitorTestGroupAdd, \
    Show as _WatcherConnectionMonitorTestGroupShow, List as _WatcherConnectionMonitorTestGroupList

logger = get_logger(__name__)


def get_network_watcher_from_location(cmd, watcher_name="watcher_name", rg_name="watcher_rg"):
    from ..aaz.latest.network.watcher import List

    args = cmd.ctx.args
    location = args.location.to_serialized_data()
    watcher_list = List(cli_ctx=cmd.cli_ctx)(command_args={})
    watcher = next((w for w in watcher_list if w["location"].lower() == location.lower()), None)
    if not watcher:
        raise ValidationError(f"network watcher is not enabled for region {location}.")

    id_parts = parse_resource_id(watcher["id"])
    setattr(args, rg_name, id_parts["resource_group"])
    setattr(args, watcher_name, id_parts["name"])


def get_network_watcher_from_vm(cmd):
    args = cmd.ctx.args
    compute_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_COMPUTE).virtual_machines
    vm_name = parse_resource_id(args.vm.to_serialized_data())["name"]
    vm = compute_client.get(args.resource_group_name, vm_name)
    args.location = vm.location
    get_network_watcher_from_location(cmd)


def get_network_watcher_from_resource(cmd):
    args = cmd.ctx.args
    resource = get_arm_resource_by_id(cmd.cli_ctx, args.resource.to_serialized_data())
    args.location = resource.location
    get_network_watcher_from_location(cmd)


def get_network_watcher_from_vmss(cmd):
    args = cmd.ctx.args
    compute_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_COMPUTE).virtual_machine_scale_sets
    vmss_name = parse_resource_id(args.target.to_serialized_data())["name"]
    vmss = compute_client.get(args.resource_group_name, vmss_name)
    args.location = vmss.location
    get_network_watcher_from_location(cmd)


class TestIPFlow(_TestIPFlow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            registered=False,
        )
        args_schema.local = AAZStrArg(
            options=["--local"],
            help="Private IPv4 address for the VMs NIC and the port of the packet in X.X.X.X:PORT format. "
                 "`*` can be used for port when direction is outbound.",
            required=True,
        )
        args_schema.remote = AAZStrArg(
            options=["--remote"],
            help="IPv4 address and port for the remote side of the packet X.X.X.X:PORT format. "
                 "`*` can be used for port when the direction is inbound.",
            required=True,
        )
        args_schema.resource_group_name = AAZStrArg(
            options=["-g", "--resource-group"],
            help="Name of the resource group the target VM is in.",
        )
        args_schema.vm._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute"
                     "/virtualMachines/{}",
        )
        args_schema.nic._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Network"
                     "/networkInterfaces/{}",
        )
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        args_schema.local_ip_address._required = False
        args_schema.local_ip_address._registered = False
        args_schema.local_port._required = False
        args_schema.local_port._registered = False
        args_schema.remote_ip_address._required = False
        args_schema.remote_ip_address._registered = False
        args_schema.remote_port._required = False
        args_schema.remote_port._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        try:
            args.local_ip_address, args.local_port = args.local.to_serialized_data().split(":")
            args.remote_ip_address, args.remote_port = args.remote.to_serialized_data().split(":")
        except:
            raise ValidationError("usage error: the format of the '--local' and '--remote' should be like x.x.x.x:port")

        get_network_watcher_from_vm(self)


class ShowNextHop(_ShowNextHop):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            registered=False,
        )
        args_schema.resource_group_name = AAZStrArg(
            options=["-g", "--resource-group"],
            help="Name of the resource group the target VM is in.",
        )
        args_schema.vm._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute"
                     "/virtualMachines/{}",
        )
        args_schema.nic._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Network"
                     "/networkInterfaces/{}",
        )
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_vm(self)


class ShowSecurityGroupView(_ShowSecurityGroupView):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            registered=False,
        )
        args_schema.resource_group_name = AAZStrArg(
            options=["-g", "--resource-group"],
            help="Name of the resource group the target VM is in.",
        )
        args_schema.vm._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute"
                     "/virtualMachines/{}",
        )
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_vm(self)


class RunConfigurationDiagnostic(_RunConfigurationDiagnostic):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            registered=False,
        )
        args_schema.destination = AAZStrArg(
            options=["--destination"],
            arg_group="Query",
            help="Traffic destination. Accepted values are '*', IP address/CIDR, or Service Tag.",
        )
        args_schema.direction = AAZStrArg(
            options=["--direction"],
            arg_group="Query",
            help="Direction of the traffic.",
            enum={"Inbound": "Inbound", "Outbound": "Outbound"},
        )
        args_schema.port = AAZStrArg(
            options=["--port"],
            arg_group="Query",
            help="Traffic destination port. Accepted values are '*', port number (3389) or port range (80-100).",
        )
        args_schema.protocol = AAZStrArg(
            options=["--protocol"],
            arg_group="Query",
            help="Protocol to be verified on.",
            enum={"TCP": "TCP", "UDP": "UDP"},
        )
        args_schema.source = AAZStrArg(
            options=["--source"],
            arg_group="Query",
            help="Traffic source. Accepted values are '*', IP address/CIDR, or Service Tag.",
        )
        args_schema.parent = AAZStrArg(
            options=["--parent"],
            arg_group="Target",
            help="Parent path, e.g., virtualMachineScaleSets/vmss1.",
        )
        args_schema.resource_group_name = AAZStrArg(
            options=["-g", "--resource-group"],
            arg_group="Target",
            help="Name of the resource group the target resource is in.",
        )
        args_schema.resource_type = AAZStrArg(
            options=["-t", "--resource-type"],
            arg_group="Target",
            help="Resource type.",
            enum={
                "applicationGateways": "applicationGateways",
                "networkInterfaces": "networkInterfaces",
                "virtualMachines": "virtualMachines",
            },
        )
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        args_schema.queries._required = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        # validate target resource
        resource_usage = ValidationError("usage error: --resource ID | --resource NAME --resource-type TYPE --resource-group NAME [--parent PATH]")
        # omit --parent since it is optional
        id_params = [has_value(args.resource_group_name), has_value(args.resource_type)]
        if not is_valid_resource_id(args.resource.to_serialized_data()):
            if not all(id_params):
                raise resource_usage
            # infer resource namespace
            NAMESPACES = {
                "virtualMachines": "Microsoft.Compute",
                "applicationGateways": "Microsoft.Network",
                "networkInterfaces": "Microsoft.Network",
            }
            resource_namespace = NAMESPACES[args.resource_type.to_serialized_data()]
            if has_value(args.parent):
                # special case for virtualMachineScaleSets/NetworkInterfaces, since it is
                # the only one to need `--parent`
                resource_namespace = "Microsoft.Compute"
            args.resource = resource_id(
                subscription=self.ctx.subscription_id,
                resource_group=args.resource_group_name,
                namespace=resource_namespace,
                type=args.resource_type,
                parent=args.parent,
                name=args.resource
            )
        elif any(id_params) or has_value(args.parent):
            raise resource_usage
        # validate query
        query_usage = ValidationError("usage error: --queries JSON | --destination DEST --source SRC --direction DIR --port PORT --protocol PROTOCOL")
        query_params = [has_value(args.destination), has_value(args.port), has_value(args.direction), has_value(args.protocol), has_value(args.source)]
        if has_value(args.queries):
            if any(query_params):
                raise query_usage
        elif not all(query_params):
            raise query_usage
        else:
            args.queries = [{
                "destination": args.destination,
                "destination_port": args.port,
                "direction": args.direction,
                "protocol": args.protocol,
                "source": args.source
            }]

        get_network_watcher_from_resource(self)


class ShowTopology(_ShowTopology):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            help="Location. Defaults to the location of the target resource group. "
                 "Topology information is only shown for resources within the target resource group "
                 "that are within the specified region.",
        )
        args_schema.resource_group_name._options = ["-g", "--resource-group"]
        args_schema.vnet._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Network"
                     "/virtualNetworks/{}",
        )
        args_schema.subnet._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Network"
                     "/virtualNetworks/{vnet}/subnets/{}",
        )
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.subnet):
            rg = parse_resource_id(args.subnet.to_serialized_data())["resource_group"]
            args.resource_group_name = None
            args.vnet = None
        elif has_value(args.vnet):
            rg = parse_resource_id(args.vnet.to_serialized_data())["resource_group"]
            args.resource_group_name = None
        else:
            rg = args.resource_group_name.to_serialized_data()
        # retrieve location from resource group
        if not has_value(args.location):
            resource_client = \
                get_mgmt_service_client(self.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).resource_groups
            resource_group = resource_client.get(rg)
            args.location = resource_group.location

        get_network_watcher_from_location(self)


class TestConnectivity(_TestConnectivity):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            registered=False,
        )
        args_schema.resource_group_name = AAZStrArg(
            options=["-g", "--resource-group"],
            help="Name of the resource group the target resource is in.",
        )
        args_schema.headers = AAZDictArg(
            options=["--headers"],
            arg_group="HTTP Configuration",
            help="Space-separated list of headers in `KEY=VALUE` format.",
        )
        args_schema.headers.Element = AAZStrArg()
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        args_schema.headers_obj._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        compute_client = get_mgmt_service_client(self.cli_ctx, ResourceType.MGMT_COMPUTE).virtual_machines
        id_parts = parse_resource_id(args.source_resource.to_serialized_data())
        vm_name = id_parts["name"]
        rg = args.resource_group_name or id_parts.get("resource_group", None)
        if not rg:
            raise ValidationError("usage error: --source-resource ID | --source-resource NAME --resource-group NAME")

        vm = compute_client.get(rg, vm_name)
        args.location = vm.location
        get_network_watcher_from_location(self)

        if has_value(args.source_resource) and not is_valid_resource_id(args.source_resource.to_serialized_data()):
            args.source_resource = resource_id(
                subscription=self.ctx.subscription_id,
                resource_group=rg,
                namespace="Microsoft.Compute",
                type="virtualMachines",
                name=args.source_resource
            )

        if has_value(args.dest_resource) and not is_valid_resource_id(args.dest_resource.to_serialized_data()):
            args.dest_resource = resource_id(
                subscription=self.ctx.subscription_id,
                resource_group=args.resource_group_name,
                namespace="Microsoft.Compute",
                type="virtualMachines",
                name=args.dest_resource
            )

        if has_value(args.headers):
            args.headers_obj = [{"name": k, "value": v} for k, v in args.headers.items()]


class PacketCaptureCreate(_PacketCaptureCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            registered=False,
        )
        args_schema.resource_group_name = AAZStrArg(
            options=["-g", "--resource-group"],
            help="Name of the resource group the target resource is in.",
            required=True,
        )
        args_schema.vm = AAZResourceIdArg(
            options=["--vm"],
            help="Name or ID of the VM to target",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute"
                         "/virtualMachines/{}",
            ),
        )
        args_schema.target._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute"
                     "/virtualMachineScaleSets/{}",
        )
        args_schema.storage_account._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Storage"
                     "/storageAccounts/{}",
        )
        args_schema.target._required = False
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.target_type) and args.target_type.to_serialized_data().lower() == "azurevmss":
            get_network_watcher_from_vmss(self)
        else:
            # set the appropriate fields if target is vm
            get_network_watcher_from_vm(self)
            args.target = args.vm
            args.include, args.exclude = None, None

        storage_usage = ValidationError("usage error: --storage-account NAME_OR_ID [--storage-path PATH] [--file-path PATH] | --file-path PATH")
        if not has_value(args.storage_account) and (has_value(args.storage_path) or not has_value(args.file_path)):
            raise storage_usage

        if has_value(args.file_path):
            path = args.file_path.to_serialized_data()
            if not path.endswith(".cap"):
                raise ValidationError("usage error: --file-path PATH must end with the '*.cap' extension")

            if not path.startswith("/"):
                path = path.replace("/", "\\")
            args.file_path = path


class PacketCaptureDelete(_PacketCaptureDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            required=True,
        )
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)


class PacketCaptureList(_PacketCaptureList):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            required=True,
        )
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)


class PacketCaptureShow(_PacketCaptureShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            required=True,
        )
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)


class PacketCaptureShowStatus(_PacketCaptureShowStatus):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            required=True,
        )
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)


class PacketCaptureStop(_PacketCaptureStop):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location = AAZResourceLocationArg(
            required=True,
        )
        args_schema.watcher_rg._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_name._registered = False
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)


def process_nw_cm_v2_create_namespace(cmd):
    args = cmd.ctx.args
    validate_tags(args)
    if not has_value(args.location):  # location is None only occurs in creating a V2 connection monitor
        endpoint_source_resource_id = args.endpoint_source_resource_id.to_serialized_data()
        from azure.mgmt.resource import ResourceManagementClient
        # parse and verify endpoint_source_resource_id
        if not has_value(args.endpoint_source_resource_id):
            raise ValidationError('usage error: --location/--endpoint-source-resource-id '
                                  'is required to create a V2 connection monitor')
        if is_valid_resource_id(endpoint_source_resource_id) is False:
            raise ValidationError('usage error: "{}" is not a valid resource id'.format(endpoint_source_resource_id))

        resource = parse_resource_id(endpoint_source_resource_id)
        resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceManagementClient)
        resource_api_version = _resolve_api_version(resource_client,
                                                    resource['namespace'],
                                                    resource['resource_parent'],
                                                    resource['resource_type'])
        resource = resource_client.resources.get_by_id(endpoint_source_resource_id, resource_api_version)

        args.location = resource.location
        if not has_value(args.location):
            raise ValidationError("Can not get location from --endpoint-source-resource-id")

    if not has_value(args.test_config_protocol):
        raise ValidationError('usage error: --protocol is required to create a test '
                              'configuration for V2 connection monitor')

    if has_value(args.output_type) and not has_value(args.workspace_ids):
        raise ValidationError('usage error: --output-type is specified but no other resource id provided')


class WatcherConnectionMonitorCreate(_WatcherConnectionMonitorCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group._required = False

        args_schema.auto_start._registered = False
        args_schema.monitoring_interval_in_seconds._registered = False
        args_schema.source._registered = False
        args_schema.destination._registered = False
        args_schema.endpoints._registered = False
        args_schema.test_configurations._registered = False
        args_schema.test_groups._registered = False
        args_schema.outputs._registered = False

        # V2 Endpoint
        args_schema.endpoint_dest_address = AAZStrArg(
            options=["--endpoint-dest-address"],
            help="Address of the destination of connection monitor endpoint (IP or domain name)",
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_dest_coverage_level = AAZStrArg(
            options=["--endpoint-dest-coverage-level"],
            help="Test coverage for the endpoint.",
            enum={"AboveAverage": "AboveAverage", "Average": "Average", "BelowAverage": "BelowAverage",
                  "Default": "Default", "Full": "Full", "Low": "Low"},
            arg_group="V2 Endpoint"
        )
        args_schema.endpoint_dest_name = AAZStrArg(
            options=["--endpoint-dest-name"],
            help="The name of the destination of connection monitor endpoint. "
                 "If you are creating a V2 Connection Monitor, it's required.",
            required=True,
            arg_group="V2 Endpoint"
        )
        args_schema.endpoint_dest_resource_id = AAZStrArg(
            options=["--endpoint-dest-resource-id"],
            help="Resource ID of the destination of connection monitor endpoint.",
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_dest_type = AAZStrArg(
            options=["--endpoint-dest-type"],
            help="The endpoint type.",
            enum={"AzureArcVM": "AzureArcVM", "AzureSubnet": "AzureSubnet", "AzureVM": "AzureVM",
                  "AzureVMSS": "AzureVMSS", "AzureVNet": "AzureVNet", "ExternalAddress": "ExternalAddress",
                  "MMAWorkspaceMachine": "MMAWorkspaceMachine", "MMAWorkspaceNetwork": "MMAWorkspaceNetwork"},
            arg_group="V2 Endpoint"
        )
        args_schema.endpoint_source_address = AAZStrArg(
            options=["--endpoint-source-address"],
            help="Address of the source of connection monitor endpoint (IP or domain name).",
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_source_coverage_level = AAZStrArg(
            options=["--endpoint-source-coverage-level"],
            help="Test coverage for the endpoint.",
            enum={"AboveAverage": "AboveAverage", "Average": "Average", "BelowAverage": "BelowAverage",
                  "Default": "Default", "Full": "Full", "Low": "Low"},
            arg_group="V2 Endpoint"
        )
        args_schema.endpoint_source_name = AAZStrArg(
            options=["--endpoint-source-name"],
            help="The name of the source of connection monitor endpoint. "
                 "If you are creating a V2 Connection Monitor, it's required.",
            required=True,
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_source_resource_id = AAZStrArg(
            options=["--endpoint-source-resource-id"],
            help="Resource ID of the source of connection monitor endpoint. "
                 "If endpoint is intended to used as source, this option is required.",
            required=True,
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_source_type = AAZStrArg(
            options=["--endpoint-source-type"],
            help="The endpoint type.",
            enum={"AzureArcVM": "AzureArcVM", "AzureSubnet": "AzureSubnet", "AzureVM": "AzureVM",
                  "AzureVMSS": "AzureVMSS", "AzureVNet": "AzureVNet", "ExternalAddress": "ExternalAddress",
                  "MMAWorkspaceMachine": "MMAWorkspaceMachine", "MMAWorkspaceNetwork": "MMAWorkspaceNetwork"},
            arg_group="V2 Endpoint"
        )

        # V2 Output
        args_schema.output_type = AAZStrArg(
            options=["--type", "--output-type"],
            help="Connection monitor output destination type. Currently, only \"Workspace\" is supported.",
            enum={"Workspace": "Workspace"},
            arg_group="V2 Output"
        )
        args_schema.workspace_ids = AAZListArg(
            options=["--workspace-ids"],
            help="Space-separated list of ids of log analytics workspace.",
            arg_group="V2 Output"
        )
        args_schema.workspace_ids.Element = AAZStrArg()

        # V2 Test Configuration
        args_schema.test_config_name = AAZStrArg(
            options=["--test-config-name"],
            help="The name of the connection monitor test configuration. "
                 "If you are creating a V2 Connection Monitor, it's required.",
            required=True,
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_frequency = AAZIntArg(
            options=["--frequency"],
            help="The frequency of test evaluation, in seconds.",
            arg_group="V2 Test Configuration",
            default=60,
        )
        args_schema.test_config_http_method = AAZStrArg(
            options=["--http-method"],
            help="The HTTP method to use.",
            arg_group="V2 Test Configuration",
            enum={"Get": "Get", "Post": "Post"},
        )
        args_schema.test_config_http_path = AAZStrArg(
            options=["--http-path"],
            help='The path component of the URI. For instance, "/dir1/dir2".',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_http_port = AAZIntArg(
            options=["--http-port"],
            help='The port to connect to.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_http_valid_status_codes = AAZListArg(
            options=["--http-valid-status-codes"],
            help="Space-separated list of HTTP status codes to consider successful. For instance, '2xx 301-304 418'",
            arg_group="V2 Test Configuration"
        )
        args_schema.test_config_http_valid_status_codes.Element = AAZStrArg()

        args_schema.test_config_http_prefer_https = AAZBoolArg(
            options=["--https-prefer"],
            help='Value indicating whether HTTPS is preferred over HTTP in cases where the choice is not explicit. '
                 ' Allowed values: false, true.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_icmp_disable_trace_route = AAZBoolArg(
            options=["--icmp-disable-trace-route"],
            help='Value indicating whether path evaluation with trace route should be disabled. false is default. '
                 ' Allowed values: false, true.',
            arg_group="V2 Test Configuration",
        )

        args_schema.test_config_preferred_ip_version = AAZStrArg(
            options=["--preferred-ip-version"],
            help='The preferred IP version to use in test evaluation. '
                 'The connection monitor may choose to use a different version depending on other parameters.',
            arg_group="V2 Test Configuration",
            enum={"IPv4": "IPv4", "IPv6": "IPv6"},
        )
        args_schema.test_config_protocol = AAZStrArg(
            options=["--protocol"],
            help='The protocol to use in test evaluation.',
            arg_group="V2 Test Configuration",
            enum={"Http": "Http", "Icmp": "Icmp", "Tcp": "Tcp"},
        )

        args_schema.test_config_tcp_disable_trace_route = AAZBoolArg(
            options=["--tcp-disable-trace-route"],
            help='Value indicating whether path evaluation with trace route should be disabled. false is default. '
                 'Allowed values: false, true.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_tcp_port = AAZIntArg(
            options=["--tcp-port"],
            help='The port to connect to.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_tcp_port_behavior = AAZStrArg(
            options=["--tcp-port-behavior"],
            help='Destination port behavior.',
            arg_group="V2 Test Configuration",
            enum={"ListenIfAvailable": "ListenIfAvailable", "None": "None"},
        )
        args_schema.test_config_threshold_failed_percent = AAZIntArg(
            options=["--threshold-failed-percent"],
            help='The maximum percentage of failed checks permitted for a test to evaluate as successful.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_threshold_round_trip_time = AAZFloatArg(
            options=["--threshold-round-trip-time"],
            help='The maximum round-trip time in milliseconds permitted for a test to evaluate as successful.',
            arg_group="V2 Test Configuration",
        )

        # V2 Test Group
        args_schema.test_group_disable = AAZBoolArg(
            options=["--test-group-disable"],
            help='Value indicating whether test group is disabled. false is default.',
            arg_group="V2 Test Group",
        )
        args_schema.test_group_name = AAZStrArg(
            options=["--test-group-name"],
            help='The name of the connection monitor test group.',
            arg_group="V2 Test Group",
            default="DefaultTestGroup"
        )
        return args_schema

    def pre_operations(self):
        process_nw_cm_v2_create_namespace(self)
        get_network_watcher_from_location(self, watcher_name='network_watcher_name', rg_name='resource_group')
        args = self.ctx.args

        # deal with endpoint
        src_endpoint = {
            "name": args.endpoint_source_name,
            "resource_id": args.endpoint_source_resource_id,
            "address": args.endpoint_source_address,
            "type": args.endpoint_source_type,
            "coverage_level": args.endpoint_source_coverage_level
        }
        dst_endpoint = {
            "name": args.endpoint_dest_name,
            "resource_id": args.endpoint_dest_resource_id,
            "address": args.endpoint_dest_address,
            "type": args.endpoint_dest_type,
            "coverage_level": args.endpoint_dest_coverage_level
        }

        # deal with test configuration
        test_config = {
            "name": args.test_config_name,
            "test_frequency_sec": args.test_config_frequency,
            "protocol": args.test_config_protocol,
            "preferred_ip_version": args.test_config_preferred_ip_version,
        }
        if has_value(args.test_config_threshold_failed_percent) or \
                has_value(args.test_config_threshold_round_trip_time):
            test_config['success_threshold'] = {
                "checks_failed_percent": args.test_config_threshold_failed_percent,
                "round_trip_time_ms": args.test_config_threshold_round_trip_time
            }
        if args.test_config_protocol == "Tcp":
            tcp_config = {
                "port": args.test_config_tcp_port,
                "destination_port_behavior": args.test_config_tcp_port_behavior,
                "disable_trace_route": args.test_config_tcp_disable_trace_route,
            }
            test_config['tcp_configuration'] = tcp_config
        elif args.test_config_protocol == "Icmp":
            icmp_config = {"disable_trace_route": args.test_config_icmp_disable_trace_route}
            test_config['icmp_configuration'] = icmp_config
        elif args.test_config_protocol == "Http":
            http_config = {
                "port": args.test_config_http_port,
                "method": args.test_config_http_method,
                "path": args.test_config_http_path,
                "valid_status_code_ranges": args.test_config_http_valid_status_codes,
                "prefer_https": args.test_config_http_prefer_https,
            }
            test_config['http_configuration'] = http_config
        else:
            raise ValidationError('Unsupported protocol: "{}" for test configuration'.format(args.test_config_protocol))

        # deal with test group
        test_group = {
            "name": args.test_group_name,
            "disable": args.test_group_disable,
            "test-configurations": [tc['name'] for tc in [test_config]],
            "sources": [e['name'] for e in [src_endpoint]],
            "destinations": [e['name'] for e in [dst_endpoint]]
        }

        # If 'workspace_ids' option is specified but 'output_type' is not
        # then still it should be implicit that 'output-type' is 'Workspace'
        # since only supported value for output_type is 'Workspace' currently.
        if has_value(args.workspace_ids) and not has_value(args.output_type):
            args.output_type = 'Workspace'

        if has_value(args.output_type) and has_value(args.workspace_ids):
            if args.output_type != "Workspace":
                raise ValidationError('Unsupported output type: "{}"'.format(args.output_type))
            args.outputs = []
            for workspace_id in args.workspace_ids:
                output = {
                    "type": args.output_type,
                    "workspace_id": workspace_id,
                }
                args.outputs.append(output)
        else:
            args.outputs = []
        args.endpoints = [src_endpoint, dst_endpoint]
        args.test_configurations = [test_config]
        args.test_groups = [test_group]


class WatcherConnectionMonitorStart(_WatcherConnectionMonitorStart):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group_name._registered = False
        args_schema.resource_group_name._required = False
        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self,
                                          watcher_name='network_watcher_name',
                                          rg_name='resource_group_name'
                                          )


class WatcherConnectionMonitorStop(_WatcherConnectionMonitorStop):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group_name._registered = False
        args_schema.resource_group_name._required = False
        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self,
                                          watcher_name='network_watcher_name',
                                          rg_name='resource_group_name'
                                          )


class WatcherConnectionMonitorList(_WatcherConnectionMonitorList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group_name._registered = False
        args_schema.resource_group_name._required = False
        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self,
                                          watcher_name='network_watcher_name',
                                          rg_name='resource_group_name'
                                          )


class WatcherConnectionMonitorShow(_WatcherConnectionMonitorShow):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group_name._registered = False
        args_schema.resource_group_name._required = False
        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self,
                                          watcher_name='network_watcher_name',
                                          rg_name='resource_group_name'
                                          )


class WatcherConnectionMonitorQuery(_WatcherConnectionMonitorQuery):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group_name._registered = False
        args_schema.resource_group_name._required = False
        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self,
                                          watcher_name='network_watcher_name',
                                          rg_name='resource_group_name'
                                          )


class WatcherConnectionMonitorDelete(_WatcherConnectionMonitorDelete):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group_name._registered = False
        args_schema.resource_group_name._required = False
        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self,
                                          watcher_name='network_watcher_name',
                                          rg_name='resource_group_name'
                                          )


class NwFlowLogCreate(_NwFlowLogCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group._required = False
        args_schema.location._required = True
        args_schema.flow_analytics_configuration._registered = False
        args_schema.retention_policy._registered = False
        args_schema.target_resource_id._registered = False
        args_schema.traffic_analytics_interval = AAZIntArg(
            options=['--interval'], arg_group="Traffic Analytics",
            help="Interval in minutes at which to conduct flow analytics. Temporarily allowed values are 10 and 60.",
            default=60,
            fmt=AAZIntArgFormat(
                maximum=60,
                minimum=10,
            )
        )
        args_schema.user_assigned_identity = AAZResourceIdArg(
            options=["--user-assigned-identity"],
            help="Name or ID of the ManagedIdentity Resource.",
            required=False,
        )
        args_schema.retention = AAZIntArg(
            options=['--retention'],
            help="Number of days to retain logs.",
        )
        args_schema.traffic_analytics_enabled = AAZBoolArg(
            options=['--traffic-analytics'], arg_group="Traffic Analytics",
            help="Enable traffic analytics. Defaults to true if `--workspace` is provided."
        )
        args_schema.traffic_analytics_workspace = AAZResourceIdArg(
            options=['--workspace'], arg_group="Traffic Analytics",
            help="Name or ID of a Log Analytics workspace. Must be in the same region of flow log",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.OperationalInsights/workspaces/{}"
            )
        )
        args_schema.vnet = AAZResourceIdArg(
            options=['--vnet'],
            help="Name or ID of the Virtual Network Resource.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}"
            )
        )
        args_schema.subnet = AAZResourceIdArg(
            options=['--subnet'],
            help="Name or ID of Subnet.",
        )
        args_schema.nic = AAZResourceIdArg(
            options=['--nic'],
            help="Name or ID of the Network Interface (NIC) Resource.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/networkInterfaces/{}"
            )
        )
        args_schema.nsg = AAZResourceIdArg(
            options=['--nsg'],
            help="Name or ID of the network security group.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/networkSecurityGroups/{}"
            )
        )
        args_schema.storage_account._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{}"
        )

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        get_network_watcher_from_location(self,
                                          watcher_name='network_watcher_name',
                                          rg_name='resource_group')
        if has_value(args.subnet):
            subnet = args.subnet.to_serialized_data()
            if not is_valid_resource_id(subnet) and has_value(args.vnet):
                args.subnet = args.vnet.to_serialized_data() + "/subnets/" + subnet

        if not has_value(args.enabled):
            args.enabled = True
        if sum(map(bool, [args.vnet, args.subnet, args.nic, args.nsg])) == 0:
            raise RequiredArgumentMissingError("Please enter atleast one target resource ID.")
        if sum(map(bool, [args.vnet, args.nic, args.nsg])) > 1:
            raise MutuallyExclusiveArgumentError("Please enter only one target resource ID.")

        if has_value(args.subnet):
            args.target_resource_id = args.subnet
        elif has_value(args.vnet) and not has_value(args.subnet):
            args.target_resource_id = args.vnet
        elif has_value(args.nic):
            args.target_resource_id = args.nic
        elif has_value(args.nsg):
            args.target_resource_id = args.nsg

        if has_value(args.user_assigned_identity):
            user_assigned_identity = args.user_assigned_identity.to_serialized_data()
            is_valid_miresource_id = validate_managed_identity_resource_id(user_assigned_identity)
            if not is_valid_miresource_id:
                raise CLIError('Managed Identity resource id is invalid')
            if user_assigned_identity.lower() != 'none':
                args.identity = {
                    "type": "UserAssigned",
                    "user_assigned_identities": {user_assigned_identity: {}}
                }
            else:
                args.identity = {
                    "type": "None"
                }

        if has_value(args.retention):
            if args.retention > 0:
                args.retention_policy = {"days": args.retention, "enabled": True}

        if has_value(args.traffic_analytics_workspace):

            workspace = get_arm_resource_by_id(self.cli_ctx, args.traffic_analytics_workspace.to_serialized_data())
            if not workspace:
                raise CLIError('Name or ID of workspace is invalid')

            args.flow_analytics_configuration = {"workspace_id": workspace.properties['customerId'],
                                                 "workspace_region": workspace.location,
                                                 "workspace_resource_id": workspace.id}
            if has_value(args.traffic_analytics_enabled):
                args.flow_analytics_configuration['enabled'] = args.traffic_analytics_enabled
            if has_value(args.traffic_analytics_interval):
                args.flow_analytics_configuration['traffic_analytics_interval'] = args.traffic_analytics_interval


class NwFlowLogUpdate(_NwFlowLogUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group._required = False
        args_schema.location._required = True
        args_schema.flow_analytics_configuration._registered = False
        args_schema.retention_policy._registered = False
        args_schema.target_resource_id._registered = False
        args_schema.retention = AAZIntArg(
            options=['--retention'],
            help="Number of days to retain logs.",
            nullable=True,
        )
        args_schema.traffic_analytics_interval = AAZIntArg(
            options=['--interval'], arg_group="Traffic Analytics",
            help="Interval in minutes at which to conduct flow analytics. Temporarily allowed values are 10 and 60.",
            nullable=True,
            fmt=AAZIntArgFormat(
                maximum=60,
                minimum=10,
            )
        )
        args_schema.user_assigned_identity = AAZResourceIdArg(
            options=["--user-assigned-identity"],
            help="Name or ID of the ManagedIdentity Resource.",
            required=False,
        )
        args_schema.traffic_analytics_enabled = AAZBoolArg(
            options=['--traffic-analytics'], arg_group="Traffic Analytics", nullable=True,
            help="Enable traffic analytics. Defaults to true if `--workspace` is provided."
        )
        args_schema.traffic_analytics_workspace = AAZResourceIdArg(
            options=['--workspace'], arg_group="Traffic Analytics", nullable=True,
            help="Name or ID of a Log Analytics workspace. Must be in the same region of flow log",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.OperationalInsights/workspaces/{}"
            )
        )
        args_schema.vnet = AAZResourceIdArg(
            options=['--vnet'],
            help="Name or ID of the Virtual Network Resource.",
            nullable=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}"
            )
        )
        args_schema.subnet = AAZResourceIdArg(
            options=['--subnet'],
            help="Name or ID of Subnet.",
            nullable=True,
        )
        args_schema.nic = AAZResourceIdArg(
            options=['--nic'],
            help="Name or ID of the Network Interface (NIC) Resource.",
            nullable=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/networkInterfaces/{}"
            )
        )
        args_schema.nsg = AAZResourceIdArg(
            options=['--nsg'],
            help="Name or ID of the network security group.",
            nullable=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/networkSecurityGroups/{}"
            )
        )
        args_schema.storage_account._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{}"
        )

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        get_network_watcher_from_location(self,
                                          watcher_name='network_watcher_name',
                                          rg_name='resource_group')
        if has_value(args.subnet):
            subnet = args.subnet.to_serialized_data()
            if not is_valid_resource_id(subnet) and has_value(args.vnet):
                args.subnet = args.vnet.to_serialized_data() + "/subnets/" + subnet

        if sum(map(bool, [args.vnet, args.nic, args.nsg])) > 1:
            raise MutuallyExclusiveArgumentError("Please enter only one target resource ID.")
        if has_value(args.subnet):
            args.target_resource_id = args.subnet
        elif has_value(args.vnet) and not has_value(args.subnet):
            args.target_resource_id = args.vnet
        elif has_value(args.nic):
            args.target_resource_id = args.nic
        elif has_value(args.nsg):
            args.target_resource_id = args.nsg
        if has_value(args.retention) and args.retention > 0:
            args.retention_policy = {"days": args.retention, "enabled": True}

        if has_value(args.user_assigned_identity):
            user_assigned_identity = args.user_assigned_identity.to_serialized_data()
            is_valid_miresource_id = validate_managed_identity_resource_id(user_assigned_identity)
            if not is_valid_miresource_id:
                raise CLIError('Managed Identity resource id is invalid')
            if user_assigned_identity.lower() != 'none':
                args.identity = {
                    "type": "UserAssigned",
                    "user_assigned_identities": {user_assigned_identity: {}}
                }
            else:
                args.identity = {
                    "type": "None"
                }

        if has_value(args.traffic_analytics_workspace):
            workspace = get_arm_resource_by_id(self.cli_ctx, args.traffic_analytics_workspace.to_serialized_data())
            if not workspace:
                raise CLIError('Name or ID of workspace is invalid')

            args.flow_analytics_configuration = {
                "workspace_id": workspace.properties['customerId'],
                "workspace_region": workspace.location,
                "workspace_resource_id": workspace.id
            }
            if has_value(args.traffic_analytics_enabled):
                args.flow_analytics_configuration['enabled'] = args.traffic_analytics_enabled
            if has_value(args.traffic_analytics_interval):
                args.flow_analytics_configuration['traffic_analytics_interval'] = args.traffic_analytics_interval


class NwFlowLogList(_NwFlowLogList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group._registered = False
        args_schema.resource_group._required = False
        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location to identify the exclusive Network Watcher under a region. "
                 "Only one Network Watcher can be existed per subscription and region.",
            required=True,
            fmt=AAZResourceLocationArgFormat(
                resource_group_arg="resource_group",
            ),
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self,
                                          watcher_name='network_watcher_name',
                                          rg_name='resource_group')


class NwFlowLogDelete(_NwFlowLogDelete):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group._registered = False
        args_schema.resource_group._required = False
        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location to identify the exclusive Network Watcher under a region. "
                 "Only one Network Watcher can be existed per subscription and region.",
            required=True,
            fmt=AAZResourceLocationArgFormat(
                resource_group_arg="resource_group",
            ),
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self,
                                          watcher_name='network_watcher_name',
                                          rg_name='resource_group')


class NwTroubleshootingStart(_NwTroubleshootingStart):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._required = False
        args_schema.target_resource_id._registered = False
        args_schema.target_resource_id._required = False
        args_schema.resource_group_name = AAZStrArg(
            options=["-g", "--resource-group"],
            help="Name of resource group. You can configure the default group using `az configure --defaults group=<name>`.",
        )
        args_schema.resource_type = AAZStrArg(
            options=["-t", "--resource-type"],
            help="The type of target resource to troubleshoot, if resource ID is not specified.",
            enum={"vnetGateway": "virtualNetworkGateways", "vpnConnection": "connections"},
        )
        args_schema.resource = AAZResourceIdArg(
            options=["--resource"],
            help="Name or ID of the resource to troubleshoot.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Network/{resource_type}/{}"
            )
        )
        args_schema.storage_account._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Storage/storageAccounts/{}"
        )
        args_schema.location = AAZResourceLocationArg(
            registered=False,
        )

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        storage_usage = CLIError('usage error: --storage-account NAME_OR_ID [--storage-path PATH]')
        if has_value(args.storage_path) and not has_value(args.storage_account):
            raise storage_usage
        if has_value(args.resource):
            args.target_resource_id = args.resource
        get_network_watcher_from_resource(self)


class NwTroubleshootingShow(_NwTroubleshootingShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._required = False
        args_schema.target_resource_id._registered = False
        args_schema.target_resource_id._required = False
        args_schema.resource_group_name = AAZStrArg(
            options=["-g", "--resource-group"],
            help="Name of resource group. You can configure the default group using `az configure --defaults group=<name>`.",
        )
        args_schema.resource_type = AAZStrArg(
            options=["-t", "--resource-type"],
            help="The resource type.",
            enum={"vnetGateway": "virtualNetworkGateways", "vpnConnection": "connections"},
        )
        args_schema.resource = AAZResourceIdArg(
            options=["--resource"],
            help="Name or ID of the resource to troubleshoot.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group_name}/providers/Microsoft.Network/{resource_type}/{}"
            )
        )
        args_schema.location = AAZResourceLocationArg(
            registered=False,
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        get_network_watcher_from_resource(self)
        if has_value(args.resource):
            args.target_resource_id = args.resource


class WatcherConnectionMonitorOutputAdd(_WatcherConnectionMonitorOutputAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.output_type._required = True
        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.output_type) and not has_value(args.workspace_id):
            raise ValidationError('usage error: --type is specified but no other resource id provided')
        get_network_watcher_from_location(self)


class WatcherConnectionMonitorOutputList(_WatcherConnectionMonitorOutputList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)


class WatcherConnectionMonitorOutputRemove(_WatcherConnectionMonitorUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._required = False
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)
        args = self.ctx.args
        args.outputs = []


class WatcherConnectionMonitorEndpointAdd(_WatcherConnectionMonitorEndpointAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.filter_items._registered = False
        args_schema.filter_type._registered = False
        args_schema.scope_exclude._registered = False
        args_schema.scope_include._registered = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True
        )
        args_schema.address_exclude = AAZListArg(
            options=["--address-exclude"],
            help="List of address of the endpoint item which needs to be excluded to the endpoint scope.",
        )
        args_schema.address_exclude.Element = AAZStrArg()

        args_schema.address_include = AAZListArg(
            options=["--address-include"],
            help="List of address of the endpoint item which needs to be included to the endpoint scope.",
        )
        args_schema.address_include.Element = AAZStrArg()

        args_schema.dest_test_groups = AAZListArg(
            options=["--dest-test-groups"],
            help="Space-separated list of names for test group to reference as destination.",
            arg_group="V2 Test Group"
        )
        args_schema.dest_test_groups.Element = AAZStrArg()

        args_schema.source_test_groups = AAZListArg(
            options=["--source-test-groups"],
            help="Space-separated list of names for test group to reference as source.",
            arg_group="V2 Test Group"
        )
        args_schema.source_test_groups.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.dest_test_groups) or has_value(args.source_test_groups):
            dest_test_groups, source_test_groups = args.dest_test_groups, args.source_test_groups
            if dest_test_groups is None and source_test_groups is None:
                raise ValidationError('usage error: endpoint has to be referenced from at least one existing '
                                      'test group via --dest-test-groups/--source-test-groups')
        get_network_watcher_from_location(self)

        args.scope_include = assign_aaz_list_arg(
            args.scope_include,
            args.address_include,
            element_transformer=lambda _, tmp_ip: {"address": tmp_ip}
        )

        args.scope_exclude = assign_aaz_list_arg(
            args.scope_exclude,
            args.address_exclude,
            element_transformer=lambda _, tmp_ip: {"address": tmp_ip}
        )

    def pre_instance_create(self):
        args = self.ctx.args
        name = args.endpoint_name.to_serialized_data()
        instance = self.ctx.vars.instance
        src_test_groups = set()
        dst_test_groups = set()
        if has_value(args.source_test_groups):
            src_test_groups = set(args.source_test_groups.to_serialized_data())
        if has_value(args.dest_test_groups):
            dst_test_groups = set(args.dest_test_groups.to_serialized_data())
        for test_group in instance.properties.test_groups:
            if test_group.name.to_serialized_data() in src_test_groups:
                test_group.sources.append(name)
            if test_group.name.to_serialized_data() in dst_test_groups:
                test_group.destinations.append(name)


class WatcherConnectionMonitorEndpointShow(_WatcherConnectionMonitorEndpointShow):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)


class WatcherConnectionMonitorEndpointList(_WatcherConnectionMonitorEndpointList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)


class WatcherConnectionMonitorEndpointRemove(_WatcherConnectionMonitorEndpointRemove):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        args_schema.test_groups = AAZListArg(
            options=["--test-groups"],
            help="Space-separated list of names of test group which only need to "
                 "be affected if specified.",
            arg_group="V2 Test Group",
        )
        args_schema.test_groups.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)

    def post_instance_delete(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        name = args.endpoint_name.to_serialized_data()
        # refresh test groups

        temp_test_groups = instance.properties.test_groups
        if has_value(args.test_groups):
            temp_test_groups = [t for t in instance.properties.test_groups
                                if t.name.to_serialized_data() in args.test_groups]

        for test_group in temp_test_groups:
            test_group.sources = [tc for tc in test_group.sources if tc != name]
            test_group.destinations = [tc for tc in test_group.destinations if tc != name]


class WatcherConnectionMonitorTestConfigurationAdd(_MonitorTestConfigurationAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False
        args_schema.http_request_headers._registered = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        args_schema.http_request_header = AAZDictArg(
            options=["--http-request-header"],
            help="The HTTP headers to transmit with the request. List of property=value pairs to define HTTP headers.",
            arg_group="HTTP Protocol",
        )
        args_schema.http_request_header.Element = AAZStrArg()

        args_schema.test_groups = AAZListArg(
            options=["--test-groups"],
            help="Space-separated list of names of test group which only need to be affected if specified.",
            required=True,
        )
        args_schema.test_groups.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)

    def pre_instance_create(self):
        args = self.ctx.args
        name = args.test_configuration_name.to_serialized_data()

        if has_value(args.http_request_header):
            for tmp_name, val in args.http_request_header.items():
                args.http_request_headers.append({
                    "name": tmp_name,
                    "value": val,
                })

        instance = self.ctx.vars.instance
        if has_value(args.test_groups):
            for test_group in instance.properties.test_groups:
                if test_group.name.to_serialized_data() in args.test_groups:
                    test_group.test_configurations.append(name)


class WatcherConnectionMonitorTestConfigurationShow(_MonitorTestConfigurationShow):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)


class WatcherConnectionMonitorTestConfigurationList(_MonitorTestConfigurationList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)


class WatcherConnectionMonitorTestConfigurationRemove(_MonitorTestConfigurationRemove):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        args_schema.test_groups = AAZListArg(
            options=["--test-groups"],
            help="Space-separated list of names of test group which only need to "
                 "be affected if specified.",
        )
        args_schema.test_groups.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)

    def post_instance_delete(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        name = args.test_configuration_name.to_serialized_data()

        # refresh test groups
        temp_test_groups = instance.properties.test_groups
        if has_value(args.test_groups):
            temp_test_groups = [t for t in instance.properties.test_groups
                                if t.name.to_serialized_data() in args.test_groups]

        for test_group in temp_test_groups:
            test_group.test_configurations = [tc for tc in test_group.test_configurations if tc != name]


class WatcherConnectionMonitorTestGroupAdd(_WatcherConnectionMonitorTestGroupAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.destinations._registered = False
        args_schema.destinations._required = False
        args_schema.sources._registered = False
        args_schema.sources._required = False
        args_schema.test_configurations._registered = False
        args_schema.test_configurations._required = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        # V2 Endpoint
        args_schema.endpoint_dest_name = AAZStrArg(
            options=["--endpoint-dest-name"],
            help="The name of the destination of connection monitor endpoint. "
                 "If you are creating a V2 Connection Monitor, it's required.",
            arg_group="V2 Endpoint",
            required=True
        )
        args_schema.endpoint_source_name = AAZStrArg(
            options=["--endpoint-source-name"],
            help="The name of the source of connection monitor endpoint. "
                 "If you are creating a V2 Connection Monitor, it's required.",
            arg_group="V2 Endpoint",
            required=True
        )
        args_schema.endpoint_dest_address = AAZStrArg(
            options=["--endpoint-dest-address"],
            help="Address of the destination of connection monitor endpoint (IP or domain name)",
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_dest_resource_id = AAZStrArg(
            options=["--endpoint-dest-resource-id"],
            help="Resource ID of the destination of connection monitor endpoint.",
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_source_address = AAZStrArg(
            options=["--endpoint-source-address"],
            help="Address of the source of connection monitor endpoint (IP or domain name).",
            arg_group="V2 Endpoint",
        )
        args_schema.endpoint_source_resource_id = AAZStrArg(
            options=["--endpoint-source-resource-id"],
            help="Resource ID of the source of connection monitor endpoint. "
                 "If endpoint is intended to used as source, this option is required.",
            arg_group="V2 Endpoint",
        )

        # V2 Test Configuration
        args_schema.test_config_name = AAZStrArg(
            options=["--test-config-name"],
            help="The name of the connection monitor test configuration. "
                 "If you are creating a V2 Connection Monitor, it's required.",
            arg_group="V2 Test Configuration",
            required=True
        )
        args_schema.test_config_frequency = AAZStrArg(
            options=["--frequency"],
            help="The frequency of test evaluation, in seconds.  Default: 60.",
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_http_method = AAZStrArg(
            options=["--http-method"],
            help="The HTTP method to use.",
            arg_group="V2 Test Configuration",
            enum={"Get": "Get", "Post": "Post"},
        )
        args_schema.test_config_http_path = AAZStrArg(
            options=["--http-path"],
            help='The path component of the URI. For instance, "/dir1/dir2".',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_http_port = AAZIntArg(
            options=["--http-port"],
            help='The port to connect to.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_http_valid_status_codes = AAZListArg(
            options=["--http-valid-status-codes"],
            help="Space-separated list of HTTP status codes to consider successful. For instance, '2xx 301-304 418'",
            arg_group="V2 Test Configuration"
        )
        args_schema.test_config_http_valid_status_codes.Element = AAZStrArg()

        args_schema.test_config_http_prefer_https = AAZBoolArg(
            options=["--https-prefer"],
            help='Value indicating whether HTTPS is preferred over HTTP in cases where the choice is not explicit. '
                 ' Allowed values: false, true.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_icmp_disable_trace_route = AAZBoolArg(
            options=["--icmp-disable-trace-route"],
            help='Value indicating whether path evaluation with trace route should be disabled. false is default. '
                 ' Allowed values: false, true.',
            arg_group="V2 Test Configuration",
        )

        args_schema.test_config_preferred_ip_version = AAZStrArg(
            options=["--preferred-ip-version"],
            help='The preferred IP version to use in test evaluation. '
                 'The connection monitor may choose to use a different version depending on other parameters.',
            arg_group="V2 Test Configuration",
            enum={"IPv4": "IPv4", "IPv6": "IPv6"},
        )
        args_schema.test_config_protocol = AAZStrArg(
            options=["--protocol"],
            help='The protocol to use in test evaluation.',
            arg_group="V2 Test Configuration",
            enum={"Http": "Http", "Icmp": "Icmp", "Tcp": "Tcp"},
        )

        args_schema.test_config_tcp_disable_trace_route = AAZBoolArg(
            options=["--tcp-disable-trace-route"],
            help='Value indicating whether path evaluation with trace route should be disabled. false is default. '
                 'Allowed values: false, true.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_tcp_port = AAZIntArg(
            options=["--tcp-port"],
            help='The port to connect to.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_threshold_failed_percent = AAZIntArg(
            options=["--threshold-failed-percent"],
            help='The maximum percentage of failed checks permitted for a test to evaluate as successful.',
            arg_group="V2 Test Configuration",
        )
        args_schema.test_config_threshold_round_trip_time = AAZFloatArg(
            options=["--threshold-round-trip-time"],
            help='The maximum round-trip time in milliseconds permitted for a test to evaluate as successful.',
            arg_group="V2 Test Configuration",
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)

    # pylint: disable=too-many-boolean-expressions
    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance

        # deal with endpoint
        if has_value(args.endpoint_source_address) or has_value(args.endpoint_source_resource_id):
            src_endpoint = {
                "name": args.endpoint_source_name,
                "resource_id": args.endpoint_source_resource_id,
                "address": args.endpoint_source_address
            }
            instance.properties.endpoints.append(src_endpoint)
        if has_value(args.endpoint_dest_address) or has_value(args.endpoint_dest_resource_id):
            dst_endpoint = {
                "name": args.endpoint_dest_name,
                "resource_id": args.endpoint_dest_resource_id,
                "address": args.endpoint_dest_address
            }
            instance.properties.endpoints.append(dst_endpoint)

        args.sources.append(args.endpoint_source_name)
        args.destinations.append(args.endpoint_dest_name)

        # deal with test configuration
        if has_value(args.test_config_protocol) or has_value(args.test_config_preferred_ip_version) or \
                has_value(args.test_config_threshold_failed_percent) or \
                has_value(args.test_config_threshold_round_trip_time) or \
                has_value(args.test_config_tcp_disable_trace_route) or has_value(args.test_config_tcp_port) or \
                has_value(args.test_config_icmp_disable_trace_route) or \
                has_value(args.test_config_http_port) or has_value(args.test_config_http_method) or \
                has_value(args.test_config_http_path) or has_value(args.test_config_http_valid_status_codes) or \
                has_value(args.test_config_http_prefer_https):
            test_config = {
                "name": args.test_config_name,
                "test_frequency_sec": args.test_config_frequency,
                "protocol": args.test_config_protocol,
                "preferred_ip_version": args.test_config_preferred_ip_version,
            }
            if has_value(args.test_config_threshold_failed_percent) or \
                    has_value(args.test_config_threshold_round_trip_time):
                test_config['success_threshold'] = {
                    "checks_failed_percent": args.test_config_threshold_failed_percent,
                    "round_trip_time_ms": args.test_config_threshold_round_trip_time
                }
            if args.test_config_protocol == "Tcp":
                tcp_config = {
                    "port": args.test_config_tcp_port,
                    "disable_trace_route": args.test_config_tcp_disable_trace_route,
                }
                test_config['tcp_configuration'] = tcp_config
            elif args.test_config_protocol == "Icmp":
                icmp_config = {"disable_trace_route": args.test_config_icmp_disable_trace_route}
                test_config['icmp_configuration'] = icmp_config
            elif args.test_config_protocol == "Http":
                http_config = {
                    "port": args.test_config_http_port,
                    "method": args.test_config_http_method,
                    "path": args.test_config_http_path,
                    "valid_status_code_ranges": args.test_config_http_valid_status_codes,
                    "prefer_https": args.test_config_http_prefer_https,
                }
                test_config['http_configuration'] = http_config
            else:
                raise ValidationError('Unsupported protocol: "{}" for test configuration'.format(
                    args.test_config_protocol))
            instance.properties.test_configurations.append(test_config)
        args.test_configurations.append(args.test_config_name)


class WatcherConnectionMonitorTestGroupShow(_WatcherConnectionMonitorTestGroupShow):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)


class WatcherConnectionMonitorTestGroupList(_WatcherConnectionMonitorTestGroupList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._registered = False
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._registered = False
        args_schema.watcher_rg._required = False

        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location. Values from: `az account list-locations`. "
                 "You can configure the default location "
                 "using `az configure --defaults location=<location>`.",
            required=True,
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)


class WatcherConnectionMonitorTestGroupRemove(_WatcherConnectionMonitorUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.watcher_name._required = False
        args_schema.watcher_rg._required = False
        args_schema.test_group_name = AAZStrArg(
            options=["--test-group-name"],
            help='The name of the connection monitor test group.',
            required=True,
            registered=False,
        )
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_location(self)

    def pre_instance_update(self, instance):
        args = self.ctx.args
        name = args.test_group_name.to_serialized_data()

        instance = self.ctx.vars.instance

        new_test_groups, removed_test_group = [], None
        for t in instance.properties.test_groups:
            if t.name.to_serialized_data() == name:
                removed_test_group = t
            else:
                new_test_groups.append(t)

        if removed_test_group is None:
            raise ValidationError('test group: "{}" not exist'.format(name))
        instance.properties.test_groups = new_test_groups

        # deal with endpoints which are only referenced by this removed test group
        removed_endpoints = []
        for e in (removed_test_group.sources.to_serialized_data() +
                  removed_test_group.destinations.to_serialized_data()):
            tmp = [t for t in instance.properties.test_groups
                   if (e in t.sources.to_serialized_data() or e in t.destinations.to_serialized_data())]
            if not tmp:
                removed_endpoints.append(e)
        instance.properties.endpoints = [e for e in instance.properties.endpoints
                                         if e.name.to_serialized_data() not in removed_endpoints]

        # deal with test configurations which are only referenced by this remove test group
        removed_test_configurations = []
        for c in removed_test_group.test_configurations.to_serialized_data():
            tmp = [t for t in instance.properties.test_groups if c in t.test_configurations.to_serialized_data()]
            if not tmp:
                removed_test_configurations.append(c)
        instance.properties.test_configurations = [c for c in instance.properties.test_configurations
                                                   if c.name.to_serialized_data() not in removed_test_configurations]
