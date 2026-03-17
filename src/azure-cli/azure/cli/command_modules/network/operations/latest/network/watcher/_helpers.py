# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access

from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
from azure.cli.core.azclierror import ValidationError
from azure.cli.core.commands.arm import get_arm_resource_by_id
from azure.cli.core.aaz import has_value, AAZStrArg
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.validators import validate_tags
from azure.cli.command_modules.network._validators import _resolve_api_version
from azure.cli.command_modules.network.aaz.latest.network.watcher.connection_monitor._update import Update as _WatcherConnectionMonitorUpdate


def get_network_watcher_from_location(cmd, watcher_name="watcher_name", rg_name="watcher_rg"):
    from azure.cli.command_modules.network.aaz.latest.network.watcher._list import List

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


def process_nw_cm_v2_create_namespace(cmd):
    args = cmd.ctx.args
    validate_tags(args)
    if not has_value(args.location):  # location is None only occurs in creating a V2 connection monitor
        endpoint_source_resource_id = args.endpoint_source_resource_id.to_serialized_data()
        # parse and verify endpoint_source_resource_id
        if not has_value(args.endpoint_source_resource_id):
            raise ValidationError('usage error: --location/--endpoint-source-resource-id '
                                  'is required to create a V2 connection monitor')
        if is_valid_resource_id(endpoint_source_resource_id) is False:
            raise ValidationError('usage error: "{}" is not a valid resource id'.format(endpoint_source_resource_id))

        resource = parse_resource_id(endpoint_source_resource_id)
        resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
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


class WatcherConnectionMonitorOutputRemove(_WatcherConnectionMonitorUpdate):
    AZ_NAME = None

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


class WatcherConnectionMonitorTestGroupRemove(_WatcherConnectionMonitorUpdate):
    AZ_NAME = None

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
