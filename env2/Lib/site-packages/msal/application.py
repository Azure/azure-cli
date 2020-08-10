import time
try:  # Python 2
    from urlparse import urljoin
except:  # Python 3
    from urllib.parse import urljoin
import logging
import sys
import warnings

import requests

from .oauth2cli import Client, JwtAssertionCreator
from .authority import Authority
from .mex import send_request as mex_send_request
from .wstrust_request import send_request as wst_send_request
from .wstrust_response import *
from .token_cache import TokenCache


# The __init__.py will import this. Not the other way around.
__version__ = "1.0.0"

logger = logging.getLogger(__name__)

def decorate_scope(
        scopes, client_id,
        reserved_scope=frozenset(['openid', 'profile', 'offline_access'])):
    if not isinstance(scopes, (list, set, tuple)):
        raise ValueError("The input scopes should be a list, tuple, or set")
    scope_set = set(scopes)  # Input scopes is typically a list. Copy it to a set.
    if scope_set & reserved_scope:
        # These scopes are reserved for the API to provide good experience.
        # We could make the developer pass these and then if they do they will
        # come back asking why they don't see refresh token or user information.
        raise ValueError(
            "API does not accept {} value as user-provided scopes".format(
                reserved_scope))
    if client_id in scope_set:
        if len(scope_set) > 1:
            # We make developers pass their client id, so that they can express
            # the intent that they want the token for themselves (their own
            # app).
            # If we do not restrict them to passing only client id then they
            # could write code where they expect an id token but end up getting
            # access_token.
            raise ValueError("Client Id can only be provided as a single scope")
        decorated = set(reserved_scope)  # Make a writable copy
    else:
        decorated = scope_set | reserved_scope
    return list(decorated)


def extract_certs(public_cert_content):
    # Parses raw public certificate file contents and returns a list of strings
    # Usage: headers = {"x5c": extract_certs(open("my_cert.pem").read())}
    public_certificates = re.findall(
        r'-----BEGIN CERTIFICATE-----(?P<cert_value>[^-]+)-----END CERTIFICATE-----',
        public_cert_content, re.I)
    if public_certificates:
        return [cert.strip() for cert in public_certificates]
    # The public cert tags are not found in the input,
    # let's make best effort to exclude a private key pem file.
    if "PRIVATE KEY" in public_cert_content:
        raise ValueError(
            "We expect your public key but detect a private key instead")
    return [public_cert_content.strip()]


