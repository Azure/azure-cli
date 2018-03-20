# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
 
from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands.parameters import (
    get_resource_name_completion_list
)
from ._constants import (
    REGISTRY_RESOURCE_TYPE
)
from ._client_factory import cf_acr_builds

class AcrBuildCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        super(AcrBuildCommandsLoader, self).__init__(cli_ctx=cli_ctx)

    def load_command_table(self, _):
        from azure.cli.core.commands import CliCommandType

        acr_build_util = CliCommandType(
            operations_tmpl='azext_acrbuildext.build#{}',    
            client_factory=cf_acr_builds
        )

        with self.command_group('acr build', acr_build_util) as g:
            g.command('show-logs', 'acr_build_show_logs')
            g.command('', 'acr_queue') # TODO: it should be moved to acr command group once we can integrate the full sdk.
        return self.command_table

    def load_arguments(self, _):
        with self.argument_context('acr build') as c:
            c.argument('registry_name', options_list=['--registry', '-r'], help='The container registry. You can configure the default registry using `az configure --defaults acr=<registry name>`', completer=get_resource_name_completion_list(REGISTRY_RESOURCE_TYPE), configured_default='acr')
            c.argument('image_name', options_list=['--image', '-t'], help="The image repository and optionally a tag in the 'repository:tag' format.")
            c.argument('source_location', options_list=['--context', '-c'], help="The local source code directory path (eg, './src') or the url to a git repository (eg, 'https://github.com/docker/rootfs.git') or a remote tarball (eg, 'http://server/context.tar.gz').")
            c.argument('docker_file_path', options_list=['--file', '-f'], help="The relative path of the the docker file to the source code root folder (Default is 'Dockerfile').")
            c.argument('timeout', help='The build timeout in seconds.')
            c.argument('build_args', nargs='+', help='The space-separated build arguments in a format of <name>=<value>.')
            c.argument('secret_build_args', nargs='+', help='The space-separated secret build arguments in a format of <name>=<value>.')
            c.argument('no_logs', options_list=['--no-logs'], action='store_true', help='Do not show logs after successfully queuing the build.') 
        return self.argument_context

COMMAND_LOADER_CLS = AcrBuildCommandsLoader
