# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['appconfig'] = """
    type: group
    short-summary: Manage App Configurations.
    """

helps['appconfig create'] = """
    type: command
    short-summary: Create an App Configuration.
    examples:
        - name: Create an App Configuration with name, location and resource group.
          text:
            az appconfig create -g MyResourceGroup -n MyAppConfiguration -l westus
    """

helps['appconfig delete'] = """
    type: command
    short-summary: Delete an App Configuration.
    examples:
        - name: Delete an App Configuration under resource group
          text:
            az appconfig delete -g MyResourceGroup -n MyAppConfiguration
    """

helps['appconfig update'] = """
    type: command
    short-summary: Update an App Configuration.
    examples:
        - name: Update tags of an App Configuration
          text:
            az appconfig update -g MyResourceGroup -n MyAppConfiguration --tags key1=value1 key2=value2
    """

helps['appconfig list'] = """
    type: command
    short-summary: Lists all App Configurations under the current subscription.
    examples:
        - name: List all App Configurations under a resource group
          text:
            az appconfig list -g MyResourceGroup
    """

helps['appconfig show'] = """
    type: command
    short-summary: Show properties of an App Configuration.
    examples:
        - name: Show properties of an App Configuration
          text:
            az appconfig show -g MyResourceGroup -n MyAppConfiguration
    """

helps['appconfig credential'] = """
    type: group
    short-summary: Manage credentials for App Configurations
    """

helps['appconfig credential list'] = """
    type: command
    short-summary: List access keys of an App Configuration.
    examples:
        - name: List access keys of an App Configuration
          text:
            az appconfig credential list -g MyResourceGroup -n MyAppConfiguration
    """

helps['appconfig credential regenerate'] = """
    type: command
    short-summary: Regenerate an access key for an App Configuration.
    examples:
        - name: Regenerate a read only access key for an App Configuration
          text:
            az appconfig credential regenerate -g MyResourceGroup -n MyAppConfiguration --id 0-l0-s0:8ldbreMVH+d7EjaSUg3H
    """

helps['appconfig kv'] = """
    type: group
    short-summary: Manage key-values stored in an App Configuration.
    """

helps['appconfig kv import'] = """
    type: command
    short-summary: Import configurations into your App Configuration from another place.
    examples:
        - name: Import all keys with label test from a file.
          text:
            az appconfig kv import -n MyAppConfiguration --label test -s file --path D:/abc.json --format json
        - name: Import all keys with null label from an App Configuration.
          text:
            az appconfig kv import -n MyAppConfiguration -s appconfig --src-name AnotherAppConfiguration
        - name: Import all keys with null label from an App Service appliaction.
          text:
            az appconfig kv import -n MyAppConfiguration -s appservice --appservice-account MyAppService
    """

helps['appconfig kv export'] = """
    type: command
    short-summary: Export configurations to another place from your App Configuration.
    examples:
        - name: Export all keys with label test to a json file.
          text:
            az appconfig kv export -n MyAppConfiguration --label test -d file --path D:/abc.json --format json
        - name: Export all keys with null label to another App Configuration.
          text:
            az appconfig kv export -n MyAppConfiguration -d appconfig --dest-name AnotherAppConfiguration
        - name: Export all keys with null label to an App Service appliaction.
          text:
            az appconfig kv export -n MyAppConfiguration -d appservice  --appservice-account MyAppService
    """

helps['appconfig kv set'] = """
    type: command
    short-summary: Set a key-value.
    examples:
        - name: Set a key-value with label MyLabel.
          text:
            az appconfig kv set -n MyAppConfiguration --key color --label MyLabel --value red
        - name: Set a key with null label using connection string.
          text:
            az appconfig kv set --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --key color --value red --tags key1=value1 key2=value2
    """

helps['appconfig kv delete'] = """
    type: command
    short-summary: Delete key-values.
    examples:
        - name: Delete a key using App Configuration name without confirmation.
          text:
            az appconfig kv delete -n MyAppConfiguration --key color --label MyLabel --yes
        - name: Delete a key using connection string.
          text:
            az appconfig kv delete --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --key color --label MyLabel
    """

helps['appconfig kv show'] = """
    type: command
    short-summary: Show all attributes of a key-value.
    examples:
        - name: Show a key-value using App Configuration name with a specific label and datetime
          text:
            az appconfig kv show -n MyAppConfiguration --key color --label MyLabel --datetime "2019-05-01T11:24:12Z"
        - name: Show a key-value using connection string with label
          text:
            az appconfig kv show --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --key color --label MyLabel
    """

helps['appconfig kv list'] = """
    type: command
    short-summary: List key-values.
    examples:
        - name: List all key-values.
          text:
            az appconfig kv list -n MyAppConfiguration
        - name: List a specfic key for any label start with v1. using connection string.
          text:
            az appconfig kv list --key color --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --label v1.*
        - name: List all keys with any labels and query only key, value and tags.
          text:
            az appconfig kv list --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --fields key value tags --datetime "2019-05-01T11:24:12Z"
        - name: List 150 key-values with any labels.
          text:
            az appconfig kv list --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx  --top 150
    """

helps['appconfig revision'] = """
    type: group
    short-summary: Manage revisions for key-values stored in an App Configuration.
    """

helps['appconfig revision list'] = """
    type: command
    short-summary: Lists revision history of key-values.
    examples:
        - name: List revision history of key "color" label "test" using App Configuration name.
          text:
            az appconfig revision list -n MyAppConfiguration --key color --label test
        - name: List revision history for key "color" with any labels using connection string
          text:
            az appconfig revision list --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --key color --datetime "2019-05-01T11:24:12Z"
    """

helps['appconfig kv lock'] = """
    type: command
    short-summary: Lock a key-value to prohibit write operations.
    examples:
        - name: Lock a key-value using App Configuration name.
          text:
            az appconfig kv lock -n MyAppConfiguration --key color --label test
        - name: Force locking a key-value using connection string.
          text:
            az appconfig kv lock --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --key color --label test --yes
    """

helps['appconfig kv unlock'] = """
    type: command
    short-summary: Unlock a key-value to gain write operations.
    examples:
        - name: Unlock a key-value using App Configuration name.
          text:
            az appconfig kv unlock -n MyAppConfiguration --key color --label test
        - name: Force unlocking a key-value using connection string.
          text:
            az appconfig kv unlock --connection-string Endpoint=https://contoso.azconfig.io;Id=xxx;Secret=xxx --key color --label test --yes
    """
