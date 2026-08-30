# Encryption manual test plan

## Prerequisites

**Identities:** 2 users + 2 service principals. Users only land in the token cache, service
principals only in the secret store. That split is what proves a logout removed the right one.

**Make encryption work on WSL.** A fresh WSL has no keyring, so the CLI silently falls back to
plaintext and every encryption check would pass for the wrong reason:

```bash
sudo apt install gir1.2-secret-1 libsecret-tools

sudo apt install libgirepository1.0-dev python3-dev 

sudo apt install \             
  libcairo2-dev \
  libgirepository1.0-dev \
  gir1.2-secret-1 \
  pkg-config \
  python3-dev

```

**secret-tool** ships in `libsecret-tools`. It is your window into the keyring:

```bash
secret-tool lookup xdg:schema "Microsoft Azure CLI" type "Token cache"
secret-tool lookup xdg:schema "Microsoft Azure CLI" type "Secret store"
```

On macOS use `security find-generic-password -s "Microsoft Azure CLI" -a "Token cache" -w`.

**Turning D-Bus off.** Do not uninstall anything, just point it at nothing for one command:
```bash
DBUS_SESSION_BUS_ADDRESS=unix:path=/nonexistent az login
```

**Switching encryption.** `az config set core.encrypt_token_cache=true|false`

**Between every test:**

```bash
az account clear && rm -f ~/.azure/msal_token_cache.* ~/.azure/service_principal_entries.*
```

## File extensions

| Extension | When | What is inside |
| --- | --- | --- |
| `.json` | encryption off | plaintext, the secret is readable |
| `.bin` | encryption on, Windows | the ciphertext itself |
| `.sig` | encryption on, Linux/macOS | an empty file, a modification timestamp only. The payload is in the keyring |

On Linux and macOS, deleting the `.sig` file only *hides* the credential. The copy in
libsecret/Keychain is still there. Several tests below exist to guard that trap.

## The matrix

|  | encryption ON | encryption OFF |
| --- | --- | --- |
| **D-Bus OK** | keyring + empty `.sig` | plaintext `.json` |
| **D-Bus dead** | falls back to `.json` + warning | plaintext `.json` |

## The tests

**1. Backend matrix.** Run all four cells above: log in all 4 identities, log one out, clear, log in
again. Verify the right file extension exists and the wrong one does not.

**2. Flag flip.** off then on then off.
Simulate old version default off then new version default on then rollback to old version
Verify `.json` and `.sig` coexist, that flipping migrates
nothing and deletes nothing, and that the original plaintext credentials come back unchanged which means user can rollback as long as no az account clear execution.

**3. Selective logout and rollback.** Log out one user and one service principal, then set
encryption back to false. Verify the other three survive, and that you can still log in and get a
token afterwards.

**4. `az account clear`, including idempotency.** Log in with encryption on, flip to off, then
clear. Verify both the files and the *keyring entries* are empty. This is the main point: with the
setting off the keyring is no longer the configured store, but it still holds the secret. Then run
clear a second time should idempotent and success. And az login user and app should work after clear.

**5. Warning on the console.** Encryption on, D-Bus dead, log in. Expect a warning mentioning
plaintext on stderr, and the keyring still empty and debug log should show try to use encryption failure detail.
## How to verify anything

Three checks, in this order:

1. `ls -l ~/.azure/msal_token_cache.* ~/.azure/service_principal_entries.*` — the right file is
   present, the wrong one is absent, and `.sig` is 0 bytes.
2. `secret-tool lookup ...` — is the payload really in the keyring, or really gone?
3. `az account get-access-token --scope https://graph.microsoft.com/.default` — an uncached scope,
   so a service principal with no refresh token has to actually read the stored secret. This is the
   only check that proves the store *works* rather than merely *exists*.

