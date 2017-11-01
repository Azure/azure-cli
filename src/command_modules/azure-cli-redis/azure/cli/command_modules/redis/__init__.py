# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

from azure.cli.command_modules.redis._help import helps


class RedisCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.sdk.util import CliCommandType
        from azure.cli.command_modules.redis._client_factory import cf_redis
        redis_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.redis.custom#{}',
            client_factory=cf_redis)
        super(RedisCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                  min_profile='2017-03-10-profile',
                                                  custom_command_type=redis_custom)
        self.module_name = __name__

    def load_command_table(self, args):
        super(RedisCommandsLoader, self).load_command_table(args)
        from azure.cli.command_modules.redis.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        super(RedisCommandsLoader, self).load_arguments(command)
        from azure.cli.command_modules.redis._params import load_arguments
        load_arguments(self, command)

COMMAND_LOADER_CLS = RedisCommandsLoader
