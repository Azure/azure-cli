Microsoft Azure CLI 'acr' Command Module
==================================

Commands to manage Azure container registries
-------------
::

    Group
        az acr: Commands to manage Azure container registries.

    Subgroups:
        credential: Manage admin user credential for Azure container registries.
        repository: Manage repositories for Azure container registries.

    Commands:
        check-name: Check whether the container registry name is available.
        create    : Create a container registry.
        delete    : Delete a container registry.
        list      : List container registries.
        show      : Get a container registry.
        update    : Update a container registry.

Create a container registry
-------------
::

    Command
        az acr create: Create a container registry.

    Arguments
        --location -l       [Required]: Location.
        --name -n           [Required]: Name of container registry.
        --resource-group -g [Required]: Name of resource group.
        --enable-admin                : Enable admin user.
        --storage-account-name -s     : Name of an existing storage account.

    Examples
        Create a container registry with a new storage account
            az acr create -n myRegistry -g myResourceGroup -l southcentralus
        Create a container registry with an existing storage account
            az acr create -n myRegistry -g myResourceGroup -l southcentralus -s myStorageAccount

Delete a container registry
-------------
::

    Command
        az acr delete: Delete a container registry.

    Arguments
        --name -n [Required]: Name of container registry.
        --resource-group -g : Name of resource group.

List container registries
-------------
::

    Command
        az acr list: List container registries.

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
        az acr show: Get a container registry.

    Arguments
        --name -n [Required]: Name of container registry.
        --resource-group -g : Name of resource group.

Update a container registry
-------------
::

    Command
        az acr update: Update a container registry.
    
    Arguments
        --name -n      [Required]: Name of container registry.
        --admin-user-enabled -a  : Whether the admin user account is enabled.  Allowed values: false,
                                   true.
        --resource-group -g      : Name of resource group.
        --storage-account-name -s: Name of an existing storage account.
        --tags                   : Space separated tags in 'key[=value]' format. Use "" to clear
                                   existing tags.
    
    Generic Update Arguments
        --add                    : Add an object to a list of objects by specifying a path and key value
                                   pairs.  Example: --add property.listProperty <key=value, string or
                                   JSON string>.
        --remove                 : Remove a property or an element from a list.  Example: --remove
                                   property.list <indexToRemove> OR --remove propertyToRemove.
        --set                    : Update an object by specifying a property path and value to set.
                                   Example: --set property1.property2=<value>.
    
    Examples
        Update tags for a container registry
            az acr update -n myRegistry --tags key1=value1 key2=value2
        Update storage account for a container registry
            az acr update -n myRegistry --storage-account-name myStorageAccount
        Enable admin user for a container registry
            az acr update -n myRegistry --admin-user-enabled true

Get login credentials for a container registry
-------------
::

    Command
        az acr credential show: Get login credentials for a container registry.

    Arguments
        --name -n [Required]: Name of container registry.
        --resource-group -g : Name of resource group.

Regenerate login credentials for a container registry
-------------
::

    Command
        az acr credential renew: Regenerate login credentials for a container registry.

    Arguments
        --name -n [Required]: Name of container registry.
        --resource-group -g : Name of resource group.

List repositories in a given container registry
-------------
::

    Command
        az acr repository list: List repositories in a given container registry.

    Arguments
        --name -n [Required]: Name of container registry.
        --password -p       : Password used to log into a container registry.
        --username -u       : Username used to log into a container registry.

    Examples
        List repositories in a given container registry if admin user is enabled
            az acr repository list -n myRegistry
        List repositories in a given container registry with credentials
            az acr repository list -n myRegistry -u myUsername -p myPassword

Show tags of a given repository in a given container registry
-------------
::

    Command
        az acr repository show-tags: Show tags of a given repository in a given container registry.

    Arguments
        --name -n    [Required]: Name of container registry.
        --repository [Required]: The repository to obtain tags from.
        --password -p          : Password used to log into a container registry.
        --username -u          : Username used to log into a container registry.

    Examples
        Show tags of a given repository in a given container registry if admin user is enabled
            az acr repository show-tags -n myRegistry --repository myRepository
        Show tags of a given repository in a given container registry with credentials
            az acr repository show-tags -n myRegistry --repository myRepository -u myUsername -p
            myPassword
