# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""SDK-independent STR operations shared by the existing SQL command handlers."""

from azure.cli.core.aaz import (
    AAZBoolArg, AAZBoolType, AAZCommand, AAZHttpOperation, AAZIntArg,
    AAZIntType, AAZObjectType, AAZStrArg, AAZStrType,
)


class _ShortTermRetentionPolicy(AAZCommand):
    def _handler(self, command_args):
        # None means omitted in the existing Python handlers, not an explicit JSON null.
        super()._handler({key: value for key, value in command_args.items() if value is not None})

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        schema = super()._build_arguments_schema(*args, **kwargs)
        schema.resource_group_name = AAZStrArg(required=True)
        schema.parent_name = AAZStrArg(required=True)
        schema.database_name = AAZStrArg(required=True)
        schema.managed = AAZBoolArg(default=False)
        schema.deleted = AAZBoolArg(default=False)
        schema.retention_days = AAZIntArg()
        schema.diffbackup_hours = AAZIntArg()
        schema.lock_immutability = AAZBoolArg()
        return schema

    def _output(self, _result=None):
        return self.deserialize_output(self.ctx.vars.instance, client_flatten=True)


class ShortTermRetentionPolicyGet(_ShortTermRetentionPolicy):
    def _handler(self, command_args):
        super()._handler(command_args)
        _PolicyGet(ctx=self.ctx)()
        return self._output()


class ShortTermRetentionPolicySet(_ShortTermRetentionPolicy):
    AZ_SUPPORT_NO_WAIT = True

    def _handler(self, command_args):
        super()._handler(command_args)
        return self.build_lro_poller(self._execute_operations, self._output)

    def _execute_operations(self):
        yield _PolicySet(ctx=self.ctx)()


class _PolicyOperation(AAZHttpOperation):  # pylint: disable=abstract-method
    CLIENT_TYPE = "MgmtClient"

    @property
    def url(self):
        parent_type = "managedInstances" if self.ctx.args.managed else "servers"
        child_type = "restorableDroppedDatabases" if self.ctx.args.deleted else "databases"
        return self.client.format_url(
            "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}"
            "/providers/Microsoft.Sql/" + parent_type + "/{parentName}/" + child_type +
            "/{databaseName}/backupShortTermRetentionPolicies/default",
            **self.url_parameters
        )

    @property
    def url_parameters(self):
        return {
            **self.serialize_url_param("subscriptionId", self.ctx.subscription_id, required=True),
            **self.serialize_url_param("resourceGroupName", self.ctx.args.resource_group_name, required=True),
            **self.serialize_url_param("parentName", self.ctx.args.parent_name, required=True),
            **self.serialize_url_param("databaseName", self.ctx.args.database_name, required=True),
        }

    @property
    def query_parameters(self):
        return {"api-version": "2026-08-01-preview"}

    @property
    def header_parameters(self):
        return {"Accept": "application/json", "Content-Type": "application/json"}

    @property
    def error_format(self):
        return "ODataV4Format"

    def on_success(self, session):
        self.ctx.set_var(
            "instance", self.deserialize_http_content(session),
            schema_builder=self._build_response_schema,
        )

    @staticmethod
    def _build_response_schema():
        schema = AAZObjectType()
        schema.id = AAZStrType(flags={"read_only": True})
        schema.name = AAZStrType(flags={"read_only": True})
        schema.type = AAZStrType(flags={"read_only": True})
        schema.properties = AAZObjectType(flags={"client_flatten": True})
        properties = schema.properties
        properties.retention_days = AAZIntType(serialized_name="retentionDays")
        properties.diff_backup_interval_in_hours = AAZIntType(serialized_name="diffBackupIntervalInHours")
        properties.lock_immutability = AAZBoolType(serialized_name="lockImmutability")
        properties.immutability_status = AAZStrType(
            serialized_name="immutabilityStatus", flags={"read_only": True},
        )
        schema.system_data = AAZObjectType(serialized_name="systemData", flags={"read_only": True})
        system_data = schema.system_data
        system_data.created_by = AAZStrType(serialized_name="createdBy")
        system_data.created_by_type = AAZStrType(serialized_name="createdByType")
        system_data.created_at = AAZStrType(serialized_name="createdAt")
        system_data.last_modified_by = AAZStrType(serialized_name="lastModifiedBy")
        system_data.last_modified_by_type = AAZStrType(serialized_name="lastModifiedByType")
        system_data.last_modified_at = AAZStrType(serialized_name="lastModifiedAt")
        return schema


class _PolicyGet(_PolicyOperation):
    @property
    def method(self):
        return "GET"

    def __call__(self, *args, **kwargs):
        session = self.client.send_request(request=self.make_request(), stream=False, **kwargs)
        if session.http_response.status_code == 200:
            return self.on_success(session)
        return self.on_error(session.http_response)


class _PolicySet(_PolicyOperation):
    @property
    def method(self):
        return "PUT"

    @property
    def content(self):
        value, builder = self.new_content_builder(self.ctx.args, typ=AAZObjectType)
        builder.set_prop("properties", AAZObjectType)
        properties = builder.get(".properties")
        properties.set_prop("retentionDays", AAZIntType, ".retention_days")
        if not self.ctx.args.managed:
            properties.set_prop("diffBackupIntervalInHours", AAZIntType, ".diffbackup_hours")
        if not self.ctx.args.deleted:
            properties.set_prop("lockImmutability", AAZBoolType, ".lock_immutability")
        return self.serialize_content(value)

    def __call__(self, *args, **kwargs):
        session = self.client.send_request(request=self.make_request(), stream=False, **kwargs)
        if session.http_response.status_code in (200, 202):
            return self.client.build_lro_polling(
                self.ctx.args.no_wait, session, self.on_success, self.on_error,
                lro_options={"final-state-via": "location"},
                path_format_arguments=self.url_parameters,
            )
        return self.on_error(session.http_response)
