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
    "relay hyco authorization-rule update",
)
class Update(AAZCommand):
    """Update Authorization Rule for given Relay Service Hybrid Connection.

    :example: Update Authorization Rule for given Relay Service Hybrid Connection
        az relay hyco authorization-rule update --resource-group myresourcegroup --namespace-name mynamespace --hybrid-connection-name myhyco --name myauthorule --rights Send
    """

    _aaz_info = {
        "version": "2017-04-01",
        "resources": [
            ["mgmt-plane", "/subscriptions/{}/resourcegroups/{}/providers/microsoft.relay/namespaces/{}/hybridconnections/{}/authorizationrules/{}", "2017-04-01"],
        ]
    }

    AZ_SUPPORT_GENERIC_UPDATE = True

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

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.name = AAZStrArg(
            options=["-n", "--name"],
            help="Name of Hybrid Connection Authorization Rule.",
            required=True,
            id_part="child_name_2",
            fmt=AAZStrArgFormat(
                min_length=1,
            ),
        )
        _args_schema.hybrid_connection_name = AAZStrArg(
            options=["--hybrid-connection-name"],
            help="Name of Hybrid Connection.",
            required=True,
            id_part="child_name_1",
            fmt=AAZStrArgFormat(
                min_length=1,
            ),
        )
        _args_schema.namespace_name = AAZStrArg(
            options=["--namespace-name"],
            help="Name of Namespace.",
            required=True,
            id_part="name",
            fmt=AAZStrArgFormat(
                max_length=50,
                min_length=6,
            ),
        )
        _args_schema.resource_group = AAZResourceGroupNameArg(
            required=True,
        )
        _args_schema.rights = AAZListArg(
            options=["--rights"],
            help="Space-separated list of Authorization rule rights. Allowed values: Listen, Manage, Send.",
            fmt=AAZListArgFormat(
                unique=True,
            ),
        )

        rights = cls._args_schema.rights
        rights.Element = AAZStrArg(
            nullable=True,
            enum={"Listen": "Listen", "Manage": "Manage", "Send": "Send"},
        )
        return cls._args_schema

    def _execute_operations(self):
        self.pre_operations()
        self.HybridConnectionsGetAuthorizationRule(ctx=self.ctx)()
        self.pre_instance_update(self.ctx.vars.instance)
        self.InstanceUpdateByJson(ctx=self.ctx)()
        self.InstanceUpdateByGeneric(ctx=self.ctx)()
        self.post_instance_update(self.ctx.vars.instance)
        self.HybridConnectionsCreateOrUpdateAuthorizationRule(ctx=self.ctx)()
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

    class HybridConnectionsGetAuthorizationRule(AAZHttpOperation):
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
                "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Relay/namespaces/{namespaceName}/hybridConnections/{hybridConnectionName}/authorizationRules/{authorizationRuleName}",
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
                    "authorizationRuleName", self.ctx.args.name,
                    required=True,
                ),
                **self.serialize_url_param(
                    "hybridConnectionName", self.ctx.args.hybrid_connection_name,
                    required=True,
                ),
                **self.serialize_url_param(
                    "namespaceName", self.ctx.args.namespace_name,
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
                    "api-version", "2017-04-01",
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
            _UpdateHelper._build_schema_authorization_rule_read(cls._schema_on_200)

            return cls._schema_on_200

    class HybridConnectionsCreateOrUpdateAuthorizationRule(AAZHttpOperation):
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
                "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Relay/namespaces/{namespaceName}/hybridConnections/{hybridConnectionName}/authorizationRules/{authorizationRuleName}",
                **self.url_parameters
            )

        @property
        def method(self):
            return "PUT"

        @property
        def error_format(self):
            return "ODataV4Format"

        @property
        def url_parameters(self):
            parameters = {
                **self.serialize_url_param(
                    "authorizationRuleName", self.ctx.args.name,
                    required=True,
                ),
                **self.serialize_url_param(
                    "hybridConnectionName", self.ctx.args.hybrid_connection_name,
                    required=True,
                ),
                **self.serialize_url_param(
                    "namespaceName", self.ctx.args.namespace_name,
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
                    "api-version", "2017-04-01",
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
            _UpdateHelper._build_schema_authorization_rule_read(cls._schema_on_200)

            return cls._schema_on_200

    class InstanceUpdateByJson(AAZJsonInstanceUpdateOperation):

        def __call__(self, *args, **kwargs):
            self._update_instance(self.ctx.vars.instance)

        def _update_instance(self, instance):
            _instance_value, _builder = self.new_content_builder(
                self.ctx.args,
                value=instance,
                typ=AAZObjectType
            )
            _builder.set_prop("properties", AAZObjectType, ".", typ_kwargs={"flags": {"required": True, "client_flatten": True}})

            properties = _builder.get(".properties")
            if properties is not None:
                properties.set_prop("rights", AAZListType, ".rights", typ_kwargs={"flags": {"required": True}})

            rights = _builder.get(".properties.rights")
            if rights is not None:
                rights.set_elements(AAZStrType, ".")

            return _instance_value

    class InstanceUpdateByGeneric(AAZGenericInstanceUpdateOperation):

        def __call__(self, *args, **kwargs):
            self._update_instance_by_generic(
                self.ctx.vars.instance,
                self.ctx.generic_update_args
            )


class _UpdateHelper:
    """Helper class for Update"""

    _schema_authorization_rule_read = None

    @classmethod
    def _build_schema_authorization_rule_read(cls, _schema):
        if cls._schema_authorization_rule_read is not None:
            _schema.id = cls._schema_authorization_rule_read.id
            _schema.name = cls._schema_authorization_rule_read.name
            _schema.properties = cls._schema_authorization_rule_read.properties
            _schema.type = cls._schema_authorization_rule_read.type
            return

        cls._schema_authorization_rule_read = _schema_authorization_rule_read = AAZObjectType()

        authorization_rule_read = _schema_authorization_rule_read
        authorization_rule_read.id = AAZStrType(
            flags={"read_only": True},
        )
        authorization_rule_read.name = AAZStrType(
            flags={"read_only": True},
        )
        authorization_rule_read.properties = AAZObjectType(
            flags={"required": True, "client_flatten": True},
        )
        authorization_rule_read.type = AAZStrType(
            flags={"read_only": True},
        )

        properties = _schema_authorization_rule_read.properties
        properties.rights = AAZListType(
            flags={"required": True},
        )

        rights = _schema_authorization_rule_read.properties.rights
        rights.Element = AAZStrType()

        _schema.id = cls._schema_authorization_rule_read.id
        _schema.name = cls._schema_authorization_rule_read.name
        _schema.properties = cls._schema_authorization_rule_read.properties
        _schema.type = cls._schema_authorization_rule_read.type


__all__ = ["Update"]