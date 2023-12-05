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

        access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IlQxU3QtZExUdnlXUmd4Ql82NzZ1OGtyWFMtSSIsImtpZCI6IlQxU3QtZExUdnlXUmd4Ql82NzZ1OGtyWFMtSSJ9.eyJhdWQiOiJodHRwczovL21hbmFnZW1lbnQuY29yZS53aW5kb3dzLm5ldC8iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC81NDgyNmIyMi0zOGQ2LTRmYjItYmFkOS1iN2I5M2EzZTljNWEvIiwiaWF0IjoxNzAxMDUzNDEyLCJuYmYiOjE3MDEwNTM0MTIsImV4cCI6MTcwMTA1ODk5OSwiYWNyIjoiMSIsImFpbyI6IkFiUUFTLzhWQUFBQVFBVGtZaVpXSllDQVZzVjRWUlRvdjV0dHQyUnF5a3NMTm9Oc0l5ZUJGamJCZUlMYXQ3dm1ydkxUbEo0Vk5XWVNZcnlvQkpReVBxSkFNNmM0VmF2bTdZaHFCRzVpOWswSlN5SWVjejBwWHk1YXZkNXFhaVlFZW1kb0FJRUpGWHc5ajE3TlA0aERPMGNHS3hzQjJNYUczcE9ON24vakRLSmRUN2g0UmNZazltbUFNSjJ3Qlo5OC9LcDMyUEVXdDEzQ1RJL2xxVU5lNlhzTTAzMzMrV2wwekVYWEw0dGp2UTNpMWcwRC9pSnpzSE09IiwiYWx0c2VjaWQiOiI1OjoxMDAzMjAwMERDMzk4MDAxIiwiYW1yIjpbInJzYSJdLCJhcHBpZCI6IjA0YjA3Nzk1LThkZGItNDYxYS1iYmVlLTAyZjllMWJmN2I0NiIsImFwcGlkYWNyIjoiMCIsImVtYWlsIjoieWlzaGl3YW5nQG1pY3Jvc29mdC5jb20iLCJmYW1pbHlfbmFtZSI6IldhbmciLCJnaXZlbl9uYW1lIjoiWWlzaGkiLCJncm91cHMiOlsiZTRiYjBiNTYtMTAxNC00MGY4LTg4YWItM2Q4YThjYjBlMDg2Il0sImlkcCI6Imh0dHBzOi8vc3RzLndpbmRvd3MubmV0LzcyZjk4OGJmLTg2ZjEtNDFhZi05MWFiLTJkN2NkMDExZGI0Ny8iLCJpZHR5cCI6InVzZXIiLCJpcGFkZHIiOiIyNDA0OmY4MDE6ODA1MDozOjgwYmU6OjM0MSIsIm5hbWUiOiJZaXNoaSBXYW5nIiwib2lkIjoiMzcwN2ZiMmYtYWMxMC00NTkxLWEwNGYtOGIwZDc4NmVhMzdkIiwicHVpZCI6IjEwMDMyMDAwRTFDQjlGNDEiLCJyaCI6IjAuQVRjQUltdUNWTlk0c2stNjJiZTVPajZjV2taSWYza0F1dGRQdWtQYXdmajJNQk0zQUtRLiIsInNjcCI6InVzZXJfaW1wZXJzb25hdGlvbiIsInN1YiI6IlhBREpxenU5ekhzY1FLTU9mZlVpT2xsSmcxWmxnbmMwT2dtWFpaallTWEkiLCJ0aWQiOiI1NDgyNmIyMi0zOGQ2LTRmYjItYmFkOS1iN2I5M2EzZTljNWEiLCJ1bmlxdWVfbmFtZSI6Inlpc2hpd2FuZ0BtaWNyb3NvZnQuY29tIiwidXRpIjoiNTdrbDY5aDQtVTJGS25vX0hqVnpBUSIsInZlciI6IjEuMCIsIndpZHMiOlsiNjJlOTAzOTQtNjlmNS00MjM3LTkxOTAtMDEyMTc3MTQ1ZTEwIiwiMTNiZDFjNzItNmY0YS00ZGNmLTk4NWYtMThkM2I4MGYyMDhhIl0sInhtc19jYWUiOiIxIiwieG1zX2NjIjpbIkNQMSJdLCJ4bXNfdGNkdCI6MTQxMjIwNjg0MH0.s1FnxnZDAEQaNGZFuNLHHXLfPxzzpERz8nySgZoQVacaCAokBrvs5eiwWyVdhtVJt2OpQAiku7Uul1fXQg_GXUq2mqrZh9Ttn3Cp4gRHSNNJDEYB5VINyk4MxVCqB-Gkir0-qU5DVtViTNJOPw-LssYImOXmxIrqDwLas4Tn1yRS-mD50nzTFeg5gpsSlr0lZWmJQfE6ZtdP6oEEUVs3rg2kNHRbYnrPOjJa3B8DCLxkwyE9Mt6Ti7nUu979Lm0jTEOvHn0bh1f-Y5F9edlNYuK3z5PMn-FYP5ws0IEClC82VpDpNYw6ROkUo6KHVnI37LivuwNDxmDhRwb_2Iy8Ow'
        expected_access_token = '_REDACTED_JWT_TOKEN_'
        self.assertEqual(redact_credential_for_string(access_token), expected_access_token)

        ssh_pub_key = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCof7rG2sYVyHSDPp4lbrq5zu8N8D7inS4Qb+ZZ5Kh410znTcoVJSNsLOhrM2COxg5LXca3DQMBi4S/V8UmMnwxwDVf38GvU+0QVDR6vSO6lPlj2OpPLk4OEdTv3qcj/gpEBvv1RCacpFuu5bL546r4BqG4f0dJXqBd5tT4kjpO9ytOZ1Wkg8tA35UvbucVAsDBfOZ5GtsnflPtKCY9h20LeXEjyDZ8eFzAGH/vNrfWPiWWznwN9EoPghIQHCiC0mnJgdsABraUzeTTMjxahi0DXBxb5dsKd6YbJxQw/V+AohVMPfPvs9y95Aj7IxM2zrtgBswC8bT0z678svTJSFX9 test@example.com'
        expected_ssh_pub_key = 'ssh-rsa _REDACTED_SSH_KEY_ _REDACTED_EMAIL_@example.com'
        self.assertEqual(redact_credential_for_string(ssh_pub_key), expected_ssh_pub_key)

        object_id = '3707fb2f-ac10-4591-a04f-8b0d786ea37d'
        expected_object_id = '_REDACTED_GUID_'
        self.assertEqual(redact_credential_for_string(object_id), expected_object_id)

    def test_redact_credential_for_json(self):
        content = {
            'tenant': '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a',
            'account_name': 'testaccount',
            'account_sas': 'sv=2019-02-02&ss=bfqt&srt=sco&sp=rwdlacup&se=2020-02-12T00:00:00Z&st=2020-02-11T00:00:00Z&spr=https&sig=u0JHN%2Bix9jsXw71NwfNF6TtQvckxuHHGRI6ldXzRMDA%3D',
            'connection_string': 'BlobEndpoint=https://testaccount.blob.core.windows.net/;QueueEndpoint=https://testaccount.queue.core.windows.net/;FileEndpoint=https://testaccount.file.core.windows.net/;TableEndpoint=https://testaccount.table.core.windows.net/;SharedAccessSignature=sv=2022-11-02&ss=b&srt=sco&sp=rwdlaciytfx&se=2023-11-24T13:18:46Z&st=2023-11-24T05:18:46Z&spr=https&sig=U%2BNC2LK1JRF2NOc4p7YhMvOvIVvRB0GOyM2cAHQeGMY%3D',
            'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IlQxU3QtZExUdnlXUmd4Ql82NzZ1OGtyWFMtSSIsImtpZCI6IlQxU3QtZExUdnlXUmd4Ql82NzZ1OGtyWFMtSSJ9.eyJhdWQiOiJodHRwczovL21hbmFnZW1lbnQuY29yZS53aW5kb3dzLm5ldC8iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC81NDgyNmIyMi0zOGQ2LTRmYjItYmFkOS1iN2I5M2EzZTljNWEvIiwiaWF0IjoxNzAxMDUzNDEyLCJuYmYiOjE3MDEwNTM0MTIsImV4cCI6MTcwMTA1ODk5OSwiYWNyIjoiMSIsImFpbyI6IkFiUUFTLzhWQUFBQVFBVGtZaVpXSllDQVZzVjRWUlRvdjV0dHQyUnF5a3NMTm9Oc0l5ZUJGamJCZUlMYXQ3dm1ydkxUbEo0Vk5XWVNZcnlvQkpReVBxSkFNNmM0VmF2bTdZaHFCRzVpOWswSlN5SWVjejBwWHk1YXZkNXFhaVlFZW1kb0FJRUpGWHc5ajE3TlA0aERPMGNHS3hzQjJNYUczcE9ON24vakRLSmRUN2g0UmNZazltbUFNSjJ3Qlo5OC9LcDMyUEVXdDEzQ1RJL2xxVU5lNlhzTTAzMzMrV2wwekVYWEw0dGp2UTNpMWcwRC9pSnpzSE09IiwiYWx0c2VjaWQiOiI1OjoxMDAzMjAwMERDMzk4MDAxIiwiYW1yIjpbInJzYSJdLCJhcHBpZCI6IjA0YjA3Nzk1LThkZGItNDYxYS1iYmVlLTAyZjllMWJmN2I0NiIsImFwcGlkYWNyIjoiMCIsImVtYWlsIjoieWlzaGl3YW5nQG1pY3Jvc29mdC5jb20iLCJmYW1pbHlfbmFtZSI6IldhbmciLCJnaXZlbl9uYW1lIjoiWWlzaGkiLCJncm91cHMiOlsiZTRiYjBiNTYtMTAxNC00MGY4LTg4YWItM2Q4YThjYjBlMDg2Il0sImlkcCI6Imh0dHBzOi8vc3RzLndpbmRvd3MubmV0LzcyZjk4OGJmLTg2ZjEtNDFhZi05MWFiLTJkN2NkMDExZGI0Ny8iLCJpZHR5cCI6InVzZXIiLCJpcGFkZHIiOiIyNDA0OmY4MDE6ODA1MDozOjgwYmU6OjM0MSIsIm5hbWUiOiJZaXNoaSBXYW5nIiwib2lkIjoiMzcwN2ZiMmYtYWMxMC00NTkxLWEwNGYtOGIwZDc4NmVhMzdkIiwicHVpZCI6IjEwMDMyMDAwRTFDQjlGNDEiLCJyaCI6IjAuQVRjQUltdUNWTlk0c2stNjJiZTVPajZjV2taSWYza0F1dGRQdWtQYXdmajJNQk0zQUtRLiIsInNjcCI6InVzZXJfaW1wZXJzb25hdGlvbiIsInN1YiI6IlhBREpxenU5ekhzY1FLTU9mZlVpT2xsSmcxWmxnbmMwT2dtWFpaallTWEkiLCJ0aWQiOiI1NDgyNmIyMi0zOGQ2LTRmYjItYmFkOS1iN2I5M2EzZTljNWEiLCJ1bmlxdWVfbmFtZSI6Inlpc2hpd2FuZ0BtaWNyb3NvZnQuY29tIiwidXRpIjoiNTdrbDY5aDQtVTJGS25vX0hqVnpBUSIsInZlciI6IjEuMCIsIndpZHMiOlsiNjJlOTAzOTQtNjlmNS00MjM3LTkxOTAtMDEyMTc3MTQ1ZTEwIiwiMTNiZDFjNzItNmY0YS00ZGNmLTk4NWYtMThkM2I4MGYyMDhhIl0sInhtc19jYWUiOiIxIiwieG1zX2NjIjpbIkNQMSJdLCJ4bXNfdGNkdCI6MTQxMjIwNjg0MH0.s1FnxnZDAEQaNGZFuNLHHXLfPxzzpERz8nySgZoQVacaCAokBrvs5eiwWyVdhtVJt2OpQAiku7Uul1fXQg_GXUq2mqrZh9Ttn3Cp4gRHSNNJDEYB5VINyk4MxVCqB-Gkir0-qU5DVtViTNJOPw-LssYImOXmxIrqDwLas4Tn1yRS-mD50nzTFeg5gpsSlr0lZWmJQfE6ZtdP6oEEUVs3rg2kNHRbYnrPOjJa3B8DCLxkwyE9Mt6Ti7nUu979Lm0jTEOvHn0bh1f-Y5F9edlNYuK3z5PMn-FYP5ws0IEClC82VpDpNYw6ROkUo6KHVnI37LivuwNDxmDhRwb_2Iy8Ow',
            'ssh_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCof7rG2sYVyHSDPp4lbrq5zu8N8D7inS4Qb+ZZ5Kh410znTcoVJSNsLOhrM2COxg5LXca3DQMBi4S/V8UmMnwxwDVf38GvU+0QVDR6vSO6lPlj2OpPLk4OEdTv3qcj/gpEBvv1RCacpFuu5bL546r4BqG4f0dJXqBd5tT4kjpO9ytOZ1Wkg8tA35UvbucVAsDBfOZ5GtsnflPtKCY9h20LeXEjyDZ8eFzAGH/vNrfWPiWWznwN9EoPghIQHCiC0mnJgdsABraUzeTTMjxahi0DXBxb5dsKd6YbJxQw/V+AohVMPfPvs9y95Aj7IxM2zrtgBswC8bT0z678svTJSFX9 test@example.com'
        }
        expected_content = {
            'tenant': '_REDACTED_GUID_',
            'account_name': 'testaccount',
            'account_sas': 'sv=2019-02-02&ss=bfqt&srt=sco&sp=rwdlacup&se=2020-02-12T00:00:00Z&st=2020-02-11T00:00:00Z&spr=https&sig=_REDACTED_SAS_TOKEN_SIG_',
            'connection_string': 'BlobEndpoint=https://testaccount.blob.core.windows.net/;QueueEndpoint=https://testaccount.queue.core.windows.net/;FileEndpoint=https://testaccount.file.core.windows.net/;TableEndpoint=https://testaccount.table.core.windows.net/;SharedAccessSignature=sv=2022-11-02&ss=b&srt=sco&sp=rwdlaciytfx&se=2023-11-24T13:18:46Z&st=2023-11-24T05:18:46Z&spr=https&sig=_REDACTED_SAS_TOKEN_SIG_',
            'access_token': '_REDACTED_JWT_TOKEN_',
            'ssh_key': 'ssh-rsa _REDACTED_SSH_KEY_ _REDACTED_EMAIL_@example.com'
        }
        self.assertEqual(redact_credential(content), expected_content)
