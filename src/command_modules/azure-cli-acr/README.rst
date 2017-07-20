Microsoft Azure CLI 'acr' Command Module
========================================

Commands to manage Azure container registries
+++++++++++++++++++++++++++++++++++++++++++++
::

    Group
        az acr: Manage Azure Container Registries.

    Subgroups:
        credential: Manage login credentials for Azure container registries.
        repository: Manage repositories for Azure container registries.
        webhook   : Manage webhooks for Azure container registries.

    Commands:
        check-name: Checks whether the container registry name is available for use.
        create    : Creates a container registry.
        delete    : Deletes a container registry.
        list      : Lists all the container registries under the current subscription.
        login     : Login to a container registry through Docker.
        show      : Gets the properties of the specified container registry.
        show-usage: Gets the quota usages for the specified container registry.
        update    : Updates a container registry.

Create a container registry
+++++++++++++++++++++++++++
::

    Command
        az acr create: Creates a container registry.

    Arguments
        --name -n           [Required]: The name of the container registry. You can configure the
                                        default registry name using `az configure --defaults
                                        acr=<registry name>`.
        --resource-group -g [Required]: Name of resource group. You can configure the default group
                                        using `az configure --defaults group=<name>`.
        --sku               [Required]: The SKU of the container registry.  Allowed values: Basic,
                                        Managed_Basic, Managed_Premium, Managed_Standard.
        --admin-enabled               : Indicates whether the admin user is enabled.  Allowed values:
                                        false, true.  Default: false.
        --location -l                 : Location. You can configure the default location using `az
                                        configure --defaults location=<location>`.
        --storage-account-name        : Provide the name of an existing storage account if you're
                                        recreating a container registry over a previous registry created
                                        storage account. Only applicable to Basic SKU.

    Examples
        Create a managed container registry. Applicable to Managed SKU.
            az acr create -n MyRegistry -g MyResourceGroup --sku Managed_Standard

        Create a container registry with a new storage account. Applicable to Basic SKU.
            az acr create -n MyRegistry -g MyResourceGroup --sku Basic

Delete a container registry
+++++++++++++++++++++++++++
::

    Command
        az acr delete: Deletes a container registry.

    Arguments
        --name -n [Required]: The name of the container registry. You can configure the default registry
                              name using `az configure --defaults acr=<registry name>`.
        --resource-group -g : Name of resource group. You can configure the default group using `az
                              configure --defaults group=<name>`.

    Examples
        Delete a container registry.
            az acr delete -n MyRegistry

List container registries
+++++++++++++++++++++++++
::

    Command
        az acr list: Lists all the container registries under the current subscription.

    Arguments
        --resource-group -g: Name of resource group. You can configure the default group using `az
                             configure --defaults group=<name>`.

    Examples
        List container registries and show the results in a table.
            az acr list -o table

        List container registries in a resource group and show the results in a table.
            az acr list -g MyResourceGroup -o table

Get a container registry
++++++++++++++++++++++++
::

    Command
        az acr show: Gets the properties of the specified container registry.

    Arguments
        --name -n [Required]: The name of the container registry. You can configure the default registry
                              name using `az configure --defaults acr=<registry name>`.
        --resource-group -g : Name of resource group. You can configure the default group using `az
                              configure --defaults group=<name>`.

    Examples
        Get the login server for a container registry.
            az acr show -n MyRegistry --query loginServer

Update a container registry
+++++++++++++++++++++++++++
::

    Command
        az acr update: Updates a container registry.

    Arguments
        --name -n   [Required]: The name of the container registry. You can configure the default
                                registry name using `az configure --defaults acr=<registry name>`.
        --admin-enabled       : Indicates whether the admin user is enabled.  Allowed values: false,
                                true.
        --resource-group -g   : Name of resource group. You can configure the default group using `az
                                configure --defaults group=<name>`.
        --storage-account-name: Provide the name of an existing storage account if you're recreating a
                                container registry over a previous registry created storage account.
                                Only applicable to Basic SKU.
        --tags                : Space separated tags in 'key[=value]' format. Use "" to clear existing
                                tags.

    Generic Update Arguments
        --add                 : Add an object to a list of objects by specifying a path and key value
                                pairs.  Example: --add property.listProperty <key=value, string or JSON
                                string>.
        --remove              : Remove a property or an element from a list.  Example: --remove
                                property.list <indexToRemove> OR --remove propertyToRemove.
        --set                 : Update an object by specifying a property path and value to set.
                                Example: --set property1.property2=<value>.

    Examples
        Update tags for a container registry.
            az acr update -n MyRegistry --tags key1=value1 key2=value2

        Update the storage account for a container registry.
            az acr update -n MyRegistry --storage-account-name MyStorageAccount

        Enable the administrator user account for a container registry.
            az acr update -n MyRegistry --admin-enabled true

