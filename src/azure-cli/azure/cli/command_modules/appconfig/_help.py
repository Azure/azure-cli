# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['appconfig'] = """
type: group
short-summary: Manage App Configurations.
"""

helps['appconfig create'] = """
type: command
short-summary: Create an App Configuration.
examples:
  - name: Create an App Configuration with name, location, sku and resource group.
    text: az appconfig create -g MyResourceGroup -n MyAppConfiguration -l westus --sku Standard
  - name: Create an App Configuration with name, location, sku and resource group with system assigned identity.
    text: az appconfig create -g MyResourceGroup -n MyAppConfiguration -l westus --sku Standard --assign-identity
  - name: Create an App Configuration with name, location, sku and resource group with user assigned identity.
    text: az appconfig create -g MyResourceGroup -n MyAppConfiguration -l westus --sku Standard --assign-identity /subscriptions/<SUBSCRIPTON ID>/resourcegroups/<RESOURCEGROUP>/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myUserAssignedIdentity
"""

helps['appconfig identity'] = """
type: group
short-summary: Managed identities for App Configurations.
"""

helps['appconfig identity assign'] = """
type: command
short-summary: Update managed identities for an App Configuration.
examples:
  - name: Enable the system-assigned identity for an existing App Configuration
    text: az appconfig identity assign -g MyResourceGroup -n MyAppConfiguration
  - name: Assign a user-assigned managed identity for an existing App Configuration
    text: az appconfig identity assign -g MyResourceGroup -n MyAppConfiguration --identities "/subscriptions/<SUBSCRIPTON ID>/resourcegroups/<RESOURCEGROUP>/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myUserAssignedIdentity"
  - name: Assign both system-assigned and user assigned identities for an existing App Configuration
    text: az appconfig identity assign -g MyResourceGroup -n MyAppConfiguration --identities [system] "/subscriptions/<SUBSCRIPTON ID>/resourcegroups/<RESOURCEGROUP>/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myUserAssignedIdentity"
"""

helps['appconfig identity remove'] = """
type: command
short-summary: Remove managed identities for an App Configuration.
examples:
  - name: Remove the system-assigned identity from a App Configuration.
    text: az appconfig identity remove -g MyResourceGroup -n MyAppConfiguration
  - name: Remove a user assigned identity from a App Configuration.
    text: az appconfig identity remove -g MyResourceGroup -n MyAppConfiguration --identities "/subscriptions/<SUBSCRIPTON ID>/resourcegroups/<RESOURCEGROUP>/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myUserAssignedIdentity"
  - name: Remove all identities from an App Configuration.
    text: az appconfig identity remove -g MyResourceGroup -n MyAppConfiguration --identities [all]
"""

helps['appconfig identity show'] = """
type: command
short-summary: Display managed identities for an App Configuration.
examples:
  - name: Display managed identities for a task.
    text: az appconfig identity show -g MyResourceGroup -n MyAppConfiguration
"""

helps['appconfig credential'] = """
type: group
short-summary: Manage credentials for App Configurations.
"""

helps['appconfig credential list'] = """
type: command
short-summary: List access keys of an App Configuration.
examples:
  - name: List access keys of an App Configuration
    text: az appconfig credential list -g MyResourceGroup -n MyAppConfiguration
"""

helps['appconfig credential regenerate'] = """
type: command
short-summary: Regenerate an access key for an App Configuration.
examples:
  - name: Regenerate a read only access key for an App Configuration
    text: az appconfig credential regenerate -g MyResourceGroup -n MyAppConfiguration --id 0-l0-s0:8ldbreMVH+d7EjaSUg3H
"""

helps['appconfig delete'] = """
type: command
short-summary: Delete an App Configuration.
examples:
  - name: Delete an App Configuration under resource group
    text: az appconfig delete -g MyResourceGroup -n MyAppConfiguration
"""

helps['appconfig kv'] = """
type: group
short-summary: Manage key-values stored in an App Configuration.
"""

helps['appconfig kv delete'] = """
type: command
short-summary: Delete key-values.
examples:
  - name: Delete a key using App Configuration name without confirmation.
    text: az appconfig kv delete -n MyAppConfiguration --key color --label MyLabel --yes
  - name: Delete a key using connection string.
    text: az appconfig kv delete --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --key color --label MyLabel
