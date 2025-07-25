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
    "afd origin-group update",
)
class Update(AAZCommand):
    """Update a new origin group within the specified profile.

    :example: Update a new origin group within the specified profile.
        az afd origin-group update -g group --origin-group-name og1 --profile-name profile --probe-request-type HEAD --probe-protocol Https --probe-interval-in-seconds 120 --probe-path /test1/azure.txt
    """

    _aaz_info = {
        "version": "2025-06-01",
        "resources": [
            ["mgmt-plane", "/subscriptions/{}/resourcegroups/{}/providers/microsoft.cdn/profiles/{}/origingroups/{}", "2025-06-01"],
        ]
    }

    AZ_SUPPORT_NO_WAIT = True

    AZ_SUPPORT_GENERIC_UPDATE = True

    def _handler(self, command_args):
        super()._handler(command_args)
        return self.build_lro_poller(self._execute_operations, self._output)

    _args_schema = None

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        if cls._args_schema is not None:
            return cls._args_schema
        cls._args_schema = super()._build_arguments_schema(*args, **kwargs)

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.origin_group_name = AAZStrArg(
            options=["-n", "--name", "--origin-group-name"],
            help="Name of the origin group which is unique within the endpoint.",
            required=True,
            id_part="child_name_1",
        )
        _args_schema.profile_name = AAZStrArg(
            options=["--profile-name"],
            help="Name of the Azure Front Door Standard or Azure Front Door Premium which is unique within the resource group.",
            required=True,
            id_part="name",
            fmt=AAZStrArgFormat(
                pattern="^[a-zA-Z0-9]+(-*[a-zA-Z0-9])*$",
                max_length=260,
                min_length=1,
            ),
        )
        _args_schema.resource_group = AAZResourceGroupNameArg(
            required=True,
        )

        # define Arg Group "LoadBalancingSettings"

        _args_schema = cls._args_schema
        _args_schema.additional_latency_in_milliseconds = AAZIntArg(
            options=["--additional-latency-in-milliseconds"],
            arg_group="LoadBalancingSettings",
            help="The additional latency in milliseconds for probes to fall into the lowest latency bucket",
            nullable=True,
        )
        _args_schema.sample_size = AAZIntArg(
            options=["--sample-size"],
            arg_group="LoadBalancingSettings",
            help="The number of samples to consider for load balancing decisions",
            nullable=True,
        )
        _args_schema.successful_samples_required = AAZIntArg(
            options=["--successful-samples-required"],
            arg_group="LoadBalancingSettings",
            help="The number of samples within the sample period that must succeed",
            nullable=True,
        )

        # define Arg Group "Properties"

        _args_schema = cls._args_schema
        _args_schema.authentication = AAZObjectArg(
            options=["--authentication"],
            arg_group="Properties",
            help="Authentication settings for origin in origin group.",
            nullable=True,
        )
        _args_schema.health_probe_settings = AAZObjectArg(
            options=["--health-probe-settings"],
            arg_group="Properties",
            help="Health probe settings to the origin that is used to determine the health of the origin.",
            nullable=True,
        )
        _args_schema.session_affinity_state = AAZStrArg(
            options=["--session-affinity-state"],
            arg_group="Properties",
            help="Whether to allow session affinity on this host. Valid options are 'Enabled' or 'Disabled'",
            nullable=True,
            enum={"Disabled": "Disabled", "Enabled": "Enabled"},
        )
        _args_schema.traffic_restoration_time_to_healed_or_new_endpoints_in_minutes = AAZIntArg(
            options=["--traffic-restoration-time-to-healed-or-new-endpoints-in-minutes"],
            arg_group="Properties",
            help="Time in minutes to shift the traffic to the endpoint gradually when an unhealthy endpoint comes healthy or a new endpoint is added. Default is 10 mins. This property is currently not supported.",
            nullable=True,
            fmt=AAZIntArgFormat(
                maximum=50,
                minimum=0,
            ),
        )

        authentication = cls._args_schema.authentication
        authentication.scope = AAZStrArg(
            options=["scope"],
            help="The scope used when requesting token from Microsoft Entra. For example, for Azure Blob Storage, scope could be \"https://storage.azure.com/.default\".",
            nullable=True,
        )
        authentication.type = AAZStrArg(
            options=["type"],
            help="The type of the authentication for the origin.",
            nullable=True,
            enum={"SystemAssignedIdentity": "SystemAssignedIdentity", "UserAssignedIdentity": "UserAssignedIdentity"},
        )
        authentication.user_assigned_identity = AAZObjectArg(
            options=["user-assigned-identity"],
            help="The user assigned managed identity to use for the origin authentication if type is UserAssignedIdentity.",
            nullable=True,
        )

        user_assigned_identity = cls._args_schema.authentication.user_assigned_identity
        user_assigned_identity.id = AAZStrArg(
            options=["id"],
            help="Resource ID.",
            nullable=True,
        )

        health_probe_settings = cls._args_schema.health_probe_settings
        health_probe_settings.probe_interval_in_seconds = AAZIntArg(
            options=["probe-interval-in-seconds"],
            help="The number of seconds between health probes.Default is 240sec.",
            nullable=True,
            fmt=AAZIntArgFormat(
                maximum=255,
                minimum=1,
            ),
        )
        health_probe_settings.probe_path = AAZStrArg(
            options=["probe-path"],
            help="The path relative to the origin that is used to determine the health of the origin.",
            nullable=True,
        )
        health_probe_settings.probe_protocol = AAZStrArg(
            options=["probe-protocol"],
            help="Protocol to use for health probe.",
            nullable=True,
            enum={"Http": "Http", "Https": "Https", "NotSet": "NotSet"},
        )
        health_probe_settings.probe_request_type = AAZStrArg(
            options=["probe-request-type"],
            help="The type of health probe request that is made.",
            nullable=True,
            enum={"GET": "GET", "HEAD": "HEAD", "NotSet": "NotSet"},
        )
        return cls._args_schema

    def _execute_operations(self):
        self.pre_operations()
        self.AFDOriginGroupsGet(ctx=self.ctx)()
        self.pre_instance_update(self.ctx.vars.instance)
        self.InstanceUpdateByJson(ctx=self.ctx)()
        self.InstanceUpdateByGeneric(ctx=self.ctx)()
        self.post_instance_update(self.ctx.vars.instance)
        yield self.AFDOriginGroupsCreate(ctx=self.ctx)()
        self.post_operations()

    @register_callback
    def pre_operations(self):
        pass

    @register_callback
    def post_operations(self):
        pass

    @register_callback
    def pre_instance_update(self, instance):
        pass

    @register_callback
    def post_instance_update(self, instance):
        pass

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result

    class AFDOriginGroupsGet(AAZHttpOperation):
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
                "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Cdn/profiles/{profileName}/originGroups/{originGroupName}",
                **self.url_parameters
            )

        @property
        def method(self):
            return "GET"

        @property
        def error_format(self):
            return "MgmtErrorFormat"

        @property
        def url_parameters(self):
            parameters = {
                **self.serialize_url_param(
                    "originGroupName", self.ctx.args.origin_group_name,
                    required=True,
                ),
                **self.serialize_url_param(
                    "profileName", self.ctx.args.profile_name,
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
                    "api-version", "2025-06-01",
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
            _UpdateHelper._build_schema_afd_origin_group_read(cls._schema_on_200)

            return cls._schema_on_200

    class AFDOriginGroupsCreate(AAZHttpOperation):
        CLIENT_TYPE = "MgmtClient"

        def __call__(self, *args, **kwargs):
            request = self.make_request()
            session = self.client.send_request(request=request, stream=False, **kwargs)
            if session.http_response.status_code in [202]:
                return self.client.build_lro_polling(
                    self.ctx.args.no_wait,
                    session,
                    self.on_200_201,
                    self.on_error,
                    lro_options={"final-state-via": "azure-async-operation"},
                    path_format_arguments=self.url_parameters,
                )
            if session.http_response.status_code in [200, 201]:
                return self.client.build_lro_polling(
                    self.ctx.args.no_wait,
                    session,
                    self.on_200_201,
                    self.on_error,
                    lro_options={"final-state-via": "azure-async-operation"},
                    path_format_arguments=self.url_parameters,
                )

            return self.on_error(session.http_response)

        @property
        def url(self):
            return self.client.format_url(
                "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Cdn/profiles/{profileName}/originGroups/{originGroupName}",
                **self.url_parameters
            )

        @property
        def method(self):
            return "PUT"

        @property
        def error_format(self):
            return "MgmtErrorFormat"

        @property
        def url_parameters(self):
            parameters = {
                **self.serialize_url_param(
                    "originGroupName", self.ctx.args.origin_group_name,
                    required=True,
                ),
                **self.serialize_url_param(
                    "profileName", self.ctx.args.profile_name,
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
                    "api-version", "2025-06-01",
                    required=True,
                ),
            }
            return parameters

        @property
        def header_parameters(self):
            parameters = {
                **self.serialize_header_param(
                    "Content-Type", "application/json",
                ),
                **self.serialize_header_param(
                    "Accept", "application/json",
                ),
            }
            return parameters

        @property
        def content(self):
            _content_value, _builder = self.new_content_builder(
                self.ctx.args,
                value=self.ctx.vars.instance,
            )

            return self.serialize_content(_content_value)

        def on_200_201(self, session):
            data = self.deserialize_http_content(session)
            self.ctx.set_var(
                "instance",
                data,
                schema_builder=self._build_schema_on_200_201
            )

        _schema_on_200_201 = None

        @classmethod
        def _build_schema_on_200_201(cls):
            if cls._schema_on_200_201 is not None:
                return cls._schema_on_200_201

            cls._schema_on_200_201 = AAZObjectType()
            _UpdateHelper._build_schema_afd_origin_group_read(cls._schema_on_200_201)

            return cls._schema_on_200_201

    class InstanceUpdateByJson(AAZJsonInstanceUpdateOperation):

        def __call__(self, *args, **kwargs):
            self._update_instance(self.ctx.vars.instance)

        def _update_instance(self, instance):
            _instance_value, _builder = self.new_content_builder(
                self.ctx.args,
                value=instance,
                typ=AAZObjectType
            )
            _builder.set_prop("properties", AAZObjectType, typ_kwargs={"flags": {"client_flatten": True}})

            properties = _builder.get(".properties")
            if properties is not None:
                properties.set_prop("authentication", AAZObjectType, ".authentication")
                properties.set_prop("healthProbeSettings", AAZObjectType, ".health_probe_settings")
                properties.set_prop("loadBalancingSettings", AAZObjectType)
                properties.set_prop("sessionAffinityState", AAZStrType, ".session_affinity_state")
                properties.set_prop("trafficRestorationTimeToHealedOrNewEndpointsInMinutes", AAZIntType, ".traffic_restoration_time_to_healed_or_new_endpoints_in_minutes")

            authentication = _builder.get(".properties.authentication")
            if authentication is not None:
                authentication.set_prop("scope", AAZStrType, ".scope")
                authentication.set_prop("type", AAZStrType, ".type")
                authentication.set_prop("userAssignedIdentity", AAZObjectType, ".user_assigned_identity")

            user_assigned_identity = _builder.get(".properties.authentication.userAssignedIdentity")
            if user_assigned_identity is not None:
                user_assigned_identity.set_prop("id", AAZStrType, ".id")

            health_probe_settings = _builder.get(".properties.healthProbeSettings")
            if health_probe_settings is not None:
                health_probe_settings.set_prop("probeIntervalInSeconds", AAZIntType, ".probe_interval_in_seconds")
                health_probe_settings.set_prop("probePath", AAZStrType, ".probe_path")
                health_probe_settings.set_prop("probeProtocol", AAZStrType, ".probe_protocol")
                health_probe_settings.set_prop("probeRequestType", AAZStrType, ".probe_request_type")

            load_balancing_settings = _builder.get(".properties.loadBalancingSettings")
            if load_balancing_settings is not None:
                load_balancing_settings.set_prop("additionalLatencyInMilliseconds", AAZIntType, ".additional_latency_in_milliseconds")
                load_balancing_settings.set_prop("sampleSize", AAZIntType, ".sample_size")
                load_balancing_settings.set_prop("successfulSamplesRequired", AAZIntType, ".successful_samples_required")

            return _instance_value

    class InstanceUpdateByGeneric(AAZGenericInstanceUpdateOperation):

        def __call__(self, *args, **kwargs):
            self._update_instance_by_generic(
                self.ctx.vars.instance,
                self.ctx.generic_update_args
            )


class _UpdateHelper:
    """Helper class for Update"""

    _schema_afd_origin_group_read = None

    @classmethod
    def _build_schema_afd_origin_group_read(cls, _schema):
        if cls._schema_afd_origin_group_read is not None:
            _schema.id = cls._schema_afd_origin_group_read.id
            _schema.name = cls._schema_afd_origin_group_read.name
            _schema.properties = cls._schema_afd_origin_group_read.properties
            _schema.system_data = cls._schema_afd_origin_group_read.system_data
            _schema.type = cls._schema_afd_origin_group_read.type
            return

        cls._schema_afd_origin_group_read = _schema_afd_origin_group_read = AAZObjectType()

        afd_origin_group_read = _schema_afd_origin_group_read
        afd_origin_group_read.id = AAZStrType(
            flags={"read_only": True},
        )
        afd_origin_group_read.name = AAZStrType(
            flags={"read_only": True},
        )
        afd_origin_group_read.properties = AAZObjectType(
            flags={"client_flatten": True},
        )
        afd_origin_group_read.system_data = AAZObjectType(
            serialized_name="systemData",
            flags={"read_only": True},
        )
        afd_origin_group_read.type = AAZStrType(
            flags={"read_only": True},
        )

        properties = _schema_afd_origin_group_read.properties
        properties.authentication = AAZObjectType()
        properties.deployment_status = AAZStrType(
            serialized_name="deploymentStatus",
            flags={"read_only": True},
        )
        properties.health_probe_settings = AAZObjectType(
            serialized_name="healthProbeSettings",
        )
        properties.load_balancing_settings = AAZObjectType(
            serialized_name="loadBalancingSettings",
        )
        properties.profile_name = AAZStrType(
            serialized_name="profileName",
            flags={"read_only": True},
        )
        properties.provisioning_state = AAZStrType(
            serialized_name="provisioningState",
            flags={"read_only": True},
        )
        properties.session_affinity_state = AAZStrType(
            serialized_name="sessionAffinityState",
        )
        properties.traffic_restoration_time_to_healed_or_new_endpoints_in_minutes = AAZIntType(
            serialized_name="trafficRestorationTimeToHealedOrNewEndpointsInMinutes",
        )

        authentication = _schema_afd_origin_group_read.properties.authentication
        authentication.scope = AAZStrType()
        authentication.type = AAZStrType()
        authentication.user_assigned_identity = AAZObjectType(
            serialized_name="userAssignedIdentity",
        )

        user_assigned_identity = _schema_afd_origin_group_read.properties.authentication.user_assigned_identity
        user_assigned_identity.id = AAZStrType()

        health_probe_settings = _schema_afd_origin_group_read.properties.health_probe_settings
        health_probe_settings.probe_interval_in_seconds = AAZIntType(
            serialized_name="probeIntervalInSeconds",
        )
        health_probe_settings.probe_path = AAZStrType(
            serialized_name="probePath",
        )
        health_probe_settings.probe_protocol = AAZStrType(
            serialized_name="probeProtocol",
        )
        health_probe_settings.probe_request_type = AAZStrType(
            serialized_name="probeRequestType",
        )

        load_balancing_settings = _schema_afd_origin_group_read.properties.load_balancing_settings
        load_balancing_settings.additional_latency_in_milliseconds = AAZIntType(
            serialized_name="additionalLatencyInMilliseconds",
        )
        load_balancing_settings.sample_size = AAZIntType(
            serialized_name="sampleSize",
        )
        load_balancing_settings.successful_samples_required = AAZIntType(
            serialized_name="successfulSamplesRequired",
        )

        system_data = _schema_afd_origin_group_read.system_data
        system_data.created_at = AAZStrType(
            serialized_name="createdAt",
        )
        system_data.created_by = AAZStrType(
            serialized_name="createdBy",
        )
        system_data.created_by_type = AAZStrType(
            serialized_name="createdByType",
        )
        system_data.last_modified_at = AAZStrType(
            serialized_name="lastModifiedAt",
        )
        system_data.last_modified_by = AAZStrType(
            serialized_name="lastModifiedBy",
        )
        system_data.last_modified_by_type = AAZStrType(
            serialized_name="lastModifiedByType",
        )

        _schema.id = cls._schema_afd_origin_group_read.id
        _schema.name = cls._schema_afd_origin_group_read.name
        _schema.properties = cls._schema_afd_origin_group_read.properties
        _schema.system_data = cls._schema_afd_origin_group_read.system_data
        _schema.type = cls._schema_afd_origin_group_read.type


__all__ = ["Update"]
