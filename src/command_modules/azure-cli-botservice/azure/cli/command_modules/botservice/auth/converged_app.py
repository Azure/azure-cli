# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import requests
from .adal_authenticator import AdalAuthenticator
from knack.util import CLIError


class ConvergedApp:

    app_provision_api_url = 'https://dev.botframework.com/api/botApp/provisionConvergedApp?name={0}'

    @staticmethod
    def provision(bot_name):

        # Use our authenticator to acquire a user token with a custom audience
        token = AdalAuthenticator.acquire_token()
        access_token = token['accessToken']

        # Prepare headers to call dev portal converged app provisioning API
        headers = {'Authorization': 'Bearer {0}'.format(access_token)}

        # Provision app
        response = requests.post(
            ConvergedApp.app_provision_api_url.format(bot_name),
            headers=headers
        )

        # TODO: Verbose logging
        if response.status_code not in [201]:
            raise CLIError(
                "Unable to provision Microsoft Application automatically. "
                "To manually provision a Microsoft Application, go to the Application Registration Portal at "
                "https://apps.dev.microsoft.com/. Once you manually create you application, "
                "pass the application Id and password as parameters for bot creation.")

        response_content = json.loads(response.content.decode('utf-8'))
        msa_app_id = response_content['AppId']
        password = response_content['Password']

        return msa_app_id, password
