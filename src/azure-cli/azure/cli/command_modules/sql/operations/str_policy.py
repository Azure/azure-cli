# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Customizations of the generated STR commands."""

from azure.cli.core.azclierror import InvalidArgumentValueError

from ..aaz.latest.sql.db.str_policy import Set as _DatabasePolicySet, Show as _DatabasePolicyShow
from ..aaz.latest.sql.midb.short_term_retention_policy import (
    Set as _ManagedDatabasePolicySet, Show as _ManagedDatabasePolicyShow,
)
from ..aaz.latest.sql.midb.short_term_retention_policy.restorable_dropped import (
    Set as _DroppedDatabasePolicySet, Show as _DroppedDatabasePolicyShow,
)


def _normalize_arguments(command_args):
    args = {key: value for key, value in command_args.items() if value is not None}
    args.setdefault("policy_name", "default")
    return args


def _execute_policy_update(operation, **kwargs):
    session = operation.client.send_request(request=operation.make_request(), stream=False, **kwargs)
    if session.http_response.status_code in (200, 202):
        return operation.client.build_lro_polling(
            operation.ctx.args.no_wait, session, operation.on_200, operation.on_error,
            path_format_arguments=operation.url_parameters,
        )
    return operation.on_error(session.http_response)


class DatabasePolicyShow(_DatabasePolicyShow):
    def _handler(self, command_args):
        return super()._handler(_normalize_arguments(command_args))


class DatabasePolicySet(_DatabasePolicySet):
    def _handler(self, command_args):
        return super()._handler(_normalize_arguments(command_args))

    class BackupShortTermRetentionPoliciesCreateOrUpdate(
            _DatabasePolicySet.BackupShortTermRetentionPoliciesCreateOrUpdate):
        def __call__(self, *args, **kwargs):
            return _execute_policy_update(self, **kwargs)

        @property
        def content(self):
            content = super().content
            properties = content["properties"]
            if "diffBackupIntervalInHours" in properties:
                interval = properties["diffBackupIntervalInHours"]
                integer_interval = int(interval)
                if integer_interval != interval:
                    raise InvalidArgumentValueError("--diffbackup-hours must be a whole number of hours.")
                properties["diffBackupIntervalInHours"] = integer_interval
            return content


class ManagedDatabasePolicyShow(_ManagedDatabasePolicyShow):
    def _handler(self, command_args):
        return super()._handler(_normalize_arguments(command_args))


class ManagedDatabasePolicySet(_ManagedDatabasePolicySet):
    def _handler(self, command_args):
        return super()._handler(_normalize_arguments(command_args))

    class ManagedBackupShortTermRetentionPoliciesCreateOrUpdate(
            _ManagedDatabasePolicySet.ManagedBackupShortTermRetentionPoliciesCreateOrUpdate):
        def __call__(self, *args, **kwargs):
            return _execute_policy_update(self, **kwargs)


class DroppedDatabasePolicyShow(_DroppedDatabasePolicyShow):
    def _handler(self, command_args):
        return super()._handler(_normalize_arguments(command_args))


class DroppedDatabasePolicySet(_DroppedDatabasePolicySet):
    def _handler(self, command_args):
        return super()._handler(_normalize_arguments(command_args))

    class ManagedRestorableDroppedDatabaseBackupShortTermRetentionPoliciesCreateOrUpdate(
            _DroppedDatabasePolicySet.ManagedRestorableDroppedDatabaseBackupShortTermRetentionPoliciesCreateOrUpdate):
        def __call__(self, *args, **kwargs):
            return _execute_policy_update(self, **kwargs)
