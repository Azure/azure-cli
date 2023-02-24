# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger
from msrestazure.tools import is_valid_resource_id, parse_resource_id, resource_id

from azure.cli.core.aaz import has_value, AAZResourceLocationArg, AAZResourceLocationArgFormat
from azure.cli.core.azclierror import ValidationError, RequiredArgumentMissingError, MutuallyExclusiveArgumentError
from azure.cli.core.commands.arm import get_arm_resource_by_id
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType

from ..aaz.latest.network.watcher import RunConfigurationDiagnostic as _RunConfigurationDiagnostic
from ..aaz.latest.network.watcher import ShowNextHop as _ShowNextHop, ShowSecurityGroupView as _ShowSecurityGroupView, \
    ShowTopology as _ShowTopology
from ..aaz.latest.network.watcher import TestConnectivity as _TestConnectivity, TestIpFlow as _TestIPFlow
from ..aaz.latest.network.watcher.connection_monitor import Start as _WatcherConnectionMonitorStart
from ..aaz.latest.network.watcher.connection_monitor import Stop as _WatcherConnectionMonitorStop
from ..aaz.latest.network.watcher.connection_monitor import Show as _WatcherConnectionMonitorShow
from ..aaz.latest.network.watcher.connection_monitor import List as _WatcherConnectionMonitorList
from ..aaz.latest.network.watcher.connection_monitor import Delete as _WatcherConnectionMonitorDelete
from ..aaz.latest.network.watcher.connection_monitor import Query as _WatcherConnectionMonitorQuery
from ..aaz.latest.network.watcher.flow_log import Create as _NwFlowLogCreate, Update as _NwFlowLogUpdate, \
    List as _NwFlowLogList, Delete as _NwFlowLogDelete
from ..aaz.latest.network.watcher.troubleshooting import Start as _NwTroubleshootingStart, \
    Show as _NwTroubleshootingShow

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