"""

helps['appconfig kv export'] = """
type: command
short-summary: Export configurations to another place from your App Configuration.
examples:
  - name: Export all keys and feature flags with label test to a json file.
    text: az appconfig kv export -n MyAppConfiguration --label test -d file --path D:/abc.json --format json
  - name: Export all keys with null label to an App Service application.
    text: az appconfig kv export -n MyAppConfiguration -d appservice  --appservice-account MyAppService
  - name: Export all keys with label test excluding feature flags to a json file.
    text: az appconfig kv export -n MyAppConfiguration --label test -d file --path D:/abc.json --format json --skip-features
  - name: Export all keys and feature flags with all labels to another App Configuration.
    text: az appconfig kv export -n MyAppConfiguration -d appconfig --dest-name AnotherAppConfiguration --key * --label * --preserve-labels
  - name: Export all keys and feature flags with all labels to another App Configuration and overwrite destination labels.
    text: az appconfig kv export -n MyAppConfiguration -d appconfig --dest-name AnotherAppConfiguration --key * --label * --dest-label ExportedKeys
"""

helps['appconfig kv import'] = """
type: command
short-summary: Import configurations into your App Configuration from another place.
examples:
  - name: Import all keys and feature flags from a file and apply test label.
    text: az appconfig kv import -n MyAppConfiguration --label test -s file --path D:/abc.json --format json
  - name: Import all keys and feature flags with null label and apply new label from an App Configuration.
    text: az appconfig kv import -n MyAppConfiguration -s appconfig --src-name AnotherAppConfiguration --label ImportedKeys
  - name: Import all keys and apply null label from an App Service appliaction.
    text: az appconfig kv import -n MyAppConfiguration -s appservice --appservice-account MyAppService
  - name: Import all keys with label test and apply test2 label excluding feature flags from an App Configuration.
    text: az appconfig kv import -n MyAppConfiguration -s appconfig --src-label test --label test2 --src-name AnotherAppConfiguration --skip-features
  - name: Import all keys and feature flags with all labels to another App Configuration.
    text: az appconfig kv import -n MyAppConfiguration -s appconfig --src-name AnotherAppConfiguration --src-key * --src-label * --preserve-labels
"""

helps['appconfig kv list'] = """
type: command
short-summary: List key-values.
examples:
  - name: List all key-values with null label.
    text: az appconfig kv list -n MyAppConfiguration --label \\0
  - name: List a specific key for any label start with v1. using connection string.
    text: az appconfig kv list --key color --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --label v1.*
  - name: List all keys with any labels and query only key, value and tags.
    text: az appconfig kv list --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --fields key value tags --datetime "2019-05-01T11:24:12Z"
  - name: List content of key vault reference with key prefix 'KVRef_' and only select key and value.
    text: az appconfig kv list -n MyAppConfiguration --key "KVRef_*" --resolve-keyvault --query "[*].{key:key, value:value}"
  - name: List key-values with multiple labels.
    text: az appconfig kv list --label test,prod,\\0 -n MyAppConfiguration
"""

helps['appconfig kv lock'] = """
type: command
short-summary: Lock a key-value to prohibit write operations.
examples:
  - name: Lock a key-value using App Configuration name.
    text: az appconfig kv lock -n MyAppConfiguration --key color --label test
  - name: Force locking a key-value using connection string.
    text: az appconfig kv lock --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --key color --label test --yes
"""

helps['appconfig kv restore'] = """
type: command
short-summary: Restore key-values.
examples:
  - name: Restore all key-values to a specific point in time.
    text: az appconfig kv restore -n MyAppConfiguration --datetime "2019-05-01T11:24:12Z"
  - name: Restore a specific key for any label start with v1. using connection string to a specific point in time.
    text: az appconfig kv restore --key color --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --label v1.* --datetime "2019-05-01T11:24:12Z"
"""

helps['appconfig kv set'] = """
type: command
short-summary: Set a key-value.
examples:
  - name: Set a key-value with label MyLabel.
    text: az appconfig kv set -n MyAppConfiguration --key color --label MyLabel --value red
  - name: Set a key with null label using connection string.
    text: az appconfig kv set --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --key color --value red --tags key1=value1 key2=value2
"""

helps['appconfig kv set-keyvault'] = """
type: command
short-summary: Set a keyvault reference.
examples:
  - name: Set a keyvault reference with label MyLabel.
    text: az appconfig kv set-keyvault -n MyAppConfiguration --key HostSecret --label MyLabel --secret-identifier https://contoso.vault.azure.net/Secrets/DummySecret/Dummyversion
  - name: Set a keyvault reference with null label and multiple tags using connection string.
    text: az appconfig kv set-keyvault --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --key HostSecret --secret-identifier https://contoso.vault.azure.net/Secrets/DummySecret --tags tag1=value1 tag2=value2
