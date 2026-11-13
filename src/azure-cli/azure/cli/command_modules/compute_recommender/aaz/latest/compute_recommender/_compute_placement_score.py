# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.aaz import (
    AAZBoolArg,
    AAZBoolType,
    AAZCommand,
    AAZHttpOperation,
    AAZIntArg,
    AAZIntType,
    AAZListArg,
    AAZListType,
    AAZObjectArg,
    AAZObjectType,
    AAZResourceLocationArg,
    AAZStrArg,
    AAZStrType,
    register_callback,
    register_command,
)


@register_command(
    "compute-recommender compute-placement-score",
    is_preview=True,
)
class ComputePlacementScore(AAZCommand):
    """Generate placement scores for regular VM SKUs.

    :example: Generate regional scores using the request location and the default instance count.
        az compute-recommender compute-placement-score --location eastus --desired-sizes "[{sku:Standard_D2_v2}]"
    :example: Compare zonal placement scores across regions for ten VM instances.
        az compute-recommender compute-placement-score --location eastus --subscription 00000000-0000-0000-0000-000000000000 --availability-zones true --desired-locations eastus eastus2 --desired-count 10 --desired-sizes "[{sku:Standard_D2_v2},{sku:Standard_D4_v2}]"
    """

    _aaz_info = {
        "version": "2026-10-05-preview",
        "resources": [
            ["mgmt-plane", "/subscriptions/{}/providers/microsoft.compute/locations/{}/placementscores/regular/generate",
             "2026-10-05-preview"],
        ],
    }

    def _handler(self, command_args):
        super()._handler(command_args)
        self._execute_operations()
        return self._output()

    _args_schema = None

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        if cls._args_schema is not None:
            return cls._args_schema
        cls._args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema = cls._args_schema
        args_schema.location = AAZResourceLocationArg(
            required=True,
            id_part="name",
        )
        args_schema.availability_zones = AAZBoolArg(
            options=["--availability-zones"],
            arg_group="ComputePlacementScoresInput",
            help="Define whether the scope is zonal (true) or regional (false).",
        )
        args_schema.desired_count = AAZIntArg(
            options=["--desired-count"],
            arg_group="ComputePlacementScoresInput",
            help="Desired instance count per region or zone. The service defaults to 1 when omitted.",
        )
        args_schema.desired_locations = AAZListArg(
            options=["--desired-locations"],
            arg_group="ComputePlacementScoresInput",
            help="Desired Azure regions. The service uses --location when omitted.",
        )
        args_schema.desired_sizes = AAZListArg(
            options=["--desired-sizes"],
            arg_group="ComputePlacementScoresInput",
            help="Desired virtual machine SKU sizes.",
            required=True,
        )
        args_schema.desired_locations.Element = AAZStrArg()
        args_schema.desired_sizes.Element = AAZObjectArg()
        args_schema.desired_sizes.Element.sku = AAZStrArg(
            options=["sku"],
            help="The virtual machine SKU size.",
        )
        return cls._args_schema

    def _execute_operations(self):
        self.pre_operations()
        self.ComputePlacementScoresPost(ctx=self.ctx)()
        self.post_operations()

    @register_callback
    def pre_operations(self):
        pass

    @register_callback
    def post_operations(self):
        pass

    def _output(self, *args, **kwargs):
        return self.deserialize_output(self.ctx.vars.instance, client_flatten=True)

    class ComputePlacementScoresPost(AAZHttpOperation):
        CLIENT_TYPE = "MgmtClient"

        def __call__(self, *args, **kwargs):
            request = self.make_request()
            session = self.client.send_request(request=request, stream=False, **kwargs)
            if session.http_response.status_code == 200:
                return self.on_200(session)
            return self.on_error(session.http_response)

        @property
        def url(self):
            return self.client.format_url(
                "/subscriptions/{subscriptionId}/providers/Microsoft.Compute/locations/{location}/placementScores/regular/generate",
                **self.url_parameters
            )

        @property
        def method(self):
            return "POST"

        @property
        def error_format(self):
            return "MgmtErrorFormat"

        @property
        def url_parameters(self):
            return {
                **self.serialize_url_param("location", self.ctx.args.location, required=True),
                **self.serialize_url_param("subscriptionId", self.ctx.subscription_id, required=True),
            }

        @property
        def query_parameters(self):
            return {
                **self.serialize_query_param("api-version", "2026-10-05-preview", required=True),
            }

        @property
        def header_parameters(self):
            return {
                **self.serialize_header_param("Content-Type", "application/json"),
                **self.serialize_header_param("Accept", "application/json"),
            }

        @property
        def content(self):
            content_value, builder = self.new_content_builder(
                self.ctx.args,
                typ=AAZObjectType,
                typ_kwargs={"flags": {"required": True, "client_flatten": True}},
            )
            builder.set_prop("availabilityZones", AAZBoolType, ".availability_zones")
            builder.set_prop("desiredCount", AAZIntType, ".desired_count")
            builder.set_prop("desiredLocations", AAZListType, ".desired_locations")
            builder.set_prop("desiredSizes", AAZListType, ".desired_sizes", typ_kwargs={"flags": {"required": True}})

            desired_locations = builder.get(".desiredLocations")
            if desired_locations is not None:
                desired_locations.set_elements(AAZStrType, ".")

            desired_sizes = builder.get(".desiredSizes")
            if desired_sizes is not None:
                desired_sizes.set_elements(AAZObjectType, ".")

            elements = builder.get(".desiredSizes[]")
            if elements is not None:
                elements.set_prop("sku", AAZStrType, ".sku")

            return self.serialize_content(content_value)

        def on_200(self, session):
            self.ctx.set_var(
                "instance",
                self.deserialize_http_content(session),
                schema_builder=self._build_schema_on_200,
            )

        _schema_on_200 = None

        @classmethod
        def _build_schema_on_200(cls):
            if cls._schema_on_200 is not None:
                return cls._schema_on_200

            cls._schema_on_200 = AAZObjectType()
            schema = cls._schema_on_200
            schema.availability_zones = AAZBoolType(serialized_name="availabilityZones")
            schema.desired_count = AAZIntType(serialized_name="desiredCount")
            schema.desired_locations = AAZListType(serialized_name="desiredLocations")
            schema.desired_locations.Element = AAZStrType()
            schema.desired_sizes = AAZListType(serialized_name="desiredSizes")
            schema.desired_sizes.Element = AAZObjectType()
            schema.desired_sizes.Element.sku = AAZStrType()
            schema.placement_scores = AAZListType(serialized_name="placementScores")
            schema.placement_scores.Element = AAZObjectType()

            element = schema.placement_scores.Element
            element.availability_zone = AAZStrType(serialized_name="availabilityZone")
            element.placement_preference = AAZIntType(serialized_name="placementPreference")
            element.region = AAZStrType()
            element.score = AAZStrType()
            element.sku = AAZStrType()
            return cls._schema_on_200


__all__ = ["ComputePlacementScore"]
