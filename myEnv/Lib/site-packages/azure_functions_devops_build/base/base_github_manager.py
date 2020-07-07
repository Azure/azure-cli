# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.service_client import ServiceClient
from msrest import Configuration

class BaseGithubManager(object):

    def __init__(self, base_url='https://api.github.com', pat=None):
        """Inits UserManager as to be able to send the right requests"""
        self._pat = pat
        self._config = Configuration(base_url=base_url)
        self._client = ServiceClient(None, self._config)

    def construct_github_request_header(self, pat=None):
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }

        if pat:
            headers["Authorization"] = "token {pat}".format(pat=pat)
        elif self._pat:
            headers["Authorization"] = "token {pat}".format(pat=self._pat)

        return headers

    def close_connection(self):
        self._client.close()
