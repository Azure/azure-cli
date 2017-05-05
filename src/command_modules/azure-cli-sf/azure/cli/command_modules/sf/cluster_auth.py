# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from msrest.authentication import Authentication


# pylint: disable=too-few-public-methods
class ClientCertAuthentication(Authentication):
    """Client certificate authentication for Service Fabric clusters"""
    def __init__(self, cert=None, ca_cert=None, no_verify=False):
        self.cert = cert
        self.ca_cert = ca_cert
        self.no_verify = no_verify

    def signed_session(self):
        """Create requests session with any required auth headers
        applied.

        :rtype: requests.Session.
        """
        session = super(ClientCertAuthentication, self).signed_session()
        if self.cert is not None:
            session.cert = self.cert
        if self.ca_cert is not None:
            session.verify = self.ca_cert
        if self.no_verify:
            session.verify = False

        return session
