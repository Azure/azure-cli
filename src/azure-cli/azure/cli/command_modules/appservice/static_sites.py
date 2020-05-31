# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.util import sdk_no_wait


def list_staticsites(cmd, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if resource_group_name:
        result = list(client.get_static_sites_by_resource_group(resource_group_name))
    else:
        result = list(client.list())
    return result


def show_staticsite(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.get_static_site(resource_group_name, name)


def list_staticsite_domains(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_custom_domains(resource_group_name, name)


def list_staticsite_secrets(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_secrets(resource_group_name, name)


def list_staticsite_functions(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_functions(resource_group_name, name)


def list_staticsite_function_app_settings(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_function_app_settings(resource_group_name, name)


def create_staticsites(cmd, resource_group_name, name, location,
                       source, token=None, branch='master',
                       app_location='/', api_location='api', app_artifact_location=None,
                       custom_domains=None, tags=None, no_wait=False):
    if not token:
        token = _get_github_access_token()

    StaticSiteARMResource, StaticSiteBuildProperties, SkuDescription = cmd.get_models(
        'StaticSiteARMResource', 'StaticSiteBuildProperties', 'SkuDescription')

    build = StaticSiteBuildProperties(
        app_location=app_location,
        api_location=api_location,
        app_artifact_location=app_artifact_location)

    sku = SkuDescription(name='Free', tier='Free')

    staticsite_deployment_properties = StaticSiteARMResource(
        name=name,
        location=location,
        type='Microsoft.Web/staticsites',
        tags=tags,
        repository_url=source,
        branch=branch,
        custom_domains=custom_domains,
        repository_token=token,
        build_properties=build,
        sku=sku)

    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return sdk_no_wait(no_wait, client.create_or_update_static_site,
                       resource_group_name=resource_group_name, name=name,
                       static_site_envelope=staticsite_deployment_properties)


def update_staticsites(cmd, no_wait=False):
    return


def delete_staticsite(cmd, resource_group_name, name, no_wait=False):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return sdk_no_wait(no_wait, client.delete_static_site,
                       resource_group_name=resource_group_name, name=name)


def _get_github_access_token():
    import os
    RANDOM_STRING = os.urandom(5).hex()
    CLIENT_ID = 'OAUTH_APP_CLIENT_ID'
    CLIENT_SECRET = 'OAUTH_APP_CLIENT_SECRET'

    authorize_url = 'https://github.com/login/oauth/authorize?' + \
                    'client_id=' + CLIENT_ID + \
                    '&client_secret=' + CLIENT_SECRET + \
                    '&state=' + RANDOM_STRING + \
                    '&scope=repo%20workflow'

    print('opening auth url')
    print(authorize_url)

    import webbrowser
    webbrowser.open(authorize_url)

    auth = _start_http_server(RANDOM_STRING, CLIENT_ID, CLIENT_SECRET)

    print('auth: ' + auth)

    return auth


def _start_http_server(sent_state, client_id, client_secret):
    ip = '127.0.0.1'
    port = 8080

    # redirect_uri = 'http://' + ip + ':' + port + '/authorization-code/callback'
    # socket_str = 'tcp://' + ip + ':' + port
    #
    # response_ok = "HTTP/1.0 200 OK\r\n" + \
    #               "Content-Type: text/plain\r\n" + \
    #               "\r\n" + "Ok. You may close this tab and return to the shell.\r\n"
    #
    # response_err = "HTTP/1.0 400 Bad Request\r\n" + \
    #                "Content-Type: text/plain\r\n" + \
    #                "\r\n" + "Bad Request\r\n"

    import http.server
    import socketserver

    class CallBackHandler(http.server.BaseHTTPRequestHandler):
        CallBackHandler.access_token = None
        CallBackHandler.state = sent_state
        CallBackHandler.client_id = client_id
        CallBackHandler.client_secret = client_secret

        def do_GET(self):
            if self.command == 'GET' and self.path.startswith('/authorization-code/callback') and '?code=' in self.path and '&state=' in self.path:
                print('path is: ' + self.path)
                received_state = self.path.split('&state=')[1]
                code = self.path.split('code=')[1].split('&')[0]

                print('state: ' + received_state)
                print('code: ' + code)

                if received_state == CallBackHandler.state:
                    import requests

                    url = 'https://github.com/login/oauth/access_token'
                    content = {
                        'client_id': CallBackHandler.client_id,
                        'client_secret': CallBackHandler.client_secret,
                        'code': code,
                        'state': received_state
                    }

                    response = requests.post(url, content)

                    print('response: ' + response.text)

                    CallBackHandler.access_token = response.text.split('access_token=')[1].split('&')[0]
                    print('access_token: ' + CallBackHandler.access_token)

            self.send_response(200)

    with socketserver.TCPServer((ip, port), CallBackHandler) as httpd:
        print("serving at port", port)
        httpd.handle_request()

    return CallBackHandler.access_token


def _get_staticsites_client_factory(cli_ctx, api_version=None):
    from azure.mgmt.web import WebSiteManagementClient
    client = get_mgmt_service_client(cli_ctx, WebSiteManagementClient).static_sites
    if api_version:
        client.api_version = api_version
    return client
