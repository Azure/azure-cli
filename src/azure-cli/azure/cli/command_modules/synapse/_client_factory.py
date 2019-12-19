# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def synapse_client_factory(cli_ctx, **_):
    pass


def synapse_data_plane_factory(cli_ctx, _):
    from azure.synapse import SynapseClient
    from azure.cli.core.profiles import ResourceType, get_api_version
    from msrestazure.azure_active_directory import AADTokenCredentials

    version = str(get_api_version(cli_ctx, ResourceType.DATA_SYNAPSE))

    def get_token(server, resource, scope): # pylint: disable=unused-argument
        import adal
        from azure.cli.core._profile import Profile
        try:
            return Profile(cli_ctx=cli_ctx).get_raw_token(resource)[0]
        except adal.AdalError as err:
            from knack.util import CLIError
            #pylint: disable=no-member
            if(hasattr(err, 'error_response') and
                    ('error_description' in err.error_response) and
                    ('AADSTS70008:' in err.error_response['error_description'])):
                raise CLIError(
                    "Credentials have expired due to inactivity. Please run 'az login'")
            raise CLIError(err)

    client = SynapseClient(AADTokenCredentials(get_token()),"dev.azuresynapse.net")

    return client

def cf_synapse_spark_batch(cli_ctx, *_, **__):
    return synapse_data_plane_factory(cli_ctx).spark_batch

def cf_synapse_spark_session(cli_ctx, *_, **__):
    return synapse_data_plane_factory(cli_ctx).spark_session

