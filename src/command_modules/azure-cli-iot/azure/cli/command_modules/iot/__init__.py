# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.events import EVENT_INVOKER_POST_PARSE_ARGS
from knack.log import get_logger
from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import CliCommandType
import azure.cli.command_modules.iot._help  # pylint: disable=unused-import
from azure.cli.core.extension import extension_exists


def handler(ctx, **kwargs):
    cmd = kwargs.get('command', None)
    if cmd and cmd.startswith('iot'):
        if not extension_exists('azure-cli-iot-ext'):
            ran_before = ctx.config.getboolean('iot', 'first_run', fallback=False)
            if not ran_before:
                extension_text = """
Comprehensive IoT data-plane functionality is available
in the Azure IoT CLI Extension. For more info and install guide
go to https://github.com/Azure/azure-iot-cli-extension
"""
                logger = get_logger(__name__)
                logger.warning(extension_text)
                ctx.config.set_value('iot', 'first_run', 'yes')


class IoTCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        iot_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.iot.custom#{}')
        cli_ctx.register_event(EVENT_INVOKER_POST_PARSE_ARGS, handler)
        super(IoTCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                custom_command_type=iot_custom,
                                                min_profile='2017-03-10-profile')

    def load_command_table(self, args):
        from azure.cli.command_modules.iot.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.iot._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = IoTCommandsLoader
