from azure.core.configuration import Configuration
from azure.mgmt.core import ARMPipelineClient


registered_clients = {}


def register_client(name):
    def decorator(cls):
        if name in registered_clients:
            assert registered_clients[name] == cls
        else:
            registered_clients[name] = cls
        return cls
    return decorator


@register_client("MgmtClient")
class AAZMgmtClient(ARMPipelineClient):

    class _Configuration(Configuration):
        def __init__(self, credential, credential_scopes, **kwargs):
            if credential is None:
                raise ValueError("Parameter 'credential' must not be None.")
            if not credential_scopes:
                raise ValueError("Parameter 'credential_scopes' is required.")
            super().__init__(**kwargs)
            self.credential = credential
            self.credential_scopes = credential_scopes
            self._configure(**kwargs)

        def _configure(
                self,
                **kwargs
        ):
            from azure.core.pipeline.policies import UserAgentPolicy, HeadersPolicy, ProxyPolicy, \
                RetryPolicy, CustomHookPolicy, RedirectPolicy, SansIOHTTPPolicy
            from azure.cli.core.sdk.policies import SafeNetworkTraceLoggingPolicy
            from ._http_policy import AAZBearerTokenCredentialPolicy

            self.user_agent_policy = kwargs.get('user_agent_policy') or UserAgentPolicy(**kwargs)
            self.headers_policy = kwargs.get('headers_policy') or HeadersPolicy(**kwargs)
            self.proxy_policy = kwargs.get('proxy_policy') or ProxyPolicy(**kwargs)
            self.logging_policy = kwargs.get('logging_policy') or SafeNetworkTraceLoggingPolicy(**kwargs)
            self.http_logging_policy = kwargs.get('http_logging_policy') or SansIOHTTPPolicy()
            self.retry_policy = kwargs.get('retry_policy') or RetryPolicy(**kwargs)
            self.custom_hook_policy = kwargs.get('custom_hook_policy') or CustomHookPolicy(**kwargs)
            self.redirect_policy = kwargs.get('redirect_policy') or RedirectPolicy(**kwargs)
            self.authentication_policy = kwargs.get('authentication_policy')
            if self.credential and not self.authentication_policy:
                self.authentication_policy = AAZBearerTokenCredentialPolicy(
                    self.credential, *self.credential_scopes, **kwargs)

    def __init__(self, cli_ctx, credential, **kwargs):
        from azure.cli.core.auth.util import resource_to_scopes
        base_url = cli_ctx.cloud.endpoints.resource_manager
        credential_scopes = resource_to_scopes(cli_ctx.cloud.endpoints.active_directory_resource_id)
        config = self._Configuration(
                credential=credential,
                credential_scopes=credential_scopes,
                **kwargs
            )
        super(AAZMgmtClient, self).__init__(
            base_url=base_url,
            config=config
        )

    def send_request(self, request, stream=False, **kwargs):
        session = self._pipeline.run(request, stream=stream, **kwargs) # pylint: disable=protected-access
        return session
