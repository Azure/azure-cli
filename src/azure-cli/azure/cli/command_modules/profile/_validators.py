# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid

from azure.cli.core.util import should_disable_connection_verify
from knack.log import get_logger

logger = get_logger(__name__)


def _is_guid(guid):
    try:
        uuid.UUID(guid)
        return True
    except ValueError:
        return False


def validate_tenant(cmd, namespace):
    """
    Make sure tenant is a GUID. If domain name is provided, resolve to GUID.
    https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-protocols-oidc#fetch-the-openid-connect-metadata-document
    """
    if namespace.tenant is not None and not _is_guid(namespace.tenant):
        import requests
        active_directory_endpoint = cmd.cli_ctx.cloud.endpoints.active_directory
        url = '{}/{}/.well-known/openid-configuration'.format(active_directory_endpoint, namespace.tenant)
        metadata = requests.get(url, verify=not should_disable_connection_verify()).json()

        # Example issuer: https://sts.windows.net/72f988bf-86f1-41af-91ab-2d7cd011db47/
        tenant_id = metadata['issuer'].split("/")[3]

        logger.debug('Resolve tenant domain name %s to GUID %s', namespace.tenant, tenant_id)
        namespace.tenant = tenant_id
