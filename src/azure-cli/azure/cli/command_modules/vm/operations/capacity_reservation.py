# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from azure.cli.core.aaz import register_command, has_value, AAZBoolArg
from ..aaz.latest.capacity.reservation import Update as _CapacityReservationUpdate, Show as _CapacityReservationShow

logger = get_logger(__name__)


@register_command(
    "capacity reservation update",
)
class CapacityReservationUpdate(_CapacityReservationUpdate):
    """Update operation to update a capacity reservation.

    :example: Update a capacity reservation.
        az capacity reservation update -c ReservationGroupName -n ReservationName -g MyResourceGroup --capacity 5 --tags key=val
    """

    def pre_operations(self):
        args = self.ctx.args
        if not has_value(args.tags):
            instance = _CapacityReservationShow(cli_ctx=self.cli_ctx)(command_args={
                "capacity_reservation_group": args.capacity_reservation_group,
                "capacity_reservation_name": args.capacity_reservation_name,
                "resource_group": args.resource_group,
            })
            args.tags = instance.get("tags", None)


@register_command(
    "capacity reservation show",
)
class CapacityReservationShow(_CapacityReservationShow):
    """Retrieve information about the capacity reservation.

    :example: Get a capacity reservation.
        az capacity reservation show -c ReservationGroupName -n ReservationName -g MyResourceGroup

    :example: Get a capacity reservation containing the instance views.
        az capacity reservation show -c ReservationGroupName -n ReservationName -g MyResourceGroup --instance-view
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.expand._registered = False
        args_schema.instance_view = AAZBoolArg(
            options=["--instance-view", "-i"],
            help="Retrieve a snapshot of the runtime properties of the capacity reservation that is managed by the platform and can change outside of control plane operations.",
            blank=True
        )

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.instance_view) and args.instance_view.to_serialized_data() is True:
            args.expand = 'instanceView'
