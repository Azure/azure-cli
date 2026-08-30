#!/usr/bin/env bash
# Puts the current shell into the state a Linux user is in when the system keyring is unreachable,
# so that plain 'az' commands can be run by hand to see the encryption warning.
#
# This must be sourced, not executed: a child process cannot change the environment of the shell
# that started it.
#
#   source scripts/encryption_warning_on.sh
#   az group list                 # warns twice
#   source scripts/encryption_warning_off.sh
#
# The real AZURE_CONFIG_DIR is left alone. Credentials go to a throwaway directory that the off
# script deletes, which matters here because the whole point is that they are written unencrypted.

if [ -n "${BASH_VERSION:-}" ]; then
    _az_warn_sourced=0
    [[ "${BASH_SOURCE[0]}" != "${0}" ]] && _az_warn_sourced=1
    _az_warn_self="${BASH_SOURCE[0]}"
elif [ -n "${ZSH_VERSION:-}" ]; then
    # zsh has no BASH_SOURCE. %x expands to the file currently being sourced.
    case "$ZSH_EVAL_CONTEXT" in
        *:file*) _az_warn_sourced=1 ;;
        *) _az_warn_sourced=0 ;;
    esac
    _az_warn_self="$(eval 'echo ${(%):-%x}')"
else
    echo "error: this script supports bash and zsh only." >&2
    return 1 2>/dev/null || exit 1
fi

if [ "$_az_warn_sourced" -eq 0 ]; then
    echo "error: this script changes the current shell, so it has to be sourced:" >&2
    echo "           source scripts/encryption_warning_on.sh" >&2
    exit 1
fi

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "error: only Linux uses libsecret. macOS Keychain and Windows DPAPI cannot be made" >&2
    echo "       unreachable through an environment variable." >&2
    return 1
fi

if [[ -n "${AZ_WARN_DEMO_ACTIVE:-}" ]]; then
    # A previous run may have left the shell half-configured, e.g. the config dir was switched but
    # the login failed. Restore first, then set up cleanly, rather than making this a dead end.
    echo "Already active from an earlier run. Restoring first, then starting fresh..."
    AZ_WARN_NO_LOGIN=1
    export AZ_WARN_NO_LOGIN
    source "$(dirname "$_az_warn_self")/encryption_warning_off.sh" >/dev/null 2>&1
    unset AZ_WARN_NO_LOGIN
fi

_az_warn_repo_root="$(cd "$(dirname "$_az_warn_self")/.." && pwd)"
_az_warn_sp_file="${AZ_LIVETEST_SP_FILE:-$HOME/.azure-cli-livetest-sp.json}"
_az_warn_python="$_az_warn_repo_root/.venv/bin/python"

if [[ ! -x "$_az_warn_python" ]]; then
    echo "error: no virtualenv python at $_az_warn_python" >&2
    echo "       Resolved the repo root as $_az_warn_repo_root, which looks wrong." >&2
    unset _az_warn_repo_root _az_warn_sp_file _az_warn_python _az_warn_self _az_warn_sourced
    return 1
fi

if [[ ! -f "$_az_warn_sp_file" ]]; then
    echo "error: $_az_warn_sp_file not found." >&2
    echo "       Set AZ_LIVETEST_SP_FILE to a JSON file with appId, password and tenant." >&2
    unset _az_warn_repo_root _az_warn_sp_file
    return 1
fi

# Remember what to put back. Whether each variable was set at all is recorded separately, so that
# the off script can unset rather than restore an empty value.
if [[ -n "${DBUS_SESSION_BUS_ADDRESS+x}" ]]; then
    AZ_WARN_SAVED_DBUS_SET=1
    AZ_WARN_SAVED_DBUS="$DBUS_SESSION_BUS_ADDRESS"
else
    AZ_WARN_SAVED_DBUS_SET=0
fi

if [[ -n "${AZURE_CONFIG_DIR+x}" ]]; then
    AZ_WARN_SAVED_CONFIG_SET=1
    AZ_WARN_SAVED_CONFIG="$AZURE_CONFIG_DIR"
else
    AZ_WARN_SAVED_CONFIG_SET=0
fi

AZ_WARN_CONFIG_DIR="$(mktemp -d -t az_warn_demo.XXXXXX)"
export AZURE_CONFIG_DIR="$AZ_WARN_CONFIG_DIR"
export DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent'
export AZ_WARN_DEMO_ACTIVE=1
export AZ_WARN_SAVED_DBUS_SET AZ_WARN_SAVED_DBUS AZ_WARN_SAVED_CONFIG_SET AZ_WARN_SAVED_CONFIG
export AZ_WARN_CONFIG_DIR

echo "Logging in so that ordinary commands have an account to work with..."
_az_warn_creds="$(python3 -c "
import json
c = json.load(open('$_az_warn_sp_file'))
print(c['appId']); print(c['password']); print(c['tenant'])")"
_az_warn_appid="$(printf '%s\n' "$_az_warn_creds" | sed -n 1p)"
_az_warn_secret="$(printf '%s\n' "$_az_warn_creds" | sed -n 2p)"
_az_warn_tenant="$(printf '%s\n' "$_az_warn_creds" | sed -n 3p)"

# Keep stderr: guessing at the cause of a login failure sends people down the wrong path.
if ! _az_warn_login_err="$("$_az_warn_python" -m azure.cli login --service-principal \
        -u "$_az_warn_appid" -p "$_az_warn_secret" --tenant "$_az_warn_tenant" -o none 2>&1)"; then
    echo "error: login failed:" >&2
    printf '%s\n' "$_az_warn_login_err" | grep -v 'Encryption is unavailable' >&2
    AZ_WARN_NO_LOGIN=1
    export AZ_WARN_NO_LOGIN
    source "$_az_warn_repo_root/scripts/encryption_warning_off.sh" >/dev/null 2>&1
    unset AZ_WARN_NO_LOGIN
    unset _az_warn_repo_root _az_warn_sp_file _az_warn_python _az_warn_self _az_warn_sourced
    unset _az_warn_creds _az_warn_appid _az_warn_secret _az_warn_tenant _az_warn_login_err
    return 1
fi

cat <<EOF

  The keyring is now unreachable for this shell only.

    AZURE_CONFIG_DIR          $AZURE_CONFIG_DIR
    DBUS_SESSION_BUS_ADDRESS  $DBUS_SESSION_BUS_ADDRESS

  Try any command that authenticates, and watch it warn twice:

    az group list
    az account get-access-token
    az account show          # no warning: reads azureProfile.json, never the credentials

  Put everything back with:

    source scripts/encryption_warning_off.sh

EOF

unset _az_warn_repo_root _az_warn_sp_file _az_warn_python _az_warn_self _az_warn_sourced
unset _az_warn_creds _az_warn_appid _az_warn_secret _az_warn_tenant _az_warn_login_err
