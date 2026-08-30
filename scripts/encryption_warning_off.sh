#!/usr/bin/env bash
# Undoes scripts/encryption_warning_on.sh: restores DBUS_SESSION_BUS_ADDRESS and AZURE_CONFIG_DIR
# to whatever they were, and deletes the throwaway config directory along with the unencrypted
# credentials that were written into it.
#
#   source scripts/encryption_warning_off.sh

if [ -n "${BASH_VERSION:-}" ]; then
    _az_warn_sourced=0
    [[ "${BASH_SOURCE[0]}" != "${0}" ]] && _az_warn_sourced=1
elif [ -n "${ZSH_VERSION:-}" ]; then
    case "$ZSH_EVAL_CONTEXT" in
        *:file*) _az_warn_sourced=1 ;;
        *) _az_warn_sourced=0 ;;
    esac
else
    echo "error: this script supports bash and zsh only." >&2
    return 1 2>/dev/null || exit 1
fi

if [ "$_az_warn_sourced" -eq 0 ]; then
    echo "error: this script changes the current shell, so it has to be sourced:" >&2
    echo "           source scripts/encryption_warning_off.sh" >&2
    exit 1
fi
unset _az_warn_sourced

if [[ -z "${AZ_WARN_DEMO_ACTIVE:-}" ]]; then
    echo "Nothing to restore: scripts/encryption_warning_on.sh is not active in this shell."
    return 0
fi

# Delete the plaintext credentials rather than leaving them in /tmp.
if [[ -n "${AZ_WARN_CONFIG_DIR:-}" && "$AZ_WARN_CONFIG_DIR" == /tmp/az_warn_demo.* ]]; then
    rm -rf "$AZ_WARN_CONFIG_DIR"
    echo "Removed $AZ_WARN_CONFIG_DIR and the unencrypted credentials in it."
fi

if [[ "${AZ_WARN_SAVED_DBUS_SET:-0}" == "1" ]]; then
    export DBUS_SESSION_BUS_ADDRESS="$AZ_WARN_SAVED_DBUS"
else
    unset DBUS_SESSION_BUS_ADDRESS
fi

if [[ "${AZ_WARN_SAVED_CONFIG_SET:-0}" == "1" ]]; then
    export AZURE_CONFIG_DIR="$AZ_WARN_SAVED_CONFIG"
else
    unset AZURE_CONFIG_DIR
fi

unset AZ_WARN_DEMO_ACTIVE AZ_WARN_CONFIG_DIR
unset AZ_WARN_SAVED_DBUS_SET AZ_WARN_SAVED_DBUS AZ_WARN_SAVED_CONFIG_SET AZ_WARN_SAVED_CONFIG

echo "Restored. DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-<unset>}"
echo "          AZURE_CONFIG_DIR=${AZURE_CONFIG_DIR:-<unset, defaults to ~/.azure>}"

# Log in again so that the restored shell is immediately usable, and so the same commands can be
# run in both states to compare them. This writes to the real config dir and replaces whatever
# account was signed in there, so set AZ_WARN_NO_LOGIN=1 to skip it.
if [[ -n "${AZ_WARN_NO_LOGIN:-}" ]]; then
    echo
    echo "Skipped signing in again (AZ_WARN_NO_LOGIN is set)."
    return 0
fi

_az_warn_off_self="${_az_warn_off_self:-}"
if [ -n "${BASH_VERSION:-}" ]; then
    _az_warn_off_self="${BASH_SOURCE[0]}"
elif [ -n "${ZSH_VERSION:-}" ]; then
    _az_warn_off_self="$(eval 'echo ${(%):-%x}')"
fi
_az_warn_off_root="$(cd "$(dirname "$_az_warn_off_self")/.." && pwd)"
_az_warn_off_sp="${AZ_LIVETEST_SP_FILE:-$HOME/.azure-cli-livetest-sp.json}"

if [[ -x "$_az_warn_off_root/.venv/bin/python" && -f "$_az_warn_off_sp" ]]; then
    echo
    echo "Signing in to ${AZURE_CONFIG_DIR:-$HOME/.azure} so the shell is ready to use..."
    _az_warn_off_creds="$(python3 -c "
import json
c = json.load(open('$_az_warn_off_sp'))
print(c['appId']); print(c['password']); print(c['tenant'])")"
    if _az_warn_off_err="$("$_az_warn_off_root/.venv/bin/python" -m azure.cli login \
            --service-principal \
            -u "$(printf '%s\n' "$_az_warn_off_creds" | sed -n 1p)" \
            -p "$(printf '%s\n' "$_az_warn_off_creds" | sed -n 2p)" \
            --tenant "$(printf '%s\n' "$_az_warn_off_creds" | sed -n 3p)" -o none 2>&1)"; then
        echo "Signed in. 'az group list' now works with no warning: the credentials are"
        echo "encrypted in the keyring, which is what the warning was telling you was missing."
    else
        echo "warning: could not sign in again:" >&2
        printf '%s\n' "$_az_warn_off_err" >&2
        echo "Run 'az login' when you need an account." >&2
    fi
    unset _az_warn_off_creds _az_warn_off_err
fi

unset _az_warn_off_self _az_warn_off_root _az_warn_off_sp
