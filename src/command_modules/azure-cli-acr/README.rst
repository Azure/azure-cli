Microsoft Azure CLI 'acr' Command Module
==================================

Commands to manage Azure container registries
-------------
::

    Group
        az acr: Commands to manage Azure container registries.

    Subgroups:
        credential: Manage administrator login credentials for Azure container registries.
        repository: Manage repositories for Azure container registries.

    Commands:
        check-name: Checks whether the container registry name is available for use.
        create    : Creates a container registry.
        delete    : Deletes a container registry.
        list      : Lists all the available container registries under the current subscription.
        show      : Gets the properties of the specified container registry.
        update    : Updates a container registry.

Create a container registry
-------------
::

    Command
        az acr create: Creates a container registry.

    Arguments
        --location -l       [Required]: Location.
        --name -n           [Required]: The name of the container registry.
        --resource-group -g [Required]: Name of resource group.
        --admin-enabled               : Indicates whether the admin user is enabled.
                                        Allowed values: false, true.  Default: false.
        --storage-account-name        : The name of an existing storage account.

    Examples
        Create a container registry with a new storage account
            az acr create -n myRegistry -g myResourceGroup -l southcentralus
        Create a container registry with an existing storage account
            az acr create -n myRegistry -g myResourceGroup -l southcentralus --storage-account-name myStorageAccount

Delete a container registry
-------------
::

    Command
        az acr delete: Deletes a container registry.

    Arguments
        --name -n [Required]: The name of the container registry.
        --resource-group -g : Name of resource group.

List container registries
-------------
::

    Command
        az acr list: Lists all the available container registries under the current subscription.

    Arguments
        --resource-group -g: Name of resource group.

    Examples
        List container registries and show result in a table
            az acr list -o table
        List container registries in a resource group and show result in a table
            az acr list -g myResourceGroup -o table

Get a container registry
-------------
::

    Command
        az acr show: Gets the properties of the specified container registry.

    Arguments
        --name -n [Required]: The name of the container registry.
        --resource-group -g : Name of resource group.

Update a container registry
-------------
::

    Command
        az acr update: Updates a container registry.

    Arguments
        --name -n   [Required]: The name of the container registry.
        --admin-enabled       : Indicates whether the admin user is enabled.
		                        Allowed values: false, true.
        --resource-group -g   : Name of resource group.
        --storage-account-name: The name of an existing storage account.
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
        Update tags for a container registry
            az acr update -n myRegistry --tags key1=value1 key2=value2
        Update storage account for a container registry
            az acr update -n myRegistry --storage-account-name myStorageAccount
        Enable admin user for a container registry
            az acr update -n myRegistry --admin-enabled true

Get login credentials for a container registry
-------------
::

    Command
        az acr credential show: Gets the administrator login credentials for the specified container registry.

    Arguments
        --name -n [Required]: The name of the container registry.
        --resource-group -g : Name of resource group.

Regenerate login credentials for a container registry
-------------
::

    Command
        az acr credential renew: Regenerates the administrator login credentials for the specified container registry.

    Arguments
        --name -n [Required]: The name of the container registry.
        --resource-group -g : Name of resource group.

List repositories in a given container registry
-------------
::

    Command
        az acr repository list: Lists repositories in the specified container registry.

    Arguments
        --name -n [Required]: The name of the container registry.
        --password -p       : The password used to log into a container registry.
        --username -u       : The username used to log into a container registry.

    Examples
        List repositories in a given container registry if admin user is enabled
            az acr repository list -n myRegistry
        List repositories in a given container registry with credentials
            az acr repository list -n myRegistry -u myUsername -p myPassword

Show tags of a given repository in a given container registry
-------------
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
        Show tags of a given repository in a given container registry if admin user is enabled
            az acr repository show-tags -n myRegistry --repository myRepository
        Show tags of a given repository in a given container registry with credentials
            az acr repository show-tags -n myRegistry --repository myRepository -u myUsername -p myPassword
