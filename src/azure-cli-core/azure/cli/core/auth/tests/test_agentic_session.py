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
            self.assertEqual(parsed["access_token"]["xms_agent_session"]["value"], "sess-456")
            self.assertTrue(parsed["access_token"]["xms_agent_session"]["essential"])

def _agentic_claims(session_id="s1"):
    return json.dumps({"access_token": {"xms_agent_session": {"essential": True, "value": session_id}}})


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
        self.assertEqual(claims["access_token"]["xms_agent_session"], {"essential": True, "value": "s1"})

    def test_merges_into_existing(self):
        existing = json.dumps({"access_token": {"nbf": {"essential": True, "value": "999"}}})
        result = merge_access_token_claims(existing, _agentic_claims("s1"))
        merged = json.loads(result)
        self.assertEqual(len(merged), 1)
        self.assertEqual(len(merged["access_token"]), 2)
        self.assertEqual(merged["access_token"]["nbf"], {"essential": True, "value": "999"})
        self.assertEqual(merged["access_token"]["xms_agent_session"], {"essential": True, "value": "s1"})

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
        self.assertEqual(merged["access_token"]["xms_agent_session"], {"essential": True, "value": "s1"})

    def test_new_claims_overwrites_existing_key(self):
        existing = json.dumps({"access_token": {"xms_agent_session": {"essential": True, "value": "old"}}})
        result = merge_access_token_claims(existing, _agentic_claims("new"))
        merged = json.loads(result)
        self.assertEqual(len(merged), 1)
        self.assertEqual(len(merged["access_token"]), 1)
        self.assertEqual(merged["access_token"]["xms_agent_session"], {"essential": True, "value": "new"})

    def test_creates_access_token_when_missing_in_existing(self):
        existing = json.dumps({"id_token": {"auth_time": {"essential": True}}})
        result = merge_access_token_claims(existing, _agentic_claims())
        merged = json.loads(result)
        self.assertEqual(len(merged), 2)
        self.assertEqual(len(merged["access_token"]), 1)
        self.assertEqual(merged["id_token"], {"auth_time": {"essential": True}})
        self.assertEqual(merged["access_token"]["xms_agent_session"], {"essential": True, "value": "s1"})

    def test_handles_null_access_token_in_existing(self):
        existing = json.dumps({"access_token": None})
        result = merge_access_token_claims(existing, _agentic_claims())
        merged = json.loads(result)
        self.assertEqual(len(merged), 1)
        self.assertEqual(len(merged["access_token"]), 1)
        self.assertEqual(merged["access_token"]["xms_agent_session"], {"essential": True, "value": "s1"})


if __name__ == '__main__':
    unittest.main()
