# Cognitive Services BYO AKS CLI Plan

## 1. Background and Goal

Based on [Azure/azure-rest-api-specs#45245](https://github.com/Azure/azure-rest-api-specs/pull/45245) and the [Vienna BYO AKS setup](https://msdata.visualstudio.com/Vienna/_git/vienna/pullrequest/2285162), add BYO AKS (customer-owned AKS agent hosting) support to `az cognitiveservices account create`.

* **Scope**: Support BYO AKS account binding in `az cognitiveservices account create`:
  1. `properties.agent_hosting_configurations` (`ManagedClusterAgentHostingConfiguration`)
  2. Optional `properties.network_injections` (`NetworkInjection` when a subnet is provided)
  3. Account-level managed identity (`identity.user_assigned_identities` including the hosting-management UAI)
  4. The `--agent-hosting` array and `--subnet` argument, validation, help, and tests.
* **Prerequisite**: `azure-mgmt-cognitiveservices>=15.0.0b5` (which introduced `AgentHostingConfiguration`, `ManagedClusterAgentHostingConfiguration`, and `AgentHostingType`). In `azure-cli`, [Azure/azure-cli#34112](https://github.com/Azure/azure-cli/pull/34112) upgrades the dependency directly from `15.0.0b4` to `15.0.0b6`.

---

## 2. API Specification

The service API represents agent hosting configuration, network injection, and account identity as separate properties. The selected CLI design accepts `--agent-hosting` as an array containing one configuration object, with the optional subnet supplied through `--subnet`.

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

Network injection is configured on `AccountProperties.network_injections`:

* `scenario`: `"agent"` (`ScenarioType.AGENT`)
* `subnet_arm_id`: Subnet ARM resource ID (`Microsoft.Network/virtualNetworks/subnets`)
* `use_microsoft_managed_network`: `False`

The optional `--subnet` maps to REST `networkInjections[0].subnetArmId` / SDK `network_injections[0].subnet_arm_id`. When omitted, the CLI does not send `networkInjections`.

---

## 3. CLI Argument Options

Target command: `az cognitiveservices account create` (`--agent-hosting` is marked `is_preview=True`; `--subnet` is not).

### 3.1 Option A: JSON Array (Selected)

Selected to preserve the `AgentHostingConfiguration[]` shape: the CLI accepts an array containing exactly one Agent Hosting object. The object is expanded into `agentHostingConfigurations[0]` and the account identity. Accepts an inline JSON array or `@<file>` parsed via `shell_safe_json_parse`:

| CLI Option | Python Argument | Mapped SDK Target | Requirement | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--agent-hosting` | `agent_hosting` | `properties.agent_hosting_configurations` & `identity.user_assigned_identities` | Required when BYO AKS is used | JSON array (or `@<file>`) containing exactly one object with `name`, `hostingType`, `clusterResourceId`, `hostingManagementIdentityResourceId`, `storageAccountResourceId`, and `workloadIdentityResourceId`. |
| `--subnet` | `subnet` | `properties.network_injections[0].subnet_arm_id` | Optional | Subnet ARM resource ID. |

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
    --subnet "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/subnet1" \
    --agent-hosting '[
      {
        "name": "default",
        "hostingType": "ManagedCluster",
        "clusterResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ContainerService/managedClusters/cluster1",
        "hostingManagementIdentityResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/account-control-plane",
        "storageAccountResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/storage1",
        "workloadIdentityResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/aks-workload"
      }
    ]'
```

---

### 3.2 Option B: Flattened Arguments

Alternative design exposing flattened parameters under `arg_group="Agent Hosting"`. Not selected because it spreads one provisioning aggregate across multiple flags and makes the complete configuration harder to pass through files or other tooling.

| CLI Option | Python Argument | Mapped SDK Target | Requirement |
| :--- | :--- | :--- | :--- |
| `--agent-hosting-name` | `agent_hosting_name` | `agent_hosting_configurations[0].name` | Required when BYO AKS is used |
| `--agent-hosting-cluster` | `agent_hosting_cluster` | `agent_hosting_configurations[0].cluster_resource_id` | Required when BYO AKS is used |
| `--agent-hosting-storage` | `agent_hosting_storage` | `agent_hosting_configurations[0].storage_account_resource_id` | Required when BYO AKS is used |
| `--agent-hosting-management-identity` | `agent_hosting_management_identity` | `agent_hosting_configurations[0].hosting_management_identity_resource_id` & `identity.user_assigned_identities` | Required when BYO AKS is used (automatically attached to account identity) |
| `--agent-hosting-workload-identity` | `agent_hosting_workload_identity` | `agent_hosting_configurations[0].workload_identity_resource_id` | Required when BYO AKS is used (not attached to account identity) |
| `--subnet` | `subnet` | `network_injections[0].subnet_arm_id` | Optional |

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
    --agent-hosting-name default \
    --agent-hosting-cluster "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ContainerService/managedClusters/cluster1" \
    --agent-hosting-storage "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/storage1" \
    --agent-hosting-management-identity "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/account-control-plane" \
    --agent-hosting-workload-identity "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/aks-workload" \
    --subnet "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/subnet1"
```

---

## 4. Implementation Notes

1. **Trigger & Argument Validation**:
   * Parse `--agent-hosting` in `_params.py` with `type=shell_safe_json_parse`, following the current repository pattern for JSON arguments. `custom.py:create()` receives the parsed value and validates its schema.
   * If both `--agent-hosting` and `--subnet` are `None` (not provided): preserve existing behavior (do not send empty `agentHostingConfigurations` or `networkInjections` arrays).
   * Require the parsed value to be a `list` of length `1` (`minItems=1`, `maxItems=1`; reject non-list, `[]`, and `len > 1`). Require the item to be a `dict` with the 6 required `camelCase` keys (`name`, `hostingType == "ManagedCluster"`, `clusterResourceId`, `hostingManagementIdentityResourceId`, `storageAccountResourceId`, and `workloadIdentityResourceId`). Reject unknown keys and empty/non-string values. Validate the 4 required ARM IDs with `is_valid_resource_id()`.
   * Map the object to `ManagedClusterAgentHostingConfiguration` and `hostingManagementIdentityResourceId` to the account identity.
   * Handle `--subnet` separately from the hosting model builder: validate a non-empty string and `is_valid_resource_id()`, then construct `NetworkInjection` as in Section 2.2. Neither argument requires the other; omit the corresponding property when its argument is not provided.
2. **Account Identity Construction (`custom.py`)**:
   * Keep existing `has_system_identity = bool(assign_identity or allow_project_management)` logic in `create()`.
   * Collect `hostingManagementIdentityResourceId` from the validated aggregate into `user_assigned_identities` (do not attach `workloadIdentityResourceId` to the account identity).
   * Construct `Identity` directly in `create()` (without modifying shared `compose_identity()`):
     * `SystemAssigned, UserAssigned` when both `has_system_identity` and `user_assigned_identities` are present (default for `AIServices`).
     * `UserAssigned` when `not has_system_identity` and `user_assigned_identities` is present.
     * `SystemAssigned` when `has_system_identity` is present without BYO AKS (unchanged existing behavior).
3. **Validation Boundary & Isolation**:
   * **CLI**: Checks the aggregate JSON schema, non-empty strings, and `is_valid_resource_id()` syntax, then constructs SDK models. No extra preflight `GET` calls are made to AKS, Storage, subnet, UAI, or RBAC.
   * **Zero Impact on Existing Commands**: Both arguments are scoped to `cognitiveservices account create`, with `--agent-hosting` under `Agent Hosting` and `--subnet` under `Network`. Shared helpers in `_utils.py` are not modified, and both new `create()` parameters default to `None`.
   * **REST Service (Vienna RP)**: Validates resource types, `name` constraints, distinct management vs. workload UAIs, subscription/region alignment, AKS OIDC/Workload Identity state, and RBAC permissions.

---

## 5. File Changes & Verification

| File Path | Planned Change |
| :--- | :--- |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_params.py` | Register `--agent-hosting` (preview) and `--subnet` arguments and their parameter help under `cognitiveservices account create`. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/custom.py` | Map `--agent-hosting` to `properties.agent_hosting_configurations` and `params.identity`; independently validate and map `--subnet` to `properties.network_injections` in `create()`. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_help.py` | Add a BYO AKS account creation example. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/tests/latest/test_agent_hosting.py` | Add `ScenarioTest` (`self.cmd(...)` for CI `missing_parameter_test_coverage`) and unit tests for argument validation, serialized wire payload (`agentHostingConfigurations`, `networkInjections`, `identity`), all four hosting/subnet combinations, and non-BYO regression. |

### Verification Checklist

* **Pre-request Validation**: Non-list input, empty list `[]`, multi-item list (`len > 1`), non-object item, unknown/missing keys, empty/non-string values, unsupported `hostingType`, and invalid ARM resource IDs fail before any SDK call.
* **Wire Serialization**: Verify the serialized body passed to `client.begin_create` contains 1 `agentHostingConfigurations` item (`hostingType="ManagedCluster"`), expected `identity` (`SystemAssigned, UserAssigned` default for `AIServices`, or `UserAssigned` when system identity is disabled, with only `hostingManagementIdentityResourceId` in `userAssignedIdentities`), and either 1 `networkInjections` item (`scenario="agent"`, `subnetArmId`, `useMicrosoftManagedNetwork=False`) when `--subnet` is provided or no `networkInjections` field when it is omitted.
* **Non-BYO & Update Regression**: Non-BYO `account create` sends no `agentHostingConfigurations`; `--subnet` alone adds network injection without changing identity. With neither argument, the existing payload is unchanged. `account update` omits `agentHostingConfigurations`.
* **Live ARM Verification**: Creating a new BYO AKS account via `az cognitiveservices account create` reaches `Succeeded` and `account show` returns the expected bindings.
* **Checks**: `azdev style cognitiveservices`, `azdev linter cognitiveservices`, and `azdev test test_agent_hosting`.
