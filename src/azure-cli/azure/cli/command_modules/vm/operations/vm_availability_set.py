# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from azure.mgmt.core.tools import is_valid_resource_id
from azure.cli.core.aaz import has_value, AAZStrArg
from ..aaz.latest.vm.availability_set import Update as _Update

logger = get_logger(__name__)

PPG_RID_TEMPLATE = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/proximityPlacementGroups/{}"


class AvailabilitySetUpdate(_Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.ppg = AAZStrArg(
            options=["--ppg"],
            help="Name or ID of the proximity placement group that the availability set should be associated with."
        )
        args_schema.sku._registered = False
        args_schema.platform_fault_domain_count._registered = False
        args_schema.proximity_placement_group._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.ppg):
            ppg = args.ppg.to_serialized_data()
            args.proximity_placement_group.id = ppg if is_valid_resource_id(ppg) else PPG_RID_TEMPLATE.format(self.ctx.subscription_id, args.resource_group, ppg)
