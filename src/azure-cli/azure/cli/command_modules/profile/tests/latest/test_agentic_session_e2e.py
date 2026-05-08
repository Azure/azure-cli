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
        # Login to the agent test tenant where xms_cli_ses eSTS feature is enabled
        self._tenant_id = os.environ.get('AZURE_AGENTIC_TEST_TENANT',
                                         'c6f398fc-b904-4326-98b0-d8ce4b0db27a')
        self.cmd('az login --tenant {}'.format(self._tenant_id))

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