class TestIPFlow(_TestIPFlow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArgFormat
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
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArgFormat
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
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArgFormat
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
        from azure.cli.core.aaz import AAZStrArg
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
        from azure.cli.core.aaz import AAZResourceIdArgFormat
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
        from azure.cli.core.aaz import AAZDictArg, AAZStrArg
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


def update_network_watcher_from_location(ctx, cli_ctx, watcher_name='watcher_name',
                                         rg_name='watcher_rg'):

    from ..aaz.latest.network.watcher import List as NetworkWatcherList
    network_watcher_list = NetworkWatcherList(cli_ctx=cli_ctx)(command_args={})
    args = ctx.args
    location = args.location.to_serialized_data()
    watcher = next((x for x in network_watcher_list if x['location'].lower() == location.lower()), None)
    if not watcher:
        raise ValidationError("network watcher is not enabled for region '{}'.".format(location))
    id_parts = parse_resource_id(watcher['id'])
    setattr(args, rg_name, id_parts['resource_group'])
    setattr(args, watcher_name, id_parts['name'])


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
            fmt=AAZResourceLocationArgFormat(
                resource_group_arg="resource_group_name",
            ),
        )
        return args_schema

    def pre_operations(self):
        update_network_watcher_from_location(self.ctx,
                                             self.cli_ctx,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group_name')


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
            fmt=AAZResourceLocationArgFormat(
                resource_group_arg="resource_group_name",
            ),
        )
        return args_schema

    def pre_operations(self):
        update_network_watcher_from_location(self.ctx,
                                             self.cli_ctx,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group_name')


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
            fmt=AAZResourceLocationArgFormat(
                resource_group_arg="resource_group_name",
            ),
        )
        return args_schema

    def pre_operations(self):
        update_network_watcher_from_location(self.ctx,
                                             self.cli_ctx,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group_name')


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
            fmt=AAZResourceLocationArgFormat(
                resource_group_arg="resource_group_name",
            ),
        )
        return args_schema

    def pre_operations(self):
        update_network_watcher_from_location(self.ctx,
                                             self.cli_ctx,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group_name')


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
            fmt=AAZResourceLocationArgFormat(
                resource_group_arg="resource_group_name",
            ),
        )
        return args_schema

    def pre_operations(self):
        update_network_watcher_from_location(self.ctx,
                                             self.cli_ctx,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group_name')


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
            fmt=AAZResourceLocationArgFormat(
                resource_group_arg="resource_group_name",
            ),
        )
        return args_schema

    def pre_operations(self):
        update_network_watcher_from_location(self.ctx,
                                             self.cli_ctx,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group_name')


class NwFlowLogCreate(_NwFlowLogCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat, AAZIntArg, AAZIntArgFormat, AAZBoolArg
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
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{}"
            )
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
        update_network_watcher_from_location(self.ctx,
                                             self.cli_ctx,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group')
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

        if has_value(args.retention):
            if args.retention > 0:
                args.retention_policy = {"days": args.retention, "enabled": (args.retention > 0)}

        if has_value(args.traffic_analytics_workspace):

            from azure.cli.core.commands.arm import get_arm_resource_by_id
            workspace = get_arm_resource_by_id(self.cli_ctx, args.traffic_analytics_workspace.to_serialized_data())
            if not workspace:
                from knack.util import CLIError
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
        from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat, AAZIntArg, AAZIntArgFormat, AAZBoolArg

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
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{}"
            )
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
        update_network_watcher_from_location(self.ctx,
                                             self.cli_ctx,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group')
        # args = self.ctx.args
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

        if args.retention > 0:
            args.retention_policy = {"days": args.retention, "enabled": (args.retention > 0)}

        if has_value(args.traffic_analytics_workspace):
            from azure.cli.core.commands.arm import get_arm_resource_by_id
            workspace = get_arm_resource_by_id(self.cli_ctx, args.traffic_analytics_workspace.to_serialized_data())
            if not workspace:
                from knack.util import CLIError
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
        update_network_watcher_from_location(self.ctx,
                                             self.cli_ctx,
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
        update_network_watcher_from_location(self.ctx,
                                             self.cli_ctx,
                                             watcher_name='network_watcher_name',
                                             rg_name='resource_group')


class NwTroubleshootingStart(_NwTroubleshootingStart):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat, AAZStrArg

        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group._required = False
        args_schema.target_resource_id._registered = False
        args_schema.target_resource_id._required = False
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
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/{resource_type}/{}"
            )
        )
        args_schema.storage_account._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{}"
        )
        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location to identify the exclusive Network Watcher under a region. "
                 "Only one Network Watcher can be existed per subscription and region.",
            fmt=AAZResourceLocationArgFormat(
                resource_group_arg="resource_group",
            ),
        )
        args_schema.location._registered = False
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_resource(self)
        get_network_watcher_from_location(self, watcher_name='network_watcher_name', rg_name='resource_group')
        args = self.ctx.args
        if has_value(args.resource):
            args.target_resource_id = args.resource


class NwTroubleshootingShow(_NwTroubleshootingShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_watcher_name._registered = False
        args_schema.network_watcher_name._required = False
        args_schema.resource_group._required = False
        args_schema.target_resource_id._registered = False
        args_schema.target_resource_id._required = False
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
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/{resource_type}/{}"
            )
        )
        args_schema.location = AAZResourceLocationArg(
            options=["-l", "--location"],
            help="Location to identify the exclusive Network Watcher under a region. "
                 "Only one Network Watcher can be existed per subscription and region.",
            fmt=AAZResourceLocationArgFormat(
                resource_group_arg="resource_group",
            ),
        )
        args_schema.location._registered = False
        return args_schema

    def pre_operations(self):
        get_network_watcher_from_resource(self)
        get_network_watcher_from_location(self, watcher_name='network_watcher_name', rg_name='resource_group')
        args = self.ctx.args
        if has_value(args.resource):
            args.target_resource_id = args.resource
