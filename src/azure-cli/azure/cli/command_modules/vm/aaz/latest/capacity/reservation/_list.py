# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#
# Code generated by aaz-dev-tools
# --------------------------------------------------------------------------------------------

# pylint: skip-file
# flake8: noqa

from azure.cli.core.aaz import *


@register_command(
    "capacity reservation list",
)
class List(AAZCommand):
    """List all of the capacity reservations in the specified capacity reservation group. Use the nextLink property in the response to get the next page of capacity reservations.

    :example: List capacity reservation.
        az capacity reservation list -c ReservationGroupName -g MyResourceGroup
    """

    _aaz_info = {
        "version": "2024-11-01",
        "resources": [
            ["mgmt-plane", "/subscriptions/{}/resourcegroups/{}/providers/microsoft.compute/capacityreservationgroups/{}/capacityreservations", "2024-11-01"],
        ]
    }

    AZ_SUPPORT_PAGINATION = True

    def _handler(self, command_args):
        super()._handler(command_args)
        return self.build_paging(self._execute_operations, self._output)

    _args_schema = None

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        if cls._args_schema is not None:
            return cls._args_schema
        cls._args_schema = super()._build_arguments_schema(*args, **kwargs)

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.capacity_reservation_group = AAZStrArg(
            options=["-c", "--capacity-reservation-group"],
            help="The name of the capacity reservation group.",
            required=True,
        )
        _args_schema.resource_group = AAZResourceGroupNameArg(
            required=True,
        )
        return cls._args_schema

    def _execute_operations(self):
        self.pre_operations()
        self.CapacityReservationsListByCapacityReservationGroup(ctx=self.ctx)()
        self.post_operations()

    @register_callback
    def pre_operations(self):
        pass

    @register_callback
    def post_operations(self):
        pass

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        return result, next_link

    class CapacityReservationsListByCapacityReservationGroup(AAZHttpOperation):
        CLIENT_TYPE = "MgmtClient"

        def __call__(self, *args, **kwargs):
            request = self.make_request()
            session = self.client.send_request(request=request, stream=False, **kwargs)
            if session.http_response.status_code in [200]:
                return self.on_200(session)

            return self.on_error(session.http_response)

        @property
        def url(self):
            return self.client.format_url(
                "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Compute/capacityReservationGroups/{capacityReservationGroupName}/capacityReservations",
                **self.url_parameters
            )

        @property
        def method(self):
            return "GET"

        @property
        def error_format(self):
            return "ODataV4Format"

        @property
        def url_parameters(self):
            parameters = {
                **self.serialize_url_param(
                    "capacityReservationGroupName", self.ctx.args.capacity_reservation_group,
                    required=True,
                ),
                **self.serialize_url_param(
                    "resourceGroupName", self.ctx.args.resource_group,
                    required=True,
                ),
                **self.serialize_url_param(
                    "subscriptionId", self.ctx.subscription_id,
                    required=True,
                ),
            }
            return parameters

        @property
        def query_parameters(self):
            parameters = {
                **self.serialize_query_param(
                    "api-version", "2024-11-01",
                    required=True,
                ),
            }
            return parameters

        @property
        def header_parameters(self):
            parameters = {
                **self.serialize_header_param(
                    "Accept", "application/json",
                ),
            }
            return parameters

        def on_200(self, session):
            data = self.deserialize_http_content(session)
            self.ctx.set_var(
                "instance",
                data,
                schema_builder=self._build_schema_on_200
            )

        _schema_on_200 = None

        @classmethod
        def _build_schema_on_200(cls):
            if cls._schema_on_200 is not None:
                return cls._schema_on_200

            cls._schema_on_200 = AAZObjectType()

            _schema_on_200 = cls._schema_on_200
            _schema_on_200.next_link = AAZStrType(
                serialized_name="nextLink",
            )
            _schema_on_200.value = AAZListType(
                flags={"required": True},
            )

            value = cls._schema_on_200.value
            value.Element = AAZObjectType()

            _element = cls._schema_on_200.value.Element
            _element.id = AAZStrType(
                flags={"read_only": True},
            )
            _element.location = AAZStrType(
                flags={"required": True},
            )
            _element.name = AAZStrType(
                flags={"read_only": True},
            )
            _element.properties = AAZObjectType(
                flags={"client_flatten": True},
            )
            _element.sku = AAZObjectType(
                flags={"required": True},
            )
            _element.tags = AAZDictType()
            _element.type = AAZStrType(
                flags={"read_only": True},
            )
            _element.zones = AAZListType()

            properties = cls._schema_on_200.value.Element.properties
            properties.instance_view = AAZObjectType(
                serialized_name="instanceView",
                flags={"read_only": True},
            )
            properties.platform_fault_domain_count = AAZIntType(
                serialized_name="platformFaultDomainCount",
                flags={"read_only": True},
            )
            properties.provisioning_state = AAZStrType(
                serialized_name="provisioningState",
                flags={"read_only": True},
            )
            properties.provisioning_time = AAZStrType(
                serialized_name="provisioningTime",
                flags={"read_only": True},
            )
            properties.reservation_id = AAZStrType(
                serialized_name="reservationId",
                flags={"read_only": True},
            )
            properties.time_created = AAZStrType(
                serialized_name="timeCreated",
                flags={"read_only": True},
            )
            properties.virtual_machines_associated = AAZListType(
                serialized_name="virtualMachinesAssociated",
                flags={"read_only": True},
            )

            instance_view = cls._schema_on_200.value.Element.properties.instance_view
            instance_view.statuses = AAZListType()
            instance_view.utilization_info = AAZObjectType(
                serialized_name="utilizationInfo",
            )

            statuses = cls._schema_on_200.value.Element.properties.instance_view.statuses
            statuses.Element = AAZObjectType()

            _element = cls._schema_on_200.value.Element.properties.instance_view.statuses.Element
            _element.code = AAZStrType()
            _element.display_status = AAZStrType(
                serialized_name="displayStatus",
            )
            _element.level = AAZStrType()
            _element.message = AAZStrType()
            _element.time = AAZStrType()

            utilization_info = cls._schema_on_200.value.Element.properties.instance_view.utilization_info
            utilization_info.current_capacity = AAZIntType(
                serialized_name="currentCapacity",
                flags={"read_only": True},
            )
            utilization_info.virtual_machines_allocated = AAZListType(
                serialized_name="virtualMachinesAllocated",
                flags={"read_only": True},
            )

            virtual_machines_allocated = cls._schema_on_200.value.Element.properties.instance_view.utilization_info.virtual_machines_allocated
            virtual_machines_allocated.Element = AAZObjectType()
            _ListHelper._build_schema_sub_resource_read_only_read(virtual_machines_allocated.Element)

            virtual_machines_associated = cls._schema_on_200.value.Element.properties.virtual_machines_associated
            virtual_machines_associated.Element = AAZObjectType()
            _ListHelper._build_schema_sub_resource_read_only_read(virtual_machines_associated.Element)

            sku = cls._schema_on_200.value.Element.sku
            sku.capacity = AAZIntType()
            sku.name = AAZStrType()
            sku.tier = AAZStrType()

            tags = cls._schema_on_200.value.Element.tags
            tags.Element = AAZStrType()

            zones = cls._schema_on_200.value.Element.zones
            zones.Element = AAZStrType()

            return cls._schema_on_200


class _ListHelper:
    """Helper class for List"""

    _schema_sub_resource_read_only_read = None

    @classmethod
    def _build_schema_sub_resource_read_only_read(cls, _schema):
        if cls._schema_sub_resource_read_only_read is not None:
            _schema.id = cls._schema_sub_resource_read_only_read.id
            return

        cls._schema_sub_resource_read_only_read = _schema_sub_resource_read_only_read = AAZObjectType()

        sub_resource_read_only_read = _schema_sub_resource_read_only_read
        sub_resource_read_only_read.id = AAZStrType(
            flags={"read_only": True},
        )

        _schema.id = cls._schema_sub_resource_read_only_read.id


__all__ = ["List"]
