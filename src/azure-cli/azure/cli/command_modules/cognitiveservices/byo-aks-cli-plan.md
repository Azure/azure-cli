# Cognitive Services BYO AKS CLI Plan

## 1. Background and Goal

Based on [Azure/azure-rest-api-specs#45245](https://github.com/Azure/azure-rest-api-specs/pull/45245) and the [Vienna BYO AKS setup](https://msdata.visualstudio.com/Vienna/_git/vienna/pullrequest/2285162), add BYO AKS (customer-owned AKS agent hosting) support to `az cognitiveservices account create`.

* **Reference**: [BYO-AKS Simplified Onboarding - Technical Design Spec.docx](https://onedrive.cloud.microsoft/:w:/a@qm93vz2m/S/cQqIkrxyppadT4x5zoMK2dAJEgUCgeqpDY_qXO3pZHHQNlYVFQ?isSPOFile=1&ovuser=72f988bf-86f1-41af-91ab-2d7cd011db47%2Czhujiayi%40microsoft.com&wdExp=TEAMS-TREATMENT&web=1&clickparams=eyJBcHBOYW1lIjoiVGVhbXMtRGVza3RvcCIsIkFwcFZlcnNpb24iOiI0OS8yNjEwMDIxMjAxMSJ9).
* **Scope**: Add BYO AKS preflight and SDK provisioning to `az cognitiveservices account create`, including identities, Storage, and required grants. Other commands are unchanged.
* **Prerequisite**: `azure-mgmt-cognitiveservices>=15.0.0b5` (which introduced `AgentHostingConfiguration`, `ManagedClusterAgentHostingConfiguration`, and `AgentHostingType`). In `azure-cli`, [Azure/azure-cli#34112](https://github.com/Azure/azure-cli/pull/34112) upgrades the dependency directly from `15.0.0b4` to `15.0.0b6`.

---

## 2. API Specification

The service API represents agent hosting configuration, network injection, and account identity as separate properties. The selected CLI design accepts flattened arguments for one hosting configuration and wraps it in a one-item array for the API, with the optional subnet supplied through `--agent-subnet`.

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

### 2.2 Network Injection

Network injection is configured on `AccountProperties.network_injections`:

* `scenario`: `"agent"` (`ScenarioType.AGENT`)
* `subnet_arm_id`: Subnet ARM resource ID (`Microsoft.Network/virtualNetworks/subnets`)
* `use_microsoft_managed_network`: `False`

The optional `--agent-subnet` maps to REST `networkInjections[0].subnetArmId` / SDK `network_injections[0].subnet_arm_id`. When omitted, the CLI does not send `networkInjections`.

---

## 3. CLI Argument Options

Target command: `az cognitiveservices account create` (hosting arguments are marked `is_preview=True`; `--agent-subnet` is not).

### 3.1 Option A: JSON Array (Not Selected)

Alternative preserving the `AgentHostingConfiguration[]` shape through an inline JSON array or `@<file>`. Not selected because the current scope is one configuration with simple fields: flattened arguments avoid JSON quoting and expose per-field help and validation. Any future array-input support will be handled separately.

| CLI Option | Python Argument | Mapped SDK Target | Requirement | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--agent-hosting` | `agent_hosting` | `properties.agent_hosting_configurations` & `identity.user_assigned_identities` | Required when BYO AKS is used | JSON array (or `@<file>`) containing one object: required `clusterResourceId` and optional Storage/identity IDs. CLI supplies `name` and `hostingType` internally. |
| `--agent-subnet` | `subnet` | `properties.network_injections[0].subnet_arm_id` | Optional | Subnet ARM resource ID. |

#### Example (Option A)

```bash
az cognitiveservices account create \
    -n foundryByocAccount \
    -g myResourceGroup \
    --kind AIServices \
    --sku S0 \
    -l westus \
    --custom-domain foundrybyocaccount \
    --yes \
    --agent-subnet "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/subnet1" \
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
| `--agent-subnet` | `subnet` | `network_injections[0].subnet_arm_id` | Optional |

#### Example (Option B, Full Arguments)

```bash
az cognitiveservices account create \
    -n foundryByocAccount \
    -g myResourceGroup \
    --kind AIServices \
    --sku S0 \
    -l westus \
    --custom-domain foundrybyocaccount \
    --yes \
    --agent-hosting-cluster "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ContainerService/managedClusters/cluster1" \
    --agent-hosting-storage "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/storage1" \
    --agent-hosting-management-identity "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/account-control-plane" \
    --agent-hosting-workload-identity "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/aks-workload" \
    --agent-subnet "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/subnet1"
```

#### Example (Option B, Minimal BYO AKS Arguments)

Only the cluster ID is supplied for BYO AKS; Storage and both identities are created automatically. No network injection is configured without `--agent-subnet`.

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
   * Register the four `--agent-hosting-*` resource ID arguments in `_params.py`, defaulting to `None`. Expose the network argument as `--agent-subnet` (Python argument `subnet`).
   * If all hosting arguments and `--agent-subnet` are `None` (not provided): preserve existing behavior (do not send empty `agentHostingConfigurations` or `networkInjections` arrays).
   * When `--agent-hosting-cluster` is supplied, `account create` runs preflight, creates/reuses dependencies and configures prerequisite grants, then creates the account. No additional switch is required.
   * Require the cluster ID for BYO AKS and resolve optional fields before constructing the request. Resolve each identity independently: create if omitted, otherwise reuse. Reject empty/non-string values and validate supplied ARM IDs with `is_valid_resource_id()`.
   * Build one `ManagedClusterAgentHostingConfiguration` with internal values `name="default"` and `hostingType="ManagedCluster"`, and wrap it in a one-item list for the API.
   * Handle `--agent-subnet` separately from the hosting model builder: validate a non-empty string and `is_valid_resource_id()`, then construct `NetworkInjection` as in Section 2.2. Hosting and subnet inputs are independent; omit each property when its corresponding inputs are not provided.
2. **Account Identity Construction (`custom.py`)**:
   * Keep existing `has_system_identity = bool(assign_identity or allow_project_management)` logic in `create()`.
   * Add the resolved hosting-management identity to `user_assigned_identities` (do not attach the workload identity to the account identity).
   * Construct `Identity` directly in `create()` (without modifying shared `compose_identity()`):
     * `SystemAssigned, UserAssigned` when both `has_system_identity` and `user_assigned_identities` are present (default for `AIServices`).
     * `UserAssigned` when `not has_system_identity` and `user_assigned_identities` is present.
     * `SystemAssigned` when `has_system_identity` is present without BYO AKS (unchanged existing behavior).
3. **Validation Boundary & Isolation**:
   * **CLI**: Checks hosting inputs, non-empty strings, and `is_valid_resource_id()` syntax. When `--agent-hosting-cluster` is supplied, perform the read-only preflight checks below before Azure writes.
   * **Zero Impact on Existing Commands**: All new arguments are scoped to `cognitiveservices account create`, with `--agent-hosting-*` under `Agent Hosting` and `--agent-subnet` under `Network`. Shared helpers in `_utils.py` are not modified, and all new `create()` parameters default to `None`.
   * **REST Service (Vienna RP)**: Validates resource types, `name` constraints, distinct management vs. workload UAIs, subscription/region alignment, AKS OIDC/Workload Identity state, and RBAC permissions.

### 4.1 Preflight Checks

Resolve the create/reuse plan and perform read-only checks before any Azure writes. Report check ID, resource/scope, observed/expected state, missing evidence, and remediation with `PASS`, `FAIL`, `UNVERIFIED`, or `NOT_APPLICABLE`. Mandatory `FAIL`/`UNVERIFIED` stops provisioning. Check planned resources through their properties and existing parent-scope permissions, not GETs on future resources.

Check IDs follow the Word reference: I = input resolution, A = AKS, S = Storage, N = network, and P = operator permissions. Only Account-related checks are retained.

| Check | Required Logic |
| :--- | :--- |
| I01-I03: inputs/context | Validate full resource IDs, types, existence/readiness, and create/reuse decisions; distinguish malformed, absent, and unreadable resources. Cross-subscription references must belong to the same tenant. |
| A01-A04: AKS baseline | Supported Standard offering, Kubernetes >= 1.31; reject Automatic/Arc. Accept Azure CNI Overlay or Pod Subnet, not kubenet/Node Subnet. Require managed identity, readable OIDC issuer, and Workload Identity. |
| A05: system pool | A System pool with >= 4 vCPU / 16 GiB; recommended VM SKU names are not hard requirements. |
| A06-A10: agent pool | One User pool must simultaneously satisfy Azure Linux, `KataVmIsolation`, >= 1 node, >= 8 vCPU / 32 GiB, image baseline `AKSAzureLinux-V3katagen2-202608.14.0`, label `agents.ai.azure.com/sandbox-node=true`, disabled SSH, and `Succeeded` state. Read AgentPool child resources and cluster readiness; never combine different pools' partial results. |
| A11: policy | Verify a supported, enforced network-policy/engine configuration. Azure Policy add-on or Azure CNI alone is insufficient evidence. |
| S01-S02: supplied Storage | Require StorageV2, Hot, HNS disabled, HTTPS only, TLS >= 1.2, shared keys disabled, anonymous Blob disabled, and a valid HTTPS Blob endpoint. Zone redundancy is a recommendation, not a blocker; unknown redundancy evidence emits a warning. |
| S03: Storage network | Public baseline requires `publicNetworkAccess=Enabled` and firewall `defaultAction=Allow`. Private/restricted Storage is `NOT_APPLICABLE` for this public-only check, with an explicit unverified-network warning; provisioning may continue. API/read/endpoint failures still block. Planned Storage uses SDK request properties, not a pre-creation GET. |
| N01: telemetry egress | Deferred; no telemetry-egress check runs during preflight or provisioning. |
| N02: supplied Agent subnet | During BYO-AKS preflight, if `--agent-subnet` selects an existing subnet, read subnet/VNet and the selected agent pool's Node subnet. Check canonical private IPv4 CIDRs, at least /27 capacity, VNet containment, non-overlap with the selected Node subnet, and `Microsoft.App/environments` delegation. No selected existing subnet means `NOT_APPLICABLE`. PASS does not prove routing, DNS, or connectivity. |
| P02-P04/P06: permissions | Check required reads, identity assign/action, and creation permissions for planned RG/UAMI/Storage writes. Require `roleAssignments/write` at the actual resource or existing parent scope only for Assignment branches below. Keep P03 as specified in the reference: require `Microsoft.ContainerService/managedClusters/write` and `Microsoft.Network/virtualNetworks/write` at the relevant parent RGs, although the supplied AKS is not modified. |

Evaluate operator Actions/NotActions using operator/token-group assignments and role definitions. For MI Permission Validation, check actual principal IDs, inherited assignments, and Actions/NotActions plus DataActions/NotDataActions; G03 Blob access cannot be inferred from management-plane permissions. Exclusions apply within their role, not as global denies. Missing or unverifiable access in a Validation branch stops provisioning, without repairing the grant. Grant writes require an unconditional allow. Do not claim full evaluation of deny assignments, conditions, or tenant policy, and do not modify tenant-wide Graph permissions/policy.

### 4.2 Provision

Unlike the reference's single ARM deployment, az uses sequential SDK calls. After preflight passes, prepare dependencies and only the grants marked Assignment below; wait for these operations to complete and resolve real resource/principal IDs before constructing the Account request. Finally, reuse `custom.py` model construction and call `client.begin_create(resource_group_name, account_name, params)`. No ARM template or deployment submission is used.

**Reminder**: Create a Foundry project separately using the existing `az cognitiveservices account project create` command for subsequent hosted-agent use. Configure a Project connection only if required by that workflow; no Project/ACR/connection automation is added here.

```text
Read-only preflight: validate supplied access and operator authority
    -> SDK: create RG if needed and omitted UAMIs/Storage; reference supplied resources
    -> SDK: ensure Assignment grants G01-G03; wait for completion
    -> SDK: client.begin_create(...) with resolved hosting/network/identity models
```

If the RG exists and both identities and Storage are supplied with all Validation checks passed, skip dependency writes.

| Resource | Create/Reuse Rules |
| :--- | :--- |
| Hosting/Workload UAMIs | For each identity independently, create if omitted or check/reuse if supplied. Only Hosting UAMI is attached to account identity; supplied identities remain customer-owned. |
| Storage | Create if omitted: StorageV2/Hot, HNS off, HTTPS only, TLS 1.2+, shared keys and anonymous Blob off. Default `Standard_ZRS`; use `Standard_LRS` only for the maintained unsupported-region list, not as a runtime-error fallback. Supplied Storage is checked/reused without rewriting. |
| Account | Preserve the existing Account/Identity model construction and final SDK submission. Required G01-G03 permissions must be validated or assigned before account hosting submission. |

#### Resource Naming (Proposed; Pending Meeting Discussion)

For CLI-created Storage and Workload MI, use Foundry account-based names. This proposal is not finalized and requires meeting discussion. Hosting MI naming remains to be confirmed.

```text
accountPart = lowercase(foundryAccountName), retaining only ASCII a-z/0-9
accountResourceId = /subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.CognitiveServices/accounts/{foundryAccountName}
resourceToken = first 10 lowercase hex characters of SHA256(UTF8(lowercase(accountResourceId)))
Storage = (first 14 characters of accountPart) + resourceToken
Workload MI = lowercase(foundryAccountName) + "-workload-mi"
```

For account `team-ai-prod` and illustrative token `a1b2c3d4e5`:

| Resource | Default Name |
| :--- | :--- |
| Storage | `teamaiproda1b2c3d4e5` |
| Workload MI | `team-ai-prod-workload-mi` |

Storage names are at most 24 characters. No local path or azd environment is used. Supplied resources keep their names; a matching generated name alone does not establish ownership.

#### Grant Matrix

| ID | Principal | Role | Scope | Validation / Assignment |
| :--- | :--- | :--- | :--- | :--- |
| G01 | Hosting UAMI | Reader + Kubernetes Extension Contributor | Supplied AKS | Validate if Hosting UAMI is supplied; otherwise assign. |
| G02 | Hosting UAMI | Managed Identity Federated Identity Credential Contributor | Workload UAMI | Validate if both identities are supplied; otherwise assign. |
| G03 | Workload UAMI | Storage Blob Data Contributor | Resolved Storage | Validate if Workload UAMI and Storage are supplied; otherwise assign. |

Validation branches perform no grant writes and require no operator `roleAssignments/write`. Assignment branches use actual principal object IDs, stable assignment IDs, exact scopes, and compatible grant reuse. Do not expand G01 to AKS Contributor/cluster-admin. Service-managed extension/FIC lifecycle remains with the service, not the client.

### 4.3 Errors, Retry, and Cleanup

* Preserve service errors and correlation IDs. Resource/grant creation completion does not prove RBAC data-plane propagation.
* Retain exact owned resource/grant IDs, attempt records, and SDK operation results after preparation or Account failure for retry/cleanup; retry uses deterministic resource identities.
* Clean up only recorded tool-created resources/grants. Supplied AKS, Storage, identities, and customer grants remain unowned; do not delete them indirectly by deleting their RG.

---

## 5. File Changes & Verification

| File Path | Planned Change |
| :--- | :--- |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_params.py` | Register the four `--agent-hosting-*` resource ID arguments (preview) and `--agent-subnet`; do not expose hosting `name` or `hostingType`. Apply the required/default rules in Section 3.2. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/custom.py` | Run preflight and SDK dependency preparation before the existing Account model construction and `client.begin_create(...)`; preserve hosting, network injection, and identity mappings. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_help.py` | Add a BYO AKS account creation example. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/` preflight/provisioning helpers and client factories | Implement SDK checks, resource/grant preparation, and ownership records in Sections 4.1-4.3; no ARM template. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/tests/latest/test_agent_hosting.py` | Add `ScenarioTest` (`self.cmd(...)` for CI `missing_parameter_test_coverage`) and unit tests for argument validation, serialized wire payload (`agentHostingConfigurations`, `networkInjections`, `identity`), all four hosting/subnet combinations, and non-BYO regression. |

### Verification Checklist

* **Pre-request Validation**: Missing cluster input, empty/non-string supplied values, and invalid ARM resource IDs fail before Azure writes.
* **Wire Serialization**: Verify the serialized body passed to `client.begin_create` contains 1 `agentHostingConfigurations` item (`name="default"`, `hostingType="ManagedCluster"`), expected `identity` (`SystemAssigned, UserAssigned` default for `AIServices`, or `UserAssigned` when system identity is disabled, with only `hostingManagementIdentityResourceId` in `userAssignedIdentities`), and either 1 `networkInjections` item (`scenario="agent"`, `subnetArmId`, `useMicrosoftManagedNetwork=False`) when `--agent-subnet` is provided or no `networkInjections` field when it is omitted.
* **Non-BYO & Update Regression**: Non-BYO `account create` sends no `agentHostingConfigurations`; `--agent-subnet` alone adds network injection without changing identity or triggering BYO-AKS preflight. With no new arguments, the existing payload is unchanged. `account update` omits `agentHostingConfigurations`.
* **Live Account Verification**: Creating a new BYO AKS account via `az cognitiveservices account create` reaches `Succeeded` and `account show` returns the expected bindings.
* **Preflight**: Mandatory FAIL/UNVERIFIED causes zero Azure writes; cover the resource/permission checks, same-pool qualification, Storage warnings, N01 deferral, and N02 scope.
* **Permissions**: Cover all eight supplied/created combinations of Hosting UAMI, Workload UAMI, and Storage; Validation branches never assign grants, and G03 checks DataActions/NotDataActions.
* **Provisioning**: Verify SDK resource/grant completion and actual IDs before Account submission, no deployment submission, and no dependency writes when all supplied resources pass Validation and the RG exists. Project creation stays separate and performs no ACR operations.
* **Retry/Cleanup**: Verify stable resource reuse, retained attempt/output records, preserved service errors, and no deletion of supplied resources/customer grants.
* **Checks**: `azdev style cognitiveservices`, `azdev linter cognitiveservices`, and `azdev test test_agent_hosting`.
