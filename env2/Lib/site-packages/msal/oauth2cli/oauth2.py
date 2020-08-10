"""This OAuth2 client implementation aims to be spec-compliant, and generic."""
# OAuth2 spec https://tools.ietf.org/html/rfc6749

try:
    from urllib.parse import urlencode, parse_qs
except ImportError:
    from urlparse import parse_qs
    from urllib import urlencode
import logging
import warnings
import time
import base64

import requests



class BaseClient(object):
    # This low-level interface works. Yet you'll find its sub-class
    # more friendly to remind you what parameters are needed in each scenario.
    # More on Client Types at https://tools.ietf.org/html/rfc6749#section-2.1

    @staticmethod
    def encode_saml_assertion(assertion):
        return base64.urlsafe_b64encode(assertion).rstrip(b'=')  # Per RFC 7522

    CLIENT_ASSERTION_TYPE_JWT = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
    CLIENT_ASSERTION_TYPE_SAML2 = "urn:ietf:params:oauth:client-assertion-type:saml2-bearer"
    client_assertion_encoders = {CLIENT_ASSERTION_TYPE_SAML2: encode_saml_assertion}

    def __init__(
            self,
            server_configuration,  # type: dict
            client_id,  # type: str
            client_secret=None,  # type: Optional[str]
            client_assertion=None,  # type: Union[bytes, callable, None]
            client_assertion_type=None,  # type: Optional[str]
            default_headers=None,  # type: Optional[dict]
            default_body=None,  # type: Optional[dict]
            verify=True,  # type: Union[str, True, False, None]
            proxies=None,  # type: Optional[dict]
            timeout=None,  # type: Union[tuple, float, None]
            ):
        """Initialize a client object to talk all the OAuth2 grants to the server.

        Args:
            server_configuration (dict):
                It contains the configuration (i.e. metadata) of the auth server.
                The actual content typically contains keys like
                "authorization_endpoint", "token_endpoint", etc..
                Based on RFC 8414 (https://tools.ietf.org/html/rfc8414),
                you can probably fetch it online from either
                https://example.com/.../.well-known/oauth-authorization-server
                or
                https://example.com/.../.well-known/openid-configuration
            client_id (str): The client's id, issued by the authorization server
            client_secret (str):  Triggers HTTP AUTH for Confidential Client
            client_assertion (bytes, callable):
                The client assertion to authenticate this client, per RFC 7521.
                It can be a raw SAML2 assertion (this method will encode it for you),
                or a raw JWT assertion.
                It can also be a callable (recommended),
                so that we will do lazy creation of an assertion.
            client_assertion_type (str):
                The type of your :attr:`client_assertion` parameter.
                It is typically the value of :attr:`CLIENT_ASSERTION_TYPE_SAML2` or
                :attr:`CLIENT_ASSERTION_TYPE_JWT`, the only two defined in RFC 7521.
            default_headers (dict):
                A dict to be sent in each request header.
                It is not required by OAuth2 specs, but you may use it for telemetry.
            default_body (dict):
                A dict to be sent in each token request body. For example,
                you could choose to set this as {"client_secret": "your secret"}
                if your authorization server wants it to be in the request body
                (rather than in the request header).
        """
        self.configuration = server_configuration
        self.client_id = client_id
        self.client_secret = client_secret
        self.client_assertion = client_assertion
        self.default_body = default_body or {}
        if client_assertion_type is not None:
            self.default_body["client_assertion_type"] = client_assertion_type
        self.logger = logging.getLogger(__name__)
        self.session = s = requests.Session()
        s.headers.update(default_headers or {})
        s.verify = verify
        s.proxies = proxies or {}
        self.timeout = timeout

    def _build_auth_request_params(self, response_type, **kwargs):
        # response_type is a string defined in
        #   https://tools.ietf.org/html/rfc6749#section-3.1.1
        # or it can be a space-delimited string as defined in
        #   https://tools.ietf.org/html/rfc6749#section-8.4
        response_type = self._stringify(response_type)

        params = {'client_id': self.client_id, 'response_type': response_type}
        params.update(kwargs)  # Note: None values will override params
        params = {k: v for k, v in params.items() if v is not None}  # clean up
        if params.get('scope'):
            params['scope'] = self._stringify(params['scope'])
        return params  # A dict suitable to be used in http request

    def _obtain_token(  # The verb "obtain" is influenced by OAUTH2 RFC 6749
            self, grant_type,
            params=None,  # a dict to be sent as query string to the endpoint
            data=None,  # All relevant data, which will go into the http body
            headers=None,  # a dict to be sent as request headers
            timeout=None,
            post=None,  # A callable to replace requests.post(), for testing.
                        # Such as: lambda url, **kwargs:
                        #   Mock(status_code=200, json=Mock(return_value={}))
            **kwargs  # Relay all extra parameters to underlying requests
            ):  # Returns the json object came from the OAUTH2 response
        _data = {'client_id': self.client_id, 'grant_type': grant_type}

        if self.default_body.get("client_assertion_type") and self.client_assertion:
            # See https://tools.ietf.org/html/rfc7521#section-4.2
            encoder = self.client_assertion_encoders.get(
                    self.default_body["client_assertion_type"], lambda a: a)
            _data["client_assertion"] = encoder(
                self.client_assertion()  # Do lazy on-the-fly computation
                if callable(self.client_assertion) else self.client_assertion)

        _data.update(self.default_body)  # It may contain authen parameters
        _data.update(data or {})  # So the content in data param prevails
        # We don't have to clean up None values here, because requests lib will.

        if _data.get('scope'):
            _data['scope'] = self._stringify(_data['scope'])

        # Quoted from https://tools.ietf.org/html/rfc6749#section-2.3.1
        # Clients in possession of a client password MAY use the HTTP Basic
        # authentication.
        # Alternatively, (but NOT RECOMMENDED,)
        # the authorization server MAY support including the
        # client credentials in the request-body using the following
        # parameters: client_id, client_secret.
        auth = None
        if self.client_secret and self.client_id:
            auth = (self.client_id, self.client_secret)  # for HTTP Basic Auth

        if "token_endpoint" not in self.configuration:
            raise ValueError("token_endpoint not found in configuration")
        _headers = {'Accept': 'application/json'}
        _headers.update(headers or {})
        resp = (post or self.session.post)(
            self.configuration["token_endpoint"],
            headers=_headers, params=params, data=_data, auth=auth,
            timeout=timeout or self.timeout,
            **kwargs)
        if resp.status_code >= 500:
            resp.raise_for_status()  # TODO: Will probably retry here
        try:
            # The spec (https://tools.ietf.org/html/rfc6749#section-5.2) says
            # even an error response will be a valid json structure,
            # so we simply return it here, without needing to invent an exception.
            return resp.json()
        except ValueError:
            self.logger.exception(
                    "Token response is not in json format: %s", resp.text)
            raise

    def obtain_token_by_refresh_token(self, refresh_token, scope=None, **kwargs):
        """Obtain an access token via a refresh token.

        :param refresh_token: The refresh token issued to the client
        :param scope: If omitted, is treated as equal to the scope originally
            granted by the resource ownser,
            according to https://tools.ietf.org/html/rfc6749#section-6
        """
        data = kwargs.pop('data', {})
        data.update(refresh_token=refresh_token, scope=scope)
        return self._obtain_token("refresh_token", data=data, **kwargs)

    def _stringify(self, sequence):
        if isinstance(sequence, (list, set, tuple)):
            return ' '.join(sorted(sequence))  # normalizing it, ascendingly
        return sequence  # as-is


