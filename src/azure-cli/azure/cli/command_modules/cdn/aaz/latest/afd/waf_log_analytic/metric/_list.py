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
    "afd waf-log-analytic metric list",
)
class List(AAZCommand):
    """Get Waf related log analytics report for AFD profile.
    """

    _aaz_info = {
        "version": "2025-06-01",
        "resources": [
            ["mgmt-plane", "/subscriptions/{}/resourcegroups/{}/providers/microsoft.cdn/profiles/{}/getwafloganalyticsmetrics", "2025-06-01"],
        ]
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

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.profile_name = AAZStrArg(
            options=["--profile-name"],
            help="Name of the Azure Front Door Standard or Azure Front Door Premium profile which is unique within the resource group. which is unique within the resource group.",
            required=True,
        )
        _args_schema.resource_group = AAZResourceGroupNameArg(
            required=True,
        )
        _args_schema.actions = AAZListArg(
            options=["--actions"],
        )
        _args_schema.date_time_begin = AAZDateTimeArg(
            options=["--date-time-begin"],
            help="The start datetime.",
            required=True,
        )
        _args_schema.date_time_end = AAZDateTimeArg(
            options=["--date-time-end"],
            help="The end datetime.",
            required=True,
        )
        _args_schema.granularity = AAZStrArg(
            options=["--granularity"],
            help="The interval granularity.",
            required=True,
            enum={"P1D": "P1D", "PT1H": "PT1H", "PT5M": "PT5M"},
        )
        _args_schema.group_by = AAZListArg(
            options=["--group-by"],
        )
        _args_schema.metrics = AAZListArg(
            options=["--metrics"],
            required=True,
        )
        _args_schema.rule_types = AAZListArg(
            options=["--rule-types"],
        )

        actions = cls._args_schema.actions
        actions.Element = AAZStrArg(
            enum={"allow": "allow", "block": "block", "log": "log", "redirect": "redirect"},
        )

        group_by = cls._args_schema.group_by
        group_by.Element = AAZStrArg(
            enum={"customDomain": "customDomain", "httpStatusCode": "httpStatusCode"},
        )

        metrics = cls._args_schema.metrics
        metrics.Element = AAZStrArg(
            enum={"clientRequestCount": "clientRequestCount"},
        )

        rule_types = cls._args_schema.rule_types
        rule_types.Element = AAZStrArg(
            enum={"bot": "bot", "custom": "custom", "managed": "managed"},
        )
        return cls._args_schema

    def _execute_operations(self):
        self.pre_operations()
        self.LogAnalyticsGetWafLogAnalyticsMetrics(ctx=self.ctx)()
        self.post_operations()

    @register_callback
    def pre_operations(self):
        pass

    @register_callback
    def post_operations(self):
        pass

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result

    class LogAnalyticsGetWafLogAnalyticsMetrics(AAZHttpOperation):
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
                "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Cdn/profiles/{profileName}/getWafLogAnalyticsMetrics",
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
                    "actions", self.ctx.args.actions,
                ),
                **self.serialize_query_param(
                    "dateTimeBegin", self.ctx.args.date_time_begin,
                    required=True,
                ),
                **self.serialize_query_param(
                    "dateTimeEnd", self.ctx.args.date_time_end,
                    required=True,
                ),
                **self.serialize_query_param(
                    "granularity", self.ctx.args.granularity,
                    required=True,
                ),
                **self.serialize_query_param(
                    "groupBy", self.ctx.args.group_by,
                ),
                **self.serialize_query_param(
                    "metrics", self.ctx.args.metrics,
                    required=True,
                ),
                **self.serialize_query_param(
                    "ruleTypes", self.ctx.args.rule_types,
                ),
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

            _schema_on_200 = cls._schema_on_200
            _schema_on_200.date_time_begin = AAZStrType(
                serialized_name="dateTimeBegin",
            )
            _schema_on_200.date_time_end = AAZStrType(
                serialized_name="dateTimeEnd",
            )
            _schema_on_200.granularity = AAZStrType()
            _schema_on_200.series = AAZListType()

            series = cls._schema_on_200.series
            series.Element = AAZObjectType()

            _element = cls._schema_on_200.series.Element
            _element.data = AAZListType()
            _element.groups = AAZListType()
            _element.metric = AAZStrType()
            _element.unit = AAZStrType()

            data = cls._schema_on_200.series.Element.data
            data.Element = AAZObjectType()

            _element = cls._schema_on_200.series.Element.data.Element
            _element.date_time = AAZStrType(
                serialized_name="dateTime",
            )
            _element.value = AAZFloatType()

            groups = cls._schema_on_200.series.Element.groups
            groups.Element = AAZObjectType()

            _element = cls._schema_on_200.series.Element.groups.Element
            _element.name = AAZStrType()
            _element.value = AAZStrType()

            return cls._schema_on_200


class _ListHelper:
    """Helper class for List"""


__all__ = ["List"]
