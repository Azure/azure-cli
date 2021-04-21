# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger

from ._client_factory import web_client_factory
from ._constants import (GITHUB_OAUTH_CLIENT_ID, GITHUB_OAUTH_REDIRECT_URI, GITHUB_OAUTH_SCOPES)

logger = get_logger(__name__)

def get_github_access_token(cmd, scope_list=None):
    import os
    random_state = os.urandom(5).hex()

    authorize_url = 'https://github.com/login/oauth/authorize?' \
                    'client_id={}&state={}&redirect_uri={}'.format(
                        GITHUB_OAUTH_CLIENT_ID, random_state, GITHUB_OAUTH_REDIRECT_URI)
    if scope_list:
        for scope in scope_list:
            if scope not in GITHUB_OAUTH_SCOPES:
                raise ValidationError("Requested github oauth scope is invalid")
        _scope_string = "&scope="
        for i in range(len(scope_list)):
            if i != 0:
                _scope_string += "+"
            _scope_string += scope_list[i]
        authorize_url += _scope_string
    logger.warning('Opening OAuth URL')

    # Get code to exchange for access token
    access_code = _start_http_server(random_state, authorize_url)

    if access_code:
        client = web_client_factory(cmd.cli_ctx)
        response = client.generate_github_access_token_for_appservice_cli_async(access_code, random_state)

        if response.access_token:
            return response.access_token
    return None


def _start_http_server(random_state, authorize_url):
    ip = '127.0.0.1'
    port = 3000
    
    import http.server
    import webbrowser
    import socketserver
    import urllib.parse as urlparse

    class Server(socketserver.TCPServer):
        allow_reuse_address = True

    class CallBackHandler(http.server.BaseHTTPRequestHandler):
        access_token = None
        
        def do_GET(self):
            parsed_params = urlparse.parse_qs(urlparse.urlparse(self.path).query)
            received_state = parsed_params.get('state', [None])[0]
            received_code = parsed_params.get('code', [None])[0]

            if (self.path.startswith('/TokenAuthorize') and received_state and received_code and (random_state == received_state)):
                CallBackHandler.received_code = received_code
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write('GitHub account authenticated. You may close this tab'.encode('utf-8'))
            else:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write('Unable to authenticate GitHub account. Please close this tab'.encode('utf-8'))

    try:
        server = Server((ip, port), CallBackHandler)
        webbrowser.open(authorize_url)
        logger.warning('Listening at port: {}'.format(port))
        server.handle_request()
    except Exception as e:
        raise CLIError('Socket error: {}. Please try again, or provide personal access token'.format(e))

    return CallBackHandler.received_code if hasattr(CallBackHandler, 'received_code') else None
