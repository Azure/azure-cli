# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-import

from azure.cli.command_modules.policyinsights._help import helps
from azure.cli.core import AzCommandsLoader


class PolicyInsightsCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        from ._exception_handler import policy_insights_exception_handler

        policyinsights_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.policyinsights.custom#{}',
            exception_handler=policy_insights_exception_handler)

        super().__init__(
            cli_ctx=cli_ctx,
            resource_type=ResourceType.MGMT_POLICYINSIGHTS,
            custom_command_type=policyinsights_custom)

    def load_command_table(self, args):
        from .commands import load_command_table
        from azure.cli.core.aaz import load_aaz_command_table
        try:
            from . import aaz
        except ImportError:
            aaz = None
        if aaz:
            load_aaz_command_table(
                loader=self,
                aaz_pkg_name=aaz.__name__,
                args=args
            )

        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from ._params import load_arguments

        load_arguments(self, command)


COMMAND_LOADER_CLS = PolicyInsightsCommandsLoader
