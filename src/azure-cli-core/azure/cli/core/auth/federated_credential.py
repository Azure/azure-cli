# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Get OIDC ID tokens from CI/CD providers for `az login --federated-credential-provider`.

The token is fetched on demand rather than passed in once, so long-running jobs can keep getting new access tokens
after the first ID token expires.
"""

import os
import threading

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)

PROVIDER_GITHUB = 'github'
PROVIDER_AZURE_PIPELINES = 'azure-pipelines'
PROVIDERS = (PROVIDER_GITHUB, PROVIDER_AZURE_PIPELINES)

# MSAL may invoke the client_assertion callback from multiple threads, so token requests are serialized.
_federated_id_token_lock = threading.Lock()

# (connect, read) timeouts in seconds for OIDC ID token requests, so a network stall fails fast instead of
# hanging token acquisition on a long-running CI job.
_OIDC_HTTP_TIMEOUT = (10, 30)

_DEFAULT_AAD_TOKEN_EXCHANGE_AUDIENCE = 'api://AzureADTokenExchange'

_GITHUB_DISPLAY_NAME = 'GitHub Actions'
_GITHUB_REQUEST_URL_ENV = 'ACTIONS_ID_TOKEN_REQUEST_URL'
_GITHUB_REQUEST_TOKEN_ENV = 'ACTIONS_ID_TOKEN_REQUEST_TOKEN'

_ADO_DISPLAY_NAME = 'Azure Pipelines'
# Predefined variable System.OidcRequestUri.
_ADO_REQUEST_URL_ENV = 'SYSTEM_OIDCREQUESTURI'
# Predefined variable System.AccessToken. It's a secret, so YAML pipelines must map it into the step's env.
_ADO_REQUEST_TOKEN_ENV = 'SYSTEM_ACCESSTOKEN'
# Set by the AzureCLI@2 task to the ID of the service connection the task runs with.
_ADO_SERVICE_CONNECTION_ENV = 'AZURESUBSCRIPTION_SERVICE_CONNECTION_ID'
_ADO_DEFAULT_API_VERSION = '7.1'


def get_federated_id_token(provider, audience=None):
    """Get a fresh OIDC ID token from a CI/CD provider.

    Used as MSAL's client_assertion callback for `az login --federated-credential-provider`, so MSAL can get a new
    ID token whenever it needs a new access token. audience only applies to GitHub Actions; Azure Pipelines sets
    the token's audience itself.
    """
    with _federated_id_token_lock:
        if provider == PROVIDER_GITHUB:
            return _get_id_token_github(audience or _DEFAULT_AAD_TOKEN_EXCHANGE_AUDIENCE)
        if provider == PROVIDER_AZURE_PIPELINES:
            return _get_id_token_azure_pipelines()
    raise CLIError(f"Unknown federated credential provider '{provider}'. Supported values: {', '.join(PROVIDERS)}.")


def _require_env(provider, names, hint):
    """Return the values of the environment variables in names, or raise a CLIError listing any that are missing."""
    values = [os.environ.get(name) for name in names]
    missing = [name for name, value in zip(names, values) if not value]
    if missing:
        raise CLIError("'--federated-credential-provider {}' requires environment variable(s): {}. {}"
                       .format(provider, ', '.join(missing), hint))
    return values


def _request_id_token(display_name, method, url, headers, token_field):
    """Send an ID token request to the provider and return the token from the JSON response field."""
    import requests
    try:
        response = method(url, headers=headers, timeout=_OIDC_HTTP_TIMEOUT)
    except requests.exceptions.Timeout:
        raise CLIError(f'Timed out requesting an ID token from {display_name}. Please retry.')
    except requests.exceptions.RequestException as ex:
        raise CLIError(f'Failed to reach the {display_name} OIDC endpoint: {ex}')
    if not response.ok:
        raise CLIError(f'Failed to retrieve an ID token from {display_name}: '
                       f'{response.status_code} {response.reason}')
    try:
        body = response.json()
    except ValueError:
        body = None
    id_token = body.get(token_field) if isinstance(body, dict) else None
    if not id_token:
        raise CLIError(f'{display_name} OIDC endpoint did not return an ID token.')
    # Never log the token value itself.
    logger.debug('Retrieved a fresh ID token from %s.', display_name)
    return id_token


def _get_id_token_github(audience):
    """Get an OIDC ID token from GitHub Actions.

    GitHub only sets the request URL and token when the workflow or job has the 'id-token: write' permission.
    https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-cloud-providers
    """
    from urllib.parse import quote
    import requests

    request_url, request_token = _require_env(
        PROVIDER_GITHUB,
        (_GITHUB_REQUEST_URL_ENV, _GITHUB_REQUEST_TOKEN_ENV),
        "Grant the workflow or job the 'id-token: write' permission.")

    # The request URL normally already has a query string (api-version), so append with the right separator.
    separator = '&' if '?' in request_url else '?'
    url = f"{request_url}{separator}audience={quote(audience, safe='')}"
    headers = {
        'Authorization': f'bearer {request_token}',
        'Accept': 'application/json; api-version=2.0',
        'Content-Type': 'application/json'
    }
    return _request_id_token(_GITHUB_DISPLAY_NAME, requests.get, url, headers, 'value')


def _get_id_token_azure_pipelines():
    """Get an OIDC ID token for a service connection from Azure Pipelines.

    Calls the pipeline's oidctoken API, authenticated with System.AccessToken. The API has no audience parameter.
    Inputs come from the environment:

    - SYSTEM_OIDCREQUESTURI: predefined variable System.OidcRequestUri
    - SYSTEM_ACCESSTOKEN: predefined variable System.AccessToken, which YAML pipelines must map into the step's env
    - AZURESUBSCRIPTION_SERVICE_CONNECTION_ID: set by the AzureCLI@2 task

    https://learn.microsoft.com/azure/devops/pipelines/build/variables
    https://learn.microsoft.com/rest/api/azure/devops/distributedtask/oidctoken/create
    """
    from urllib.parse import quote, parse_qsl, urlencode, urlsplit
    import requests

    request_url, request_token, service_connection_id = _require_env(
        PROVIDER_AZURE_PIPELINES,
        (_ADO_REQUEST_URL_ENV, _ADO_REQUEST_TOKEN_ENV, _ADO_SERVICE_CONNECTION_ENV),
        "Map System.AccessToken into the step's env as SYSTEM_ACCESSTOKEN, and run az in an AzureCLI@2 task, "
        "which sets AZURESUBSCRIPTION_SERVICE_CONNECTION_ID.")

    parts = urlsplit(request_url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if key != 'serviceConnectionId']
    if not any(key == 'api-version' for key, _ in query):
        query.append(('api-version', _ADO_DEFAULT_API_VERSION))
    query.append(('serviceConnectionId', service_connection_id))
    url = parts._replace(path=parts.path.rstrip('/'), query=urlencode(query, quote_via=quote)).geturl()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'bearer {request_token}',
        # Prevents the service from responding with a redirect HTTP status code.
        'X-TFS-FedAuthRedirect': 'Suppress',
    }
    return _request_id_token(_ADO_DISPLAY_NAME, requests.post, url, headers, 'oidcToken')
