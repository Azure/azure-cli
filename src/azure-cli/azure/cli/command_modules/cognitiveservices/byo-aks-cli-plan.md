# Cognitive Services BYO AKS CLI Plan

## 1. Background and Goal

Based on [Azure/azure-rest-api-specs#45245](https://github.com/Azure/azure-rest-api-specs/pull/45245) and the [Vienna BYO AKS setup](https://msdata.visualstudio.com/Vienna/_git/vienna/pullrequest/2285162), add BYO AKS (customer-owned AKS agent hosting) support to `az cognitiveservices account create`.

* **Reference**: [BYO-AKS Simplified Onboarding - Technical Design Spec.docx](https://onedrive.cloud.microsoft/:w:/a@qm93vz2m/S/cQqIkrxyppadT4x5zoMK2dAJEgUCgeqpDY_qXO3pZHHQNlYVFQ?isSPOFile=1&ovuser=72f988bf-86f1-41af-91ab-2d7cd011db47%2Czhujiayi%40microsoft.com&wdExp=TEAMS-TREATMENT&web=1&clickparams=eyJBcHBOYW1lIjoiVGVhbXMtRGVza3RvcCIsIkFwcFZlcnNpb24iOiI0OS8yNjEwMDIxMjAxMSJ9).
* **Scope**: Add BYO AKS preflight and SDK provisioning to `az cognitiveservices account create`, including identities, Storage, and required grants. Other commands are unchanged.
* **Prerequisite**: `azure-mgmt-cognitiveservices>=15.0.0b5` (which introduced `AgentHostingConfiguration`, `ManagedClusterAgentHostingConfiguration`, and `AgentHostingType`). In `azure-cli`, [Azure/azure-cli#34112](https://github.com/Azure/azure-cli/pull/34112) upgrades the dependency directly from `15.0.0b4` to `15.0.0b6`.

### User Scenario

1. Prepare a supported AKS cluster.
2. Create the Account with `--agent-hosting-cluster`. Omit the Storage and identity arguments to let the CLI create and configure them automatically.
3. Create the Project with `az cognitiveservices account project create`.
4. Prepare a model deployment and an ACR for the Hosted Agent. Grant `AcrPull` to the Project identity and the AKS kubelet identity, then create the Project's Container Registry connection. Configure Application Insights separately when telemetry is needed.
5. Configure azd with the Project endpoint, model name, ACR, and BYO AKS resource IDs, then deploy and invoke the Hosted Agent.

The Account command prepares the Account-level BYO AKS dependencies. Project, model, ACR, connections, agent deployment, and telemetry remain separate downstream steps.

---

## 2. API Specification

The service API represents agent hosting configuration and account identity as separate properties. The selected CLI design accepts flattened arguments for one hosting configuration and wraps it in a one-item array for the API.

### 2.1 Agent Hosting Configuration

`AccountProperties.agentHostingConfigurations` has `Lifecycle.Read` and `Lifecycle.Create` visibility (immutable after creation, `@minItems(1)`, `@maxItems(1)`):

| Property | Type | Required | Description & Allowed ARM Resource Type |
| :--- | :--- | :--- | :--- |
| `name` | `string` | Yes | CLI supplies `"default"` internally; not a user parameter. |
| `hostingType` | `string` | Yes | CLI supplies the fixed discriminator `"ManagedCluster"` internally; not a user parameter. |
| `hostingManagementIdentityResourceId` | `arm-id` | Yes | Control-plane user-assigned managed identity (`Microsoft.ManagedIdentity/userAssignedIdentities`). Must also be assigned in `account.identity.userAssignedIdentities`. |
| `workloadIdentityResourceId` | `arm-id` | Yes | Workload user-assigned managed identity federated to AKS service accounts (`Microsoft.ManagedIdentity/userAssignedIdentities`). |
| `clusterResourceId` | `arm-id` | Yes | Customer-owned AKS managed cluster (`Microsoft.ContainerService/managedClusters`). |
| `storageAccountResourceId` | `arm-id` | Yes | Customer-owned storage account (`Microsoft.Storage/storageAccounts`). |

## 3. CLI Argument Options

Target command: `az cognitiveservices account create` (hosting arguments are marked `is_preview=True`).

### 3.1 Option A: JSON Array (Not Selected)

Alternative preserving the `AgentHostingConfiguration[]` shape through an inline JSON array or `@<file>`. Not selected because the current scope is one configuration with simple fields: flattened arguments avoid JSON quoting and expose per-field help and validation. Any future array-input support will be handled separately.

| CLI Option | Python Argument | Mapped SDK Target | Requirement | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--agent-hosting` | `agent_hosting` | `properties.agent_hosting_configurations` & `identity.user_assigned_identities` | Required when BYO AKS is used | JSON array (or `@<file>`) containing one object: required `clusterResourceId` and optional Storage/identity IDs. CLI supplies `name` and `hostingType` internally. |

#### Example (Option A)

```bash
az cognitiveservices account create \
    -n foundryByocAccount \
    -g myResourceGroup \
    --kind AIServices \
    --sku S0 \
    -l westus \
    --custom-domain foundrybyocaccount \
    --agent-hosting '[
      {
        "clusterResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ContainerService/managedClusters/cluster1",
        "hostingManagementIdentityResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/account-control-plane",
        "storageAccountResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/storage1",
        "workloadIdentityResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/aks-workload"
      }
    ]'
```

---

### 3.2 Option B: Flattened Arguments (Selected)

Selected for the single-configuration scope, following the repository guideline to expose simple object properties as individual parameters under `arg_group="Agent Hosting"` (`doc/command_guidelines.md`, Single Complex Parameters). The CLI sets `name="default"` and `hostingType="ManagedCluster"` internally; neither is exposed as a user parameter. The account's own `--name` remains unchanged.

| CLI Option | Python Argument | Mapped SDK Target | Requirement |
| :--- | :--- | :--- | :--- |
| `--agent-hosting-cluster` | `agent_hosting_cluster` | `agent_hosting_configurations[0].cluster_resource_id` | Required when BYO AKS is used |
| `--agent-hosting-storage` | `agent_hosting_storage` | `agent_hosting_configurations[0].storage_account_resource_id` | Optional; create if omitted, otherwise check/reuse |
| `--agent-hosting-management-identity` | `agent_hosting_management_identity` | `agent_hosting_configurations[0].hosting_management_identity_resource_id` & `identity.user_assigned_identities` | Optional; create if omitted, otherwise reuse (automatically attached to account identity) |
| `--agent-hosting-workload-identity` | `agent_hosting_workload_identity` | `agent_hosting_configurations[0].workload_identity_resource_id` | Optional; create if omitted, otherwise reuse (not attached to account identity) |

#### Example (Option B, Full Arguments)

```bash
az cognitiveservices account create \
    -n foundryByocAccount \
    -g myResourceGroup \
    --kind AIServices \
    --sku S0 \
    -l westus \
    --custom-domain foundrybyocaccount \
    --agent-hosting-cluster "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ContainerService/managedClusters/cluster1" \
    --agent-hosting-storage "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/storage1" \
    --agent-hosting-management-identity "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/account-control-plane" \
    --agent-hosting-workload-identity "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/aks-workload"
```

#### Example (Option B, Minimal BYO AKS Arguments)

Only the cluster ID is supplied for BYO AKS; Storage and both identities are created automatically.

```bash
az cognitiveservices account create \
    -n foundryByocAccount \
    -g myResourceGroup \
    --kind AIServices \
    --sku S0 \
    -l westus \
    --custom-domain foundrybyocaccount \
    --yes \
    --agent-hosting-cluster "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ContainerService/managedClusters/cluster1"
```

---

## 4. Implementation Notes

1. **Trigger & Argument Validation**:
   * Register the four `--agent-hosting-*` resource ID arguments in `_params.py`, defaulting to `None`.
   * If all hosting arguments are `None` (not provided): preserve existing behavior (do not send an empty `agentHostingConfigurations` array).
   * When `--agent-hosting-cluster` is supplied, `account create` runs preflight, creates/reuses dependencies and configures prerequisite grants, then creates the account. No additional switch is required.
   * Require the cluster ID for BYO AKS and resolve optional fields before constructing the request. Resolve each identity independently: create if omitted, otherwise reuse. Reject empty/non-string values and validate supplied ARM IDs once before model construction.
   * Build one `ManagedClusterAgentHostingConfiguration` with internal values `name="default"` and `hostingType="ManagedCluster"`, and wrap it in a one-item list for the API.
2. **Account Identity Construction (`custom.py`)**:
   * Keep existing `has_system_identity = bool(assign_identity or allow_project_management)` logic in `create()`.
   * Add the resolved hosting-management identity to `user_assigned_identities` (do not attach the workload identity to the account identity).
   * Construct `Identity` directly in `create()` (without modifying shared `compose_identity()`):
     * `SystemAssigned, UserAssigned` when both `has_system_identity` and `user_assigned_identities` are present (default for `AIServices`).
     * `UserAssigned` when `not has_system_identity` and `user_assigned_identities` is present.
     * `SystemAssigned` when `has_system_identity` is present without BYO AKS (unchanged existing behavior).
3. **Validation Boundary & Isolation**:
   * **CLI**: Checks hosting inputs, non-empty strings, and `is_valid_resource_id()` syntax. When `--agent-hosting-cluster` is supplied, perform the read-only preflight checks below before Azure writes.
   * **Zero Impact on Existing Commands**: All new arguments are scoped to `cognitiveservices account create`, with `--agent-hosting-*` under `Agent Hosting`. Shared helpers in `_utils.py` are not modified, and all new `create()` parameters default to `None`.
   * **REST Service (Vienna RP)**: Validates configuration shape, resource types, distinct identities, Hosting UAMI attachment and Account/AKS/Storage subscription alignment. Provisioning checks AKS region, OIDC/Workload Identity, CNI, Kata/labels and Workload client/tenant IDs. ARM authorization failures are not static RBAC validation.

### 4.1 Preflight Checks

Preflight is read-only and completes before any Azure writes. Report each check's name, resource/scope, observed/expected state, missing evidence, and remediation with `PASS`, `FAIL`, `UNVERIFIED`, or `NOT_APPLICABLE`. Mandatory `FAIL`/`UNVERIFIED` stops provisioning.

1. **Inputs and resources**: Validate resource IDs once in `custom.create()`; distinguish malformed, absent and unreadable resources. The target RG must exist; missing RG fails before writes, and read/authentication errors are not treated as absence. Account, AKS and Storage must share a subscription and region; UAMIs may differ, but referenced hosting resources must share a tenant. Require non-empty `principalId` on both UAMIs and `clientId`/`tenantId` on Workload UAMI; check reused identities during preflight and new identities after creation. For planned resources, check request properties and permissions at the existing RG, not GETs on future resources.
2. **AKS cluster**: Require Standard AKS (no pricing-tier restriction), Kubernetes >= 1.31, managed identity, readable OIDC issuer, Workload Identity, and `Succeeded` state; reject Automatic/Arc. Require `networkPlugin=azure` and `networkPluginMode=overlay`. Reject kubenet and non-Overlay networking; check network policy separately under A11. Do not modify the cluster.
3. **Node pools**: Require a `Succeeded` System pool with >= 4 vCPU / 16 GiB. One User pool must simultaneously satisfy Azure Linux, `KataVmIsolation`, >= 1 current node, >= 8 vCPU / 32 GiB, image `AKSAzureLinux-V3katagen2-202608.14.0` or later in the same series, case-sensitive label `agents.ai.azure.com/sandbox-node=true`, disabled SSH, and `Succeeded` state. Autoscaling capacity does not replace the current-node requirement. Read AgentPool child resources; never combine different pools' partial results. Recommended VM SKU names are not hard requirements.
4. **Supplied Storage**: Require the Account region, StorageV2/Hot, HNS disabled, HTTPS only, TLS >= 1.2, shared keys and anonymous Blob disabled, and a valid HTTPS Blob endpoint. Missing/unknown zone redundancy only warns. The public-network baseline requires `publicNetworkAccess=Enabled` and firewall `defaultAction=Allow`; private/restricted Storage is `NOT_APPLICABLE` for this check, with an unverified-network warning, and may continue. API/read/endpoint failures still block.
5. **Permissions**: Check required reads, Account creation, Hosting UAMI assign/action and omitted UAMI/Storage creation. Determine creation permissions from omitted inputs, not failed reads; use each target ARM ID's RG when the resource is absent and deduplicate the shared UAMI creation check. Workload UAMI needs no operator assign/action; G02 covers its FIC-management grant. Require `roleAssignments/write` at the actual resource or target RG only for Assignment branches below. Retain `Microsoft.ContainerService/managedClusters/write` at the AKS parent RG; remove RG-creation and VNet-write checks.

Use ARM `permissions.list_for_resource_group` / `list_for_resource` for operator permissions, matching concrete Actions case-insensitively after each Permission's NotActions. Do not decode login tokens or resolve operator groups locally. These APIs describe the caller, not UAMIs: preserve MI validation using actual principal IDs, inherited assignments, role definitions, Actions/NotActions and DataActions/NotDataActions. G03 Blob access cannot be inferred from management-plane permissions. Exclusions are local to each grant. Missing/unverifiable permission blocks writes; Validation branches never repair grants. Require unconditional grants without claiming full evaluation of conditions, deny assignments, tenant policy or RBAC propagation.

Match requested MI wildcards against combined effective grants, not wildcard strings. Other roles can supply excluded actions; G01-G03 requirements are unchanged.

For BYO AKS, validate Account names before dependency queries: 2-64 characters, alphanumeric first character, then alphanumerics, `_` or `-`. Live AIServices checks confirmed `_` succeeds and `.` fails; do not apply DNS naming rules to Account names. Only check domain availability when `custom_domain` will actually be submitted and is new or changed. Use the root `CognitiveServicesManagementClient.check_domain_availability` with the actual domain and kind; never substitute `account_name`. Account GET treats only 404 as absent; other errors propagate, and domain comparison ignores case.

Telemetry-egress checks remain deferred. Static checks do not prove live routing, DNS, connectivity, or RBAC propagation.

**A11 - NetworkPolicy configuration**: From the existing AKS GET, pass when `networkPolicy` is `azure` or `calico`, or `networkDataplane=cilium` (no separate policy value required). Explicit `none` on the Azure/default dataplane fails; missing/unknown evidence is `UNVERIFIED`. Both block writes. Verify configured capability only, not runtime isolation or product certification; no Kubernetes access, probes or cluster updates. Sources: [AKS](https://learn.microsoft.com/azure/aks/use-network-policies), [Cilium](https://learn.microsoft.com/azure/aks/azure-cni-powered-by-cilium#network-policy-enforcement-with-cilium), [Kubernetes](https://kubernetes.io/docs/concepts/services-networking/network-policies/#prerequisites).

### 4.2 Auto Provision

Unlike the reference's single ARM deployment, az uses sequential SDK calls. After preflight passes, prepare dependencies and only the grants marked Assignment below; wait for these operations to complete and resolve real resource/principal IDs before constructing the Account request. Finally, reuse `custom.py` model construction and call `client.begin_create(resource_group_name, account_name, params)`. No ARM template or deployment submission is used.

**Reminder**: Create a Foundry project separately using the existing `az cognitiveservices account project create` command for subsequent hosted-agent use. Configure a Project connection only if required by that workflow; no Project/ACR/connection automation is added here.

```text
Read-only preflight: validate supplied access and operator authority
    -> SDK: create omitted UAMIs/Storage in the existing RG; reference supplied resources
    -> SDK: ensure Assignment grants G01-G03; wait for completion
    -> SDK: client.begin_create(...) with resolved hosting and identity models
```

If both identities and Storage are supplied with all Validation checks passed, skip dependency writes.

| Resource | Create/Reuse Rules |
| :--- | :--- |
| Hosting/Workload UAMIs | For each identity independently, create if omitted or check/reuse if supplied. Only Hosting UAMI is attached to account identity; supplied identities remain customer-owned. |
| Storage | Create if omitted using the configuration and SKU selection below. Supplied Storage is checked/reused without rewriting. |
| Account | Preserve the existing Account/Identity model construction and final SDK submission. Required G01-G03 permissions must be validated or assigned before account hosting submission. |

#### Auto-created Storage Configuration

The SDK create request must match the Storage resource configuration in the supplied `2023-05-01` template; the template itself is not deployed. Apply these settings only when Storage is omitted, with no Storage create/update or tag changes for supplied Storage.

| Resource Field | Required Value |
| :--- | :--- |
| `name` / `location` | `plan.storageName` / Account `location` |
| `kind` / `sku.name` | `StorageV2` / `plan.storageSku` |
| `tags` | User-provided Account tags without an additional CLI-specific ownership tag. |
| `accessTier` / `isHnsEnabled` | `Hot` / `false` |
| `publicNetworkAccess` / `networkAcls.defaultAction` | `Enabled` / `Allow` |
| `minimumTlsVersion` / `supportsHttpsTrafficOnly` | `TLS1_2` / `true` |
| `allowBlobPublicAccess` / `allowSharedKeyAccess` | `false` / `false` |

#### Storage SKU Selection

During preflight, list the subscription's Microsoft.Storage SKUs. Set `plan.storageSku` to `Standard_ZRS` when StorageV2 ZRS is available without a matching location restriction; otherwise use `Standard_LRS`. This applies only to auto-created Storage. Do not change supplied Storage or switch SKU after a creation error.

#### Resource Naming (Proposed; Pending Meeting Discussion)

For CLI-created Storage, Hosting MI, and Workload MI, use the following Account-based names initially; final naming remains subject to meeting discussion.

```text
accountPart = lowercase(foundryAccountName), retaining only ASCII a-z/0-9
accountResourceId = /subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.CognitiveServices/accounts/{foundryAccountName}
resourceToken = first 10 lowercase hex characters of SHA256(UTF8(lowercase(accountResourceId)))
Storage = (first 14 characters of accountPart) + resourceToken
Hosting MI = lowercase(foundryAccountName) + "-hosting-mi"
Workload MI = lowercase(foundryAccountName) + "-workload-mi"
```

For account `team-ai-prod` and illustrative token `a1b2c3d4e5`:

| Resource | Proposed Default Name |
| :--- | :--- |
| Storage | `teamaiproda1b2c3d4e5` |
| Hosting MI | `team-ai-prod-hosting-mi` |
| Workload MI | `team-ai-prod-workload-mi` |

Storage names are at most 24 characters. No local path or azd environment is used. Supplied resources keep their names; a matching generated name alone does not establish ownership.

The deterministic naming function produces valid generated UAMI names; do not duplicate its rules with a second preflight regexp.

Validate and reuse existing generated-name resources without updates; never create the RG automatically.

#### Grant Matrix

| ID | Principal | Role | Scope | Validation / Assignment |
| :--- | :--- | :--- | :--- | :--- |
| G01 | Hosting UAMI | Reader + Kubernetes Extension Contributor | Supplied AKS | Validate if Hosting UAMI is supplied; otherwise assign. |
| G02 | Hosting UAMI | Managed Identity Federated Identity Credential Contributor | Workload UAMI | Validate if both identities are supplied; otherwise assign. |
| G03 | Workload UAMI | Storage Blob Data Contributor | Resolved Storage | Validate if Workload UAMI and Storage are supplied; otherwise assign. |

Validation branches perform no grant writes and require no operator `roleAssignments/write`. Assignment branches use actual principal object IDs, stable assignment IDs, exact scopes, and compatible grant reuse. Do not expand G01 to AKS Contributor/cluster-admin. Service-managed extension/FIC lifecycle remains with the service, not the client.

Keep deterministic `uuid.uuid5` assignment names. A 409 is successful only for `RoleAssignmentExists` followed by a readable assignment with matching principal, role and exact scope, without a conflicting condition. Otherwise re-raise the original error.

### 4.3 Errors and Partial Provisioning

* Preserve service errors and correlation IDs. Resource/grant creation completion does not prove RBAC data-plane propagation.
* Log resource/grant IDs before writes, reused resources, and dependency IDs before Account submission. On dependency failure, warn about partial completion and re-raise the original error. Return the Account SDK poller unchanged.
* No local journal, ownership ledger, recovery file, automatic rollback or deletion. Preserve supplied/reused resources, customer grants and unrelated RG contents; deterministic names do not prove ownership.
* Deterministic names and compatible grants support reuse, not full recovery. Inspect Azure state before retrying.

**TODO - Recovery design**: Define interrupted/active/concurrent attempt handling, completion and ownership reconciliation, Account poller outcomes and cleanup UX. Recovery is not implemented.

---

## 5. File Changes & Verification

| File Path | Planned Change |
| :--- | :--- |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_params.py` | Register the four `--agent-hosting-*` resource ID arguments (preview); do not expose hosting `name` or `hostingType`. Apply the required/default rules in Section 3.2. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/custom.py` | Run preflight and SDK dependency preparation before the existing Account model construction and `client.begin_create(...)`; preserve hosting and identity mappings. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_help.py` | Add a BYO AKS account creation example. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_agent_hosting.py` | Prepare dependencies/grants from immutable preflight results; log progress/errors without a local journal or ARM deployment. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_agent_hosting_preflight.py` | Implement Section 4.1; return resolved IDs, resources, check results and pending grants. Keep SDK/RBAC caches local; no Azure/filesystem writes. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_client_factory.py` | Create subscription-scoped BYO AKS SDK clients. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/tests/latest/test_agent_hosting.py` | Use focused `ScenarioTest` coverage for CLI argument binding and unit tests for validation, serialized wire payload (`agentHostingConfigurations`, `identity`), and non-BYO regression. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/tests/latest/test_agent_hosting_preparation.py` | Test Section 4.1, all eight dependency/grant combinations, reuse, permission semantics and partial failures without live Azure writes. |

### Verification Checklist

* **Pre-request Validation**: Invalid Account names, missing RG, missing cluster, empty/non-string inputs and invalid ARM IDs fail before Azure writes. Check new/changed and unavailable domains, and preservation of non-404 Account read errors.
* **Wire Serialization**: Verify the serialized body passed to `client.begin_create` contains 1 `agentHostingConfigurations` item (`name="default"`, `hostingType="ManagedCluster"`) and expected `identity` (`SystemAssigned, UserAssigned` default for `AIServices`, or `UserAssigned` when system identity is disabled, with only `hostingManagementIdentityResourceId` in `userAssignedIdentities`). The request does not contain `networkInjections`.
* **Non-BYO & Update Regression**: Non-BYO `account create` sends no `agentHostingConfigurations`. With no new arguments, the existing payload is unchanged. `account update` omits `agentHostingConfigurations`.
* **Live Account Verification**: Creating a new BYO AKS account via `az cognitiveservices account create` reaches `Succeeded` and `account show` returns the expected bindings.
* **Preflight**: Mandatory FAIL/UNVERIFIED causes zero Azure writes. Preserve pool, image, label, SSH, identity, region, Azure CNI Overlay and network-policy thresholds, including count >= 1 with autoscaling. Telemetry remains deferred; no Kubernetes operations or traffic tests.
* **Permissions**: Cover all eight dependency combinations, ARM caller permission scopes/errors and MI wildcard/DataAction semantics. Verify compatible 409 recovery and propagation of all other conflicts.
* **Storage Configuration**: Verify all auto-created Storage fields, user-tag propagation, ZRS preference with LRS fallback, and supplied Storage region validation; supplied Storage causes no Storage create/update.
* **Provisioning**: Verify SDK resource/grant completion and actual IDs before Account submission, no deployment submission, and no dependency writes when all supplied resources pass Validation and the RG exists. Project creation stays separate and performs no ACR operations.
* **Partial Failure**: Verify stable reuse, resource-ID logs, original errors and no automatic deletion. Recovery remains TODO.
* **Checks**: `azdev style cognitiveservices`, `azdev linter cognitiveservices`, and `azdev test test_agent_hosting test_agent_hosting_preparation --discover`.
