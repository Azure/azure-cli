# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods
from azure.cli.core.auth.util import resource_to_scopes


# This class is used to pass in custom token audience that will be respected by the SDK.
# Users can configure an audience based on their cloud.
class AppConfigurationCliCredential:

    def __init__(self, credential, resource: str = None):
        self._impl = credential
        self._resource = resource

    def get_token(self, *scopes, **kwargs):

        if self._resource is not None:
            scopes = resource_to_scopes(self._resource)

        return self._impl.get_token(*scopes, **kwargs)
