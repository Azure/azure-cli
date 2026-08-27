# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import unittest
from unittest.mock import patch

from azure.cli.core.auth.agentic_session import (
    COPILOT_AGENT_SESSION_ID,
    build_agentic_session_params,
    merge_access_token_claims,
)


class TestBuildAgenticSessionParams(unittest.TestCase):

    def test_returns_none_when_env_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            session_id, claims = build_agentic_session_params()
            self.assertIsNone(session_id)
            self.assertIsNone(claims)

    def test_returns_none_when_env_is_empty_string(self):
        with patch.dict(os.environ, {COPILOT_AGENT_SESSION_ID: ""}):
            session_id, claims = build_agentic_session_params()
            self.assertIsNone(session_id)
            self.assertIsNone(claims)

    def test_returns_session_id_and_claims(self):
        with patch.dict(os.environ, {COPILOT_AGENT_SESSION_ID: "sess-456"}):
            session_id, claims = build_agentic_session_params()
            self.assertEqual(session_id, "sess-456")
            parsed = json.loads(claims)
            self.assertEqual(parsed["access_token"]["xms_cli_sid"]["values"], ["sess-456"])

def _agentic_claims(session_id="s1"):
    return json.dumps({"access_token": {"xms_cli_sid": {"values": [session_id]}}})


class TestMergeAccessTokenClaims(unittest.TestCase):

    # --- Validation ---

    def test_raises_when_new_claims_is_none(self):
        with self.assertRaises(ValueError):
            merge_access_token_claims(None, None)

    def test_raises_when_new_access_token_is_null(self):
        new = json.dumps({"access_token": None})
        with self.assertRaises(ValueError):
            merge_access_token_claims(None, new)

    # --- Merging ---

    def test_merges_into_none(self):
        result = merge_access_token_claims(None, _agentic_claims("s1"))
        claims = json.loads(result)
        self.assertEqual(len(claims), 1)
        self.assertEqual(len(claims["access_token"]), 1)
        self.assertEqual(claims["access_token"]["xms_cli_sid"], {"values": ["s1"]})

    def test_merges_into_existing(self):
        existing = json.dumps({"access_token": {"nbf": {"essential": True, "value": "999"}}})
        result = merge_access_token_claims(existing, _agentic_claims("s1"))
        merged = json.loads(result)
        self.assertEqual(len(merged), 1)
        self.assertEqual(len(merged["access_token"]), 2)
        self.assertEqual(merged["access_token"]["nbf"], {"essential": True, "value": "999"})
        self.assertEqual(merged["access_token"]["xms_cli_sid"], {"values": ["s1"]})

    def test_preserves_non_access_token_keys(self):
        existing = json.dumps({
            "access_token": {"nbf": {"essential": True}},
            "id_token": {"auth_time": {"essential": True}}
        })
        result = merge_access_token_claims(existing, _agentic_claims())
        merged = json.loads(result)
        self.assertEqual(len(merged), 2)
        self.assertEqual(len(merged["access_token"]), 2)
        self.assertEqual(merged["id_token"], {"auth_time": {"essential": True}})
        self.assertEqual(merged["access_token"]["nbf"], {"essential": True})
        self.assertEqual(merged["access_token"]["xms_cli_sid"], {"values": ["s1"]})

    def test_new_claims_overwrites_existing_key(self):
        existing = json.dumps({"access_token": {"xms_cli_sid": {"values": ["old"]}}})
        result = merge_access_token_claims(existing, _agentic_claims("new"))
        merged = json.loads(result)
        self.assertEqual(len(merged), 1)
        self.assertEqual(len(merged["access_token"]), 1)
        self.assertEqual(merged["access_token"]["xms_cli_sid"], {"values": ["new"]})

    def test_creates_access_token_when_missing_in_existing(self):
        existing = json.dumps({"id_token": {"auth_time": {"essential": True}}})
        result = merge_access_token_claims(existing, _agentic_claims())
        merged = json.loads(result)
        self.assertEqual(len(merged), 2)
        self.assertEqual(len(merged["access_token"]), 1)
        self.assertEqual(merged["id_token"], {"auth_time": {"essential": True}})
        self.assertEqual(merged["access_token"]["xms_cli_sid"], {"values": ["s1"]})

    def test_handles_null_access_token_in_existing(self):
        existing = json.dumps({"access_token": None})
        result = merge_access_token_claims(existing, _agentic_claims())
        merged = json.loads(result)
        self.assertEqual(len(merged), 1)
        self.assertEqual(len(merged["access_token"]), 1)
        self.assertEqual(merged["access_token"]["xms_cli_sid"], {"values": ["s1"]})


