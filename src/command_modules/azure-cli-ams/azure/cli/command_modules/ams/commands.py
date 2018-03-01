# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from ._client_factory import cf_media

def load_command_table(self, _):
    
    def _not_found(message):
        def _inner_not_found(ex):
            from azure.mgmt.media.models.api_error import ApiErrorException
            from knack.util import CLIError

            if isinstance(ex, ApiErrorException) \
                    and ex.response is not None \
                    and ex.response.status_code == 404:
                raise CLIError(message)
            raise ex
        return _inner_not_found

    not_found_msg = "{}(s) not found. Please verify the resource(s), group or it's parent resources " \
                    "exist."
    ams_not_found_msg = not_found_msg.format('Media Service')

    ams_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.media.operations#MediaservicesOperations.{}',
        client_factory=cf_media,
        exception_handler=_not_found(ams_not_found_msg)
    )

    ams_encoding_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.media.operations#TransformsOperations.{}',
        client_factory=cf_media,
        exception_handler=_not_found(ams_not_found_msg)
    )

    ams_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.ams.custom#{}'
    )
    
    with self.command_group('ams', ams_sdk) as g:        
        g.command('show', 'get')
        g.command('list', 'list')
        g.custom_command('create', 'create_mediaservice', custom_command_type=ams_custom)

    with self.command_group('ams transform', ams_encoding_sdk) as g:        
        g.command('list', 'list')
        g.command('show', 'show')