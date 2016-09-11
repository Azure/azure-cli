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
        storage   : Manage storage accounts for Azure container registries.

    Commands:
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
        --app-id                      : The app id of an existing service principal. If provided, no
                                        --new-sp or -p should be specified.
        --enable-admin                : Enable admin user.
        --new-sp                      : Create a new service principal. If provided, no --app-id should
                                        be specified. Optional: Use -p to specify a password.
        --password -p                 : Password used to log into a container registry.
        --role -r                     : Name of role. (Owner, Contributor, Reader).  Default: Reader.
        --storage-account-name -s     : Name of new or existing storage account. If not provided, a
                                        random storage account name will be generated.

    Examples
        Create a container registry with a new storage account
            az acr create -n myRegistry -g myResourceGroup -l southus
        Create a container registry with an existing storage account
            az acr create -n myRegistry -g myResourceGroup -l southus -s myStorageAccount
        Create a container registry with a new service principal
            az acr create -n myRegistry -g myResourceGroup -l southus --new-sp -p myPassword -r Owner
        Create a container registry with an existing service principal
            az acr create -n myRegistry -g myResourceGroup -l southus --app-id myAppId -r Owner

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
        --name -n [Required]: Name of container registry.
        --app-id            : The app id of an existing service principal. If provided, no --new-sp or
                            -p should be specified.
        --disable-admin     : Disable admin user.
        --enable-admin      : Enable admin user.
        --new-sp            : Create a new service principal. If provided, no --app-id should be
                            specified. Optional: Use -p to specify a password.
        --password -p       : Password used to log into a container registry.
        --resource-group -g : Name of resource group.
        --role -r           : Name of role. (Owner, Contributor, Reader).  Default: Reader.
        --tags              : Space separated tags in 'key[=value]' format. Use "" to clear existing
                            tags.
        --tenant-id -t      : Tenant id for service principal login. Warning: Changing tenant id will
                            invalidate assigned access of existing service principals.

    Examples
        Update tags of a container registry
            az acr update -n myRegistry --tags key1=value1;key2=value2
        Update a container registry with a new service principal
            az acr update -n myRegistry --new-sp -p myPassword -r Owner
        Update a container registry with an existing service principal
            az acr update -n myRegistry --app-id myAppId -r Owner

Update storage account for a container registry
-------------
::

    Command
        az acr storage update: Update storage account for a container registry.

    Arguments
        --name -n                 [Required]: Name of container registry.
        --storage-account-name -s [Required]: Name of new or existing storage account.
        --resource-group -g                 : Name of resource group.

Get admin username and password for a container registry
-------------
::

    Command
        az acr credential show: Get admin username and password for a container registry.

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
