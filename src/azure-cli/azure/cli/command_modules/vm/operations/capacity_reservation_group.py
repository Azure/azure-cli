# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from ..aaz.latest.capacity.reservation.group import List as _CapacityReservationGroupList

logger = get_logger(__name__)


class CapacityReservationGroupList(_CapacityReservationGroupList):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZBoolArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vm_instance = AAZBoolArg(
            options=['--vm-instance'],
            help="Retrieve the Virtual Machine Instance "
                 "which are associated to capacity reservation group in the response.",
            nullable=True
        )
        args_schema.vmss_instance = AAZBoolArg(
            options=['--vmss-instance'],
            help="Retrieve the ScaleSet VM Instance which are associated to capacity reservation group in the response.",
            nullable=True
        )
        args_schema.expand._registered = False
        return args_schema

    def pre_operations(self):
        from azure.cli.core.aaz import has_value
        args = self.ctx.args
        if args.vm_instance:
            args.expand = "virtualMachines/$ref"
        if args.vmss_instance:
            if has_value(args.expand):
                args.expand = args.expand.to_serialized_data() + ",virtualMachineScaleSetVMs/$ref"
            else:
                args.expand = "virtualMachineScaleSetVMs/$ref"
