# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.core.credential_helper import CredentialType, is_containing_credential, distinguish_credential, redact_credential_for_string, redact_credential


class TestCredentialHelper(unittest.TestCase):

    def test_redact_credential_for_string(self):
        sas_token = 'sv=2019-02-02&ss=bfqt&srt=sco&sp=rwdlacup&se=2020-02-12T00:00:00Z&st=2020-02-11T00:00:00Z&spr=https&sig=u0JHN%2Bix9jsXw71NwfNF6TtQvckxuHHGRI6ldXzRMDA%3D'
        expected_sas_token = 'sv=2019-02-02&ss=bfqt&srt=sco&sp=rwdlacup&se=2020-02-12T00:00:00Z&st=2020-02-11T00:00:00Z&spr=https&sig=_REDACTED_SAS_TOKEN_SIG_'
        self.assertEqual(redact_credential_for_string(sas_token), expected_sas_token)
