# -*- coding: utf-8 -*-
# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Low-level calls to REST end-points.

Specific interfaces to the Data-lake Store filesystem layer and authentication code.
"""

# standard imports
import logging
import os
import threading
import time
import uuid
import platform
import sys

if sys.version_info >= (3, 4):
    import urllib.parse as urllib
else:
    import urllib

from .retry import ExponentialRetryPolicy, retry_decorator_for_auth

# 3rd party imports
import adal
import requests
import requests.exceptions

# this is required due to github issue, to ensure we don't lose perf from openPySSL: https://github.com/pyca/pyopenssl/issues/625
enforce_no_py_open_ssl = None
try:
    from requests.packages.urllib3.contrib.pyopenssl import extract_from_urllib3 as enforce_no_py_open_ssl
except ImportError:
    # in the case of debian/ubuntu system packages, the import is slightly different
    try:
        from urllib3.contrib.pyopenssl import extract_from_urllib3 as enforce_no_py_open_ssl
    except ImportError:
        # if OpenSSL is unavailable in both cases then there is no need to "undo" it.
        pass

if enforce_no_py_open_ssl:
    enforce_no_py_open_ssl()

from .exceptions import DatalakeBadOffsetException, DatalakeRESTException
from .exceptions import FileNotFoundError, PermissionError
from . import __version__

logger = logging.getLogger(__name__)

# TODO: This client id should be removed and it should be a required parameter for authentication.
default_client = os.environ.get('azure_client_id', "04b07795-8ddb-461a-bbee-02f9e1bf7b46")
default_store = os.environ.get('azure_data_lake_store_name', None)
default_adls_suffix = os.environ.get('azure_data_lake_store_url_suffix', 'azuredatalakestore.net')

# Constants
DEFAULT_RESOURCE_ENDPOINT = "https://datalake.azure.net/"
MAX_CONTENT_LENGTH = 2**16

# This is the maximum number of active pool connections
# that are supported during a single operation (such as upload or download of a file).
# This ensures that no connections are prematurely evicted, which has negative performance implications.
MAX_POOL_CONNECTIONS = 1024

# TODO: a breaking change should be made to add a new parameter specific for service_principal_app_id
# instead of overloading client_id, which is also used by other login methods to indicate what application
# is requesting the authentication (for example, in an interactive prompt).
def auth(tenant_id=None, username=None,
         password=None, client_id=default_client,
         client_secret=None, resource=DEFAULT_RESOURCE_ENDPOINT,
         require_2fa=False, authority=None, retry_policy=None, **kwargs):
    """ User/password authentication

    Parameters
    ----------

    tenant_id: str
        associated with the user's subscription, or "common"
    username: str
        active directory user
    password: str
        sign-in password
    client_id: str
        the service principal client
    client_secret: str
        the secret associated with the client_id
    resource: str
        resource for auth (e.g., https://datalake.azure.net/)
    require_2fa: bool
        indicates this authentication attempt requires two-factor authentication
    authority: string
        The full URI of the authentication authority to authenticate against (such as https://login.microsoftonline.com/)
    kwargs: key/values
        Other parameters, for future use

    Returns
    -------
    :type DataLakeCredential :mod: `A DataLakeCredential object`
    """

    if not authority:
        authority = 'https://login.microsoftonline.com/'


    if not tenant_id:
        tenant_id = os.environ.get('azure_tenant_id', "common")

    context = adal.AuthenticationContext(authority +
                                         tenant_id)

    if tenant_id is None or client_id is None:
        raise ValueError("tenant_id and client_id must be supplied for authentication")

    if not username:
        username = os.environ.get('azure_username', None)

    if not password:
        password = os.environ.get('azure_password', None)

    if not client_secret:
        client_secret = os.environ.get('azure_client_secret', None)

    # You can explicitly authenticate with 2fa, or pass in nothing to the auth call
    # and the user will be prompted to login interactively through a browser.

    @retry_decorator_for_auth(retry_policy=retry_policy)
    def get_token_internal():
        # Internal function used so as to use retry decorator
        if require_2fa or (username is None and password is None and client_secret is None):
            code = context.acquire_user_code(resource, client_id)
            print(code['message'])
            out = context.acquire_token_with_device_code(resource, code, client_id)
        elif username and password:
            out = context.acquire_token_with_username_password(resource, username,
                                                               password, client_id)
        elif client_id and client_secret:
            out = context.acquire_token_with_client_credentials(resource, client_id,
                                                                client_secret)
            # for service principal, we store the secret in the credential object for use when refreshing.
            out.update({'secret': client_secret})
        else:
            raise ValueError("No authentication method found for credentials")
        return out
    out = get_token_internal()

    out.update({'access': out['accessToken'], 'resource': resource,
                'refresh': out.get('refreshToken', False),
                'time': time.time(), 'tenant': tenant_id, 'client': client_id})

    return DataLakeCredential(out)


class DataLakeCredential:
    # Be careful modifying this. DataLakeCredential is a general class in azure, and we have to maintain parity.
    def __init__(self, token):
        self.token = token

    def signed_session(self):
        # type: () -> requests.Session
        """Create requests session with any required auth headers applied.

        :rtype: requests.Session
        """
        session = requests.Session()
        if time.time() - self.token['time'] > self.token['expiresIn'] - 100:
            self.refresh_token()

        scheme, token = self.token['tokenType'], self.token['access']
        header = "{} {}".format(scheme, token)
        session.headers['Authorization'] = header
        return session

    def refresh_token(self, authority=None):
        """ Refresh an expired authorization token

        Parameters
        ----------
        authority: string
            The full URI of the authentication authority to authenticate against (such as https://login.microsoftonline.com/)
        """
        if self.token.get('refresh', False) is False and (not self.token.get('secret') or not self.token.get('client')):
            raise ValueError("Token cannot be auto-refreshed.")

        if not authority:
            authority = 'https://login.microsoftonline.com/'

        context = adal.AuthenticationContext(authority +
                                             self.token['tenant'])

        if self.token.get('secret') and self.token.get('client'):
            out = context.acquire_token_with_client_credentials(self.token['resource'],
                                                                self.token['client'],
                                                                self.token['secret'])
            out.update({'secret': self.token['secret']})
        else:
            out = context.acquire_token_with_refresh_token(self.token['refresh'],
                                                           client_id=self.token['client'],
                                                           resource=self.token['resource'])
        # common items to update
        out.update({'access': out['accessToken'],
                    'time': time.time(), 'tenant': self.token['tenant'],
                    'resource': self.token['resource'], 'client': self.token['client']})

        self.token = out

class DatalakeRESTInterface:
    """ Call factory for webHDFS endpoints on ADLS

    Parameters
    ----------
    store_name: str
        The name of the Data Lake Store account to execute operations against.
    token: dict
        from `auth()` or `refresh_token()` or other ADAL source
    url_suffix: str (None)
        Domain to send REST requests to. The end-point URL is constructed
        using this and the store_name. If None, use default.
    api_version: str (2018-09-01)
        The API version to target with requests. Changing this value will
        change the behavior of the requests, and can cause unexpected behavior or
        breaking changes. Changes to this value should be undergone with caution.
    req_timeout_s: float(60)
        This is the timeout for each requests library call.
    kwargs: optional arguments to auth
        See ``auth()``. Includes, e.g., username, password, tenant; will pull
        values from environment variables if not provided.
    """

    ends = {
        # OP: (HTTP method, required fields, allowed fields)
        'APPEND': ('post', set(), {'append', 'offset', 'syncFlag', 'filesessionid', 'leaseid'}),
        'CHECKACCESS': ('get', set(), {'fsaction'}),
        'CONCAT': ('post', {'sources'}, {'sources'}),
        'MSCONCAT': ('post', set(), {'deleteSourceDirectory'}),
        'CREATE': ('put', set(), {'overwrite', 'write', 'syncFlag', 'filesessionid', 'leaseid'}),
        'DELETE': ('delete', set(), {'recursive'}),
        'GETCONTENTSUMMARY': ('get', set(), set()),
        'GETFILESTATUS': ('get', set(), set()),
        'LISTSTATUS': ('get', set(), {'listSize', 'listAfter'}),
        'MKDIRS': ('put', set(), set()),
        'OPEN': ('get', set(), {'offset', 'length', 'read', 'filesessionid'}),
        'RENAME': ('put', {'destination'}, {'destination'}),
        'SETOWNER': ('put', set(), {'owner', 'group'}),
        'SETPERMISSION': ('put', set(), {'permission'}),
        'SETEXPIRY': ('put', {'expiryOption'}, {'expiryOption', 'expireTime'}),
        'SETACL': ('put', {'aclSpec'}, {'aclSpec'}),
        'MODIFYACLENTRIES': ('put', {'aclSpec'}, {'aclSpec'}),
        'REMOVEACLENTRIES': ('put', {'aclSpec'}, {'aclSpec'}),
        'REMOVEACL': ('put', set(), set()),
        'MSGETACLSTATUS': ('get', set(), set()),
        'REMOVEDEFAULTACL': ('put', set(), set())
    }

    def __init__(self, store_name=default_store, token=None,
                 url_suffix=default_adls_suffix, api_version='2018-09-01', req_timeout_s=60, **kwargs):
        # in the case where an empty string is passed for the url suffix, it must be replaced with the default.
        url_suffix = url_suffix or default_adls_suffix
        self.local = threading.local()
        if token is None:
            token = auth(**kwargs)
        self.token = token

        # There is a case where the user can opt to exclude an API version, in which case
        # the service itself decides on the API version to use (it's default).
        self.api_version = api_version or None
        self.head = None
        self._check_token()  # Retryable method. Will ensure that signed_session token is current when we set it on next line
        self.head = {'Authorization': token.signed_session().headers['Authorization']}
        self.url = 'https://%s.%s/' % (store_name, url_suffix)
        self.webhdfs = 'webhdfs/v1/'
        self.extended_operations = 'webhdfsext/'
        self.user_agent = "python/{} ({}) {}/{} Azure-Data-Lake-Store-SDK-For-Python".format(
            platform.python_version(),
            platform.platform(),
            __name__,
            __version__)
        self.req_timeout_s = req_timeout_s

    @property
    def session(self):
        try:
            s = self.local.session
        except AttributeError:
            s = None
        if not s:
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=MAX_POOL_CONNECTIONS,
                pool_maxsize=MAX_POOL_CONNECTIONS)
            s = requests.Session()
            s.mount(self.url, adapter)
            self.local.session = s
        return s

    def _check_token(self, retry_policy= None):
        @retry_decorator_for_auth(retry_policy=retry_policy)
        def check_token_internal():
            cur_session = self.token.signed_session()
            if not self.head or self.head.get('Authorization') != cur_session.headers['Authorization']:
                self.head = {'Authorization': cur_session.headers['Authorization']}
                self.local.session = None
        check_token_internal()

    def _log_request(self, method, url, op, path, params, headers, retry_count):
        msg = "HTTP Request\n{} {}\n".format(method.upper(), url)
        msg += "{} '{}' {}\n\n".format(
            op, path,
            " ".join(["{}={}".format(key, params[key]) for key in params]))
        msg += "\n".join(["{}: {}".format(header, headers[header])
                          for header in headers if header != 'Authorization'])
        msg += "\nAuthorization header length:" + str(len(headers['Authorization']))
        if retry_count > 0:
            msg += "retry-count:{}".format(retry_count)
        logger.debug(msg)

    def _content_truncated(self, response):
        if 'content-length' not in response.headers:
            return False
        return int(response.headers['content-length']) > MAX_CONTENT_LENGTH

    def _log_response(self, response, payload=False):
        msg = "HTTP Response\n{}\n{}".format(
            response.status_code,
            "\n".join(["{}: {}".format(header, response.headers[header])
                       for header in response.headers]))
        if payload:
            msg += "\n\n{}".format(response.content[:MAX_CONTENT_LENGTH])
            if self._content_truncated(response):
                msg += "\n(Response body was truncated)"
        logger.debug(msg)

    def log_response_and_raise(self, response, exception, level=logging.ERROR):
        msg = "Exception " + repr(exception)
        if response is not None:
            msg += "\n{}\n{}".format(
                response.status_code,
                "\n".join([
                    "{}: {}".format(header, response.headers[header])
                    for header in response.headers]))
            msg += "\n\n{}".format(response.content[:MAX_CONTENT_LENGTH])
            if self._content_truncated(response):
                msg += "\n(Response body was truncated)"
        logger.log(level, msg)
        raise exception

    def _is_json_response(self, response):
        if 'content-type' not in response.headers:
            return False
        return response.headers['content-type'].startswith('application/json')

    def call(self, op, path='', is_extended=False, expected_error_code=None, retry_policy=None, headers = {},  **kwargs):
        """ Execute a REST call

        Parameters
        ----------
        op: str
            webHDFS operation to perform, one of `DatalakeRESTInterface.ends`
        path: str
            filepath on the remote system
        is_extended: bool (False)
            Indicates if the API call comes from the webhdfs extensions path or the basic webhdfs path.
            By default, all requests target the official webhdfs path. A small subset of custom convenience
            methods specific to Azure Data Lake Store target the extension path (such as SETEXPIRY).
        expected_error_code: int
            Optionally indicates a specific, expected error code, if any. In the event that this error
            is returned, the exception will be logged to DEBUG instead of ERROR stream. The exception
            will still be raised, however, as it is expected that the caller will expect to handle it
            and do something different if it is raised.
        kwargs: dict
            other parameters, as defined by the webHDFS standard and
            https://msdn.microsoft.com/en-us/library/mt710547.aspx
        """
        retry_policy = ExponentialRetryPolicy() if retry_policy is None else retry_policy
        if op not in self.ends:
            raise ValueError("No such op: %s", op)
        method, required, allowed = self.ends[op]
        allowed.add('api-version')
        data = kwargs.pop('data', b'')
        stream = kwargs.pop('stream', False)
        keys = set(kwargs)
        if required > keys:
            raise ValueError("Required parameters missing: %s",
                             required - keys)
        if keys - allowed > set():
            raise ValueError("Extra parameters given: %s",
                             keys - allowed)
        params = {'OP': op}
        if self.api_version:
            params['api-version'] = self.api_version

        params.update(kwargs)

        if is_extended:
            url = self.url + self.extended_operations
        else:
            url = self.url + self.webhdfs
        url += urllib.quote(path)

        retry_count = -1
        request_id = str(uuid.uuid1())
        while True:
            retry_count += 1
            last_exception = None
            self._check_token()
            try:
                response = self.__call_once(method=method,
                                            url=url,
                                            params=params,
                                            data=data,
                                            stream=stream,
                                            request_id=request_id,
                                            retry_count=retry_count,
                                            op=op,
                                            path=path,
                                            headers=headers,
                                            **kwargs)
                # Trigger download here so any errors can be retried. response.content is cached for future use.
                temp_download = response.content
            except requests.exceptions.RequestException as e:
                last_exception = e
                response = None

            request_successful = self.is_successful_response(response, last_exception)
            if request_successful or not retry_policy.should_retry(response, last_exception, retry_count):
                break

        if not request_successful and last_exception is not None:
            raise DatalakeRESTException('HTTP error: ' + repr(last_exception))
        
        exception_log_level = logging.ERROR
        if expected_error_code and response.status_code == expected_error_code:
            logger.log(logging.DEBUG, 'Error code: {} was an expected potential error from the caller. Logging the exception to the debug stream'.format(response.status_code))
            exception_log_level = logging.DEBUG

        if response.status_code == 403:
            self.log_response_and_raise(response, PermissionError(path), level=exception_log_level)
        elif response.status_code == 404:
            self.log_response_and_raise(response, FileNotFoundError(path), level=exception_log_level)
        elif response.status_code >= 400:
            err = DatalakeRESTException(
                'Data-lake REST exception: %s, %s' % (op, path))
            if self._is_json_response(response):
                out = response.json()
                if 'RemoteException' in out:
                    exception = out['RemoteException']['exception']
                    if exception == 'BadOffsetException':
                        err = DatalakeBadOffsetException(path)
                        self.log_response_and_raise(response, err, level=logging.DEBUG)
            self.log_response_and_raise(response, err, level=exception_log_level)
        else:
            self._log_response(response)

        if self._is_json_response(response):
            out = response.json()
            if out.get('boolean', True) is False:
                err = DatalakeRESTException(
                    'Operation failed: %s, %s' % (op, path))
                self.log_response_and_raise(response, err)
            return out
        return response

    def is_successful_response(self, response, exception):
        if exception is not None:
            return False
        if 100 <= response.status_code < 300:
            return True
        return False

    def __call_once(self, method, url, params, data, stream, request_id, retry_count, op, path='', headers={}, **kwargs):
        func = getattr(self.session, method)
        req_headers = self.head.copy()
        req_headers['x-ms-client-request-id'] = request_id + "." + str(retry_count)
        req_headers['User-Agent'] = self.user_agent
        req_headers.update(headers)
        self._log_request(method, url, op, urllib.quote(path), kwargs, req_headers, retry_count)
        return func(url, params=params, headers=req_headers, data=data, stream=stream, timeout=self.req_timeout_s)

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop('local', None)
        return state

"""
Not yet implemented (or not applicable)
http://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/WebHDFS.html

GETFILECHECKSUM
GETHOMEDIRECTORY
GETDELEGATIONTOKEN n/a - use auth
GETDELEGATIONTOKENS n/a - use auth
GETXATTRS
LISTXATTRS
CREATESYMLINK n/a
SETREPLICATION n/a
SETTIMES
RENEWDELEGATIONTOKEN n/a - use auth
CANCELDELEGATIONTOKEN n/a - use auth
CREATESNAPSHOT
RENAMESNAPSHOT
SETXATTR
REMOVEXATTR
"""
