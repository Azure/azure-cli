Microsoft Azure CLI 'acr' Command Module
========================================

Commands to manage Azure container registries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

    Group
        az acr: Manage Azure container registries.

    Subgroups:
        credential: Manage login credentials for Azure container registries.
        repository: Manage repositories for Azure container registries.

    Commands:
        check-name: Checks whether the container registry name is available for use.
        create    : Creates a container registry.
        delete    : Deletes a container registry.
        list      : Lists all the container registries under the current subscription.
        show      : Gets the properties of the specified container registry.
        update    : Updates a container registry.

Create a container registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

    Command
        az acr create: Creates a container registry.

    Arguments
        --name -n           [Required]: The name of the container registry.
        --resource-group -g [Required]: Name of resource group. You can configure the default group
                                        using 'az configure --defaults group=<name>'.
        --sku               [Required]: The SKU of the container registry.  Allowed values: Basic.
        --admin-enabled               : Indicates whether the admin user is enabled.  Allowed values:
                                        false, true.
        --location -l                 : Location. You can configure the default location using 'az
                                        configure --defaults location=<location>'.
        --storage-account-name        : Default: A new storage account will be created. Provide the name
                                        of an existing storage account if you're recreating a container
                                        registry over a previous registry created storage account.

    Examples
        Create a container registry with a new storage account.
            az acr create -n MyRegistry -g MyResourceGroup --sku Basic

Delete a container registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

    Command
        az acr delete: Deletes a container registry.

    Arguments
        --name -n [Required]: The name of the container registry.
        --resource-group -g : Name of resource group. You can configure the default group using 'az
                            configure --defaults group=<name>'.

    Examples
        Delete a container registry
            az acr delete -n MyRegistry

List container registries
^^^^^^^^^^^^^^^^^^^^^^^^^
::

    Command
        az acr list: Lists all the container registries under the current subscription.

    Arguments
        --resource-group -g: Name of resource group. You can configure the default group using 'az
                            configure --defaults group=<name>'.

    Examples
        List container registries and show the results in a table.
            az acr list -o table

        List container registries in a resource group and show the results in a table.
            az acr list -g MyResourceGroup -o table

Get a container registry
^^^^^^^^^^^^^^^^^^^^^^^^
::

    Command
        az acr show: Gets the properties of the specified container registry.

    Arguments
        --name -n [Required]: The name of the container registry.
        --resource-group -g : Name of resource group. You can configure the default group using 'az
                            configure --defaults group=<name>'.

    Examples
        Get the login server for a container registry.
            az acr show -n MyRegistry --query loginServer

Update a container registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

    Command
        az acr update: Updates a container registry.

    Arguments
        --name -n   [Required]: The name of the container registry.
        --admin-enabled       : Indicates whether the admin user is enabled.  Allowed values: false,
                                true.
        --resource-group -g   : Name of resource group. You can configure the default group using 'az
                                configure --defaults group=<name>'.
        --storage-account-name: Provide the name of an existing storage account if you're recreating a
                                container registry over a previous registry created storage account.
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

Get login credentials for a container registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

    Command
        az acr credential show: Gets the login credentials for the specified container registry.

    Arguments
        --name -n [Required]: The name of the container registry.
        --resource-group -g : Name of resource group. You can configure the default group using 'az
                            configure --defaults group=<name>'.

    Examples
        Get the login credentials for a container registry.
            az acr credential show -n MyRegistry

        Get the username used to log into a container registry.
            az acr credential show -n MyRegistry --query username

        Get one of the passwords used to log into a container registry.
            az acr credential show -n MyRegistry --query passwords[0].value

Regenerate login credentials for a container registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

    Command
        az acr credential renew: Regenerates one of the login credentials for the specified container
        registry.

    Arguments
        --name -n       [Required]: The name of the container registry.
        --password-name [Required]: The name of password to regenerate.  Allowed values: password,
                                    password2.
        --resource-group -g       : Name of resource group. You can configure the default group using
                                    'az configure --defaults group=<name>'.

    Examples
        Renew the second password for a container registry.
            az acr credential renew -n MyRegistry --password-name password2

List repositories in a given container registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

    Command
        az acr repository list: Lists repositories in the specified container registry.

    Arguments
        --name -n [Required]: The name of the container registry.
        --password -p       : The password used to log into a container registry.
        --username -u       : The username used to log into a container registry.

    Examples
        List repositories in a given container registry. Enter login credentials in the prompt if admin
        user is disabled.
            az acr repository list -n MyRegistry

Show tags of a given repository in a given container registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

    Command
        az acr repository show-tags: Shows tags of a given repository in the specified container
        registry.

    Arguments
        --name -n    [Required]: The name of the container registry.
        --repository [Required]: The repository to obtain tags from.
        --password -p          : The password used to log into a container registry.
        --username -u          : The username used to log into a container registry.

    Examples
        Show tags of a given repository in a given container registry. Enter login credentials in the
        prompt if admin user is disabled.
            az acr repository show-tags -n MyRegistry --repository MyRepository
