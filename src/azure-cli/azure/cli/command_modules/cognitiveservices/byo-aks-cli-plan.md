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

### 3.1 Option A: JSON Input (Selected)

Selected for future extensibility: `agentHostingConfigurations` is a polymorphic array (`AgentHostingConfiguration[]`) designed to support multiple items and new `hostingType` values in future API versions. Accepts an inline JSON array or `@<file>` (expanded by the CLI framework and parsed once via `shell_safe_json_parse`), paired with `--agent-hosting-subnet`:

| CLI Option | Python Argument | Mapped SDK Target | Requirement | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--agent-hosting-configurations` | `agent_hosting_configurations` | `properties.agent_hosting_configurations` & `identity.user_assigned_identities` | Required when BYO AKS is used | JSON array string (or `@<file>`) of `ManagedClusterAgentHostingConfiguration` objects (schema in Section 2.1). `hostingManagementIdentityResourceId` is automatically attached to `account.identity.userAssignedIdentities`. |
| `--agent-hosting-subnet` | `agent_hosting_subnet` | `properties.network_injections[0].subnet_arm_id` | Required when BYO AKS is used | ARM resource ID of the agent injection subnet (`scenario="agent"`, `use_microsoft_managed_network=False`). |

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

### 3.2 Option B: Flattened Arguments

Alternative design exposing flattened parameters under `arg_group="Agent Hosting"`. Not selected because flat flags only bind to a single item (`[0]`) and cannot scale when future API versions allow multiple configurations or new `hostingType` values.

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
   * Keep `--agent-hosting-configurations` as a raw string in `argparse` (do not set `type=shell_safe_json_parse` directly, which would turn explicit JSON `null` into `None` and silently bypass validation) and parse/validate it once in `custom.py:create()` via `shell_safe_json_parse` (so both CLI invocations and direct unit test calls share the same validation path).
   * If both `--agent-hosting-configurations` and `--agent-hosting-subnet` are `None` (not provided): preserve existing behavior (do not send empty `agentHostingConfigurations` or `networkInjections` arrays).
   * If only one is provided: raise `RequiredArgumentMissingError` requiring both `--agent-hosting-configurations` and `--agent-hosting-subnet`.
   * Require the parsed value to be a `list` of length `1` (`minItems=1, maxItems=1`; reject `null`, non-list, `[]`, and `len > 1`), require the item to be a `dict` with only the 6 expected `camelCase` keys (`name`, `hostingType == "ManagedCluster"`, and 4 valid ARM IDs checked via `is_valid_resource_id()`) with non-empty `str` values, validate `is_valid_resource_id(agent_hosting_subnet)`, and map the `camelCase` fields to `ManagedClusterAgentHostingConfiguration`.
2. **Account Identity Construction (`custom.py`)**:
   * Keep existing `has_system_identity = bool(assign_identity or allow_project_management)` logic in `create()`.
   * Collect `hosting_management_identity_resource_id` from the validated configuration into `user_assigned_identities = {uai_id: UserAssignedIdentity() for uai_id in mgmt_identity_ids}` (do not attach `workload_identity_resource_id` to the account identity).
   * Construct `Identity` directly in `create()` (without modifying shared `compose_identity()`):
     * `SystemAssigned, UserAssigned` when both `has_system_identity` and `user_assigned_identities` are present (default for `AIServices`).
     * `UserAssigned` when `not has_system_identity` and `user_assigned_identities` is present.
     * `SystemAssigned` when `has_system_identity` is present without BYO AKS (unchanged existing behavior).
3. **Validation Boundary & Isolation**:
   * **CLI**: Checks parameter completeness, single-item JSON schema, non-empty strings, and `is_valid_resource_id()` syntax, then constructs SDK models. No extra preflight `GET` calls are made to AKS, Storage, UAI, or RBAC.
   * **Zero Impact on Existing Commands**: All new arguments are scoped strictly to `argument_context('cognitiveservices account create', arg_group='Agent Hosting')`, shared helpers in `_utils.py` and `_params.py` are not modified, and all new `create()` parameters default to `None`.
   * **REST Service (Vienna RP)**: Validates resource types, `name` constraints, distinct management vs. workload UAIs, subscription/region alignment, AKS OIDC/Workload Identity state, and RBAC permissions.

---

## 5. File Changes & Verification

| File Path | Planned Change |
| :--- | :--- |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_params.py` | Register preview `--agent-hosting-configurations` and `--agent-hosting-subnet` arguments under `cognitiveservices account create`. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/custom.py` | Validate `--agent-hosting-configurations` / `--agent-hosting-subnet` and set `properties.agent_hosting_configurations`, `properties.network_injections`, and `params.identity` in `create()`. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/_help.py` | Add parameter help (clarifying JSON schema, management vs. workload UAI, agent injection subnet vs. AKS node subnet, and pre-provisioned resource/RBAC prerequisites) and BYO AKS example. |
| `src/azure-cli/azure/cli/command_modules/cognitiveservices/tests/latest/test_byox.py` | Add `ScenarioTest` (`self.cmd(...)` for CI `missing_parameter_test_coverage`) and unit tests for argument validation, serialized wire payload (`agentHostingConfigurations`, `networkInjections`, `identity`), and non-BYO regression. |

### Verification Checklist

* **Pre-request Validation**: Missing paired flag, explicit JSON `null`, non-list, empty list `[]`, multi-item list (`len > 1`), non-object item, unknown/missing keys, empty/non-string values, and invalid ARM resource IDs fail before any SDK call.
* **Wire Serialization**: Verify the serialized body passed to `client.begin_create` contains 1 `agentHostingConfigurations` item (`hostingType="ManagedCluster"`), 1 `networkInjections` item (`scenario="agent"`, `subnetArmId`, `useMicrosoftManagedNetwork=False`), and expected `identity` (`SystemAssigned, UserAssigned` default for `AIServices`, or `UserAssigned` when system identity is disabled, with only `hostingManagementIdentityResourceId` in `userAssignedIdentities`).
* **Non-BYO & Update Regression**: Non-BYO `account create` sends no `agentHostingConfigurations` / `networkInjections`; `account update` omits `agentHostingConfigurations`.
* **Live ARM Verification**: Creating a new BYO AKS account via `az cognitiveservices account create` reaches `Succeeded` and `account show` returns the expected bindings.
* **Checks**: `azdev style cognitiveservices`, `azdev linter cognitiveservices`, and `azdev test test_byox`.