class TestUserCredentialAgenticSession(unittest.TestCase):
    """Verify that UserCredential.acquire_token merges agentic claims and passes
    client_session param when COPILOT_AGENT_SESSION_ID is set."""

    def _build_user_credential(self, enable_broker=False):
        """Build a UserCredential with mocked MSAL app."""
        from unittest.mock import MagicMock, PropertyMock
        from azure.cli.core.auth.msal_credentials import UserCredential

        cred = object.__new__(UserCredential)

        cred._msal_app = MagicMock()
        cred._msal_app.client_id = "test-client-id"
        cred._msal_app._enable_broker = enable_broker
        type(cred._msal_app).authority = PropertyMock(return_value=MagicMock(
            instance="login.microsoftonline.com",
            tenant="test-tenant",
            is_adfs=False,
        ))
        cred._account = {
            "home_account_id": "uid.utid",
            "username": "user@test.com",
        }
        return cred

    @patch.dict(os.environ, {COPILOT_AGENT_SESSION_ID: "agent-sess-1"})
    def test_non_broker_passes_data_only(self):
        """Non-broker path: client_session in data for ext_cache_key, no claims_challenge."""
        cred = self._build_user_credential(enable_broker=False)
        cred._msal_app.acquire_token_silent_with_error.return_value = {
            "access_token": "agent-tagged-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        result = cred.acquire_token(["https://management.azure.com/.default"])

        self.assertEqual(result["access_token"], "agent-tagged-token")

        call_kwargs = cred._msal_app.acquire_token_silent_with_error.call_args
        self.assertIsNone(call_kwargs.kwargs.get("claims_challenge"))
        self.assertEqual(call_kwargs.kwargs["data"], {"client_session": "agent-sess-1"})
        self.assertEqual(call_kwargs.kwargs["params"], {"client_session": "agent-sess-1"})

    @patch.dict(os.environ, {COPILOT_AGENT_SESSION_ID: "agent-sess-1"})
    def test_broker_passes_claims_and_data(self):
        """Broker path: claims_challenge with xms_cli_sid AND client_session in data."""
        cred = self._build_user_credential(enable_broker=True)
        cred._msal_app.acquire_token_silent_with_error.return_value = {
            "access_token": "agent-tagged-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        result = cred.acquire_token(["https://management.azure.com/.default"])

        self.assertEqual(result["access_token"], "agent-tagged-token")

        call_kwargs = cred._msal_app.acquire_token_silent_with_error.call_args
        claims = json.loads(call_kwargs.kwargs["claims_challenge"])
        self.assertEqual(claims["access_token"]["xms_cli_sid"]["values"], ["agent-sess-1"])
        self.assertEqual(call_kwargs.kwargs["data"], {"client_session": "agent-sess-1"})
        self.assertEqual(call_kwargs.kwargs["params"], {"client_session": "agent-sess-1"})

    @patch.dict(os.environ, {}, clear=True)
    def test_no_agentic_params_without_env(self):
        """When COPILOT_AGENT_SESSION_ID is not set, no agentic params are added."""
        cred = self._build_user_credential(enable_broker=False)
        cred._msal_app.acquire_token_silent_with_error.return_value = {
            "access_token": "normal-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        result = cred.acquire_token(["https://management.azure.com/.default"])

        self.assertEqual(result["access_token"], "normal-token")

        call_kwargs = cred._msal_app.acquire_token_silent_with_error.call_args
        self.assertIsNone(call_kwargs.kwargs.get("claims_challenge"))
        self.assertNotIn("params", call_kwargs.kwargs)

    @patch.dict(os.environ, {COPILOT_AGENT_SESSION_ID: "agent-sess-2"})
    def test_broker_merges_with_existing_claims(self):
        """Broker path: agentic claims are merged with existing claims_challenge."""
        cred = self._build_user_credential(enable_broker=True)
        cred._msal_app.acquire_token_silent_with_error.return_value = {
            "access_token": "token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        existing_claims = json.dumps({"access_token": {"nbf": {"essential": True, "value": "999"}}})
        cred.acquire_token(["scope"], claims_challenge=existing_claims)

        call_kwargs = cred._msal_app.acquire_token_silent_with_error.call_args
        claims = json.loads(call_kwargs.kwargs["claims_challenge"])
        self.assertEqual(claims["access_token"]["nbf"], {"essential": True, "value": "999"})
        self.assertEqual(claims["access_token"]["xms_cli_sid"]["values"], ["agent-sess-2"])


if __name__ == '__main__':
    unittest.main()
