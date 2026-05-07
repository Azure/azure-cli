# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Live scenario tests for agentic session differentiation.

These tests verify the end-to-end cache isolation behavior between manual (human)
and agent token acquisition flows.

Prerequisites:
  - Run with a user account that has access to at least one subscription.
"""

import os

from azure.cli.core.auth.util import decode_access_token
from azure.cli.testsdk import LiveScenarioTest


class AgenticSessionScenarioTest(LiveScenarioTest):
    """Live scenario tests for agent vs manual token cache isolation."""

    def _clean_state(self):
        os.environ.pop('COPILOT_AGENT_SESSION_ID', None)
        self.cmd('az account clear')

    def setUp(self):
        super().setUp()
        self._clean_state()
        self.cmd('az login')

    def tearDown(self):
        self._clean_state()

    def _get_access_token(self):
        """Get an access token and return (raw_token, decoded_claims)."""
        result = self.cmd('az account get-access-token').get_output_in_json()
        token = result['accessToken']
        claims = decode_access_token(token)
        return token, claims

    # --- 5 core cache isolation tests ---

    def test_manual_manual_reuses_cache(self):
        """Manual followed by manual should reuse the cached token."""
        _, claims1 = self._get_access_token()
        _, claims2 = self._get_access_token()

        self.assertEqual(claims1.get('uti'), claims2.get('uti'),
                         "Manual + manual should reuse cached token (same uti)")

    def test_agent_agent_reuses_cache(self):
        """Agent followed by agent (same session ID) should reuse the cached token."""
        os.environ['COPILOT_AGENT_SESSION_ID'] = 'e2e-session-same-reuse-01'
        try:
            _, claims1 = self._get_access_token()
            _, claims2 = self._get_access_token()

            self.assertEqual(claims1.get('uti'), claims2.get('uti'),
                             "Agent + agent (same session) should reuse cached token (same uti)")
            self.assertIn('xms_cli_ses', claims1,
                          "Agent token should contain xms_cli_ses claim")
            self.assertIn('xms_cli_ses', claims2,
                          "Agent token should contain xms_cli_ses claim")
        finally:
            os.environ.pop('COPILOT_AGENT_SESSION_ID', None)

    def test_manual_then_agent_does_not_reuse_cache(self):
        """Manual followed by agent should NOT reuse the manual cached token."""
        _, manual_claims = self._get_access_token()

        os.environ['COPILOT_AGENT_SESSION_ID'] = 'e2e-agent-after-manual'
        try:
            _, agent_claims = self._get_access_token()

            self.assertNotEqual(manual_claims.get('uti'), agent_claims.get('uti'),
                                "Manual then agent should NOT reuse cache (different uti)")
            self.assertNotIn('xms_cli_ses', manual_claims,
                             "Manual token should NOT contain xms_cli_ses claim")
            self.assertIn('xms_cli_ses', agent_claims,
                          "Agent token should contain xms_cli_ses claim")
        finally:
            os.environ.pop('COPILOT_AGENT_SESSION_ID', None)

    def test_agent_then_manual_does_not_reuse_cache(self):
        """Agent followed by manual should NOT reuse the agent cached token."""
        os.environ['COPILOT_AGENT_SESSION_ID'] = 'e2e-manual-after-agent'
        try:
            _, agent_claims = self._get_access_token()
        finally:
            os.environ.pop('COPILOT_AGENT_SESSION_ID', None)

        _, manual_claims = self._get_access_token()

        self.assertNotEqual(agent_claims.get('uti'), manual_claims.get('uti'),
                            "Agent then manual should NOT reuse cache (different uti)")
        self.assertIn('xms_cli_ses', agent_claims,
                      "Agent token should contain xms_cli_ses claim")
        self.assertNotIn('xms_cli_ses', manual_claims,
                         "Manual token should NOT contain xms_cli_ses claim")

    def test_agent_session1_then_agent_session2_does_not_reuse_cache(self):
        """Agent with session1 followed by agent with session2 should NOT reuse cache."""
        try:
            os.environ['COPILOT_AGENT_SESSION_ID'] = 'e2e-session-AAA-isolation'
            _, claims_a = self._get_access_token()

            os.environ['COPILOT_AGENT_SESSION_ID'] = 'e2e-session-BBB-isolation'
            _, claims_b = self._get_access_token()

            self.assertNotEqual(claims_a.get('uti'), claims_b.get('uti'),
                                "Agent session1 then session2 should NOT reuse cache (different uti)")
            self.assertIn('xms_cli_ses', claims_a,
                          "Agent token A should contain xms_cli_ses claim")
            self.assertIn('xms_cli_ses', claims_b,
                          "Agent token B should contain xms_cli_ses claim")
            self.assertNotEqual(claims_a.get('xms_cli_ses'), claims_b.get('xms_cli_ses'),
                                "Different sessions should have different xms_cli_ses values")
        finally:
            os.environ.pop('COPILOT_AGENT_SESSION_ID', None)

    # --- Wire-level test ---

    def test_client_session_in_request_body(self):
        """
        Send client_session in the /token POST body. Verify:
          1. The ESTS request POST body contains client_session.
          2. The issued access token contains xms_cli_sid, xms_cli_ses, and xms_sess_fct.
          3. xms_cli_ses echoes back the client_session value verbatim.
          4. xms_sess_fct contains 21 (AgenticSession facet).
        """
        import msal
        import urllib3
        from urllib.parse import parse_qs

        captured_posts = []
        original_urlopen = urllib3.HTTPConnectionPool.urlopen

        def patched_urlopen(self_conn, method, url, body=None, headers=None, **kwargs):
            if ('login.microsoftonline.com' in str(getattr(self_conn, 'host', ''))
                    and method == 'POST' and '/oauth2/v2.0/token' in url):
                captured_posts.append({
                    "url": url,
                    "body": body.decode('utf-8') if isinstance(body, bytes) else body,
                })
            return original_urlopen(self_conn, method, url, body=body, headers=headers, **kwargs)

        cache = msal.SerializableTokenCache()
        cache_file = os.path.expanduser("~/.azure/msal_token_cache.json")
        with open(cache_file) as f:
            cache.deserialize(f.read())

        app = msal.PublicClientApplication(
            "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
            authority="https://login.microsoftonline.com/organizations",
            token_cache=cache,
        )
        accounts = app.get_accounts()
        self.assertTrue(accounts, "Must be logged in with at least one account")
        account = accounts[0]

        client_session_value = "e2e-test-session-claims-12345678"

        urllib3.HTTPConnectionPool.urlopen = patched_urlopen
        try:
            result = app.acquire_token_silent_with_error(
                ["https://management.core.windows.net//.default"],
                account,
                force_refresh=True,
                data={"client_session": client_session_value},
            )
        finally:
            urllib3.HTTPConnectionPool.urlopen = original_urlopen

        # --- Assert on REQUEST ---
        self.assertTrue(captured_posts, "Should have made at least one POST to ESTS token endpoint")
        last_post = captured_posts[-1]
        parsed_body = parse_qs(last_post["body"])
        self.assertIn("client_session", parsed_body,
                       "Request POST body must contain client_session")
        self.assertEqual(parsed_body["client_session"][0], client_session_value)

        # --- Assert on RESPONSE token ---
        self.assertIn("access_token", result, f"Token request failed: {result.get('error')}")
        token_claims = decode_access_token(result["access_token"])

        # xms_cli_ses: verbatim echo of client_session
        self.assertIn("xms_cli_ses", token_claims,
                       "Issued token must contain 'xms_cli_ses' claim")
        self.assertEqual(token_claims["xms_cli_ses"], client_session_value,
                         "xms_cli_ses must match the client_session value sent")

        # xms_cli_sid: deterministic session ID derived from client_session
        self.assertIn("xms_cli_sid", token_claims,
                       "Issued token must contain 'xms_cli_sid' claim")

        # xms_sess_fct: session facets — must contain 21 (AgenticSession)
        self.assertIn("xms_sess_fct", token_claims,
                       "Issued token must contain 'xms_sess_fct' claim")
        sess_fct_values = str(token_claims["xms_sess_fct"]).split()
        self.assertIn("21", sess_fct_values,
                       "xms_sess_fct must contain 21 (AgenticSession facet)")
