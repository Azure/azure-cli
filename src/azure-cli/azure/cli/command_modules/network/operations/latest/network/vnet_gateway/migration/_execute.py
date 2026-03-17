# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.vnet_gateway.migration._execute import Execute as _VNetGatewayMigrationExecute


class VNetGatewayMigrationExecute(_VNetGatewayMigrationExecute):

    class VirtualNetworkGatewaysInvokeExecuteMigration(_VNetGatewayMigrationExecute.VirtualNetworkGatewaysInvokeExecuteMigration):

        # to handle the LRO response with no response body
        def __call__(self, *args, **kwargs):
            request = self.make_request()
            session = self.client.send_request(request=request, stream=False, **kwargs)
            if session.http_response.status_code in [202]:
                return self.client.build_lro_polling(
                    self.ctx.args.no_wait,
                    session,
                    lambda _: None,
                    self.on_error,
                    lro_options={"final-state-via": "location"},
                    path_format_arguments=self.url_parameters,
                )

            return self.on_error(session.http_response)