Login to a container registry
+++++++++++++++++++++++++++++
::

    Command
        az acr login: Login to a container registry through Docker.

    Arguments
        --name -n [Required]: The name of the container registry. You can configure the default registry
                              name using `az configure --defaults acr=<registry name>`.
        --password -p       : The password used to log into a container registry.
        --resource-group -g : Name of resource group. You can configure the default group using `az
                              configure --defaults group=<name>`.
        --username -u       : The username used to log into a container registry.

    Examples
        Login to a container registry
            az acr login -n MyRegistry

Get the quota usages for a container registry
+++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az acr show-usage: Gets the quota usages for the specified container registry.

    Arguments
        --name -n [Required]: The name of the container registry. You can configure the default registry
                              name using `az configure --defaults acr=<registry name>`.
        --resource-group -g : Name of resource group. You can configure the default group using `az
                              configure --defaults group=<name>`.

    Examples
        Get the quota usages for a container registry.
            az acr show-usage -n MyRegistry

Commands to manage login credentials for Azure container registries
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Group
        az acr credential: Manage login credentials for Azure container registries.

    Commands:
        renew: Regenerates one of the login credentials for the specified container registry.
        show : Gets the login credentials for the specified container registry.

Get login credentials for a container registry
++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az acr credential show: Gets the login credentials for the specified container registry.

    Arguments
        --name -n [Required]: The name of the container registry. You can configure the default registry
                              name using `az configure --defaults acr=<registry name>`.
        --resource-group -g : Name of resource group. You can configure the default group using `az
                              configure --defaults group=<name>`.

    Examples
        Get the login credentials for a container registry.
            az acr credential show -n MyRegistry

        Get the username used to log into a container registry.
            az acr credential show -n MyRegistry --query username

        Get one of the passwords used to log into a container registry.
            az acr credential show -n MyRegistry --query passwords[0].value

Regenerate login credentials for a container registry
+++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az acr credential renew: Regenerates one of the login credentials for the specified container
        registry.

    Arguments
        --name -n       [Required]: The name of the container registry. You can configure the default
                                    registry name using `az configure --defaults acr=<registry name>`.
        --password-name [Required]: The name of password to regenerate.  Allowed values: password,
                                    password2.
        --resource-group -g       : Name of resource group. You can configure the default group using
                                    `az configure --defaults group=<name>`.

    Examples
        Renew the second password for a container registry.
            az acr credential renew -n MyRegistry --password-name password2

Commands to manage repositories for Azure container registries
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Group
        az acr repository: Manage repositories for Azure container registries.

    Commands:
        delete        : Deletes a repository or a manifest/tag from the given repository in the
                        specified container registry.
        list          : Lists repositories in the specified container registry.
        show-manifests: Shows manifests of a given repository in the specified container registry.
        show-tags     : Shows tags of a given repository in the specified container registry.

List repositories in a given container registry
+++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az acr repository list: Lists repositories in the specified container registry.

    Arguments
        --name -n [Required]: The name of the container registry. You can configure the default registry
                              name using `az configure --defaults acr=<registry name>`.
        --password -p       : The password used to log into a container registry.
        --resource-group -g : Name of resource group. You can configure the default group using `az
                              configure --defaults group=<name>`.
        --username -u       : The username used to log into a container registry.

    Examples
        List repositories in a given container registry.
            az acr repository list -n MyRegistry

Show tags of a given repository in a given container registry
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az acr repository show-tags: Shows tags of a given repository in the specified container
        registry.

    Arguments
        --name -n    [Required]: The name of the container registry. You can configure the default
                                 registry name using `az configure --defaults acr=<registry name>`.
        --repository [Required]: The repository to obtain tags from.
        --password -p          : The password used to log into a container registry.
        --resource-group -g    : Name of resource group. You can configure the default group using `az
                                 configure --defaults group=<name>`.
        --username -u          : The username used to log into a container registry.

    Examples
        Show tags of a given repository in a given container registry.
            az acr repository show-tags -n MyRegistry --repository MyRepository

Show manifests of a given repository in a given container registry
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az acr repository show-manifests: Shows manifests of a given repository in the specified
        container registry.

    Arguments
        --name -n    [Required]: The name of the container registry. You can configure the default
                                 registry name using `az configure --defaults acr=<registry name>`.
        --repository [Required]: The repository to obtain manifests from.
        --password -p          : The password used to log into a container registry.
        --resource-group -g    : Name of resource group. You can configure the default group using `az
                                 configure --defaults group=<name>`.
        --username -u          : The username used to log into a container registry.

    Examples
        Show manifests of a given repository in a given container registry.
            az acr repository show-manifests -n MyRegistry --repository MyRepository