class ClientApplication(object):

    def __init__(
            self, client_id,
            client_credential=None, authority=None, validate_authority=True,
            token_cache=None,
            verify=True, proxies=None, timeout=None,
            client_claims=None):
        """Create an instance of application.

        :param client_id: Your app has a client_id after you register it on AAD.
        :param client_credential:
            For :class:`PublicClientApplication`, you simply use `None` here.
            For :class:`ConfidentialClientApplication`,
            it can be a string containing client secret,
            or an X509 certificate container in this form::

                {
                    "private_key": "...-----BEGIN PRIVATE KEY-----...",
                    "thumbprint": "A1B2C3D4E5F6...",
                    "public_certificate": "...-----BEGIN CERTIFICATE-----..." (Optional. See below.)
                }

            *Added in version 0.5.0*:
            public_certificate (optional) is public key certificate
            which will be sent through 'x5c' JWT header only for
            subject name and issuer authentication to support cert auto rolls.

        :param dict client_claims:
            *Added in version 0.5.0*:
            It is a dictionary of extra claims that would be signed by
            by this :class:`ConfidentialClientApplication` 's private key.
            For example, you can use {"client_ip": "x.x.x.x"}.
            You may also override any of the following default claims::

                {
                    "aud": the_token_endpoint,
                    "iss": self.client_id,
                    "sub": same_as_issuer,
                    "exp": now + 10_min,
                    "iat": now,
                    "jti": a_random_uuid
                }

        :param str authority:
            A URL that identifies a token authority. It should be of the format
            https://login.microsoftonline.com/your_tenant
            By default, we will use https://login.microsoftonline.com/common
        :param bool validate_authority: (optional) Turns authority validation
            on or off. This parameter default to true.
        :param TokenCache cache:
            Sets the token cache used by this ClientApplication instance.
            By default, an in-memory cache will be created and used.
        :param verify: (optional)
            It will be passed to the
            `verify parameter in the underlying requests library
            <http://docs.python-requests.org/en/v2.9.1/user/advanced/#ssl-cert-verification>`_
        :param proxies: (optional)
            It will be passed to the
            `proxies parameter in the underlying requests library
            <http://docs.python-requests.org/en/v2.9.1/user/advanced/#proxies>`_
        :param timeout: (optional)
            It will be passed to the
            `timeout parameter in the underlying requests library
            <http://docs.python-requests.org/en/v2.9.1/user/advanced/#timeouts>`_
        """
        self.client_id = client_id
        self.client_credential = client_credential
        self.client_claims = client_claims
        self.verify = verify
        self.proxies = proxies
        self.timeout = timeout
        self.authority = Authority(
                authority or "https://login.microsoftonline.com/common/",
                validate_authority, verify=verify, proxies=proxies, timeout=timeout)
            # Here the self.authority is not the same type as authority in input
        self.token_cache = token_cache or TokenCache()
        self.client = self._build_client(client_credential, self.authority)
        self.authority_groups = None

    def _build_client(self, client_credential, authority):
        client_assertion = None
        client_assertion_type = None
        default_body = {"client_info": 1}
        if isinstance(client_credential, dict):
            assert ("private_key" in client_credential
                    and "thumbprint" in client_credential)
            headers = {}
            if 'public_certificate' in client_credential:
                headers["x5c"] = extract_certs(client_credential['public_certificate'])
            assertion = JwtAssertionCreator(
                client_credential["private_key"], algorithm="RS256",
                sha1_thumbprint=client_credential.get("thumbprint"), headers=headers)
            client_assertion = assertion.create_regenerative_assertion(
                audience=authority.token_endpoint, issuer=self.client_id,
                additional_claims=self.client_claims or {})
            client_assertion_type = Client.CLIENT_ASSERTION_TYPE_JWT
        else:
            default_body['client_secret'] = client_credential
        server_configuration = {
            "authorization_endpoint": authority.authorization_endpoint,
            "token_endpoint": authority.token_endpoint,
            "device_authorization_endpoint":
                urljoin(authority.token_endpoint, "devicecode"),
            }
        return Client(
            server_configuration,
            self.client_id,
            default_headers={
                "x-client-sku": "MSAL.Python", "x-client-ver": __version__,
                "x-client-os": sys.platform,
                "x-client-cpu": "x64" if sys.maxsize > 2 ** 32 else "x86",
                },
            default_body=default_body,
            client_assertion=client_assertion,
            client_assertion_type=client_assertion_type,
            on_obtaining_tokens=self.token_cache.add,
            on_removing_rt=self.token_cache.remove_rt,
            on_updating_rt=self.token_cache.update_rt,
            verify=self.verify, proxies=self.proxies, timeout=self.timeout)

    def get_authorization_request_url(
            self,
            scopes,  # type: list[str]
            # additional_scope=None,  # type: Optional[list]
            login_hint=None,  # type: Optional[str]
            state=None,  # Recommended by OAuth2 for CSRF protection
            redirect_uri=None,
            response_type="code",  # Can be "token" if you use Implicit Grant
            prompt=None,
            **kwargs):
        """Constructs a URL for you to start a Authorization Code Grant.

        :param list[str] scopes: (Required)
            Scopes requested to access a protected API (a resource).
        :param str state: Recommended by OAuth2 for CSRF protection.
        :param str login_hint:
            Identifier of the user. Generally a User Principal Name (UPN).
        :param str redirect_uri:
            Address to return to upon receiving a response from the authority.
        :param str response_type:
            Default value is "code" for an OAuth2 Authorization Code grant.
            You can use other content such as "id_token".
        :param str prompt:
            By default, no prompt value will be sent, not even "none".
            You will have to specify a value explicitly.
            Its valid values are defined in Open ID Connect specs
            https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest
        :return: The authorization url as a string.
        """
        """ # TBD: this would only be meaningful in a new acquire_token_interactive()
        :param additional_scope: Additional scope is a concept only in AAD.
            It refers to other resources you might want to prompt to consent
            for in the same interaction, but for which you won't get back a
            token for in this particular operation.
            (Under the hood, we simply merge scope and additional_scope before
            sending them on the wire.)
        """
        authority = kwargs.pop("authority", None)  # Historically we support this
        if authority:
            warnings.warn(
                "We haven't decided if this method will accept authority parameter")
        # The previous implementation is, it will use self.authority by default.
        # Multi-tenant app can use new authority on demand
        the_authority = Authority(
            authority,
            verify=self.verify, proxies=self.proxies, timeout=self.timeout,
            ) if authority else self.authority

        client = Client(
            {"authorization_endpoint": the_authority.authorization_endpoint},
            self.client_id)
        return client.build_auth_request_uri(
            response_type=response_type,
            redirect_uri=redirect_uri, state=state, login_hint=login_hint,
            prompt=prompt,
            scope=decorate_scope(scopes, self.client_id),
            )

    def acquire_token_by_authorization_code(
            self,
            code,
            scopes,  # Syntactically required. STS accepts empty value though.
            redirect_uri=None,
                # REQUIRED, if the "redirect_uri" parameter was included in the
                # authorization request as described in Section 4.1.1, and their
                # values MUST be identical.
            **kwargs):
        """The second half of the Authorization Code Grant.

        :param code: The authorization code returned from Authorization Server.
        :param list[str] scopes: (Required)
            Scopes requested to access a protected API (a resource).

            If you requested user consent for multiple resources, here you will
            typically want to provide a subset of what you required in AuthCode.

            OAuth2 was designed mostly for singleton services,
            where tokens are always meant for the same resource and the only
            changes are in the scopes.
            In AAD, tokens can be issued for multiple 3rd party resources.
            You can ask authorization code for multiple resources,
            but when you redeem it, the token is for only one intended
            recipient, called audience.
            So the developer need to specify a scope so that we can restrict the
            token to be issued for the corresponding audience.

        :return: A dict representing the json response from AAD:

            - A successful response would contain "access_token" key,
            - an error response would contain "error" and usually "error_description".
        """
        # If scope is absent on the wire, STS will give you a token associated
        # to the FIRST scope sent during the authorization request.
        # So in theory, you can omit scope here when you were working with only
        # one scope. But, MSAL decorates your scope anyway, so they are never
        # really empty.
        assert isinstance(scopes, list), "Invalid parameter type"
        self._validate_ssh_cert_input_data(kwargs.get("data", {}))
        return self.client.obtain_token_by_authorization_code(
            code, redirect_uri=redirect_uri,
            data=dict(
                kwargs.pop("data", {}),
                scope=decorate_scope(scopes, self.client_id)),
            **kwargs)

    def get_accounts(self, username=None):
        """Get a list of accounts which previously signed in, i.e. exists in cache.

        An account can later be used in :func:`~acquire_token_silent`
        to find its tokens.

        :param username:
            Filter accounts with this username only. Case insensitive.
        :return: A list of account objects.
            Each account is a dict. For now, we only document its "username" field.
            Your app can choose to display those information to end user,
            and allow user to choose one of his/her accounts to proceed.
        """
        accounts = self._find_msal_accounts(environment=self.authority.instance)
        if not accounts:  # Now try other aliases of this authority instance
            for alias in self._get_authority_aliases(self.authority.instance):
                accounts = self._find_msal_accounts(environment=alias)
                if accounts:
                    break
        if username:
            # Federated account["username"] from AAD could contain mixed case
            lowercase_username = username.lower()
            accounts = [a for a in accounts
                if a["username"].lower() == lowercase_username]
        # Does not further filter by existing RTs here. It probably won't matter.
        # Because in most cases Accounts and RTs co-exist.
        # Even in the rare case when an RT is revoked and then removed,
        # acquire_token_silent() would then yield no result,
        # apps would fall back to other acquire methods. This is the standard pattern.
        return accounts

    def _find_msal_accounts(self, environment):
        return [a for a in self.token_cache.find(
            TokenCache.CredentialType.ACCOUNT, query={"environment": environment})
            if a["authority_type"] in (
                TokenCache.AuthorityType.ADFS, TokenCache.AuthorityType.MSSTS)]

    def _get_authority_aliases(self, instance):
        if not self.authority_groups:
            resp = requests.get(
                "https://login.microsoftonline.com/common/discovery/instance?api-version=1.1&authorization_endpoint=https://login.microsoftonline.com/common/oauth2/authorize",
                headers={'Accept': 'application/json'},
                verify=self.verify, proxies=self.proxies, timeout=self.timeout)
            resp.raise_for_status()
            self.authority_groups = [
                set(group['aliases']) for group in resp.json()['metadata']]
        for group in self.authority_groups:
            if instance in group:
                return [alias for alias in group if alias != instance]
        return []

    def remove_account(self, account):
        """Sign me out and forget me from token cache"""
        self._forget_me(account)

    def _sign_out(self, home_account):
        # Remove all relevant RTs and ATs from token cache
        owned_by_home_account = {
            "environment": home_account["environment"],
            "home_account_id": home_account["home_account_id"],}  # realm-independent
        app_metadata = self._get_app_metadata(home_account["environment"])
        # Remove RTs/FRTs, and they are realm-independent
        for rt in [rt for rt in self.token_cache.find(
                TokenCache.CredentialType.REFRESH_TOKEN, query=owned_by_home_account)
                # Do RT's app ownership check as a precaution, in case family apps
                # and 3rd-party apps share same token cache, although they should not.
                if rt["client_id"] == self.client_id or (
                    app_metadata.get("family_id")  # Now let's settle family business
                    and rt.get("family_id") == app_metadata["family_id"])
                ]:
            self.token_cache.remove_rt(rt)
        for at in self.token_cache.find(  # Remove ATs
                # Regardless of realm, b/c we've removed realm-independent RTs anyway
                TokenCache.CredentialType.ACCESS_TOKEN, query=owned_by_home_account):
            # To avoid the complexity of locating sibling family app's AT,
            # we skip AT's app ownership check.
            # It means ATs for other apps will also be removed, it is OK because:
            # * non-family apps are not supposed to share token cache to begin with;
            # * Even if it happens, we keep other app's RT already, so SSO still works
            self.token_cache.remove_at(at)

    def _forget_me(self, home_account):
        # It implies signout, and then also remove all relevant accounts and IDTs
        self._sign_out(home_account)
        owned_by_home_account = {
            "environment": home_account["environment"],
            "home_account_id": home_account["home_account_id"],}  # realm-independent
        for idt in self.token_cache.find(  # Remove IDTs, regardless of realm
                TokenCache.CredentialType.ID_TOKEN, query=owned_by_home_account):
            self.token_cache.remove_idt(idt)
        for a in self.token_cache.find(  # Remove Accounts, regardless of realm
                TokenCache.CredentialType.ACCOUNT, query=owned_by_home_account):
            self.token_cache.remove_account(a)

    def acquire_token_silent(
            self,
            scopes,  # type: List[str]
            account,  # type: Optional[Account]
            authority=None,  # See get_authorization_request_url()
            force_refresh=False,  # type: Optional[boolean]
            **kwargs):
        """Acquire an access token for given account, without user interaction.

        It is done either by finding a valid access token from cache,
        or by finding a valid refresh token from cache and then automatically
        use it to redeem a new access token.

        :param list[str] scopes: (Required)
            Scopes requested to access a protected API (a resource).
        :param account:
            one of the account object returned by :func:`~get_accounts`,
            or use None when you want to find an access token for this client.
        :param force_refresh:
            If True, it will skip Access Token look-up,
            and try to find a Refresh Token to obtain a new Access Token.
        :return:
            - A dict containing "access_token" key, when cache lookup succeeds.
            - None when cache lookup does not yield anything.
        """
        assert isinstance(scopes, list), "Invalid parameter type"
        self._validate_ssh_cert_input_data(kwargs.get("data", {}))
        if authority:
            warnings.warn("We haven't decided how/if this method will accept authority parameter")
        # the_authority = Authority(
        #     authority,
        #     verify=self.verify, proxies=self.proxies, timeout=self.timeout,
        #     ) if authority else self.authority
        result = self._acquire_token_silent_from_cache_and_possibly_refresh_it(
            scopes, account, self.authority, force_refresh=force_refresh, **kwargs)
        if result:
            return result
        for alias in self._get_authority_aliases(self.authority.instance):
            the_authority = Authority(
                "https://" + alias + "/" + self.authority.tenant,
                validate_authority=False,
                verify=self.verify, proxies=self.proxies, timeout=self.timeout)
            result = self._acquire_token_silent_from_cache_and_possibly_refresh_it(
                scopes, account, the_authority, force_refresh=force_refresh, **kwargs)
            if result:
                return result

    def _acquire_token_silent_from_cache_and_possibly_refresh_it(
            self,
            scopes,  # type: List[str]
            account,  # type: Optional[Account]
            authority,  # This can be different than self.authority
            force_refresh=False,  # type: Optional[boolean]
            **kwargs):
        if not force_refresh:
            query={
                    "client_id": self.client_id,
                    "environment": authority.instance,
                    "realm": authority.tenant,
                    "home_account_id": (account or {}).get("home_account_id"),
                    }
            key_id = kwargs.get("data", {}).get("key_id")
            if key_id:  # Some token types (SSH-certs, POP) are bound to a key
                query["key_id"] = key_id
            matches = self.token_cache.find(
                self.token_cache.CredentialType.ACCESS_TOKEN,
                target=scopes,
                query=query)
            now = time.time()
            for entry in matches:
                expires_in = int(entry["expires_on"]) - now
                if expires_in < 5*60:
                    continue  # Removal is not necessary, it will be overwritten
                logger.debug("Cache hit an AT")
                return {  # Mimic a real response
                    "access_token": entry["secret"],
                    "token_type": entry.get("token_type", "Bearer"),
                    "expires_in": int(expires_in),  # OAuth2 specs defines it as int
                    }
        return self._acquire_token_silent_by_finding_rt_belongs_to_me_or_my_family(
                authority, decorate_scope(scopes, self.client_id), account,
                **kwargs)

    def _acquire_token_silent_by_finding_rt_belongs_to_me_or_my_family(
            self, authority, scopes, account, **kwargs):
        query = {
            "environment": authority.instance,
            "home_account_id": (account or {}).get("home_account_id"),
            # "realm": authority.tenant,  # AAD RTs are tenant-independent
            }
        app_metadata = self._get_app_metadata(authority.instance)
        if not app_metadata:  # Meaning this app is now used for the first time.
            # When/if we have a way to directly detect current app's family,
            # we'll rewrite this block, to support multiple families.
            # For now, we try existing RTs (*). If it works, we are in that family.
            # (*) RTs of a different app/family are not supposed to be
            # shared with or accessible by us in the first place.
            at = self._acquire_token_silent_by_finding_specific_refresh_token(
                authority, scopes,
                dict(query, family_id="1"),  # A hack, we have only 1 family for now
                rt_remover=lambda rt_item: None,  # NO-OP b/c RTs are likely not mine
                break_condition=lambda response:  # Break loop when app not in family
                    # Based on an AAD-only behavior mentioned in internal doc here
                    # https://msazure.visualstudio.com/One/_git/ESTS-Docs/pullrequest/1138595
                    "client_mismatch" in response.get("error_additional_info", []),
                **kwargs)
            if at:
                return at
        if app_metadata.get("family_id"):  # Meaning this app belongs to this family
            at = self._acquire_token_silent_by_finding_specific_refresh_token(
                authority, scopes, dict(query, family_id=app_metadata["family_id"]),
                **kwargs)
            if at:
                return at
        # Either this app is an orphan, so we will naturally use its own RT;
        # or all attempts above have failed, so we fall back to non-foci behavior.
        return self._acquire_token_silent_by_finding_specific_refresh_token(
            authority, scopes, dict(query, client_id=self.client_id), **kwargs)

    def _get_app_metadata(self, environment):
        apps = self.token_cache.find(  # Use find(), rather than token_cache.get(...)
            TokenCache.CredentialType.APP_METADATA, query={
                "environment": environment, "client_id": self.client_id})
        return apps[0] if apps else {}

    def _acquire_token_silent_by_finding_specific_refresh_token(
            self, authority, scopes, query,
            rt_remover=None, break_condition=lambda response: False, **kwargs):
        matches = self.token_cache.find(
            self.token_cache.CredentialType.REFRESH_TOKEN,
            # target=scopes,  # AAD RTs are scope-independent
            query=query)
        logger.debug("Found %d RTs matching %s", len(matches), query)
        client = self._build_client(self.client_credential, authority)
        for entry in matches:
            logger.debug("Cache attempts an RT")
            response = client.obtain_token_by_refresh_token(
                entry, rt_getter=lambda token_item: token_item["secret"],
                on_removing_rt=rt_remover or self.token_cache.remove_rt,
                scope=scopes,
                **kwargs)
            if "error" not in response:
                return response
            logger.debug(
                "Refresh failed. {error}: {error_description}".format(**response))
            if break_condition(response):
                break

    def _validate_ssh_cert_input_data(self, data):
        if data.get("token_type") == "ssh-cert":
            if not data.get("req_cnf"):
                raise ValueError(
                    "When requesting an SSH certificate, "
                    "you must include a string parameter named 'req_cnf' "
                    "containing the public key in JWK format "
                    "(https://tools.ietf.org/html/rfc7517).")
            if not data.get("key_id"):
                raise ValueError(
                    "When requesting an SSH certificate, "
                    "you must include a string parameter named 'key_id' "
                    "which identifies the key in the 'req_cnf' argument.")