"""

helps['appconfig kv show'] = """
type: command
short-summary: Show all attributes of a key-value.
examples:
  - name: Show a key-value using App Configuration name with a specific label and datetime
    text: az appconfig kv show -n MyAppConfiguration --key color --label MyLabel --datetime "2019-05-01T11:24:12Z"
  - name: Show a key-value using connection string with label
    text: az appconfig kv show --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --key color --label MyLabel
"""

helps['appconfig kv unlock'] = """
type: command
short-summary: Unlock a key-value to gain write operations.
examples:
  - name: Unlock a key-value using App Configuration name.
    text: az appconfig kv unlock -n MyAppConfiguration --key color --label test
  - name: Force unlocking a key-value using connection string.
    text: az appconfig kv unlock --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --key color --label test --yes
"""

helps['appconfig list'] = """
type: command
short-summary: Lists all App Configurations under the current subscription.
examples:
  - name: List all App Configurations under a resource group
    text: az appconfig list -g MyResourceGroup
"""

helps['appconfig revision'] = """
type: group
short-summary: Manage revisions for key-values stored in an App Configuration.
"""

helps['appconfig revision list'] = """
type: command
short-summary: Lists revision history of key-values.
examples:
  - name: List revision history of a key-value using App Configuration name.
    text: az appconfig revision list -n MyAppConfiguration --key color --label test
  - name: List revision history of a key-value with multiple labels.
    text: az appconfig revision list -n MyAppConfiguration --key color --label test,prod,\\0
  - name: List revision history for key "color" with any labels using connection string
    text: az appconfig revision list --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --key color --datetime "2019-05-01T11:24:12Z"
"""

helps['appconfig show'] = """
type: command
short-summary: Show properties of an App Configuration.
examples:
  - name: Show properties of an App Configuration
    text: az appconfig show -g MyResourceGroup -n MyAppConfiguration
"""

helps['appconfig update'] = """
type: command
short-summary: Update an App Configuration.
examples:
  - name: Update tags of an App Configuration
    text: az appconfig update -g MyResourceGroup -n MyAppConfiguration --tags key1=value1 key2=value2
  - name: Upgrade sku of an App Configuration to standard
    text: az appconfig update -g MyResourceGroup -n MyAppConfiguration --sku Standard
  - name: Enable customer encryption key with system assigned identity
    text: az appconfig update -g MyResourceGroup -n MyAppConfiguration --encryption-key-name myKey --encryption-key-version keyVersion --encryption-key-vault https://keyVaultName.vault.azure.net
  - name: Remove customer encryption key
    text: az appconfig update -g MyResourceGroup -n MyAppConfiguration --encryption-key-name ""
