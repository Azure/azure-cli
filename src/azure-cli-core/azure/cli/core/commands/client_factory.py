# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import _debug
from azure.cli.core.auth.util import resource_to_scopes
from azure.cli.core.extension import EXTENSIONS_MOD_PREFIX
from azure.cli.core.profiles import ResourceType, CustomResourceType, get_api_version, get_sdk
from azure.cli.core.profiles._shared import get_client_class, SDKProfile
from azure.cli.core.util import get_az_user_agent, is_track2
from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


def _is_vendored_sdk_path(path_comps):
    return len(path_comps) >= 5 and path_comps[4] == 'vendored_sdks'


def resolve_client_arg_name(operation, kwargs):
    if not isinstance(operation, str):
        raise CLIError("operation should be type 'str'. Got '{}'".format(type(operation)))
    if 'client_arg_name' in kwargs:
        logger.info("Keyword 'client_arg_name' is deprecated and should be removed.")
        return kwargs['client_arg_name']
    path, op_path = operation.split('#', 1)

    path_comps = path.split('.')
    if path_comps[0] == 'azure':
        if path_comps[1] != 'cli' or _is_vendored_sdk_path(path_comps):
            # Public SDK: azure.mgmt.resource... (mgmt-plane) or azure.storage.blob... (data-plane)
            # Vendored SDK: azure.cli.command_modules.keyvault.vendored_sdks...
            client_arg_name = 'self'
        else:
            # CLI custom method: azure.cli.command_modules.resource...
            client_arg_name = 'client'
    elif path_comps[0].startswith(EXTENSIONS_MOD_PREFIX):
        # for CLI extensions
        # SDK method: the operation takes the form '<class name>.<method_name>'
        # custom method: the operation takes the form '<method_name>'
        op_comps = op_path.split('.')
        client_arg_name = 'self' if len(op_comps) > 1 else 'client'
    else:
        raise ValueError('Unrecognized operation: {}'.format(operation))
    return client_arg_name


def get_mgmt_service_client(cli_ctx, client_or_resource_type, subscription_id=None, api_version=None,
                            aux_subscriptions=None, aux_tenants=None, **kwargs):
    """
     :params subscription_id: the current account's subscription
     :param aux_subscriptions: mainly for cross tenant scenarios, say vnet peering.
    """
    if not subscription_id and 'subscription_id' in cli_ctx.data:
        subscription_id = cli_ctx.data['subscription_id']

    sdk_profile = None
    if isinstance(client_or_resource_type, (ResourceType, CustomResourceType)):
        # Get the versioned client
        client_type = get_client_class(client_or_resource_type)
        api_version = api_version or get_api_version(cli_ctx, client_or_resource_type, as_sdk_profile=True)
        if isinstance(api_version, SDKProfile):
            sdk_profile = api_version.profile
            api_version = None
    else:
        # Get the non-versioned client
        client_type = client_or_resource_type
    client, _ = _get_mgmt_service_client(cli_ctx, client_type, subscription_id=subscription_id,
                                         api_version=api_version, sdk_profile=sdk_profile,
                                         aux_subscriptions=aux_subscriptions,
                                         aux_tenants=aux_tenants,
                                         **kwargs)
    return client


def get_subscription_service_client(cli_ctx):
    return _get_mgmt_service_client(cli_ctx, get_client_class(ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS),
                                    subscription_bound=False,
                                    api_version=get_api_version(cli_ctx, ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS))


