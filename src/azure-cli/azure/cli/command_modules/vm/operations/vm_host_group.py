# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from azure.cli.core.aaz import AAZBoolArg, AAZStrArg
from ..aaz.latest.vm.host.group import Show as _VMHostGroupShow, Update as _VMHostGroupUpdate

logger = get_logger(__name__)


class VMHostGroupShow(_VMHostGroupShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.expand._registered = False

        return args_schema


class VMHostGroupUpdate(_VMHostGroupUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.acquire_policy_token = AAZBoolArg(
            options=["--acquire-policy-token"],
            arg_group="Global Policy",
            help="Acquiring an Azure Policy token automatically for this resource operation",
            nullable=True,
        )

        args_schema.change_reference = AAZStrArg(
            options=["--change-reference"],
            arg_group="Global Policy",
            help="The related change reference ID for this resource operation"
        )

        return args_schema

    def pre_operations(self):
        self.cli_ctx.data['_acquire_policy_token'] = self.ctx.args.acquire_policy_token
        self.cli_ctx.data['_change_reference'] = self.ctx.args.change_reference


def convert_show_result_to_snake_case(result):
    new_result = {}
    if 'location' in result:
        new_result['location'] = result['location']

    if 'tags' in result:
        new_result['tags'] = result['tags']

    if 'zones' in result:
        new_result['zones'] = result['zones']

    if 'additionalCapabilities' in result:
        new_result['additional_capabilities'] = result['additionalCapabilities']

        if new_result['additional_capabilities'].get('ultraSSDEnabled'):
            new_result['additional_capabilities']['ultra_ssd_enabled'] = new_result['additional_capabilities']['ultraSSDEnabled']
            new_result['additional_capabilities'].pop('ultraSSDEnabled')

    if 'platformFaultDomainCount' in result:
        new_result['platform_fault_domain_count'] = result['platformFaultDomainCount']

    if 'supportAutomaticPlacement' in result:
        new_result['support_automatic_placement'] = result['supportAutomaticPlacement']
    return new_result
