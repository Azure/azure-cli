# Cognitive Services BYO AKS CLI Plan

## 1. Background and Goal

Based on [Azure/azure-rest-api-specs#45245](https://github.com/Azure/azure-rest-api-specs/pull/45245) and the [Vienna BYO AKS setup](https://msdata.visualstudio.com/Vienna/_git/vienna/pullrequest/2285162), add BYO AKS (customer-owned AKS agent hosting) support to `az cognitiveservices account create`.

* **Scope**: Support BYO AKS account binding in `az cognitiveservices account create`:
  1. `properties.agent_hosting_configurations` (`ManagedClusterAgentHostingConfiguration`)
  2. `properties.network_injections` (`NetworkInjection` for the agent subnet)
  3. Account-level managed identity (`identity.user_assigned_identities` including the hosting-management UAI)
  4. CLI arguments, validation, help, and tests.
* **Prerequisite**: `azure-mgmt-cognitiveservices>=15.0.0b5` (which introduced `AgentHostingConfiguration`, `ManagedClusterAgentHostingConfiguration`, and `AgentHostingType`). In `azure-cli`, [Azure/azure-cli#34112](https://github.com/Azure/azure-cli/pull/34112) upgrades the dependency directly from `15.0.0b4` to `15.0.0b6`.

---

## 2. API Specification

### 2.1 Agent Hosting Configuration

`AccountProperties.agentHostingConfigurations` has `Lifecycle.Read` and `Lifecycle.Create` visibility (immutable after creation, `@minItems(1)`, `@maxItems(1)`):

| Property | Type | Required | Description & Allowed ARM Resource Type |
| :--- | :--- | :--- | :--- |
| `name` | `string` | Yes | Unique configuration name within the account (1–64 chars). |
| `hostingType` | `string` | Yes | Fixed discriminator value `"ManagedCluster"`. |
| `hostingManagementIdentityResourceId` | `arm-id` | Yes | Control-plane user-assigned managed identity (`Microsoft.ManagedIdentity/userAssignedIdentities`). Must also be assigned in `account.identity.userAssignedIdentities`. |
| `workloadIdentityResourceId` | `arm-id` | Yes | Workload user-assigned managed identity federated to AKS service accounts (`Microsoft.ManagedIdentity/userAssignedIdentities`). |
| `clusterResourceId` | `arm-id` | Yes | Customer-owned AKS managed cluster (`Microsoft.ContainerService/managedClusters`). |
| `storageAccountResourceId` | `arm-id` | Yes | Customer-owned storage account (`Microsoft.Storage/storageAccounts`). |

### 2.2 Network Injection

BYO AKS requires an agent subnet configured on `AccountProperties.network_injections`:

* `scenario`: `"agent"` (`ScenarioType.AGENT`)
* `subnet_arm_id`: Agent subnet ARM resource ID (`Microsoft.Network/virtualNetworks/subnets`)
* `use_microsoft_managed_network`: `False`

---

## 3. CLI Argument Options

Target command: `az cognitiveservices account create` (new arguments marked `is_preview=True`).

### 3.1 Option A: Flattened Arguments (Selected)

Follows [Azure CLI Command Guidelines](https://github.com/Azure/azure-cli/blob/dev/doc/command_guidelines.md#commands-with-complex-types) by exposing flattened parameters under `arg_group="Agent Hosting"`. `--agent-hosting-management-identity` populates both `hostingManagementIdentityResourceId` and `account.identity.userAssignedIdentities`.

| CLI Option | Python Argument | Mapped SDK Target | Requirement |
| :--- | :--- | :--- | :--- |
| `--agent-hosting-name` | `agent_hosting_name` | `agent_hosting_configurations[0].name` | Required when BYO AKS is used |
| `--agent-hosting-cluster` | `agent_hosting_cluster` | `agent_hosting_configurations[0].cluster_resource_id` | Required when BYO AKS is used |
| `--agent-hosting-storage` | `agent_hosting_storage` | `agent_hosting_configurations[0].storage_account_resource_id` | Required when BYO AKS is used |
| `--agent-hosting-management-identity` | `agent_hosting_management_identity` | `agent_hosting_configurations[0].hosting_management_identity_resource_id` & `identity.user_assigned_identities` | Required when BYO AKS is used (automatically attached to account identity) |
| `--agent-hosting-workload-identity` | `agent_hosting_workload_identity` | `agent_hosting_configurations[0].workload_identity_resource_id` | Required when BYO AKS is used (not attached to account identity) |
| `--agent-hosting-subnet` | `agent_hosting_subnet` | `network_injections[0].subnet_arm_id` | Required when BYO AKS is used |

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
    --agent-hosting-name default \
    --agent-hosting-cluster "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ContainerService/managedClusters/cluster1" \
    --agent-hosting-storage "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/storage1" \
    --agent-hosting-management-identity "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/account-control-plane" \
    --agent-hosting-workload-identity "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/aks-workload" \
    --agent-hosting-subnet "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/agent-subnet"
```

---

### 3.2 Option B: JSON Input

Alternative design following legacy `--storage` / `--encryption` on `account create` and mirroring the `AgentHostingConfiguration[]` array structure (using the `camelCase` schema defined in Section 2.1), paired with `--agent-hosting-subnet` for `networkInjections`:

| CLI Option | Python Argument | Mapped SDK Target | Requirement | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--agent-hosting-configurations` | `agent_hosting_configurations` | `properties.agent_hosting_configurations` | Required when BYO AKS is used | JSON array string (or `@<file>`) of `ManagedClusterAgentHostingConfiguration` objects (`name`, `hostingType`, `hostingManagementIdentityResourceId`, `workloadIdentityResourceId`, `clusterResourceId`, `storageAccountResourceId`). |
| `--agent-hosting-subnet` | `agent_hosting_subnet` | `properties.network_injections[0].subnet_arm_id` | Required when BYO AKS is used | ARM resource ID of the agent injection subnet (`scenario="agent"`, `use_microsoft_managed_network=False`). |

#### Example (Option B)

```bash
az cognitiveservices account create \
    -n foundryByocAccount \
    -g myResourceGroup \
    --kind AIServices \
    --sku S0 \
    -l westus \
    --custom-domain foundrybyocaccount \
    --yes \
    --agent-hosting-subnet "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/agent-subnet" \
    --agent-hosting-configurations '[
      {
        "name": "default",
        "hostingType": "ManagedCluster",
        "hostingManagementIdentityResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/account-control-plane",
        "workloadIdentityResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/aks-workload",
        "clusterResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ContainerService/managedClusters/cluster1",
        "storageAccountResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/storage1"
      }
    ]'
```

---

### 3.3 Option Comparison

| Dimension | Option A (Flattened Flags — Selected) | Option B (JSON Array + Subnet Flag) |
| :--- | :--- | :--- |
| **CLI Guideline Fit** | Aligns with `doc/command_guidelines.md` (flattened arguments under `arg_group`). | Legacy JSON blob pattern (discouraged by CLI guidelines). |
| **Usability** | No shell JSON escaping; clear per-parameter help and validation. | Requires escaping JSON on CLI; still needs a separate flag for `networkInjections`. |
| **Multi-item Array** | Bound to single item (`@maxItems(1)` in current API). | Native array representation if future API versions allow multiple items. |

---

## 4. Implementation Notes

1. **Trigger & Argument Validation (Option A)**:
   * If all 6 `--agent-hosting-*` arguments are `None`: preserve existing behavior (do not send empty `agentHostingConfigurations` or `networkInjections` arrays).
   * If any `--agent-hosting-*` argument is not `None`: require all 6 `--agent-hosting-*` flags (`name`, `cluster`, `storage`, `management-identity`, `workload-identity`, `subnet`), reject empty/whitespace strings, and validate each of the 5 resource IDs with `is_valid_resource_id()`.
2. **Account Identity Construction (`custom.py`)**:
   * Keep existing `has_system_identity = bool(assign_identity or allow_project_management)` logic in `create()`.
   * When `--agent-hosting-management-identity` is provided, set `user_assigned_identities = {agent_hosting_management_identity: UserAssignedIdentity()}` (do not attach `--agent-hosting-workload-identity` to the account identity).
   * Construct `Identity` directly in `create()` (without modifying shared `compose_identity()`):
     * `SystemAssigned, UserAssigned` when both `has_system_identity` and `--agent-hosting-management-identity` are present (default for `AIServices`).
     * `UserAssigned` when `not has_system_identity` and `--agent-hosting-management-identity` is present.
     * `SystemAssigned` when `has_system_identity` is present without BYO AKS (unchanged existing behavior).
3. **Validation Boundary & Isolation**:
   * **CLI**: Checks parameter completeness, non-empty strings, and `is_valid_resource_id()` syntax, then constructs SDK models. No extra preflight `GET` calls are made to AKS, Storage, UAI, or RBAC.
   * **Zero Impact on Existing Commands**: All new arguments are scoped strictly to `argument_context('cognitiveservices account create', arg_group='Agent Hosting')`, shared helpers in `_utils.py` and `_params.py` are not modified, and all new `create()` parameters default to `None`.
   * **REST Service (Vienna RP)**: Validates resource types, `name` constraints, distinct management vs. workload UAIs, subscription/region alignment, AKS OIDC/Workload Identity state, and RBAC permissions.

---

## 5. File Changes & Verification

| File Path | Planned Change |
| :--- | :--- |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_params.py` | Register the 6 preview `--agent-hosting-*` arguments and validator under `cognitiveservices account create`. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/custom.py` | Set `properties.agent_hosting_configurations`, `properties.network_injections`, and `params.identity` in `create()`. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_help.py` | Add parameter help (clarifying management vs. workload UAI, agent injection subnet vs. AKS node subnet, and pre-provisioned resource/RBAC prerequisites) and BYO AKS example. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/tests/latest/test_byox.py` | Add tests for argument validation, serialized wire payload (`agentHostingConfigurations`, `networkInjections`, `identity`), and non-BYO regression. |

### Verification Checklist

* **Pre-request Validation**: Partial `--agent-hosting-*` flags, empty/whitespace values, and invalid ARM resource IDs fail before any SDK call.
* **Wire Serialization**: Verify the serialized body passed to `client.begin_create` contains 1 `agentHostingConfigurations` item (`hostingType="ManagedCluster"`), 1 `networkInjections` item (`scenario="agent"`, `subnetArmId`, `useMicrosoftManagedNetwork=False`), and expected `identity` (`SystemAssigned, UserAssigned` default for `AIServices`, or `UserAssigned` when system identity is disabled, with only `--agent-hosting-management-identity` in `userAssignedIdentities`).
* **Non-BYO & Update Regression**: Non-BYO `account create` sends no `agentHostingConfigurations` / `networkInjections`; `account update` omits `agentHostingConfigurations`.
* **Live ARM Verification**: Creating a new BYO AKS account via `az cognitiveservices account create` reaches `Succeeded` and `account show` returns the expected bindings.
* **Checks**: `azdev style cognitiveservices`, `azdev linter cognitiveservices`, and `azdev test test_byox`.