class PublicClientApplication(ClientApplication):  # browser app or mobile app

    def __init__(self, client_id, client_credential=None, **kwargs):
        if client_credential is not None:
            raise ValueError("Public Client should not possess credentials")
        super(PublicClientApplication, self).__init__(
            client_id, client_credential=None, **kwargs)

    def initiate_device_flow(self, scopes=None, **kwargs):
        """Initiate a Device Flow instance,
        which will be used in :func:`~acquire_token_by_device_flow`.

        :param list[str] scopes:
            Scopes requested to access a protected API (a resource).
        :return: A dict representing a newly created Device Flow object.

            - A successful response would contain "user_code" key, among others
            - an error response would contain some other readable key/value pairs.
        """
        return self.client.initiate_device_flow(
            scope=decorate_scope(scopes or [], self.client_id),
            **kwargs)

    def acquire_token_by_device_flow(self, flow, **kwargs):
        """Obtain token by a device flow object, with customizable polling effect.

        :param dict flow:
            A dict previously generated by :func:`~initiate_device_flow`.
            By default, this method's polling effect  will block current thread.
            You can abort the polling loop at any time,
            by changing the value of the flow's "expires_at" key to 0.

        :return: A dict representing the json response from AAD:

            - A successful response would contain "access_token" key,
            - an error response would contain "error" and usually "error_description".
        """
        return self.client.obtain_token_by_device_flow(
                flow,
                data=dict(kwargs.pop("data", {}), code=flow["device_code"]),
                    # 2018-10-4 Hack:
                    # during transition period,
                    # service seemingly need both device_code and code parameter.
                **kwargs)

    def acquire_token_by_username_password(
            self, username, password, scopes, **kwargs):
        """Gets a token for a given resource via user credentails.

        See this page for constraints of Username Password Flow.
        https://github.com/AzureAD/microsoft-authentication-library-for-python/wiki/Username-Password-Authentication

        :param str username: Typically a UPN in the form of an email address.
        :param str password: The password.
        :param list[str] scopes:
            Scopes requested to access a protected API (a resource).

        :return: A dict representing the json response from AAD:

            - A successful response would contain "access_token" key,
            - an error response would contain "error" and usually "error_description".
        """
        scopes = decorate_scope(scopes, self.client_id)
        if not self.authority.is_adfs:
            user_realm_result = self.authority.user_realm_discovery(username)
            if user_realm_result.get("account_type") == "Federated":
                return self._acquire_token_by_username_password_federated(
                    user_realm_result, username, password, scopes=scopes, **kwargs)
        return self.client.obtain_token_by_username_password(
                username, password, scope=scopes, **kwargs)

    def _acquire_token_by_username_password_federated(
            self, user_realm_result, username, password, scopes=None, **kwargs):
        verify = kwargs.pop("verify", self.verify)
        proxies = kwargs.pop("proxies", self.proxies)
        wstrust_endpoint = {}
        if user_realm_result.get("federation_metadata_url"):
            wstrust_endpoint = mex_send_request(
                user_realm_result["federation_metadata_url"],
                verify=verify, proxies=proxies)
            if wstrust_endpoint is None:
                raise ValueError("Unable to find wstrust endpoint from MEX. "
                    "This typically happens when attempting MSA accounts. "
                    "More details available here. "
                    "https://github.com/AzureAD/microsoft-authentication-library-for-python/wiki/Username-Password-Authentication")
        logger.debug("wstrust_endpoint = %s", wstrust_endpoint)
        wstrust_result = wst_send_request(
            username, password, user_realm_result.get("cloud_audience_urn"),
            wstrust_endpoint.get("address",
                # Fallback to an AAD supplied endpoint
                user_realm_result.get("federation_active_auth_url")),
            wstrust_endpoint.get("action"), verify=verify, proxies=proxies)
        if not ("token" in wstrust_result and "type" in wstrust_result):
            raise RuntimeError("Unsuccessful RSTR. %s" % wstrust_result)
        GRANT_TYPE_SAML1_1 = 'urn:ietf:params:oauth:grant-type:saml1_1-bearer'
        grant_type = {
            SAML_TOKEN_TYPE_V1: GRANT_TYPE_SAML1_1,
            SAML_TOKEN_TYPE_V2: self.client.GRANT_TYPE_SAML2,
            WSS_SAML_TOKEN_PROFILE_V1_1: GRANT_TYPE_SAML1_1,
            WSS_SAML_TOKEN_PROFILE_V2: self.client.GRANT_TYPE_SAML2
            }.get(wstrust_result.get("type"))
        if not grant_type:
            raise RuntimeError(
                "RSTR returned unknown token type: %s", wstrust_result.get("type"))
        self.client.grant_assertion_encoders.setdefault(  # Register a non-standard type
            grant_type, self.client.encode_saml_assertion)
        return self.client.obtain_token_by_assertion(
            wstrust_result["token"], grant_type, scope=scopes, **kwargs)


