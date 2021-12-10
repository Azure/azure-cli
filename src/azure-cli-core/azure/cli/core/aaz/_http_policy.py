from azure.core.pipeline.policies import HTTPPolicy
from azure.mgmt.core.policies._authentication import _parse_claims_challenge
from azure.core.exceptions import ServiceRequestError
import time


class AAZBearerTokenCredentialPolicy(HTTPPolicy):
    """

    Followed the implement of azure.core.pipeline.policies.BearerTokenCredentialPolicy
    """

    def __init__(self, credential, *scopes, **kwargs):  # pylint:disable=unused-argument
        super().__init__()
        self._scopes = scopes
        self._credential = credential
        self._token = None
        self._aux_tokens = None

    @staticmethod
    def _enforce_https(request):
        # move 'enforce_https' from options to context so it persists
        # across retries but isn't passed to a transport implementation
        option = request.context.options.pop("enforce_https", None)

        # True is the default setting; we needn't preserve an explicit opt in to the default behavior
        if option is False:
            request.context["enforce_https"] = option

        enforce_https = request.context.get("enforce_https", True)
        if enforce_https and not request.http_request.url.lower().startswith("https"):
            raise ServiceRequestError(
                "Bearer token authentication is not permitted for non-TLS protected (non-https) URLs."
            )

    def _update_headers(self, headers):
        """Updates the Authorization header with the bearer token.

        :param dict headers: The HTTP Request headers
        """

        headers["Authorization"] = "Bearer {}".format(self._token.token)
        if self._aux_tokens:
            headers["x-ms-authorization-auxiliary"] = ', '.join("Bearer {}".format(token.token) for token in self._aux_tokens)

    @property
    def _need_new_token(self):
        if not self._token:
            return True
        return self._token.expires_on - time.time() < 300

    @property
    def _need_new_aux_tokens(self):
        if not self._aux_tokens:
            return True
        for token in self._aux_tokens:
            if token.expires_on - time.time() < 300:
                return True
        return False

    def on_request(self, request):
        """Called before the policy sends a request.

        The base implementation authorizes the request with a bearer token.

        :param ~azure.core.pipeline.PipelineRequest request: the request
        """
        self._enforce_https(request)

        if self._need_new_token:
            self._token = self._credential.get_token(*self._scopes)

        if self._need_new_aux_tokens:
            self._aux_tokens = self._credential.get_auxiliary_tokens(*self._scopes)

        self._update_headers(request.http_request.headers)

    def authorize_request(self, request, *scopes, **kwargs):
        """Acquire a token from the credential and authorize the request with it.

        Keyword arguments are passed to the credential's get_token method. The token will be cached and used to
        authorize future requests.

        :param ~azure.core.pipeline.PipelineRequest request: the request
        :param str scopes: required scopes of authentication
        """
        self._token = self._credential.get_token(*scopes, **kwargs)
        self._aux_tokens = self._credential.get_auxiliary_tokens(*self._scopes)

        self._update_headers(request.http_request.headers)

    def send(self, request):
        """Authorize request with a bearer token and send it to the next policy

        :param request: The pipeline request object
        :type request: ~azure.core.pipeline.PipelineRequest
        """
        self.on_request(request)
        try:
            response = self.next.send(request)
            self.on_response(request, response)
        except Exception:  # pylint:disable=broad-except
            handled = self.on_exception(request)
            if not handled:
                raise
        else:
            if response.http_response.status_code == 401:
                self._token = None  # any cached token is invalid
                if "WWW-Authenticate" in response.http_response.headers:
                    request_authorized = self.on_challenge(request, response)
                    if request_authorized:
                        try:
                            response = self.next.send(request)
                            self.on_response(request, response)
                        except Exception:  # pylint:disable=broad-except
                            handled = self.on_exception(request)
                            if not handled:
                                raise

        return response

    def on_challenge(self, request, response):
        """Authorize request according to an authentication challenge

        This method is called when the resource provider responds 401 with a WWW-Authenticate header.

        :param ~azure.core.pipeline.PipelineRequest request: the request which elicited an authentication challenge
        :param ~azure.core.pipeline.PipelineResponse response: the resource provider's response
        :returns: a bool indicating whether the policy should send the request
        """
        # pylint:disable=unused-argument,no-self-use
        return False

    def on_response(self, request, response):
        """Executed after the request comes back from the next policy.

        :param request: Request to be modified after returning from the policy.
        :type request: ~azure.core.pipeline.PipelineRequest
        :param response: Pipeline response object
        :type response: ~azure.core.pipeline.PipelineResponse
        """

    def on_exception(self, request):
        """Executed when an exception is raised while executing the next policy.

        This method is executed inside the exception handler.

        :param request: The Pipeline request object
        :type request: ~azure.core.pipeline.PipelineRequest
        :return: False by default, override with True to stop the exception.
        :rtype: bool
        """
        # pylint: disable=no-self-use,unused-argument
        return False


class AAZARMChallengeAuthenticationPolicy(AAZBearerTokenCredentialPolicy):
    """Adds a bearer token Authorization header to requests.

    This policy internally handles Continuous Access Evaluation (CAE) challenges. When it can't complete a challenge,
    it will return the 401 (unauthorized) response from ARM.

    :param ~azure.core.credentials.TokenCredential credential: credential for authorizing requests
    :param str scopes: required authentication scopes
    """

    def on_challenge(self, request, response):  # pylint:disable=unused-argument
        """Authorize request according to an ARM authentication challenge

        :param ~azure.core.pipeline.PipelineRequest request: the request which elicited an authentication challenge
        :param ~azure.core.pipeline.PipelineResponse response: ARM's response
        :returns: a bool indicating whether the policy should send the request
        """

        challenge = response.http_response.headers.get("WWW-Authenticate")
        if challenge:
            claims = _parse_claims_challenge(challenge)
            if claims:
                self.authorize_request(request, *self._scopes, claims=claims)
                return True

        return False
