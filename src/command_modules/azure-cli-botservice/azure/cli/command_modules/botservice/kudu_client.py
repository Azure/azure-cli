# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import requests
import urllib3
from knack.util import CLIError
from .http_response_validator import HttpResponseValidator
from .web_app_operations import WebAppOperations


class KuduClient:
    def __init__(self, cmd, resource_group_name, name, bot):
        self.__cmd = cmd
        self.__resource_group_name = resource_group_name
        self.__name = name
        self.__bot = bot
        self.__initialized = False
        self.__scm_url = None
        self.__auth_headers = None

    def enable_zip_deploy(self, zip_file_path):
        if not self.__initialized:
            self.__initialize()

        zip_url = self.__scm_url + '/api/zipdeploy'

        headers = self.__auth_headers
        headers['content-type'] = 'application/octet-stream'

        # Read file content
        with open(os.path.realpath(os.path.expanduser(zip_file_path)), 'rb') as fs:
            zip_content = fs.read()
            r = requests.post(zip_url, data=zip_content, headers=headers)
            if r.status_code != 200:
                raise CLIError("Zip deployment {} failed with status code '{}' and reason '{}'".format(
                    zip_url, r.status_code, r.text))

        # On successful deployment navigate to the app, display the latest deployment JSON response.
        response = requests.get(self.__scm_url + '/api/deployments/latest', headers=self.__auth_headers)
        HttpResponseValidator.check_response_status(response)
        return response.json()

    def install_node_dependencies(self):
        """Installs Node.js dependencies at site/wwwroot for Node.js bots.

        Is only called when the detected bot is a Node.js bot.
        :return:
        """
        if not self.__initialized:
            self.__initialize()

        payload = {
            'command': 'npm install',
            'dir': r'site\wwwroot'
        }
        response = requests.post(self.__scm_url + '/api/command', data=json.dumps(payload), headers=self.__auth_headers)
        HttpResponseValidator.check_response_status(response)
        return response.json()

    def publish(self, zip_file_path):
        if not self.__initialized:
            self.__initialize()
        self.__empty_source_folder()

        headers = self.__auth_headers
        headers['content-type'] = 'application/octet-stream'
        with open(zip_file_path, 'rb') as fs:
            zip_content = fs.read()
            response = requests.put(self.__scm_url + '/api/zip/site/clirepo',
                                    headers=self.__auth_headers,
                                    data=zip_content)
            HttpResponseValidator.check_response_status(response)

        return self.enable_zip_deploy(zip_file_path)

    def __empty_source_folder(self):
        # the `clirepo/` folder contains the zipped up source code
        payload = {
            'command': 'rm -rf clirepo',
            'dir': r'site'
        }
        headers = self.__auth_headers
        headers['content-type'] = 'application/json'
        delete_clirepo_response = requests.post(self.__scm_url + '/api/command',
                                                data=json.dumps(payload),
                                                headers=headers)
        # TODO: Verify the necessity of this line
        response = requests.put(self.__scm_url + '/api/vfs/site/clirepo/', headers=headers)
        # TODO: Think about using Response.ok
        HttpResponseValidator.check_response_status(response, 201)

    def __initialize(self):
        site_name = WebAppOperations.get_bot_site_name(self.__bot.properties.endpoint)
        user_name, password = WebAppOperations.get_site_credential(self.__cmd.cli_ctx,
                                                                   self.__resource_group_name,
                                                                   site_name,
                                                                   None)
        self.__scm_url = WebAppOperations.get_scm_url(self.__cmd,
                                                      self.__resource_group_name,
                                                      site_name,
                                                      None)

        self.__auth_headers = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(user_name, password))
        self.__initialized = True
