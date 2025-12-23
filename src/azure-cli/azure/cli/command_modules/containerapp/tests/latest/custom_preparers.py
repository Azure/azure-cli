# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import time

from azure.cli.command_modules.containerapp._utils import format_location

from azure.cli.testsdk import CliTestError
from azure.cli.testsdk.reverse_dependency import get_dummy_cli
from azure.cli.testsdk.scenario_tests import SingleValueReplacer
from azure.cli.testsdk.preparers import NoTrafficRecordingPreparer, ResourceGroupPreparer
from .common import STAGE_LOCATION

class SubnetPreparer(NoTrafficRecordingPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='vnet', location="centralus", location_replace_stage="centralus", resource_group_parameter_name='resource_group', vnet_name=None, vnet_address_prefixes='14.0.0.0/23', subnet_address_prefixes='14.0.0.0/23',
                 delegations=None, subnet_name="default", service_endpoints=None, skip_delete=False):
        super(SubnetPreparer, self).__init__(name_prefix, 15)
        self.cli_ctx = get_dummy_cli()
        self.location = location
        self.resource_group_parameter_name = resource_group_parameter_name
        self.vnet_name = vnet_name
        if vnet_name is None:
            self.vnet_name = self.create_random_name()
        self.vnet_address_prefixes = vnet_address_prefixes
        self.subnet_address_prefixes = subnet_address_prefixes
        self.delegations = delegations
        self.subnet_name = subnet_name
        self.service_endpoints = service_endpoints
        self.skip_delete = skip_delete
        self.location_replace_stage = location_replace_stage

    def create_resource(self, name, **kwargs):
        resource_group = self._get_resource_group(**kwargs)
        subnet_id = "FAKESUBNETID"
        location = self.location
        if format_location(location) == format_location(STAGE_LOCATION):
            location = self.location_replace_stage

        try:
            self.live_only_execute(self.cli_ctx, f"az network vnet create --address-prefixes {self.vnet_address_prefixes} -g {resource_group} -n {self.vnet_name} --subnet-name {self.subnet_name} --location {location}")
            subnet_command = f"az network vnet subnet update --address-prefixes {self.subnet_address_prefixes} " \
                             f"-n {self.subnet_name} " \
                             f"-g {resource_group} " \
                             f"--vnet-name {self.vnet_name} "
            if self.service_endpoints is not None:
                subnet_command += f'--service-endpoints {self.service_endpoints} '

            if self.delegations is not None:
                subnet_command += f'--delegations {self.delegations} '

            subnet_id = self.live_only_execute(self.cli_ctx, subnet_command).get_output_in_json()["id"]
        except AttributeError:  # live only execute returns None if playing from record
            pass
        return {'subnet_id': subnet_id,
                'vnet_name': self.vnet_name,
                'subnet_name': self.subnet_name}

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'Resource group is required. Please add ' \
                       'decorator @{} in front of this preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))