class Client(BaseClient):  # We choose to implement all 4 grants in 1 class
    """This is the main API for oauth2 client.

    Its methods define and document parameters mentioned in OAUTH2 RFC 6749.
    """
    DEVICE_FLOW = {  # consts for device flow, that can be customized by sub-class
        "GRANT_TYPE": "urn:ietf:params:oauth:grant-type:device_code",
        "DEVICE_CODE": "device_code",
        }
    DEVICE_FLOW_RETRIABLE_ERRORS = ("authorization_pending", "slow_down")
    GRANT_TYPE_SAML2 = "urn:ietf:params:oauth:grant-type:saml2-bearer"  # RFC7522
    GRANT_TYPE_JWT = "urn:ietf:params:oauth:grant-type:jwt-bearer"  # RFC7523
    grant_assertion_encoders = {GRANT_TYPE_SAML2: BaseClient.encode_saml_assertion}


    def initiate_device_flow(self, scope=None, timeout=None, **kwargs):
        # type: (list, **dict) -> dict
        # The naming of this method is following the wording of this specs
        # https://tools.ietf.org/html/draft-ietf-oauth-device-flow-12#section-3.1
        """Initiate a device flow.

        Returns the data defined in Device Flow specs.
        https://tools.ietf.org/html/draft-ietf-oauth-device-flow-12#section-3.2

        You should then orchestrate the User Interaction as defined in here
        https://tools.ietf.org/html/draft-ietf-oauth-device-flow-12#section-3.3

        And possibly here
        https://tools.ietf.org/html/draft-ietf-oauth-device-flow-12#section-3.3.1
        """
        DAE = "device_authorization_endpoint"
        if not self.configuration.get(DAE):
            raise ValueError("You need to provide device authorization endpoint")
        flow = self.session.post(self.configuration[DAE],
            data={"client_id": self.client_id, "scope": self._stringify(scope or [])},
            timeout=timeout or self.timeout,
            **kwargs).json()
        flow["interval"] = int(flow.get("interval", 5))  # Some IdP returns string
        flow["expires_in"] = int(flow.get("expires_in", 1800))
        flow["expires_at"] = time.time() + flow["expires_in"]  # We invent this
        return flow

    def _obtain_token_by_device_flow(self, flow, **kwargs):
        # type: (dict, **dict) -> dict
        # This method updates flow during each run. And it is non-blocking.
        now = time.time()
        skew = 1
        if flow.get("latest_attempt_at", 0) + flow.get("interval", 5) - skew > now:
            warnings.warn('Attempted too soon. Please do time.sleep(flow["interval"])')
        data = kwargs.pop("data", {})
        data.update({
            "client_id": self.client_id,
            self.DEVICE_FLOW["DEVICE_CODE"]: flow["device_code"],
            })
        result = self._obtain_token(
            self.DEVICE_FLOW["GRANT_TYPE"], data=data, **kwargs)
        if result.get("error") == "slow_down":
            # Respecting https://tools.ietf.org/html/draft-ietf-oauth-device-flow-12#section-3.5
            flow["interval"] = flow.get("interval", 5) + 5
        flow["latest_attempt_at"] = now
        return result

    def obtain_token_by_device_flow(self,
            flow,
            exit_condition=lambda flow: flow.get("expires_at", 0) < time.time(),
            **kwargs):
        # type: (dict, Callable) -> dict
        """Obtain token by a device flow object, with customizable polling effect.

        Args:
            flow (dict):
                An object previously generated by initiate_device_flow(...).
                Its content WILL BE CHANGED by this method during each run.
                We share this object with you, so that you could implement
                your own loop, should you choose to do so.

            exit_condition (Callable):
                This method implements a loop to provide polling effect.
                The loop's exit condition is calculated by this callback.

                The default callback makes the loop run until the flow expires.
                Therefore, one of the ways to exit the polling early,
                is to change the flow["expires_at"] to a small number such as 0.

                In case you are doing async programming, you may want to
                completely turn off the loop. You can do so by using a callback as:

                    exit_condition = lambda flow: True

                to make the loop run only once, i.e. no polling, hence non-block.
        """
        while True:
            result = self._obtain_token_by_device_flow(flow, **kwargs)
            if result.get("error") not in self.DEVICE_FLOW_RETRIABLE_ERRORS:
                return result
            for i in range(flow.get("interval", 5)):  # Wait interval seconds
                if exit_condition(flow):
                    return result
                time.sleep(1)  # Shorten each round, to make exit more responsive

    def build_auth_request_uri(
            self,
            response_type, redirect_uri=None, scope=None, state=None, **kwargs):
        """Generate an authorization uri to be visited by resource owner.

        Later when the response reaches your redirect_uri,
        you can use parse_auth_response() to check the returned state.

        This method could be named build_authorization_request_uri() instead,
        but then there would be a build_authentication_request_uri() in the OIDC
        subclass doing almost the same thing. So we use a loose term "auth" here.

        :param response_type:
            Must be "code" when you are using Authorization Code Grant,
            "token" when you are using Implicit Grant, or other
            (possibly space-delimited) strings as registered extension value.
            See https://tools.ietf.org/html/rfc6749#section-3.1.1
        :param redirect_uri: Optional. Server will use the pre-registered one.
        :param scope: It is a space-delimited, case-sensitive string.
            Some ID provider can accept empty string to represent default scope.
        :param state: Recommended. An opaque value used by the client to
            maintain state between the request and callback.
        :param kwargs: Other parameters, typically defined in OpenID Connect.
        """
        if "authorization_endpoint" not in self.configuration:
            raise ValueError("authorization_endpoint not found in configuration")
        authorization_endpoint = self.configuration["authorization_endpoint"]
        params = self._build_auth_request_params(
            response_type, redirect_uri=redirect_uri, scope=scope, state=state,
            **kwargs)
        sep = '&' if '?' in authorization_endpoint else '?'
        return "%s%s%s" % (authorization_endpoint, sep, urlencode(params))

    @staticmethod
    def parse_auth_response(params, state=None):
        """Parse the authorization response being redirected back.

        :param params: A string or dict of the query string
        :param state: REQUIRED if the state parameter was present in the client
            authorization request. This function will compare it with response.
        """
        if not isinstance(params, dict):
            params = parse_qs(params)
        if params.get('state') != state:
            raise ValueError('state mismatch')
        return params

    def obtain_token_by_authorization_code(
            self, code, redirect_uri=None, **kwargs):
        """Get a token via auhtorization code. a.k.a. Authorization Code Grant.

        This is typically used by a server-side app (Confidential Client),
        but it can also be used by a device-side native app (Public Client).
        See more detail at https://tools.ietf.org/html/rfc6749#section-4.1.3

        :param code: The authorization code received from authorization server.
        :param redirect_uri:
            Required, if the "redirect_uri" parameter was included in the
            authorization request, and their values MUST be identical.
        """
        data = kwargs.pop("data", {})
        data.update(code=code, redirect_uri=redirect_uri)
        if not self.client_secret:
            # client_id is required, if the client is not authenticating itself.
            # See https://tools.ietf.org/html/rfc6749#section-4.1.3
            data["client_id"] = self.client_id
        return self._obtain_token("authorization_code", data=data, **kwargs)

    def obtain_token_by_username_password(
            self, username, password, scope=None, **kwargs):
        """The Resource Owner Password Credentials Grant, used by legacy app."""
        data = kwargs.pop("data", {})
        data.update(username=username, password=password, scope=scope)
        return self._obtain_token("password", data=data, **kwargs)

    def obtain_token_for_client(self, scope=None, **kwargs):
        """Obtain token for this client (rather than for an end user),
        a.k.a. the Client Credentials Grant, used by Backend Applications.

        We don't name it obtain_token_by_client_credentials(...) because those
        credentials are typically already provided in class constructor, not here.
        You can still explicitly provide an optional client_secret parameter,
        or you can provide such extra parameters as `default_body` during the
        class initialization.
        """
        data = kwargs.pop("data", {})
        data.update(scope=scope)
        return self._obtain_token("client_credentials", data=data, **kwargs)

    def __init__(self,
            server_configuration, client_id,
            on_obtaining_tokens=lambda event: None,  # event is defined in _obtain_token(...)
            on_removing_rt=lambda token_item: None,
            on_updating_rt=lambda token_item, new_rt: None,
            **kwargs):
        super(Client, self).__init__(server_configuration, client_id, **kwargs)
        self.on_obtaining_tokens = on_obtaining_tokens
        self.on_removing_rt = on_removing_rt
        self.on_updating_rt = on_updating_rt

    def _obtain_token(self, grant_type, params=None, data=None,
            rt_getter=lambda token_item: token_item["refresh_token"],
            *args, **kwargs):
        RT = "refresh_token"
        _data = data.copy()  # to prevent side effect
        refresh_token = _data.get(RT)
        if grant_type == RT and isinstance(refresh_token, dict):
            _data[RT] = rt_getter(refresh_token)  # Put raw RT in _data
        resp = super(Client, self)._obtain_token(
            grant_type, params, _data, *args, **kwargs)
        if "error" not in resp:
            _resp = resp.copy()
            if grant_type == RT and RT in _resp and isinstance(refresh_token, dict):
                _resp.pop(RT)  # So we skip it in on_obtaining_tokens(); it will
                               # be handled in self.obtain_token_by_refresh_token()
            if "scope" in _resp:
                scope = _resp["scope"].split()  # It is conceptually a set,
                    # but we represent it as a list which can be persisted to JSON
            else:
                # TODO: Deal with absent scope in authorization grant
                scope = _data.get("scope")
            self.on_obtaining_tokens({
                "client_id": self.client_id,
                "scope": scope,
                "token_endpoint": self.configuration["token_endpoint"],
                "grant_type": grant_type,  # can be used to know an IdToken-less
                                           # response is for an app or for a user
                "response": _resp, "params": params, "data": _data,
                })
        return resp

    def obtain_token_by_refresh_token(self, token_item, scope=None,
            rt_getter=lambda token_item: token_item["refresh_token"],
            on_removing_rt=None,
            **kwargs):
        # type: (Union[str, dict], Union[str, list, set, tuple], Callable) -> dict
        """This is an "overload" which accepts a refresh token item as a dict,
        therefore this method can relay refresh_token item to event listeners.

        :param token_item:
            A refresh token item as a dict, came from the cache managed by this lib.

            Alternatively, you can still use a refresh token (RT) as a string,
            supposedly came from a token cache managed by a different library,
            then this library will store the new RT (if Authority Server issued one)
            into this lib's cache. This is a way to migrate from other lib to us.
        :param scope: If omitted, is treated as equal to the scope originally
            granted by the resource ownser,
            according to https://tools.ietf.org/html/rfc6749#section-6
        :param rt_getter: A callable used to extract the RT from token_item
        :param on_removing_rt: If absent, fall back to the one defined in initialization
        """
        resp = super(Client, self).obtain_token_by_refresh_token(
            token_item, scope=scope,
            rt_getter=rt_getter,  # Wire up this for _obtain_token()
            **kwargs)
        if isinstance(token_item, dict):
            if resp.get('error') == 'invalid_grant':
                (on_removing_rt or self.on_removing_rt)(token_item)  # Discard old RT
            if 'refresh_token' in resp:
                self.on_updating_rt(token_item, resp['refresh_token'])
        return resp

    def obtain_token_by_assertion(
            self, assertion, grant_type, scope=None, **kwargs):
        # type: (bytes, Union[str, None], Union[str, list, set, tuple]) -> dict
        """This method implements Assertion Framework for OAuth2 (RFC 7521).
        See details at https://tools.ietf.org/html/rfc7521#section-4.1

        :param assertion:
            The assertion bytes can be a raw SAML2 assertion, or a JWT assertion.
        :param grant_type:
            It is typically either the value of :attr:`GRANT_TYPE_SAML2`,
            or :attr:`GRANT_TYPE_JWT`, the only two profiles defined in RFC 7521.
        :param scope: Optional. It must be a subset of previously granted scopes.
        """
        encoder = self.grant_assertion_encoders.get(grant_type, lambda a: a)
        data = kwargs.pop("data", {})
        data.update(scope=scope, assertion=encoder(assertion))
        return self._obtain_token(grant_type, data=data, **kwargs)

