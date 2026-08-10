# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from azure.cli.core.aaz import register_command, has_value, AAZBoolArg, AAZDictType, AAZIntType
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

    _aaz_info = {
        "version": "2026-04-01",
        "resources": [
            ["mgmt-plane", "/subscriptions/{}/resourcegroups/{}/providers/microsoft.compute/capacityreservationgroups/{}/capacityreservations/{}", "2026-04-01"],
        ]
    }

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

    class CapacityReservationsGet(_CapacityReservationShow.CapacityReservationsGet):
        _schema_on_200 = None

        @property
        def query_parameters(self):
            parameters = super().query_parameters
            parameters.update(self.serialize_query_param(
                "api-version", "2026-04-01", required=True))
            return parameters

        @classmethod
        def _build_schema_on_200(cls):
            if cls._schema_on_200 is not None:
                return cls._schema_on_200

            cls._schema_on_200 = super()._build_schema_on_200()
            utilization_info = cls._schema_on_200.properties.instance_view.utilization_info
            utilization_info.used_reserved_count_by_subscription = AAZDictType(
                serialized_name="usedReservedCountBySubscription",
                flags={"read_only": True},
            )
            utilization_info.used_reserved_count_by_subscription.Element = AAZIntType()
            return cls._schema_on_200
