# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.botservice._client_factory import (
    get_botservice_management_client,
    get_botChannels_client,
    get_botOperations_client,
    get_botConnections_client)
from azure.cli.command_modules.botservice._exception_handler import bot_exception_handler


def load_command_table(self, _):
    botOperations_commandType = CliCommandType(
        operations_tmpl='azure.mgmt.botservice.operations.bots_operations#BotsOperations.{}',  # pylint: disable=line-too-long
        client_factory=get_botservice_management_client,
        exception_handler=bot_exception_handler
    )

    botServices_commandType = CliCommandType(
        operations_tmpl='azure.mgmt.botservice.operations.bots_operations#BotsOperations.{}',  # pylint: disable=line-too-long
        client_factory=get_botOperations_client,
        exception_handler=bot_exception_handler
    )

    botConnections_commandType = CliCommandType(
        operations_tmpl='azure.mgmt.botservice.operations.bot_connection_operations#BotConnectionOperations.{}',  # pylint: disable=line-too-long
        client_factory=get_botConnections_client,
        exception_handler=bot_exception_handler
    )

    channelOperations_commandType = CliCommandType(
        operations_tmpl='azure.cli.command_modules.botservice.channel_operations#channelOperationsInstance.{}',  # pylint: disable=line-too-long
        client_factory=get_botChannels_client,
        exception_handler=bot_exception_handler
    )

    channelOperationsCreate_commandType = CliCommandType(
        operations_tmpl='azure.cli.command_modules.botservice.channel_operations#{}',  # pylint: disable=line-too-long
        client_factory=get_botChannels_client,
        exception_handler=bot_exception_handler
    )

    updateBotService_commandType = CliCommandType(
        operations_tmpl='azure.cli.command_modules.botservice.custom#{}',
        client_factory=get_botservice_management_client,
        exception_handler=bot_exception_handler
    )

    with self.command_group('bot', botOperations_commandType) as g:
        g.custom_command('create', 'create')
        g.custom_command('publish', 'publish_app')
        g.custom_command('download', 'download_app')
        g.custom_command('prepare-publish', 'prepare_publish')

    with self.command_group('bot', botServices_commandType) as g:
        g.command('show', 'get')
        g.command('delete', 'delete')

    with self.command_group('bot authsetting', botConnections_commandType) as g:
        g.command('list', 'list_by_bot_service')
        g.command('show', 'get')
        g.command('delete', 'delete')

    with self.command_group('bot', botServices_commandType) as g:
        g.generic_update_command('update', setter_name='update', setter_type=updateBotService_commandType)

    with self.command_group('bot authsetting', botOperations_commandType) as g:
        g.custom_command('create', 'create_connection')
        g.custom_command('list-providers', 'get_service_providers')

    for channel in ['facebook', 'email', 'msteams', 'skype', 'kik', 'directline', 'telegram', 'sms', 'slack']:
        with self.command_group('bot {}'.format(channel), channelOperationsCreate_commandType) as g:
            g.command('create', '{}_create'.format(channel))

        with self.command_group('bot {}'.format(channel), channelOperations_commandType) as g:
            g.command('show', '{}_get'.format(channel))
            g.command('delete', '{}_delete'.format(channel))

    with self.command_group('bot webchat', channelOperations_commandType) as g:
        g.command('show', 'webchat_get')
