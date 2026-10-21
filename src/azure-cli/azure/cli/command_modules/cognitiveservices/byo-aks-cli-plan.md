# Cognitive Services BYO AKS CLI Plan

## 1. Background and Goal

Based on [Azure/azure-rest-api-specs#45245](https://github.com/Azure/azure-rest-api-specs/pull/45245) and the [Vienna BYO AKS setup](https://msdata.visualstudio.com/Vienna/_git/vienna/pullrequest/2285162), add BYO AKS (customer-owned AKS agent hosting) support to `az cognitiveservices account create`.

* **Scope**: Support BYO AKS account binding in `az cognitiveservices account create`:
  1. `properties.agent_hosting_configurations` (`ManagedClusterAgentHostingConfiguration`)
  2. `properties.network_injections` (`NetworkInjection` for the agent subnet)
  3. Account-level managed identity (`identity.user_assigned_identities` including the hosting-management UAI)
  4. The `--agent-hosting` aggregate argument, validation, help, and tests.
* **Prerequisite**: `azure-mgmt-cognitiveservices>=15.0.0b5` (which introduced `AgentHostingConfiguration`, `ManagedClusterAgentHostingConfiguration`, and `AgentHostingType`). In `azure-cli`, [Azure/azure-cli#34112](https://github.com/Azure/azure-cli/pull/34112) upgrades the dependency directly from `15.0.0b4` to `15.0.0b6`.

---

## 2. API Specification

The service API represents agent hosting configuration, network injection, and account identity as separate properties. The selected CLI design combines the required provisioning inputs into one `--agent-hosting` object and fans them out to these service properties.

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

At the CLI layer, the subnet is supplied as `agentSubnetResourceId` inside the `--agent-hosting` aggregate object and mapped to `network_injections[0].subnet_arm_id`; it is not a separate argument in the selected Option A.

---

## 3. CLI Argument Options

Target command: `az cognitiveservices account create` (the new argument is marked `is_preview=True`).

### 3.1 Option A: Aggregated JSON Object (Selected)

Selected to follow the aggregate provisioning model in [Azure/azure-dev#9942](https://github.com/Azure/azure-dev/pull/9942): the CLI accepts one complete Agent Hosting object and expands it into `agentHostingConfigurations[0]`, `networkInjections[0]`, and the account identity. Accepts an inline JSON object or `@<file>` parsed via `shell_safe_json_parse`:

| CLI Option | Python Argument | Mapped SDK Target | Requirement | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--agent-hosting` | `agent_hosting` | `properties.agent_hosting_configurations`, `properties.network_injections` & `identity.user_assigned_identities` | Required when BYO AKS is used | JSON object (or `@<file>`) containing `name`, `hostingType`, `clusterResourceId`, `agentSubnetResourceId`, `hostingManagementIdentityResourceId`, `storageAccountResourceId`, and `workloadIdentityResourceId`. |

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
    --agent-hosting '{
      "name": "default",
      "hostingType": "ManagedCluster",
      "clusterResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ContainerService/managedClusters/cluster1",
      "agentSubnetResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/agent-subnet",
      "hostingManagementIdentityResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/account-control-plane",
      "storageAccountResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/storage1",
      "workloadIdentityResourceId": "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/aks-workload"
    }'
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
| `--agent-hosting-subnet` | `agent_hosting_subnet` | `network_injections[0].subnet_arm_id` | Required when BYO AKS is used |

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
    --agent-hosting-subnet "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/agent-subnet"
```

---

## 4. Implementation Notes

1. **Trigger & Argument Validation**:
   * Parse `--agent-hosting` in `_params.py` with `type=shell_safe_json_parse`, following the current repository pattern for JSON arguments. `custom.py:create()` receives the parsed value and validates its schema.
   * If `--agent-hosting` is `None` (not provided): preserve existing behavior (do not send empty `agentHostingConfigurations` or `networkInjections` arrays).
   * Require the parsed value to be a `dict` with only the 7 expected `camelCase` keys (`name`, `hostingType == "ManagedCluster"`, `clusterResourceId`, `agentSubnetResourceId`, `hostingManagementIdentityResourceId`, `storageAccountResourceId`, and `workloadIdentityResourceId`) with non-empty `str` values. Validate all 5 ARM IDs with `is_valid_resource_id()`.
   * Map the hosting fields to `ManagedClusterAgentHostingConfiguration`, `agentSubnetResourceId` to `NetworkInjection.subnet_arm_id`, and `hostingManagementIdentityResourceId` to the account identity.
2. **Account Identity Construction (`custom.py`)**:
   * Keep existing `has_system_identity = bool(assign_identity or allow_project_management)` logic in `create()`.
   * Collect `hostingManagementIdentityResourceId` from the validated aggregate into `user_assigned_identities` (do not attach `workloadIdentityResourceId` to the account identity).
   * Construct `Identity` directly in `create()` (without modifying shared `compose_identity()`):
     * `SystemAssigned, UserAssigned` when both `has_system_identity` and `user_assigned_identities` are present (default for `AIServices`).
     * `UserAssigned` when `not has_system_identity` and `user_assigned_identities` is present.
     * `SystemAssigned` when `has_system_identity` is present without BYO AKS (unchanged existing behavior).
3. **Validation Boundary & Isolation**:
   * **CLI**: Checks the aggregate JSON schema, non-empty strings, and `is_valid_resource_id()` syntax, then constructs SDK models. No extra preflight `GET` calls are made to AKS, Storage, subnet, UAI, or RBAC.
   * **Zero Impact on Existing Commands**: The new argument is scoped strictly to `argument_context('cognitiveservices account create', arg_group='Agent Hosting')`, shared helpers in `_utils.py` are not modified, and the new `create()` parameter defaults to `None`.
   * **REST Service (Vienna RP)**: Validates resource types, `name` constraints, distinct management vs. workload UAIs, subscription/region alignment, AKS OIDC/Workload Identity state, and RBAC permissions.

---

## 5. File Changes & Verification

| File Path | Planned Change |
| :--- | :--- |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_params.py` | Register the preview `--agent-hosting` aggregate argument and its parameter help under `cognitiveservices account create`. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/custom.py` | Validate `--agent-hosting` and fan the aggregate out to `properties.agent_hosting_configurations`, `properties.network_injections`, and `params.identity` in `create()`. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_help.py` | Add a BYO AKS account creation example. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/tests/latest/test_agent_hosting.py` | Add `ScenarioTest` (`self.cmd(...)` for CI `missing_parameter_test_coverage`) and unit tests for argument validation, serialized wire payload (`agentHostingConfigurations`, `networkInjections`, `identity`), and non-BYO regression. |

### Verification Checklist

* **Pre-request Validation**: Non-object input, unknown/missing keys, empty/non-string values, unsupported `hostingType`, and invalid ARM resource IDs fail before any SDK call.
* **Wire Serialization**: Verify the serialized body passed to `client.begin_create` contains 1 `agentHostingConfigurations` item (`hostingType="ManagedCluster"`), 1 `networkInjections` item (`scenario="agent"`, `subnetArmId`, `useMicrosoftManagedNetwork=False`), and expected `identity` (`SystemAssigned, UserAssigned` default for `AIServices`, or `UserAssigned` when system identity is disabled, with only `hostingManagementIdentityResourceId` in `userAssignedIdentities`).
* **Non-BYO & Update Regression**: Non-BYO `account create` sends no `agentHostingConfigurations` / `networkInjections`; `account update` omits `agentHostingConfigurations`.
* **Live ARM Verification**: Creating a new BYO AKS account via `az cognitiveservices account create` reaches `Succeeded` and `account show` returns the expected bindings.
* **Checks**: `azdev style cognitiveservices`, `azdev linter cognitiveservices`, and `azdev test test_agent_hosting`.