def configure_common_settings(cli_ctx, client):
    client = _debug.change_ssl_cert_verification(client)

    client.config.enable_http_logger = True

    client.config.add_user_agent(get_az_user_agent())

    try:
        command_ext_name = cli_ctx.data['command_extension_name']
        if command_ext_name:
            client.config.add_user_agent("CliExtension/{}".format(command_ext_name))
    except KeyError:
        pass

    # Prepare CommandName header
    command_name_suffix = ';completer-request' if cli_ctx.data['completer_active'] else ''
    cli_ctx.data['headers']['CommandName'] = "{}{}".format(cli_ctx.data['command'], command_name_suffix)

    # Prepare ParameterSetName header
    if cli_ctx.data.get('safe_params'):
        cli_ctx.data['headers']['ParameterSetName'] = ' '.join(cli_ctx.data['safe_params'])

    # Prepare x-ms-client-request-id header
    client.config.generate_client_request_id = 'x-ms-client-request-id' not in cli_ctx.data['headers']

    logger.debug("Adding custom headers to the client:")

    for header, value in cli_ctx.data['headers'].items():
        # msrest doesn't print custom headers in debug log, so CLI should do that
        logger.debug("    '%s': '%s'", header, value)
        # We are working with the autorest team to expose the add_header functionality of the generated client to avoid
        # having to access private members
        client._client.add_header(header, value)  # pylint: disable=protected-access


def _prepare_client_kwargs_track2(cli_ctx):
    """Prepare kwargs for Track 2 SDK client."""
    client_kwargs = {}

    # Prepare connection_verify to change SSL verification behavior, used by ConnectionConfiguration
    client_kwargs.update(_debug.change_ssl_cert_verification_track2())

    # Prepare User-Agent header, used by UserAgentPolicy
    client_kwargs['user_agent'] = get_az_user_agent()

    try:
        command_ext_name = cli_ctx.data['command_extension_name']
        if command_ext_name:
            client_kwargs['user_agent'] += "CliExtension/{}".format(command_ext_name)
    except KeyError:
        pass

    # Prepare custom headers, used by HeadersPolicy
    headers = dict(cli_ctx.data['headers'])

    # - Prepare CommandName header
    command_name_suffix = ';completer-request' if cli_ctx.data['completer_active'] else ''
    headers['CommandName'] = "{}{}".format(cli_ctx.data['command'], command_name_suffix)

    # - Prepare ParameterSetName header
    if cli_ctx.data.get('safe_params'):
        headers['ParameterSetName'] = ' '.join(cli_ctx.data['safe_params'])

    client_kwargs['headers'] = headers

    # Prepare x-ms-client-request-id header, used by RequestIdPolicy
    if 'x-ms-client-request-id' in cli_ctx.data['headers']:
        client_kwargs['request_id'] = cli_ctx.data['headers']['x-ms-client-request-id']

    # Replace NetworkTraceLoggingPolicy to redact 'Authorization' and 'x-ms-authorization-auxiliary' headers.
    #   NetworkTraceLoggingPolicy: log raw network trace, with all headers.
    from azure.cli.core.sdk.policies import SafeNetworkTraceLoggingPolicy
    client_kwargs['logging_policy'] = SafeNetworkTraceLoggingPolicy()

    # Disable ARMHttpLoggingPolicy.
    #   ARMHttpLoggingPolicy: Only log allowed information.
    from azure.core.pipeline.policies import SansIOHTTPPolicy
    client_kwargs['http_logging_policy'] = SansIOHTTPPolicy()

    return client_kwargs


def _prepare_mgmt_client_kwargs_track2(cli_ctx, cred):
    """Prepare kwargs for Track 2 SDK mgmt client."""
    client_kwargs = _prepare_client_kwargs_track2(cli_ctx)

    # Enable CAE support in mgmt SDK
    from azure.core.pipeline.policies import BearerTokenCredentialPolicy

    # Track 2 SDK maintains `scopes` and passes `scopes` to get_token.
    scopes = resource_to_scopes(cli_ctx.cloud.endpoints.active_directory_resource_id)
    policy = BearerTokenCredentialPolicy(cred, *scopes)

    client_kwargs['credential_scopes'] = scopes
    client_kwargs['authentication_policy'] = policy

    # Track 2 currently lacks the ability to take external credentials.
    #   https://github.com/Azure/azure-sdk-for-python/issues/8313
    # As a temporary workaround, manually add external tokens to 'x-ms-authorization-auxiliary' header.
    #   https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/authenticate-multi-tenant
    if hasattr(cred, "get_auxiliary_tokens"):
        aux_tokens = cred.get_auxiliary_tokens(*scopes)
        if aux_tokens:
            # Hard-code scheme to 'Bearer' as _BearerTokenCredentialPolicyBase._update_headers does.
            client_kwargs['headers']['x-ms-authorization-auxiliary'] = \
                ', '.join("Bearer {}".format(token.token) for token in aux_tokens)

    return client_kwargs


