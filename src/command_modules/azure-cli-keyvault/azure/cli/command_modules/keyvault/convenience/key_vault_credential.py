#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

#pylint: skip-file

import adal
import urllib

from msrest.authentication import authentication

from . import httpbearerchallenge
from . import httpbearerchallengecache as challengecache

class keyvaultcredential(authentication):

    def __init__(self, token):
        print('init')
        self._token = token

    def signed_session(self):
        session = super(keyvaultcredential, self).signed_session()
        session.headers['authorization'] = 'bearer {}'.format(self._token or '')
        print('signed session w/ auth: {}'.format(session.headers['authorization']))
        return session
