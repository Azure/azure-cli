# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import requests
import adal

from msrest.authentication import Authentication

from azure.cli.core.util import CLIError


class AdalAuthentication(Authentication):  # pylint: disable=too-few-public-methods

    def __init__(self, token_retriever):
        self._token_retriever = token_retriever

    def signed_session(self):
        session = super(AdalAuthentication, self).signed_session()

        try:
            scheme, token, _ = self._token_retriever()
        except adal.AdalError as err:
            # pylint: disable=no-member
            if (hasattr(err, 'error_response') and
                    ('error_description' in err.error_response) and
                    ('AADSTS70008:' in err.error_response['error_description'])):
                raise CLIError("Credentials have expired due to inactivity. Please run 'az login'")

            raise CLIError(err)
        except requests.exceptions.ConnectionError as err:
            raise CLIError('Please ensure you have network connection. Error detail: ' + str(err))

        header = "{} {}".format(scheme, token)
        session.headers['Authorization'] = header
        return session
