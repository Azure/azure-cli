# Plan: add Azure AI Search 2026-03-01-preview API support

## Goal

Add Azure CLI support for the Azure AI Search management-plane API version `2026-03-01-preview`, based on:

- Swagger: `azure-rest-api-specs/specification/search/resource-manager/Microsoft.Search/Search/preview/2026-03-01-preview/search.json`
- Current Search CLI module: `src\azure-cli\azure\cli\command_modules\search`
- Repo guidance in `doc\authoring_command_modules\authoring_commands.md`, `doc\authoring_command_modules\README.md`, and `doc\how_to_bump_SDK_version_in_cli.md`
- Prior Search PR patterns, especially Azure/azure-cli#32111 (`{Search} az search: Add 2025-05-01 support`) and Azure/azure-cli#16707 (`[Search] Upgrade to use the latest azure-mgmt-search python sdk`)

## Current state

- The Search command loader uses `ResourceType.MGMT_SEARCH`, but `src\azure-cli-core\azure\cli\core\profiles\_shared.py` leaves `MGMT_SEARCH` as `None`, so the SDK-backed commands rely on the SDK package default API version rather than a CLI profile override.
- `azure-mgmt-search` is pinned to `9.0.0` in:
  - `src\azure-cli\setup.py`
  - `src\azure-cli\requirements.py3.windows.txt`
  - `src\azure-cli\requirements.py3.Linux.txt`
  - `src\azure-cli\requirements.py3.Darwin.txt`
- The module is now mostly generated AAZ code. PR #32111 moved Search operations into `src\azure-cli\azure\cli\command_modules\search\aaz\latest\...` and pinned generated operations to `2025-05-01`.
- Custom wrappers in `custom.py` still subclass generated AAZ `search service create/update` to preserve CLI-specific behavior, especially:
  - `--ip-rules` string parsing into generated `ip_rules_internal`
  - `--auth-options` compatibility wrapper around generated auth option objects
  - mutual-exclusion validation for auth arguments
