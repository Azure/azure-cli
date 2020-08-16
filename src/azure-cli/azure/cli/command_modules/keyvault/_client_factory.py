# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def keyvault_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_KEYVAULT)


def keyvault_client_vaults_factory(cli_ctx, _):
    return keyvault_client_factory(cli_ctx).vaults


def keyvault_client_private_endpoint_connections_factory(cli_ctx, _):
    return keyvault_client_factory(cli_ctx).private_endpoint_connections


def keyvault_client_private_link_resources_factory(cli_ctx, _):
    return keyvault_client_factory(cli_ctx).private_link_resources


def keyvault_data_plane_factory(cli_ctx, _):
    from azure.keyvault import KeyVaultAuthentication, KeyVaultClient
    from azure.cli.core.profiles import ResourceType, get_api_version
    from azure.cli.core.util import should_disable_connection_verify

    version = str(get_api_version(cli_ctx, ResourceType.DATA_KEYVAULT))

    def get_token(server, resource, scope):  # pylint: disable=unused-argument
        import adal
        from azure.cli.core._profile import Profile
        try:
            return Profile(cli_ctx=cli_ctx).get_raw_token(resource)[0]
        except adal.AdalError as err:
            from knack.util import CLIError
            # pylint: disable=no-member
            if (hasattr(err, 'error_response') and
                    ('error_description' in err.error_response) and
                    ('AADSTS70008:' in err.error_response['error_description'])):
                raise CLIError(
                    "Credentials have expired due to inactivity. Please run 'az login'")
            raise CLIError(err)

    client = KeyVaultClient(KeyVaultAuthentication(get_token), api_version=version)

    # HACK, work around the fact that KeyVault library does't take confiuration object on constructor
    # which could be used to turn off the verifiaction. Remove this once we migrate to new data plane library
    # pylint: disable=protected-access
    if hasattr(client, '_client') and hasattr(client._client, 'config'):
        verify = not should_disable_connection_verify()
        client._client.config.connection.verify = verify
    else:
        from knack.log import get_logger
        logger = get_logger(__name__)
        logger.info('Could not find the configuration object to turn off the verification if needed')

    return client