Delete a repository from a container registry or delete a manifest/tag from a given repository
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az acr repository delete: Deletes a repository or a manifest/tag from the given repository in
        the specified container registry.

    Arguments
        --name -n    [Required]: The name of the container registry. You can configure the default
                                 registry name using `az configure --defaults acr=<registry name>`.
        --repository [Required]: The name of repository to delete.
        --manifest             : The sha256 based digest of manifest to delete.
        --password -p          : The password used to log into a container registry.
        --resource-group -g    : Name of resource group. You can configure the default group using `az
                                 configure --defaults group=<name>`.
        --tag                  : The name of tag to delete.
        --username -u          : The username used to log into a container registry.
        --yes -y               : Do not prompt for confirmation.

    Examples
        Delete a repository from the specified container registry.
            az acr repository delete -n MyRegistry --repository MyRepository

        Delete a tag from the given repository. This operation does not delete the manifest referenced
        by the tag or associated layer data.
            az acr repository delete -n MyRegistry --repository MyRepository --tag MyTag

        Delete the manifest referenced by a tag. This operation also deletes associated layer data and
        all other tags referencing the manifest.
            az acr repository delete -n MyRegistry --repository MyRepository --tag MyTag --manifest

        Delete a manfiest from the given repository. This operation also deletes associated layer data
        and all tags referencing the manifest.
            az acr repository delete -n MyRegistry --repository MyRepository --manifest MyManifest

Commands to manage webhooks for Azure container registries
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Group
        az acr webhook: Manage webhooks for Azure container registries.

    Commands:
        create     : Creates a webhook for a container registry.
        delete     : Deletes a webhook from a container registry.
        get-config : Gets the configuration of service URI and custom headers for the webhook.
        list       : Lists all the webhooks for the specified container registry.
        list-events: Lists recent events for the specified webhook.
        ping       : Triggers a ping event to be sent to the webhook.
        show       : Gets the properties of the specified webhook.
        update     : Updates a webhook.

Create a webhook
++++++++++++++++
::

    Command
        az acr webhook create: Creates a webhook for a container registry.

    Arguments
        --actions     [Required]: Space separated list of actions that trigger the webhook to post
                                  notifications.  Allowed values: delete, push.
        --name -n     [Required]: The name of the webhook.
        --registry -r [Required]: The name of the container registry. You can configure the default
                                  registry name using `az configure --defaults acr=<registry name>`.
        --uri         [Required]: The service URI for the webhook to post notifications.
        --headers               : Space separated custom headers in 'key[=value]' format that will be
                                  added to the webhook notifications. Use "" to clear existing headers.
        --resource-group -g     : Name of resource group. You can configure the default group using `az
                                  configure --defaults group=<name>`.
        --scope                 : The scope of repositories where the event can be triggered. For
                                  example, 'foo:*' means events for all tags under repository 'foo'.
                                  'foo:bar' means events for 'foo:bar' only. 'foo' is equivalent to
                                  'foo:latest'. Empty means events for all repositories.
        --status                : Indicates whether the webhook is enabled.  Allowed values: disabled,
                                  enabled.  Default: enabled.
        --tags                  : Space separated tags in 'key[=value]' format. Use "" to clear existing
                                  tags.

    Examples
        Create a webhook for a container registry that will deliver Docker push and delete events to the
        specified service URI.
            az acr webhook create -n MyWebhook -r MyRegistry --uri http://myservice.com --actions push
            delete

        Create a webhook for a container registry that will deliver Docker push events to the specified
        service URI with Basic authentication header.
            az acr webhook create -n MyWebhook -r MyRegistry --uri http://myservice.com --actions push
            --headers "Authorization=Basic 000000"

Delete a webhook
++++++++++++++++
::

    Command
        az acr webhook delete: Deletes a webhook from a container registry.

    Arguments
        --name -n     [Required]: The name of the webhook.
        --registry -r [Required]: The name of the container registry. You can configure the default
                                  registry name using `az configure --defaults acr=<registry name>`.
        --resource-group -g     : Name of resource group. You can configure the default group using `az
                                  configure --defaults group=<name>`.

    Examples
        Delete a webhook from a container registry.
            az acr webhook delete -n MyWebhook -r MyRegistry

