# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import requests
from knack.util import CLIError
from azure.cli.command_modules.botservice import adal_authenticator


class ConvergedApp:  # pylint:disable=too-few-public-methods

    app_provision_api_url = 'https://dev.botframework.com/api/botApp/provisionConvergedApp?name={0}'

    @staticmethod
    def provision(bot_name, verbose=False):

        # Use our authenticator to acquire a user token with a custom audience
        token = adal_authenticator.AdalAuthenticator.acquire_token()
        access_token = token['accessToken']

        # Prepare headers to call dev portal converged app provisioning API
        headers = {'Authorization': 'Bearer {0}'.format(access_token)}

        # Provision app
        response = requests.post(
            ConvergedApp.app_provision_api_url.format(bot_name),
            headers=headers
        )

        # TODO: Verbose logging
        # TODO: Fix this status_code check. If any status code below 400 is acceptable, check for response.ok instead of
        # a specific status code. See http://docs.python-requests.org/en/master/api/#requests.Response.ok
        if response.status_code not in [201]:
            if not verbose:
                raise CLIError(
                    "Unable to provision Microsoft Application automatically. "
                    "To manually provision a Microsoft Application, go to the Application Registration Portal at "
                    "https://apps.dev.microsoft.com/. Once you manually create you application, "
                    "pass the application Id and password as parameters for bot creation.")
            # Stub of logged error if verbose is True:
            else:
                raise CLIError("%s: %s" % (response.status_code, response.text))

        response_content = json.loads(response.content.decode('utf-8'))
        msa_app_id = response_content['AppId']
        password = response_content['Password']

        return msa_app_id, password
