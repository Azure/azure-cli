# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import base64
import hashlib
import hmac
import urllib
from datetime import datetime
import six

import azure.cli.command_modules.appconfig._azconfig.constants as constants


def get_endpoint_from_connection_string(connection_string):
    endpoint, _, _ = __parse_connection_string(connection_string)
    return endpoint


def generate_request_header(method,
                            custom_headers,
                            datetime_=None,
                            if_match_etag=None,
                            if_none_match_etag=None):
    header = custom_headers

    if method == constants.HttpMethods.Get:
        header.update(_generate_get_accept_header(if_match_etag))
    elif method == constants.HttpMethods.Delete:
        header.update(_generate_delete_content_type_header(if_match_etag))
    elif method == constants.HttpMethods.Put:
        header.update(_generate_put_header(if_match_etag, if_none_match_etag))
    if datetime_ is not None:
        header[constants.HttpHeaders.AcceptDateTime] = datetime_

    return header


def _generate_get_accept_header(if_match_etag=None):
    header = {}
    header[constants.HttpHeaders.Accept] = constants.HttpHeaderValues.MediaTypeApplication
    if if_match_etag is not None:
        header[constants.HttpHeaders.IfMatch] = '"{}"'.format(if_match_etag)
    return header


def _generate_delete_content_type_header(if_match_etag=None):
    header = {}
    header[constants.HttpHeaders.ContentType] = constants.HttpHeaderValues.MediaTypeKeyValueApplication
    if if_match_etag is not None:
        header[constants.HttpHeaders.IfMatch] = '"{}"'.format(if_match_etag)
    return header


def _generate_put_header(if_match_etag=None, if_none_match_etag=None):
    header = {}
    header[constants.HttpHeaders.ContentType] = constants.HttpHeaderValues.MediaTypeKeyValueApplication
    if if_match_etag is not None:
        header[constants.HttpHeaders.IfMatch] = '"{}"'.format(if_match_etag)
    if if_none_match_etag is not None:
        header[constants.HttpHeaders.IfNoneMatch] = '"{}"'.format(
            if_none_match_etag)
    return header


def sign_request(method, url, body, connection_string):
    verb = method.upper()
    host, credential, secret = __parse_connection_string(connection_string)

    # Get the path and query from url, which looks like https://host/path/query
    query_url = str(url[len(host) + 8:])

    signed_headers = "x-ms-date;host;x-ms-content-sha256"

    utc_now = __get_current_utc_time()

    if six.PY2:
        content_digest = hashlib.sha256(bytes(body)).digest()
    else:
        content_digest = hashlib.sha256(bytes(body, 'utf-8')).digest()

    content_hash = base64.b64encode(content_digest).decode('utf-8')
    string_to_sign = verb + '\n' + query_url + '\n' + \
        utc_now + ';' + host + ';' + content_hash

    # decode secret
    if six.PY2:
        decoded_secret = base64.b64decode(secret)
        digest = hmac.new(decoded_secret, bytes(
            string_to_sign), hashlib.sha256).digest()
    else:
        decoded_secret = base64.b64decode(secret, validate=True)
        digest = hmac.new(decoded_secret, bytes(
            string_to_sign, 'utf-8'), hashlib.sha256).digest()

    signature = base64.b64encode(digest).decode('utf-8')

    return {
        "x-ms-date": utc_now,
        "x-ms-content-sha256": content_hash,
        "Authorization": "HMAC-SHA256 Credential=" + credential + "&SignedHeaders=" + signed_headers + "&Signature=" + signature
    }


def __get_current_utc_time():
    return str(datetime.utcnow().strftime("%b, %d %Y %H:%M:%S ")) + "GMT"


def __parse_connection_string(connection_string):
    # connection_string looks like Endpoint=https://xxxxx;Id=xxxxx;Secret=xxxx
    segments = connection_string.split(';')
    if len(segments) != 3:
        raise ValueError('Invalid connection string.')

    endpoint = ''
    id_ = ''
    secret = ''
    for segment in segments:
        segment = segment.strip()
        if segment.startswith('Endpoint'):
            endpoint = str(segment[17:])
        elif segment.startswith('Id'):
            id_ = str(segment[3:])
        elif segment.startswith('Secret'):
            secret = str(segment[7:])
        else:
            raise ValueError('Invalid connection string.')

    if not endpoint or not id_ or not secret:
        raise ValueError('Invalid connection string.')

    return endpoint, id_, secret


def __unescape_encode_keyword(string):
    if string is not None:
        import ast

        # ast library requires quotes around string
        string = '"{0}"'.format(string)
        string = ast.literal_eval(string)

        if six.PY2:
            # python 2 compatible
            return urllib.quote(string, safe='')  # pylint: disable=E1101

        return urllib.parse.quote(string, safe='')
    return string


def unescape_encode_key_and_label(key=None, label=None):
    return __unescape_encode_keyword(key), __unescape_encode_keyword(label)
