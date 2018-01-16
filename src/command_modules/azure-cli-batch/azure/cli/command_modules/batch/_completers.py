# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer


@Completer
def load_node_agent_skus(cmd, prefix, namespace):  # pylint: disable=unused-argument
    from msrest.exceptions import ClientRequestError
    from azure.batch.models import BatchErrorException
    from azure.cli.command_modules.batch._client_factory import account_client_factory
    all_images = []
    client_creds = {}
    client_creds['account_name'] = cmd.cli_ctx.config.get('batch', 'account', None)
    client_creds['account_key'] = cmd.cli_ctx.config.get('batch', 'access_key', None)
    client_creds['account_endpoint'] = cmd.cli_ctx.config.get('batch', 'endpoint', None)
    try:
        client = account_client_factory(cmd.cli_ctx, client_creds)
        skus = client.list_node_agent_skus()
        for sku in skus:
            for image in sku['verifiedImageReferences']:
                all_images.append("{}:{}:{}:{}".format(
                    image['publisher'],
                    image['offer'],
                    image['sku'],
                    image['version']))
        return all_images
    except (ClientRequestError, BatchErrorException):
        return []