def _get_mgmt_service_client(cli_ctx,
                             client_type,
                             subscription_bound=True,
                             subscription_id=None,
                             api_version=None,
                             base_url_bound=True,
                             resource=None,
                             sdk_profile=None,
                             aux_subscriptions=None,
                             aux_tenants=None,
                             **kwargs):
    from azure.cli.core._profile import Profile
    logger.debug('Getting management service client client_type=%s', client_type.__name__)

    # Track 1 SDK doesn't maintain the `resource`. The `resource` of the token is the one passed to
    # get_login_credentials.
    resource = resource or cli_ctx.cloud.endpoints.active_directory_resource_id
    profile = Profile(cli_ctx=cli_ctx)
    cred, subscription_id, _ = profile.get_login_credentials(subscription_id=subscription_id, resource=resource,
                                                             aux_subscriptions=aux_subscriptions,
                                                             aux_tenants=aux_tenants)

    client_kwargs = {}
    if base_url_bound:
        client_kwargs = {'base_url': cli_ctx.cloud.endpoints.resource_manager}
    if api_version:
        client_kwargs['api_version'] = api_version
    if sdk_profile:
        client_kwargs['profile'] = sdk_profile
    if kwargs:
        client_kwargs.update(kwargs)

    if is_track2(client_type):
        client_kwargs.update(_prepare_mgmt_client_kwargs_track2(cli_ctx, cred))

    if subscription_bound:
        client = client_type(cred, subscription_id, **client_kwargs)
    else:
        client = client_type(cred, **client_kwargs)

    if not is_track2(client):
        configure_common_settings(cli_ctx, client)

    return client, subscription_id


def get_data_service_client(cli_ctx, service_type, storage_account_url, account_name, account_key, connection_string=None,
                            sas_token=None, socket_timeout=None, token_credential=None, endpoint_suffix=None,
                            location_mode=None):
    logger.debug('Getting data service client service_type=%s', service_type.__name__)
    try:
        client_kwargs = {'storage_account_url': storage_account_url,
                         'account_name': account_name,
                         'account_key': account_key,
                         'connection_string': connection_string,
                         'sas_token': sas_token}
        if socket_timeout:
            client_kwargs['socket_timeout'] = socket_timeout
        if token_credential:
            client_kwargs['token_credential'] = token_credential
        if endpoint_suffix:
            client_kwargs['endpoint_suffix'] = endpoint_suffix
        client = service_type(**client_kwargs)
        if location_mode:
            client.location_mode = location_mode
    except ValueError as exc:
        _ERROR_STORAGE_MISSING_INFO = get_sdk(cli_ctx, ResourceType.DATA_STORAGE,
                                              'common._error#_ERROR_STORAGE_MISSING_INFO')
        if _ERROR_STORAGE_MISSING_INFO in str(exc):
            raise ValueError(exc)
        raise CLIError('Unable to obtain data client. Check your connection parameters.')
    # TODO: enable Fiddler
    client.request_callback = _get_add_headers_callback(cli_ctx)
    return client


def get_subscription_id(cli_ctx):
    from azure.cli.core._profile import Profile
    if not cli_ctx.data.get('subscription_id'):
        cli_ctx.data['subscription_id'] = Profile(cli_ctx=cli_ctx).get_subscription_id()
    return cli_ctx.data['subscription_id']


def _get_add_headers_callback(cli_ctx):

    def _add_headers(request):
        agents = [request.headers['User-Agent'], get_az_user_agent()]
        request.headers['User-Agent'] = ' '.join(agents)

        try:
            request.headers.update(cli_ctx.data['headers'])
        except KeyError:
            pass

    return _add_headers


prepare_client_kwargs_track2 = _prepare_client_kwargs_track2
