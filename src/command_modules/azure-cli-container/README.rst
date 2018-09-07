Microsoft Azure CLI 'container' Command Module
==============================================================

Commands to manage Azure container instances
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Group
        az container: Manage Azure Container Instances.

    Commands:
        attach: Attach local standard output and error streams to a container in a container group.
        create: Create a container group.
        delete: Delete a container group.
        list  : List container groups.
        logs  : Tail the log of a container group.
        show  : Show the details of a container group.

Commands to create an Azure container group
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az container create: Create a container group.

    Arguments
        --image             [Required]: The container image name.
        --name -n           [Required]: The name of the container group.
        --resource-group -g [Required]: Name of resource group. You can configure the default group
                                        using `az configure --defaults group=<name>`.
        --command-line                : The command line to run when the container is started, e.g.
                                        '/bin/bash -c myscript.sh'.
        --cpu                            : The required number of CPU cores of the containers.  Default:
                                        1.
        --dns-name-label                 : The dns name label for container group with public IP.
        --environment-variables -e       : A list of environment variable for the container. Space-
                                        separated values in 'key=value' format.
        --file -f                        : The path to the input file.
        --image                          : The container image name.
        --ip-address                     : The IP address type of the container group.  Allowed values:
                                        Public.
        --location -l                    : Location. You can configure the default location using `az
                                        configure --defaults location=<location>`.
        --memory                         : The required memory of the containers in GB.  Default: 1.5.
        --name -n                        : The name of the container group.
        --no-wait                        : Do not wait for the long-running operation to finish.
        --os-type                        : The OS type of the containers.  Allowed values: Linux,
                                        Windows.  Default: Linux.
        --ports                          : The ports to open.  Default: [80].
        --protocol                       : The network protocol to use.  Allowed values: TCP, UDP.
        --restart-policy                 : Restart policy for all containers within the container group.
                                        Allowed values: Always, Never, OnFailure.  Default: Always.
        --secrets                        : Space-separated secrets in 'key=value' format.
        --secrets-mount-path             : The path within the container where the secrets volume should
                                        be mounted. Must not contain colon ':'.
        --secure-environment-variables   : A list of secure environment variable for the container.
                                        Space-separated values in 'key=value' format.

    Image Registry Arguments
        --registry-login-server       : The container image registry login server.
        --registry-password           : The password to log in container image registry server.
        --registry-username           : The username to log in container image registry server.

    Log Analytics Arguments
        --log-analytics-workspace       : The Log Analytics workspace name or id. Use the --subscription
                                          flag to set the subscription if not current.
        --log-analytics-workspace-key   : The Log Analytics workspace key.

    Global Arguments
        --debug                       : Increase logging verbosity to show all debug logs.
        --help -h                     : Show this help message and exit.
        --output -o                   : Output format.  Allowed values: json, jsonc, table, tsv.
                                        Default: json.
        --query                       : JMESPath query string. See http://jmespath.org/ for more
                                        information and examples.
        --verbose                     : Increase logging verbosity. Use --debug for full debug logs.

    Examples
        Create a container group and specify resources required.
            az container create -g MyResourceGroup --name MyAlpine --image alpine:latest --cpu 1
            --memory 1

        Create a container group with OS type.
            az container create -g MyResourceGroup --name MyWinApp --image winappimage:latest --os-type
            Windows

        Create a container group with public IP address.
            az container create -g MyResourceGroup --name MyAlpine --image alpine:latest --ip-address
            public

        Create a container in a container group with public IP address and UDP port.
            az container create -g MyResourceGroup --name myapp --image myimage:latest --ip-address
            public --ports 8081 --protocol UDP

        Create a container group with starting command line.
            az container create -g MyResourceGroup --name MyAlpine --image alpine:latest --command-line
            "/bin/sh -c '/path to/myscript.sh'"

        Create a container group with envrionment variables.
            az contanier create -g MyResourceGroup --name MyAlpine --image alpine:latest -e key1=value1
            key2=value2

        Create a container group using container image from Azure Container Registry.
            az container create -g MyResourceGroup --name MyAlpine --image
            myAcrRegistry.azurecr.io/alpine:latest --registry-password password

        Create a container group using container image from other private container image registry.
            az container create -g MyResourceGroup --name MyApp --image myimage:latest --cpu 1 --memory
            1.5 --registry-login-server myregistry.com --registry-username username --registry-password
            password

        Create a container in a container group that mounts an Azure File share as volume.
            az container create -g MyResourceGroup --name myapp --image myimage:latest --command-line
            "cat /mnt/azfile/myfile" --azure-file-volume-share-name myshare --azure-file-volume-account-
            name mystorageaccount --azure-file-volume-account-key mystoragekey --azure-file-volume-
            mount-path /mnt/azfile

        Create a container in a container group that mounts a git repo as volume.
            az container create -g MyResourceGroup --name myapp --image myimage:latest --command-line
            "cat /mnt/gitrepo" --gitrepo-url https://github.com/user/myrepo.git --gitrepo-dir ./dir1
            --gitrepo-mount-path /mnt/gitrepo

        Create a container in a container group using a yaml file.
            az container create -g MyResourceGroup -f containerGroup.yaml

        Create a container group using Log Analytics from a workspace name.
            az container create -g MyResourceGroup --name myapp --log-analytics-workspace myworkspace

        Create a container group using Log Analytics from a workspace id and key.
            az container create -g MyResourceGroup --name myapp --log-analytics-workspace workspaceid
            --log-analytics-workspace-key workspacekey


