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
import warnings
import time
import urllib.parse as urllib
from .retry import ExponentialRetryPolicy

# 3rd party imports
import requests
import requests.exceptions

_http_cache = {}  # Useful for MSAL. https://msal-python.readthedocs.io/en/latest/#msal.PublicClientApplication.params.http_cache

# this is required due to github issue, to ensure we don't lose perf from openPySSL: https://github.com/pyca/pyopenssl/issues/625
def enforce_no_py_open_ssl():
    try:
        from requests.packages.urllib3.contrib.pyopenssl import extract_from_urllib3
    except ImportError:
        # in the case of debian/ubuntu system packages, the import is slightly different
        try:
            from urllib3.contrib.pyopenssl import extract_from_urllib3
        except ImportError:
            # if OpenSSL is unavailable in both cases then there is no need to "undo" it.
            return
    extract_from_urllib3()

# Suppress urllib3 warning when accessing pyopenssl. This module is being removed
# soon, but we already handle its absence.
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message=r"'urllib3.contrib.pyopenssl' module is deprecated and will be removed.+",
    )
    enforce_no_py_open_ssl()

from .exceptions import DatalakeBadOffsetException, DatalakeRESTException
from .exceptions import FileNotFoundError, PermissionError
from . import __version__

logger = logging.getLogger(__name__)

default_store = os.environ.get('azure_data_lake_store_name', None)
default_adls_suffix = os.environ.get('azure_data_lake_store_url_suffix', 'azuredatalakestore.net')

# Constants
DEFAULT_RESOURCE_ENDPOINT = "https://datalake.azure.net/"
MAX_CONTENT_LENGTH = 2**16

# This is the maximum number of active pool connections
# that are supported during a single operation (such as upload or download of a file).
# This ensures that no connections are prematurely evicted, which has negative performance implications.
MAX_POOL_CONNECTIONS = 1024

class DatalakeRESTInterface:
    """ Call factory for webHDFS endpoints on ADLS

    Parameters
    ----------
    store_name: str
        The name of the Data Lake Store account to execute operations against.
    token: dict
        from `auth()` or `refresh_token()` or other MSAL source
    url_suffix: str (None)
        Domain to send REST requests to. The end-point URL is constructed
        using this and the store_name. If None, use default.
    api_version: str (2018-09-01)
        The API version to target with requests. Changing this value will
        change the behavior of the requests, and can cause unexpected behavior or
        breaking changes. Changes to this value should be undergone with caution.
    req_timeout_s: float(60)
        This is the timeout for each requests library call.
    scopes: str (None)
        The scopes to use for the token. If not provided, the default https://datalake.azure.net//.default is used.
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

    def __init__(self, store_name=default_store, token_credential=None, scopes=None, url_suffix=default_adls_suffix, **kwargs):
        # in the case where an empty string is passed for the url suffix, it must be replaced with the default.
        url_suffix = url_suffix or default_adls_suffix
        self.local = threading.local()
        self.token_credential = token_credential
        self.scopes = scopes or "https://datalake.azure.net//.default"
        self.AccessToken = None

        # There is a case where the user can opt to exclude an API version, in which case
        # the service itself decides on the API version to use (it's default).
        self.api_version = kwargs.pop('api_version', '2018-09-01')
        self.req_timeout_s = kwargs.pop('req_timeout_s', 60)

        self.url = 'https://%s.%s/' % (store_name, url_suffix)

        self.webhdfs = 'webhdfs/v1/'
        self.extended_operations = 'webhdfsext/'
        self.user_agent = "python/{} ({}) {}/{} Azure-Data-Lake-Store-SDK-For-Python".format(
            platform.python_version(),
            platform.platform(),
            __name__,
            __version__)

    def get_refreshed_bearer_token(self):
        # Check if the token is about to expire in 300 seconds and refresh it if necessary
        if self.AccessToken is None or time.time() > self.AccessToken.expires_on - 300:
            self.AccessToken = self.token_credential.get_token(self.scopes)
        return self.AccessToken.token

    @property
    def session(self):
        bearer_token = self.get_refreshed_bearer_token()
        try:
            s = self.local.session
            s.headers['Authorization'] = "Bearer " + bearer_token
        except AttributeError:
            s = None
        if not s:
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=MAX_POOL_CONNECTIONS,
                pool_maxsize=MAX_POOL_CONNECTIONS)
            s = requests.Session()
            s.mount(self.url, adapter)
            s.headers['Authorization'] = "Bearer " + bearer_token
            self.local.session = s
        return s

    def _log_request(self, method, url, op, path, params, headers, retry_count):
        msg = u"HTTP Request\n{} {}\n".format(method.upper(), url)
        param_str = u" ".join([u"{}={}".format(key, params[key]) for key in params])
        msg += u"{} '{}' {}\n\n".format(
            op, path, param_str)
        msg += u"\n".join([u"{}: {}".format(header, headers[header])
                          for header in headers if header != 'Authorization'])
        msg += u"\nAuthorization header length:" + str(len(headers['Authorization']))
        if retry_count > 0:
            msg += u"retry-count:{}".format(retry_count)
        logger.debug(msg)

    def _content_truncated(self, response):
        if 'content-length' not in response.headers:
            return False
        return int(response.headers['content-length']) > MAX_CONTENT_LENGTH

    def _log_response(self, response, payload=False):
        msg = u"HTTP Response\n{}\n{}".format(
            response.status_code,
            u"\n".join([u"{}: {}".format(header, response.headers[header])
                       for header in response.headers]))
        if payload:
            msg += u"\n\n{}".format(response.content[:MAX_CONTENT_LENGTH])
            if self._content_truncated(response):
                msg += u"\n(Response body was truncated)"
        logger.debug(msg)

    def log_response_and_raise(self, response, exception, level=logging.ERROR):
        msg = u"Exception " + repr(exception)
        if response is not None:
            msg += u"\n{}\n{}".format(
                response.status_code,
                u"\n".join([
                    u"{}: {}".format(header, response.headers[header])
                    for header in response.headers]))
            msg += u"\n\n{}".format(response.content[:MAX_CONTENT_LENGTH])
            if self._content_truncated(response):
                msg += u"\n(Response body was truncated)"
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
        req_headers = {'Authorization': self.session.headers['Authorization']}
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
https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/WebHDFS.html

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
