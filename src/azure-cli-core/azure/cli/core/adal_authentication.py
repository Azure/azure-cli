#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import adal

from msrest.authentication import Authentication

from azure.cli.core._util import CLIError

class AdalAuthentication(Authentication):#pylint: disable=too-few-public-methods

    def __init__(self, token_retriever):
        self._token_retriever = token_retriever

    def signed_session(self):
        session = super(AdalAuthentication, self).signed_session()

        try:
            scheme, token = self._token_retriever()
        except adal.AdalError as err:
            raise CLIError(err)

        header = "{} {}".format(scheme, token)
        session.headers['Authorization'] = header
        return session