Commands to get an Azure container group
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az container show: Show the details of a container group.

    Arguments

    Resource Id Arguments
        --ids              : One or more resource IDs (space-delimited). If provided, no other 'Resource
                            Id' arguments should be specified.
        --name -n          : The name of the container group.
        --resource-group -g: Name of resource group. You can configure the default group using `az
                            configure --defaults group=<name>`.

    Global Arguments
        --debug            : Increase logging verbosity to show all debug logs.
        --help -h          : Show this help message and exit.
        --output -o        : Output format.  Allowed values: json, jsonc, table, tsv.  Default: json.
        --query            : JMESPath query string. See http://jmespath.org/ for more information and
                            examples.
        --verbose          : Increase logging verbosity. Use --debug for full debug logs.

Commands to tail the logs of a Azure container group
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az container logs: Tail the log of a container group.

    Arguments
        --container-name   : The container name to tail the logs.

    Resource Id Arguments
        --ids              : One or more resource IDs (space-delimited). If provided, no other 'Resource
                            Id' arguments should be specified.
        --name -n          : The name of the container group.
        --resource-group -g: Name of resource group. You can configure the default group using `az
                            configure --defaults group=<name>`.

    Global Arguments
        --debug            : Increase logging verbosity to show all debug logs.
        --help -h          : Show this help message and exit.
        --output -o        : Output format.  Allowed values: json, jsonc, table, tsv.  Default: json.
        --query            : JMESPath query string. See http://jmespath.org/ for more information and
                            examples.
        --verbose          : Increase logging verbosity. Use --debug for full debug logs.

Commands to delete an Azure container group
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az container delete: Delete a container group.

    Arguments
        --yes -y           : Do not prompt for confirmation.

    Resource Id Arguments
        --ids              : One or more resource IDs (space-delimited). If provided, no other 'Resource
                            Id' arguments should be specified.
        --name -n          : The name of the container group.
        --resource-group -g: Name of resource group. You can configure the default group using `az
                            configure --defaults group=<name>`.

    Global Arguments
        --debug            : Increase logging verbosity to show all debug logs.
        --help -h          : Show this help message and exit.
        --output -o        : Output format.  Allowed values: json, jsonc, table, tsv.  Default: json.
        --query            : JMESPath query string. See http://jmespath.org/ for more information and
                            examples.
        --verbose          : Increase logging verbosity. Use --debug for full debug logs.

Commands to list Azure container groups by resource group
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az container list: List container groups.

    Arguments
        --resource-group -g: Name of resource group. You can configure the default group using `az
                            configure --defaults group=<name>`.

    Global Arguments
        --debug            : Increase logging verbosity to show all debug logs.
        --help -h          : Show this help message and exit.
        --output -o        : Output format.  Allowed values: json, jsonc, table, tsv.  Default: json.
        --query            : JMESPath query string. See http://jmespath.org/ for more information and
                            examples.
        --verbose          : Increase logging verbosity. Use --debug for full debug logs.


Commands to execute a command in a running container
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az container exec: Execute a command from within a running container of a container group.
            The most common use case is to open an interactive bash shell. See examples below. This
            command is currently not supported for Windows machines.

    Arguments
        --exec-command [Required]: The command to run from within the container.
        --container-name         : The container name where to execute the command. Can be ommitted for
                                container groups with only one container.
        --terminal-col-size      : The col size for the command output.  Default: 80.
        --terminal-row-size      : The row size for the command output.  Default: 20.

    Resource Id Arguments
        --ids                    : One or more resource IDs (space-delimited). If provided, no other
                                'Resource Id' arguments should be specified.
        --name -n                : The name of the container group.
        --resource-group -g      : Name of resource group. You can configure the default group using `az
                                configure --defaults group=<name>`.

    Global Arguments
        --debug                  : Increase logging verbosity to show all debug logs.
        --help -h                : Show this help message and exit.
        --output -o              : Output format.  Allowed values: json, jsonc, table, tsv.  Default:
                                json.
        --query                  : JMESPath query string. See http://jmespath.org/ for more information
                                and examples.
        --subscription           : Name or ID of subscription. You can configure the default
                                subscription using `az account set -s NAME_OR_ID`".
        --verbose                : Increase logging verbosity. Use --debug for full debug logs.

    Examples
        Stream a shell from within an nginx container.
            az container exec -g MyResourceGroup --name mynginx --container-name nginx --exec-command
            "/bin/bash"

Commands to attach to a container in a container group
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
::

    Command
        az container attach: Attach local standard output and error streams to a container in a
        container group.

    Arguments
        --container-name   : The container to attach to. If omitted, the first container in the
                            container group will be chosen.

    Resource Id Arguments
        --ids              : One or more resource IDs (space delimited). If provided, no other 'Resource
                            Id' arguments should be specified.
        --name -n          : The name of the container group.
        --resource-group -g: Name of resource group. You can configure the default group using `az
                            configure --defaults group=<name>`.

    Global Arguments
        --debug            : Increase logging verbosity to show all debug logs.
        --help -h          : Show this help message and exit.
        --output -o        : Output format.  Allowed values: json, jsonc, table, tsv.  Default: json.
        --query            : JMESPath query string. See http://jmespath.org/ for more information and
                            examples.
        --verbose          : Increase logging verbosity. Use --debug for full debug logs.
