# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

from azure.cli.command_modules.redis._help import helps  # pylint: disable=unused-import


class RedisCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        from azure.cli.command_modules.redis._client_factory import cf_redis
        redis_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.redis.custom#{}',
            client_factory=cf_redis)
        super(RedisCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                  resource_type=ResourceType.MGMT_REDIS,
                                                  custom_command_type=redis_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.redis.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.redis._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = RedisCommandsLoader