class ConfidentialClientApplication(ClientApplication):  # server-side web app

    def acquire_token_for_client(self, scopes, **kwargs):
        """Acquires token for the current confidential client, not for an end user.

        :param list[str] scopes: (Required)
            Scopes requested to access a protected API (a resource).

        :return: A dict representing the json response from AAD:

            - A successful response would contain "access_token" key,
            - an error response would contain "error" and usually "error_description".
        """
        # TBD: force_refresh behavior
        return self.client.obtain_token_for_client(
                scope=scopes,  # This grant flow requires no scope decoration
                **kwargs)

    def acquire_token_on_behalf_of(self, user_assertion, scopes, **kwargs):
        """Acquires token using on-behalf-of (OBO) flow.

        The current app is a middle-tier service which was called with a token
        representing an end user.
        The current app can use such token (a.k.a. a user assertion) to request
        another token to access downstream web API, on behalf of that user.
        See `detail docs here <https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-on-behalf-of-flow>`_ .

        The current middle-tier app has no user interaction to obtain consent.
        See how to gain consent upfront for your middle-tier app from this article.
        https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-on-behalf-of-flow#gaining-consent-for-the-middle-tier-application

        :param str user_assertion: The incoming token already received by this app
        :param list[str] scopes: Scopes required by downstream API (a resource).

        :return: A dict representing the json response from AAD:

            - A successful response would contain "access_token" key,
            - an error response would contain "error" and usually "error_description".
        """
        # The implementation is NOT based on Token Exchange
        # https://tools.ietf.org/html/draft-ietf-oauth-token-exchange-16
        return self.client.obtain_token_by_assertion(  # bases on assertion RFC 7521
            user_assertion,
            self.client.GRANT_TYPE_JWT,  # IDTs and AAD ATs are all JWTs
            scope=decorate_scope(scopes, self.client_id),  # Decoration is used for:
                # 1. Explicitly requesting an RT, without relying on AAD default
                #    behavior, even though it currently still issues an RT.
                # 2. Requesting an IDT (which would otherwise be unavailable)
                #    so that the calling app could use id_token_claims to implement
                #    their own cache mapping, which is likely needed in web apps.
            data=dict(kwargs.pop("data", {}), requested_token_use="on_behalf_of"),
            **kwargs)