- Tests live under `src\azure-cli\azure\cli\command_modules\search\tests\latest`, with live recordings in `recordings\`.

## API delta from `2025-05-01` to `2026-03-01-preview`

The swagger comparison shows:

- Existing paths: 21 -> 22.
- New path:
  - `GET /providers/Microsoft.Search/offerings`, `operationId=Offerings_List`
- New model definitions:
  - `OfferingsListResult`
  - `OfferingsByRegion`
  - `SkuOffering`
  - `SkuLimits`
  - `FeatureOffering`
  - `KnowledgeRetrieval`
  - `SearchResourceEncryptionKey`
  - `DataIdentity`
  - `DataUserAssignedIdentity`
  - `DataNoneIdentity`
  - `AzureActiveDirectoryApplicationCredentials`
- Changed service properties:
  - `SearchServiceProperties.knowledgeRetrieval`: new nullable enum-like property with values `free` and `standard`.
  - `SearchResourceEncryptionKey`: expanded from the existing CMK fields to include explicit data-plane identity and optional Azure AD application credentials for Key Vault access.

## Implementation plan

### 1. Decide the source of generated code

Use AAZ generation as the primary path, consistent with repo guidance that AAZ is recommended for control-plane APIs and can generate directly from swagger without waiting for SDK release.

If the `azure-mgmt-search` SDK has a version that includes `2026-03-01-preview`, also bump the SDK package pins so SDK-backed legacy operations stay aligned. If no SDK is published yet, keep `azure-mgmt-search==9.0.0` and only regenerate/update AAZ commands, because AAZ directly sends REST requests with explicit `api-version`.

### 2. Regenerate Search AAZ commands for `2026-03-01-preview`

Regenerate or manually refresh generated Search AAZ code under:

- `src\azure-cli\azure\cli\command_modules\search\aaz\latest\search\...`

Required generated changes:

- Update `_aaz_info["version"]` and all generated `"api-version"` query parameters from `2025-05-01` to `2026-03-01-preview`.
- Ensure existing generated commands remain present:
  - `search service create/show/list/update/delete/wait/check-name-availability/upgrade`
  - `search service admin-key ...`
  - `search service query-key ...`
  - `search service private-endpoint-connection ...`
  - `search service private-link-resource ...`
  - `search service shared-private-link-resource ...`
  - `search service network-security-perimeter-configuration ...`
  - `search usage list/show`
- Add the new top-level offerings operation as an AAZ command. Suggested command surface:
  - `az search offering list`
  - Alternative if reviewers prefer plural naming from the REST resource: `az search offerings list`
- Add help for the new command in `_help.py`, including an example:
  - `az search offering list`

### 3. Add CLI exposure for new service property `knowledgeRetrieval`

Add generated and customized support for the new service property:

- In generated `search service create`:
  - Add argument `--knowledge-retrieval` in the `Properties` argument group.
  - Enum values: `free`, `standard`.
  - Serialize to `properties.knowledgeRetrieval`.
  - Include in output schema.
- In generated `search service update`:
  - Add nullable argument `--knowledge-retrieval`.
  - Enum values: `free`, `standard`.
  - Serialize/update `properties.knowledgeRetrieval`.
  - Include in output schema.
- In `_params.py`, only add explicit metadata if needed to match established CLI style. AAZ should own most generated arg metadata.
- In `_help.py`, add examples for:
  - Creating a service with knowledge retrieval on the free plan.
  - Updating a service to the standard plan.

Open design point for implementation: because the API enum has no `disabled` value, use `null`/omission to leave or clear the value only if the generated PATCH semantics and service behavior support it. Do not invent a `disabled` CLI value unless the service team confirms it maps to a real API behavior.

### 4. Add support for expanded CMK identity/credential schema

The existing AAZ surface already exposes `--encryption-with-cmk` as a generic object with only `enforcement` modeled. The new API adds nested CMK key fields, explicit identity, and AAD app credentials.

Preferred low-risk plan:

- Keep `--encryption-with-cmk` as the generated object argument so advanced users can pass the full object.
- Ensure generated content/output schemas include:
  - `properties.encryptionWithCmk.encryptionKey.keyVaultKeyName`
  - `properties.encryptionWithCmk.encryptionKey.keyVaultKeyVersion`
  - `properties.encryptionWithCmk.encryptionKey.keyVaultUri`
  - `properties.encryptionWithCmk.encryptionKey.identity.@odata.type`
  - `properties.encryptionWithCmk.encryptionKey.identity.userAssignedIdentity`
  - `properties.encryptionWithCmk.encryptionKey.identity.federatedIdentityClientId`
  - `properties.encryptionWithCmk.encryptionKey.accessCredentials.applicationId`
  - `properties.encryptionWithCmk.encryptionKey.accessCredentials.applicationSecret`
- Mark any generated secret fields consistently with swagger (`x-ms-secret`) so CLI output and recordings do not leak secrets.
- Add first-class convenience arguments only if Search service owners want a stable CLI contract now. If adding them, suggested names:
  - `--cmk-key-name`
  - `--cmk-key-version`
  - `--cmk-key-vault-uri`
  - `--cmk-identity`
  - `--cmk-federated-client-id`
  - `--cmk-aad-application-id`
  - `--cmk-aad-application-secret`

### 5. Preserve Search custom behavior

After regeneration, reapply or verify the customizations in `custom.py`:

- `SearchServiceCreate` and `SearchServiceUpdate` must still subclass the regenerated AAZ classes.
- Keep `--ip-rules` compatibility and hiding of generated `ip_rules_internal`.
- Keep `--auth-options` compatibility and hiding of generated `api_key_only`.
- Preserve the existing mutual-exclusion checks for `--disable-local-auth`, `--auth-options`, and `--aad-auth-failure-mode`.
- Re-check existing manually hidden args (`endpoint`, `upgrade_available`, `api_key_only`, `ip_rules_internal`) against the regenerated schema. If the service now expects any previously hidden field as settable, document and intentionally expose it.

### 6. Align legacy SDK-backed operations if needed

If a new `azure-mgmt-search` package is available:

- Bump package pins in `setup.py` and all three requirements files.
- Verify whether `ResourceType.MGMT_SEARCH` should remain `None` or be set to `2026-03-01-preview` in `src\azure-cli-core\azure\cli\core\profiles\_shared.py`.
- If the SDK becomes multi-API and requires explicit version selection, follow `doc\how_to_bump_SDK_version_in_cli.md` and update the latest API profile for `MGMT_SEARCH`.

If no SDK is available:

- Do not change package pins.
- Prefer migrating remaining SDK-backed commands to AAZ if reviewers want every Search command on the preview API. PR #32111 already shows this migration pattern.

### 7. Tests and recordings

Add or update tests in `src\azure-cli\azure\cli\command_modules\search\tests\latest`:

- Update recordings for existing Search scenario tests so management requests use `api-version=2026-03-01-preview`.
- Add `test_service_create_knowledge_retrieval`:
  - Create a service with `--knowledge-retrieval free`.
  - Assert `knowledgeRetrieval == free`.
- Add `test_service_update_knowledge_retrieval`:
  - Create a service.
  - Update with `--knowledge-retrieval standard`.
  - Assert the updated output has `knowledgeRetrieval == standard`.
- Add a new offerings test:
  - `az search offering list`
  - Assert a list payload is returned and contains region entries with SKU or feature information.
- If adding first-class CMK arguments, add a unit-level argument serialization test or a recorded test with scrubbed secrets. Avoid live recordings that contain real app secrets.
- Keep `recording_processors.py` secret scrubbing current; extend it if CMK AAD credentials are recorded.

### 8. Generated indices and lint metadata

After command/help changes:

- Run `azdev latest-index generate`.
- Run `azdev latest-index verify`.
- Update `src\azure-cli-core\azure\cli\core\commandIndex.latest.json` and `src\azure-cli-core\azure\cli\core\helpIndex.latest.json` if generated output changes.
- Keep or update `src\azure-cli\azure\cli\command_modules\search\linter_exclusions.yml` only for intentional generated-command exceptions.

### 9. Validation commands

Run targeted validation first:

```powershell
azdev test search --discover --no-exitfirst
azdev test search --live --no-exitfirst
azdev style search
azdev latest-index verify
```

If the SDK is bumped, also run broader dependency/regression validation consistent with `doc\how_to_bump_SDK_version_in_cli.md`:

```powershell
azdev test --no-exitfirst
```

### 10. PR notes

Use a PR title matching recent convention:

```text
{Search} az search: Add 2026-03-01-preview support
```

Suggested history notes if customer-facing commands/arguments are added:

- `[Search] az search: Add 2026-03-01-preview support.`
- `[Search] az search offering list: Add command to list Azure AI Search offerings by region.`
- `[Search] az search service create/update: Add --knowledge-retrieval to configure the agentic retrieval billing plan.`

## Risks and review questions

- `2026-03-01-preview` is a preview API. Confirm with Search service owners whether the CLI should move all Search commands to the preview API or expose only new preview functionality.
- Confirm the preferred command group name: `search offering` vs. `search offerings`.
- Confirm whether `knowledgeRetrieval` can be cleared on update, because the swagger has no explicit `disabled` enum value.
- Confirm whether expanded CMK support should remain object-only for this release or receive first-class CLI parameters.
- If a new SDK package is unavailable, SDK-backed commands may remain on `azure-mgmt-search==9.0.0`; reviewers should confirm whether that mixed state is acceptable or whether remaining legacy commands must be migrated to AAZ.
