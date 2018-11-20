# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import copy
import json
import os
import requests
import urllib3
import zipfile
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
        self.__password = None
        self.__scm_url = None
        self.__auth_headers = None

    def download_bot_zip(self, file_save_path, folder_path):
        if not self.__initialized:
            self.__initialize()

        headers = self.__get_application_octet_stream_headers()
        # Download source code in zip format from KUDU
        response = requests.get(self.__scm_url + '/api/zip/site/clirepo/', headers=headers)
        # If the status_code is not 200, the source code was not successfully retrieved.
        # Run the prepareSrc.cmd to zip up the code and prepare it for download.
        if response.status_code != 200:
            # try getting the bot from wwwroot instead
            payload = {
                'command': 'PostDeployScripts\\prepareSrc.cmd {0}'.format(self.__password),
                'dir': r'site\wwwroot'
            }
            prepareSrc_response = requests.post(self.__scm_url + '/api/command',
                                                data=json.dumps(payload),
                                                headers=self.__get_application_json_headers())
            HttpResponseValidator.check_response_status(prepareSrc_response)

            # Overwrite previous "response" with bot-src.zip.
            # TODO: Why would we zip the file up to site/bot-src.zip and not site/clirepo?
            # TODO: Should we delete this code? Should we place it in the right place (site/clirepo) the first time?
            response = requests.get(self.__scm_url + '/api/vfs/site/bot-src.zip',
                                    headers=headers)
            HttpResponseValidator.check_response_status(response)

        download_path = os.path.join(file_save_path, 'download.zip')
        with open(os.path.join(file_save_path, 'download.zip'), 'wb') as f:
            f.write(response.content)
        zip_ref = zipfile.ZipFile(download_path)
        zip_ref.extractall(folder_path)
        zip_ref.close()
        os.remove(download_path)

    def enable_zip_deploy(self, zip_file_path):
        if not self.__initialized:
            self.__initialize()

        zip_url = self.__scm_url + '/api/zipdeploy'

        headers = self.__get_application_octet_stream_headers()

        # Read file content
        with open(os.path.realpath(os.path.expanduser(zip_file_path)), 'rb') as fs:
            zip_content = fs.read()
            r = requests.post(zip_url, data=zip_content, headers=self.__auth_headers)
            if r.status_code != 200:
                raise CLIError("Zip deployment {} failed with status code '{}' and reason '{}'".format(
                    zip_url, r.status_code, r.text))

        # On successful deployment navigate to the app, display the latest deployment JSON response.
        response = requests.get(self.__scm_url + '/api/deployments/latest', headers=self.__auth_headers)
        HttpResponseValidator.check_response_status(response)
        return response.json()

    # TODO: turn into getter
    def get_bot_site_name(self):
        return self.bot_site_name

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

    def __get_application_json_headers(self):
        headers = copy.deepcopy(self.__auth_headers)
        headers['content-type'] = 'application/json'
        return headers

    def __get_application_octet_stream_headers(self):
        headers = copy.deepcopy(self.__auth_headers)
        headers['content-type'] = 'application/octet-stream'
        return headers

    def __initialize(self):
        self.bot_site_name = WebAppOperations.get_bot_site_name(self.__bot.properties.endpoint)
        user_name, password = WebAppOperations.get_site_credential(self.__cmd.cli_ctx,
                                                                   self.__resource_group_name,
                                                                   self.bot_site_name,
                                                                   None)

        # Store the password for download_bot_zip:
        self.__password = password
        self.__scm_url = WebAppOperations.get_scm_url(self.__cmd,
                                                      self.__resource_group_name,
                                                      self.bot_site_name,
                                                      None)

        self.__auth_headers = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(user_name, password))
        self.__initialized = True