List webhooks
+++++++++++++
::

    Command
        az acr webhook list: Lists all the webhooks for the specified container registry.

    Arguments
        --registry -r [Required]: The name of the container registry. You can configure the default
                                  registry name using `az configure --defaults acr=<registry name>`.
        --resource-group -g     : Name of resource group. You can configure the default group using `az
                                  configure --defaults group=<name>`.

    Examples
        List webhooks and show the results in a table.
            az acr webhook list -r MyRegistry -o table

Get a webhook
+++++++++++++
::

    Command
        az acr webhook show: Gets the properties of the specified webhook.

    Arguments
        --name -n     [Required]: The name of the webhook.
        --registry -r [Required]: The name of the container registry. You can configure the default
                                  registry name using `az configure --defaults acr=<registry name>`.
        --resource-group -g     : Name of resource group. You can configure the default group using `az
                                  configure --defaults group=<name>`.

    Examples
        Get the properties of the specified webhook.
            az acr webhook show -n MyWebhook -r MyRegistry

Update a webhook
++++++++++++++++
::

    Command
        az acr webhook update: Updates a webhook.

    Arguments
        --name -n     [Required]: The name of the webhook.
        --registry -r [Required]: The name of the container registry. You can configure the default
                                  registry name using `az configure --defaults acr=<registry name>`.
        --actions               : Space separated list of actions that trigger the webhook to post
                                  notifications.  Allowed values: delete, push.
        --headers               : Space separated custom headers in 'key[=value]' format that will be
                                  added to the webhook notifications. Use "" to clear existing headers.
        --resource-group -g     : Name of resource group. You can configure the default group using `az
                                  configure --defaults group=<name>`.
        --scope                 : The scope of repositories where the event can be triggered. For
                                  example, 'foo:*' means events for all tags under repository 'foo'.
                                  'foo:bar' means events for 'foo:bar' only. 'foo' is equivalent to
                                  'foo:latest'. Empty means events for all repositories.
        --status                : Indicates whether the webhook is enabled.  Allowed values: disabled,
                                  enabled.
        --tags                  : Space separated tags in 'key[=value]' format. Use "" to clear existing
                                  tags.
        --uri                   : The service URI for the webhook to post notifications.

    Generic Update Arguments
        --add                   : Add an object to a list of objects by specifying a path and key value
                                  pairs.  Example: --add property.listProperty <key=value, string or
                                  JSON string>.
        --remove                : Remove a property or an element from a list.  Example: --remove
                                  property.list <indexToRemove> OR --remove propertyToRemove.
        --set                   : Update an object by specifying a property path and value to set.
                                  Example: --set property1.property2=<value>.

    Examples
        Update headers for a webhook
            az acr webhook update -n MyWebhook -r MyRegistry --headers "Authorization=Basic 000000"

        Update service URI and actions for a webhook
            az acr webhook update -n MyWebhook -r MyRegistry --uri http://myservice.com --actions push
            delete

        Disable a webhook
            az acr webhook update -n MyWebhook -r MyRegistry --status disabled

Get service URI and custom headers for a webhook
++++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az acr webhook get-config: Gets the configuration of service URI and custom headers for the
        webhook.

    Arguments
        --name -n     [Required]: The name of the webhook.
        --registry -r [Required]: The name of the container registry. You can configure the default
                                  registry name using `az configure --defaults acr=<registry name>`.
        --resource-group -g     : Name of resource group. You can configure the default group using `az
                                  configure --defaults group=<name>`.

    Examples
        Get service URI and headers for the webhook.
            az acr webhook get-config -n MyWebhook -r MyRegistry

Trigger a ping event to be sent to a webhook
++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az acr webhook ping: Triggers a ping event to be sent to the webhook.

    Arguments
        --name -n     [Required]: The name of the webhook.
        --registry -r [Required]: The name of the container registry. You can configure the default
                                  registry name using `az configure --defaults acr=<registry name>`.
        --resource-group -g     : Name of resource group. You can configure the default group using `az
                                  configure --defaults group=<name>`.

    Examples
        Triggers a ping event to be sent to the webhook.
            az acr webhook ping -n MyWebhook -r MyRegistry

List recent events for a webhook
++++++++++++++++++++++++++++++++
::

    Command
        az acr webhook list-events: Lists recent events for the specified webhook.

    Arguments
        --name -n     [Required]: The name of the webhook.
        --registry -r [Required]: The name of the container registry. You can configure the default
                                  registry name using `az configure --defaults acr=<registry name>`.
        --resource-group -g     : Name of resource group. You can configure the default group using `az
                                  configure --defaults group=<name>`.

    Examples
        List recent events for the specified webhook.
            az acr webhook list-events -n MyWebhook -r MyRegistry
