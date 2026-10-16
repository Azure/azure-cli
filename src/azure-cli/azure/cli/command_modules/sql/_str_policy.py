# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Compatibility adapters for the generated STR commands."""

from azure.cli.core.aaz import AAZCommand, AAZHttpOperation
from azure.cli.core.azclierror import InvalidArgumentValueError

from .aaz.latest.sql.db.str_policy import Set as _DatabasePolicySet, Show as _DatabasePolicyShow
from .aaz.latest.sql.midb.short_term_retention_policy import (
    Set as _ManagedDatabasePolicySet, Show as _ManagedDatabasePolicyShow,
)
from .aaz.latest.sql.midb.short_term_retention_policy.restorable_dropped import (
    Set as _DroppedDatabasePolicySet, Show as _DroppedDatabasePolicyShow,
)


class _ShortTermRetentionPolicy(AAZCommand):
    def _handler(self, command_args):
        # Internal command_args bypass CLI parsing/defaults; None means omitted, not JSON null.
        args = {key: value for key, value in command_args.items() if value is not None}
        args.setdefault("policy_name", "default")
        return super()._handler(args)


class _PolicySetOperation(AAZHttpOperation):  # pylint: disable=abstract-method
    def __call__(self, *args, **kwargs):
        session = self.client.send_request(request=self.make_request(), stream=False, **kwargs)
        if session.http_response.status_code in (200, 202):
            # Keep ARM's final policy GET after Azure-AsyncOperation, rather than the
            # spec's Location result, which can report an inconsistent immutability status.
            return self.client.build_lro_polling(
                self.ctx.args.no_wait, session, self.on_200, self.on_error,
                path_format_arguments=self.url_parameters,
            )
        return self.on_error(session.http_response)


class DatabasePolicyShow(_ShortTermRetentionPolicy, _DatabasePolicyShow):
    pass


class DatabasePolicySet(_ShortTermRetentionPolicy, _DatabasePolicySet):
    class BackupShortTermRetentionPoliciesCreateOrUpdate(
            _PolicySetOperation, _DatabasePolicySet.BackupShortTermRetentionPoliciesCreateOrUpdate):
        @property
        def content(self):
            content = super().content
            properties = content["properties"]
            if "diffBackupIntervalInHours" in properties:
                # The Swagger number enum generates floats, but SQL requires integer JSON tokens.
                interval = properties["diffBackupIntervalInHours"]
                integer_interval = int(interval)
                if integer_interval != interval:
                    raise InvalidArgumentValueError("--diffbackup-hours must be a whole number of hours.")
                properties["diffBackupIntervalInHours"] = integer_interval
            return content


class ManagedDatabasePolicyShow(_ShortTermRetentionPolicy, _ManagedDatabasePolicyShow):
    pass


class ManagedDatabasePolicySet(_ShortTermRetentionPolicy, _ManagedDatabasePolicySet):
    class ManagedBackupShortTermRetentionPoliciesCreateOrUpdate(
            _PolicySetOperation, _ManagedDatabasePolicySet.ManagedBackupShortTermRetentionPoliciesCreateOrUpdate):
        pass


class DroppedDatabasePolicyShow(_ShortTermRetentionPolicy, _DroppedDatabasePolicyShow):
    pass


class DroppedDatabasePolicySet(_ShortTermRetentionPolicy, _DroppedDatabasePolicySet):
    class ManagedRestorableDroppedDatabaseBackupShortTermRetentionPoliciesCreateOrUpdate(
            _PolicySetOperation,
            _DroppedDatabasePolicySet.ManagedRestorableDroppedDatabaseBackupShortTermRetentionPoliciesCreateOrUpdate):
        pass