"""

helps['appconfig feature'] = """
    type: group
    short-summary: Manage feature flags stored in an App Configuration.
    """

helps['appconfig feature set'] = """
    type: command
    short-summary: Set a feature flag.
    examples:
        - name: Set a feature flag with label MyLabel.
          text:
            az appconfig feature set -n MyAppConfiguration --feature color --label MyLabel
        - name: Set a feature flag with null label using connection string and set a description.
          text:
            az appconfig feature set --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --feature color --description "This is a colorful feature"
    """

helps['appconfig feature delete'] = """
    type: command
    short-summary: Delete feature flag.
    examples:
        - name: Delete a feature using App Configuration name without confirmation.
          text:
            az appconfig feature delete -n MyAppConfiguration --feature color --label MyLabel --yes
        - name: Delete a feature using connection string.
          text:
            az appconfig feature delete --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --feature color --label MyLabel
    """

helps['appconfig feature show'] = """
    type: command
    short-summary: Show all attributes of a feature flag.
    examples:
        - name: Show a feature flag using App Configuration name with a specific label
          text:
            az appconfig feature show -n MyAppConfiguration --feature color --label MyLabel
        - name: Show a feature flag using connection string and field filters
          text:
            az appconfig feature show --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --feature color --fields key locked conditions state
    """

helps['appconfig feature list'] = """
    type: command
    short-summary: List feature flags.
    examples:
        - name: List all feature flags.
          text:
            az appconfig feature list -n MyAppConfiguration
        - name: List all feature flags with null labels.
          text:
            az appconfig feature list -n MyAppConfiguration --label \\0
        - name: List a specfic feature for any label start with v1. using connection string.
          text:
            az appconfig feature list --feature color --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --label v1.*
        - name: List all features with any labels and query only key, state and conditions.
          text:
            az appconfig feature list --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --fields key state conditions
        - name: List 150 feature flags with any labels.
          text:
            az appconfig feature list --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx  --top 150
        - name: List feature flags with multiple labels.
          text:
            az appconfig feature list --label test,prod,\\0 -n MyAppConfiguration
    """

helps['appconfig feature lock'] = """
    type: command
    short-summary: Lock a feature flag to prohibit write operations.
    examples:
        - name: Lock a feature using App Configuration name.
          text:
            az appconfig feature lock -n MyAppConfiguration --feature color --label test
        - name: Force locking a feature using connection string.
          text:
            az appconfig feature lock --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --feature color --label test --yes
    """

helps['appconfig feature unlock'] = """
    type: command
    short-summary: Unlock a feature to gain write operations.
    examples:
        - name: Unlock a feature using App Configuration name.
          text:
            az appconfig feature unlock -n MyAppConfiguration --feature color --label test
        - name: Force unlocking a feature using connection string.
          text:
            az appconfig feature unlock --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --feature color --label test --yes
    """

helps['appconfig feature enable'] = """
    type: command
    short-summary: Enable a feature flag to turn it ON for use.
    examples:
        - name: enable a feature using App Configuration name.
          text:
            az appconfig feature enable -n MyAppConfiguration --feature color --label test
        - name: Force enabling a feature using connection string.
          text:
            az appconfig feature enable --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --feature color --label test --yes
    """

helps['appconfig feature disable'] = """
    type: command
    short-summary: Disable a feature flag to turn it OFF for use.
    examples:
        - name: disable a feature using App Configuration name.
          text:
            az appconfig feature disable -n MyAppConfiguration --feature color --label test
        - name: Force disabling a feature using connection string.
          text:
            az appconfig feature disable --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --feature color --label test --yes
    """

helps['appconfig feature filter'] = """
    type: group
    short-summary: Manage filters associated with feature flags stored in an App Configuration.
    """

helps['appconfig feature filter add'] = """
    type: command
    short-summary: Add a filter to a feature flag.
    examples:
        - name: Add a filter for feature 'color' with label MyLabel with name 'MyFilter' and 2 parameters.
          text:
            az appconfig feature filter add -n MyAppConfiguration --feature color --label MyLabel --filter-name MyFilter --filter-parameters Name=Value Name2=Value2
        - name: Insert a filter at index 2 (zero-based index) for feature 'color' with label MyLabel and filter name 'MyFilter' with no parameters
          text:
            az appconfig feature filter add -n MyAppConfiguration --feature color --label MyLabel --filter-name MyFilter --index 2
        - name:  Add a filter with name 'MyFilter' using connection string.
          text:
            az appconfig feature filter add --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --feature color --filter-name MyFilter
    """

helps['appconfig feature filter delete'] = """
    type: command
    short-summary: Delete a filter from a feature flag.
    examples:
        - name: Delete a filter from a feature using App Configuration name without confirmation.
          text:
            az appconfig feature filter delete -n MyAppConfiguration --feature color --filter-name MyFilter --yes
        - name: Delete a filter from a feature when you have multiple filters with that same name.
          text:
            az appconfig feature filter delete --feature color --filter-name MyFilter --index 2 --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx
        - name: Delete all filters of a feature using App Configuration name without confirmation.
          text:
            az appconfig feature filter delete -n MyAppConfiguration --feature color --label MyLabel --all --yes
    """

helps['appconfig feature filter show'] = """
    type: command
    short-summary: Show filters of a feature flag.
    examples:
        - name: Show one unique feature filter when you have multiple filters with that same name.
          text:
            az appconfig feature filter show -n MyAppConfiguration --feature color --filter-name MyFilter --index 2
        - name: Show all instances of a feature filter when you have multiple filters with that same name.
          text:
            az appconfig feature filter show --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --feature color --filter-name MyFilter
    """

helps['appconfig feature filter list'] = """
    type: command
    short-summary: List all filters for a feature flag.
    examples:
        - name: List all filters for feature flag 'color'.
          text:
            az appconfig feature filter list -n MyAppConfiguration --feature color --all
        - name: List 150 filters for feature flag 'color'
          text:
            az appconfig feature filter list --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx  --feature color --top 150
    """
