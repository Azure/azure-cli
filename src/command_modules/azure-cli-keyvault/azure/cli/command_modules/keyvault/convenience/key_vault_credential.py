#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

#pylint: skip-file

import adal
import urllib

from msrest.authentication import Authentication

from . import HttpBearerChallenge
from . import HttpBearerChallengeCache as ChallengeCache

class KeyVaultCredential(Authentication):

    def __init__(self, token):
        self._token = token

    def signed_session(self):
        session = super(KeyVaultCredential, self).signed_session()
        session.headers['Authorization'] = 'Bearer {}'.format(self._token or '')
        return session
