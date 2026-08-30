#!/usr/bin/env bash
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
#
# Signs in with a real, unlocked libsecret keyring. Run under dbus-run-session: gnome-keyring
# talks over the session bus, and a hosted runner has no session bus of its own.
#
# Expects AZ_FEDERATED_TOKEN, AZURE_CLIENT_ID and AZURE_TENANT_ID in the environment.

set -e

# An empty password creates and unlocks the login keyring in one step. Nothing here guards a real
# secret: the keyring lives and dies with this job.
#
# --login, not --unlock: --unlock asks gcr-prompter to confirm, and a prompter needs a display the
# runner does not have. --login takes the password over the daemon's control protocol and creates
# the login keyring if it is missing, so nothing is ever prompted for.
mkdir -p "$HOME/.local/share/keyrings"
eval "$(printf 'ci-only-keyring-password' | gnome-keyring-daemon --daemonize --login)"
export GNOME_KEYRING_CONTROL SSH_AUTH_SOCK
eval "$(gnome-keyring-daemon --start --components=secrets)"
export GNOME_KEYRING_CONTROL SSH_AUTH_SOCK

# Fail here rather than inside az if the keyring itself is the problem.
.cienv/bin/python .github/scripts/check_keyring_roundtrip.py

az() { "$PWD/.cienv/bin/az" "$@"; }

az account clear || true
rm -f "$HOME/.azure"/msal_token_cache.* "$HOME/.azure"/service_principal_entries.*

set +e
az login --service-principal -u "$AZURE_CLIENT_ID" --tenant "$AZURE_TENANT_ID" \
  --federated-token "$AZ_FEDERATED_TOKEN" --allow-no-subscriptions --debug -o none \
  > login.out 2> login.err
status=$?
set -e

# --debug echoes the command line, so nothing is shown until the token is gone.
.cienv/bin/python .github/scripts/scrub.py login.err login.out
if [ $status -ne 0 ]; then
  echo "::error::az login failed"
  tail -40 login.err
  exit 1
fi

ls -la "$HOME/.azure" | grep -E 'msal_token_cache|service_principal' || true
.cienv/bin/python .github/scripts/check_keyring_encryption.py login.err
