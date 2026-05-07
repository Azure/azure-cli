# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Support for Entra Agentic Sessions.

When CLI runs inside an agent context (e.g., Copilot, Azure MCP), the orchestrator sets the
COPILOT_AGENT_SESSION_ID environment variable. CLI reads it and passes it to MSAL as both:
  - A query parameter (`client_session`) so ESTS can identify the agentic session
  - A claims challenge so ESTS embeds an agentic marker claim in the token (and MSAL bypasses
    the access token cache to ensure a fresh, agent-tagged token is always fetched)

This enables downstream systems (RBAC, Defender, Purview) to enforce differentiated policies
for agent-driven vs. human-driven operations.
"""

import json
import os

from knack.log import get_logger

logger = get_logger(__name__)

COPILOT_AGENT_SESSION_ID = "COPILOT_AGENT_SESSION_ID"


def build_agentic_session_params():
    """Read COPILOT_AGENT_SESSION_ID and build the agentic claims challenge.

    :returns: (session_id, claims_challenge) — both None when env var is not set.
    """
    session_id = os.environ.get(COPILOT_AGENT_SESSION_ID) or None
    if not session_id:
        return None, None

    logger.debug("Agentic session detected (COPILOT_AGENT_SESSION_ID is set)")

    claims_challenge = json.dumps({
        "access_token": {
            "xms_cli_sid": {"values": [session_id]}
        }
    })
    return session_id, claims_challenge


def merge_access_token_claims(existing_claims, new_claims):
    """Merge new claims into an existing claims_challenge JSON string.

    :param existing_claims: Existing claims_challenge JSON string (or None).
    :param new_claims: New claims_challenge JSON string to merge in. Must not be None or empty,
        and must contain a non-empty ``access_token`` object.
    :returns: Merged claims_challenge JSON string.
    :raises ValueError: If ``new_claims`` is None, empty, or does not contain a non-empty
        ``access_token`` object.
    """
    if not new_claims:
        raise ValueError("new_claims must not be None or empty")
    new_access_token = json.loads(new_claims).get("access_token")
    if not new_access_token:
        raise ValueError("new_claims must contain a non-empty access_token")

    claims_dict = json.loads(existing_claims) if existing_claims else {}
    claims_dict["access_token"] = claims_dict.get("access_token") or {}
    claims_dict["access_token"].update(new_access_token)
    return json.dumps(claims_dict)
