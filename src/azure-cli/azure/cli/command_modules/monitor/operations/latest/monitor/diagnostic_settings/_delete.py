# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.command_modules.monitor.aaz.latest.monitor.diagnostic_settings._delete \
    import Delete as _DiagnosticSettingsDelete
from azure.cli.command_modules.monitor.operations.diagnostics_settings import (
    create_resource_parameters, update_resource_parameters,
)


class DiagnosticSettingsDelete(_DiagnosticSettingsDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        arg_schema = super()._build_arguments_schema(*args, **kwargs)
        create_resource_parameters(arg_schema, arg_group="Target Resource")
        return arg_schema

    def pre_operations(self):
        update_resource_parameters(self.ctx)
