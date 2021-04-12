# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
A temporary workaround for MSAL limitation
https://github.com/AzureAD/microsoft-authentication-library-for-python/issues/335

After a successful sign-in, if the sign-in account already exists in the token
cache, remove it first along with its tokens to prevent MSAL from returning
cached access tokens from the previous session that may have been revoked.

Otherwise, MSAL will return revoked access tokens, resulting in 401 failure
which can't be handled by commands that don't support silent reauth.
"""

# pylint: skip-file
# flake8: noqa

import json
import time

from knack.log import get_logger

from msal.oauth2cli.oauth2 import Client
from msal.token_cache import decode_id_token, canonicalize, decode_part

logger = get_logger(__name__)


def patch_token_cache_add(callback):

    def __add(self, event, now=None):
        # event typically contains: client_id, scope, token_endpoint,
        # response, params, data, grant_type
        environment = realm = None
        if "token_endpoint" in event:
            _, environment, realm = canonicalize(event["token_endpoint"])
        if "environment" in event:  # Always available unless in legacy test cases
            environment = event["environment"]  # Set by application.py
        response = event.get("response", {})
        data = event.get("data", {})
        access_token = response.get("access_token")
        refresh_token = response.get("refresh_token")
        id_token = response.get("id_token")
        id_token_claims = (
            decode_id_token(id_token, client_id=event["client_id"])
            if id_token else {})
        client_info = {}
        home_account_id = None  # It would remain None in client_credentials flow
        if "client_info" in response:  # We asked for it, and AAD will provide it
            client_info = json.loads(decode_part(response["client_info"]))
            home_account_id = "{uid}.{utid}".format(**client_info)
        elif id_token_claims:  # This would be an end user on ADFS-direct scenario
            client_info["uid"] = id_token_claims.get("sub")
            home_account_id = id_token_claims.get("sub")

        target = ' '.join(event.get("scope") or [])  # Per schema, we don't sort it

        with self._lock:
            now = int(time.time() if now is None else now)

            if client_info and not event.get("skip_account_creation"):
                account = {
                    "home_account_id": home_account_id,
                    "environment": environment,
                    "realm": realm,
                    "local_account_id": id_token_claims.get(
                        "oid", id_token_claims.get("sub")),
                    "username": id_token_claims.get("preferred_username")  # AAD
                                or id_token_claims.get("upn")  # ADFS 2019
                                or "",  # The schema does not like null
                    "authority_type":
                        self.AuthorityType.ADFS if realm == "adfs"
                        else self.AuthorityType.MSSTS,
                    # "client_info": response.get("client_info"),  # Optional
                }

                logger.debug("Remove existing account %r", account)
                logger.debug("Calling %r", callback)
                callback(account)
                self.modify(self.CredentialType.ACCOUNT, account, account)

            if id_token:
                idt = {
                    "credential_type": self.CredentialType.ID_TOKEN,
                    "secret": id_token,
                    "home_account_id": home_account_id,
                    "environment": environment,
                    "realm": realm,
                    "client_id": event.get("client_id"),
                    # "authority": "it is optional",
                }
                self.modify(self.CredentialType.ID_TOKEN, idt, idt)

            if access_token:
                expires_in = int(  # AADv1-like endpoint returns a string
                    response.get("expires_in", 3599))
                ext_expires_in = int(  # AADv1-like endpoint returns a string
                    response.get("ext_expires_in", expires_in))
                at = {
                    "credential_type": self.CredentialType.ACCESS_TOKEN,
                    "secret": access_token,
                    "home_account_id": home_account_id,
                    "environment": environment,
                    "client_id": event.get("client_id"),
                    "target": target,
                    "realm": realm,
                    "token_type": response.get("token_type", "Bearer"),
                    "cached_at": str(now),  # Schema defines it as a string
                    "expires_on": str(now + expires_in),  # Same here
                    "extended_expires_on": str(now + ext_expires_in)  # Same here
                }
                if data.get("key_id"):  # It happens in SSH-cert or POP scenario
                    at["key_id"] = data.get("key_id")
                if "refresh_in" in response:
                    refresh_in = response["refresh_in"]  # It is an integer
                    at["refresh_on"] = str(now + refresh_in)  # Schema wants a string
                self.modify(self.CredentialType.ACCESS_TOKEN, at, at)

            if refresh_token:
                rt = {
                    "credential_type": self.CredentialType.REFRESH_TOKEN,
                    "secret": refresh_token,
                    "home_account_id": home_account_id,
                    "environment": environment,
                    "client_id": event.get("client_id"),
                    "target": target,  # Optional per schema though
                    "last_modification_time": str(now),  # Optional. Schema defines it as a string.
                }
                if "foci" in response:
                    rt["family_id"] = response["foci"]
                self.modify(self.CredentialType.REFRESH_TOKEN, rt, rt)

            app_metadata = {
                "client_id": event.get("client_id"),
                "environment": environment,
            }
            if "foci" in response:
                app_metadata["family_id"] = response.get("foci")
            self.modify(self.CredentialType.APP_METADATA, app_metadata, app_metadata)

    def obtain_token_by_refresh_token(self, token_item, scope=None,
                                      rt_getter=lambda token_item: token_item["refresh_token"],
                                      on_removing_rt=None,
                                      on_updating_rt=None,
                                      on_obtaining_tokens=None,
                                      **kwargs):
        resp = super(Client, self).obtain_token_by_refresh_token(
            rt_getter(token_item)
            if not isinstance(token_item, str) else token_item,
            scope=scope,
            also_save_rt=on_updating_rt is False,
            on_obtaining_tokens=on_obtaining_tokens,
            **kwargs)
        if resp.get('error') == 'invalid_grant':
            (on_removing_rt or self.on_removing_rt)(token_item)  # Discard old RT
        RT = "refresh_token"
        if on_updating_rt is not False and RT in resp:
            (on_updating_rt or self.on_updating_rt)(token_item, resp[RT])
        return resp

    from unittest.mock import patch

    # Temporary patch for https://github.com/AzureAD/microsoft-authentication-library-for-python/issues/335
    cm_add = patch('msal.token_cache.TokenCache._TokenCache__add', __add)

    # Temporary patch for https://github.com/AzureAD/microsoft-authentication-library-for-python/pull/339
    cm_obtain_token_by_refresh_token = patch('msal.oauth2cli.oauth2.Client.obtain_token_by_refresh_token',
                                             obtain_token_by_refresh_token)
    cm_add.__enter__()
    cm_obtain_token_by_refresh_token.__enter__()
