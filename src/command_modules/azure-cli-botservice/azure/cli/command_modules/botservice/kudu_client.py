# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import copy
import json
import os
import zipfile
import requests
import urllib3

try:
    # Try importing Python 3 urllib.parse
    from urllib.parse import quote
except ImportError:
    # If urllib.parse was not imported, use Python 2 module urlparse
    from urllib import quote  # pylint: disable=import-error

from knack.util import CLIError
from azure.cli.command_modules.botservice.http_response_validator import HttpResponseValidator
from azure.cli.command_modules.botservice.web_app_operations import WebAppOperations


class KuduClient:  # pylint:disable=too-many-instance-attributes
    def __init__(self, cmd, resource_group_name, name, bot, logger):
        self.__cmd = cmd
        self.__resource_group_name = resource_group_name
        self.__name = name
        self.__bot = bot
        self.__logger = logger

        # Properties set after self.__initialize() is called.
        self.__initialized = False
        self.__password = None
        self.__scm_url = None
        self.__auth_headers = None
        self.bot_site_name = None

    def download_bot_zip(self, file_save_path, folder_path):
        """Download bot's source code from Kudu.

        This method looks for the zipped source code in the site/clirepo/ folder on Kudu. If the code is not there, the
        contents of site/wwwroot are zipped and then downloaded.

        :param file_save_path: string
        :param folder_path: string
        :return: None
        """
        if not self.__initialized:
            self.__initialize()

        headers = self.__get_application_octet_stream_headers()
        # Download source code in zip format from Kudu
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

    def get_bot_file(self, bot_file):
        """Retrieve the .bot file from Kudu.

        :param bot_file:
        :return:
        """
        if not self.__initialized:
            self.__initialize()

        if bot_file.startswith('./') or bot_file.startswith('.\\'):
            bot_file = bot_file[2:]
        # Format backslashes to forward slashes and URL escape
        bot_file = quote(bot_file.replace('\\', '/'))
        request_url = self.__scm_url + '/api/vfs/site/wwwroot/' + bot_file
        self.__logger.info('Attempting to retrieve .bot file content from %s' % request_url)
        response = requests.get(request_url, headers=self.__get_application_octet_stream_headers())
        HttpResponseValidator.check_response_status(response)
        self.__logger.info('Bot file successfully retrieved from Kudu.')
        return json.loads(response.text)

    def install_node_dependencies(self):
        """Installs Node.js dependencies at `site/wwwroot/` for Node.js bots.

        This method is only called when the detected bot is a Node.js bot.

        :return: Dictionary with results of the HTTP Kudu request
        """
        if not self.__initialized:
            self.__initialize()

        payload = {
            'command': 'npm install',
            'dir': r'site\wwwroot'
        }
        # npm install can take a very long time to complete. By default, Azure's load balancer will terminate
        # connections after 230 seconds of no inbound or outbound packets. This timeout is not configurable.
        try:
            response = requests.post(self.__scm_url + '/api/command', data=json.dumps(payload),
                                     headers=self.__get_application_json_headers())
            HttpResponseValidator.check_response_status(response)
        except CLIError as e:
            if response.status_code == 500 and 'The request timed out.' in response.text:
                self.__logger.warning('npm install is taking longer than expected and did not finish within the '
                                      'Azure-specified timeout of 230 seconds.')
                self.__logger.warning('The installation is likely still in progress. This is a known issue, please wait'
                                      ' a short while before messaging your bot. You can also visit Kudu to manually '
                                      'install the npm dependencies. (https://github.com/projectkudu/kudu/wiki)')
                self.__logger.warning('Your Kudu website for this bot is: %s' % self.__scm_url)
                self.__logger.warning('\nYou can also use `--keep-node-modules` in your `az bot publish` command to '
                                      'not `npm install` the dependencies for the bot on Kudu.')
            else:
                raise e

        return response.json()

    def publish(self, zip_file_path, keep_node_modules, detected_language):
        """Publishes zipped bot source code to Kudu.

        Performs the following steps:
        1. Empties the `site/clirepo/` folder on Kudu
        2. Pushes the code to `site/clirepo/`
        3. Deploys the code via the zipdeploy API. (https://github.com/projectkudu/kudu/wiki/REST-API#zip-deployment)
        4. Gets the results of the latest Kudu deployment

        :param zip_file_path:
        :return: Dictionary with results of the latest deployment
        """
        if not self.__initialized:
            self.__initialize()
        self.__empty_source_folder()

        headers = self.__get_application_octet_stream_headers()
        with open(zip_file_path, 'rb') as fs:
            zip_content = fs.read()
            response = requests.put(self.__scm_url + '/api/zip/site/clirepo',
                                    headers=headers,
                                    data=zip_content)
            HttpResponseValidator.check_response_status(response)

        return self.__enable_zip_deploy(zip_file_path, keep_node_modules, detected_language)

    def __empty_source_folder(self):
        """Remove the `clirepo/` folder from Kudu.

        This method is called from KuduClient.publish() in preparation for uploading the user's local source code.
        After removing the folder from Kudu, the method performs another request to recreate the `clirepo/` folder.
        :return:
        """
        # The `clirepo/` folder contains the zipped up source code
        payload = {
            'command': 'rm -rf clirepo && mkdir clirepo',
            'dir': r'site'
        }
        headers = self.__get_application_json_headers()
        response = requests.post(self.__scm_url + '/api/command', data=json.dumps(payload), headers=headers)
        HttpResponseValidator.check_response_status(response)

    def __empty_wwwroot_folder_except_for_node_modules(self):
        """Empty site/wwwroot/ folder but retain node_modules folder.
        :return:
        """
        self.__logger.info('Removing all files and folders from "site/wwwroot/" except for node_modules.')
        payload = {
            'command': '(for /D %i in (.\\*) do if not %~nxi == node_modules rmdir /s/q %i) && (for %i in (.\\*) '
                       'del %i)',
            'dir': r'site\wwwroot'
        }
        headers = self.__get_application_json_headers()
        response = requests.post(self.__scm_url + '/api/command', data=json.dumps(payload), headers=headers)
        HttpResponseValidator.check_response_status(response)
        self.__logger.info('All files and folders successfully removed from "site/wwwroot/" except for node_modules.')

    def __empty_wwwroot_folder(self):
        """Empty the site/wwwroot/ folder from Kudu.

        Empties the site/wwwroot/ folder by removing the entire directory, and then recreating it. Called when
        publishing a bot to Kudu.
        """
        self.__logger.info('Emptying the "site/wwwroot/" folder on Kudu in preparation for publishing.')
        payload = {
            'command': 'rm -rf wwwroot && mkdir wwwroot',
            'dir': r'site'
        }
        headers = self.__get_application_json_headers()
        response = requests.post(self.__scm_url + '/api/command', data=json.dumps(payload), headers=headers)
        HttpResponseValidator.check_response_status(response)
        self.__logger.info('"site/wwwroot/" successfully emptied.')

    def __enable_zip_deploy(self, zip_file_path, keep_node_modules, detected_language):
        """Pushes local bot's source code in zip format to Kudu for deployment.

        This method deploys the zipped bot source code via Kudu's zipdeploy API. This API does not run any build
        processes such as `npm install`, `dotnet restore`, `dotnet publish`, etc.

        :param zip_file_path: string
        :return: Dictionary with results of the latest deployment
        """
        if not self.__initialized:
            self.__initialize()

        zip_url = self.__scm_url + '/api/zipdeploy'
        headers = self.__get_application_octet_stream_headers()
        if not keep_node_modules or detected_language == 'Csharp':
            self.__empty_source_folder()
        else:
            self.__empty_wwwroot_folder_except_for_node_modules()

        with open(os.path.realpath(os.path.expanduser(zip_file_path)), 'rb') as fs:
            zip_content = fs.read()
            self.__logger.info('Source code read, uploading to Kudu.')
            r = requests.post(zip_url, data=zip_content, headers=headers)
            if r.status_code != 200:
                raise CLIError("Zip deployment {} failed with status code '{}' and reason '{}'".format(
                    zip_url, r.status_code, r.text))
            self.__logger.info('Source code successfully uploaded.')

        self.__logger.info('Retrieving the latest deployment info.')
        # On successful deployment navigate to the app, display the latest deployment JSON response.
        response = requests.get(self.__scm_url + '/api/deployments/latest', headers=self.__auth_headers)
        HttpResponseValidator.check_response_status(response)
        return response.json()

    def __get_application_json_headers(self):
        headers = copy.deepcopy(self.__auth_headers)
        headers['content-type'] = 'application/json'
        return headers

    def __get_application_octet_stream_headers(self):
        headers = copy.deepcopy(self.__auth_headers)
        headers['content-type'] = 'application/octet-stream'
        return headers

    def __initialize(self):
        """Generates necessary data for performing calls to Kudu based off of data passed in on initialization.

        :return: None
        """
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
