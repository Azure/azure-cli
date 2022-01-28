## Azure Data Lake Storage Gen2

Azure Data Lake Storage Gen2 is a set of capabilities dedicated to big data analytics, built on Azure Blob storage. FOr more information, please refer to
https://docs.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-introduction?toc=/azure/storage/blobs/toc.json.

### Included Features

#### Overview

There are several features for ADLS Gen2 account as shown below:
- [FileSystem](#Manage-File-Systems-in-Azure-Data-Lake-Storage-Gen2-account)
- [Directory](#Manage-Directories-in-Azure-Data-Lake-Storage-Gen2-file-system)
- [File](#Manage-Files-in-Azure-Data-Lake-Storage-Gen2-file-system)
- [Access](#Manage-Access-in-Azure-Data-Lake-Storage-Gen2-file-system)

```
❯ az storage fs -h

Group
    az storage fs : Manage file systems in Azure Data Lake Storage Gen2 account.
        This command group is in preview. It may be changed/removed in a future release.
Subgroups:
    access    : Manage file system access and permissions for Azure Data Lake Storage Gen2 account.
    directory : Manage directories in Azure Data Lake Storage Gen2 account.
    file      : Manage files in Azure Data Lake Storage Gen2 account.

Commands:
    create    : Create file system for Azure Data Lake Storage Gen2 account.
    delete    : Delete a file system in ADLS Gen2 account.
    list      : List file systems in ADLS Gen2 account.
    show      : Show properties of file system in ADLS Gen2 account.

For more specific examples, use: az find "az storage fs"
```

### Azure CLI Requirement
- Azure CLI with latest version

### Prepare with ADLS Gen2 account
- Create a ADLS Gen2 account

    ` az storage account create -n myadlsaccount -g myresourcegroup --kind StorageV2 --hns`

- Authorize access for all commands

    For all the commands inside, please provide `connection string` or a combination of `account name` and `credentials`.

    **Several Authorization access Methods:**

    1. Using connection string

        - Specify `--connection-string` parameter in your command
            `--connection-string $myconnectionstring`

        - Set Environment Variable `AZURE_STORAGE_CONNECTION_STRING`

    2. Using account name and account key

        - Specify `--account-name` and `--account-key` parameter in your command
            ```
            --account-name $myadlsaccount \
            --account-key $myaccountkey
            ```

        - Set Environment Variable `AZURE_STORAGE_ACCOUNT` and `AZURE_STORAGE_KEY` 

    3. Using account name and sas token

        - Specify `--account-name` and `--sas-token` parameter in your command
            ```
            --account-name $myadlsaccount \
            --sas-token $mysastoken
            ```

        - Set Environment Variable `AZURE_STORAGE_ACCOUNT` and `AZURE_STORAGE_SAS_TOKEN` 

    4. Using account name and Azure AD credentials

        Azure CLI commands for data operations against Blob storage support the `--auth-mode` parameter, which enables you to specify how to authorize a given operation. Set the `--auth-mode` parameter to login to authorize with Azure AD credentials. For more information, see [Authorize access to blob or queue data with Azure CLI](https://docs.microsoft.com/en-us/azure/storage/common/authorize-data-operations-cli?toc=/azure/storage/blobs/toc.json).

        - Specify `--account-name` and `--auth-mode login` parameter in your command
            ```
            --account-name $myadlsaccount \
            --auth-mode login
            ```

        - Set Environment Variable `AZURE_STORAGE_ACCOUNT` and `AZURE_STORAGE_AUTH_MODE` 

#### Manage File Systems in Azure Data Lake Storage Gen2 account

##### Create a file system in ADLS Gen2 
- Create a file system 

```
az storage fs create -n myfilesystem 
```

- Create a file system with public access for files
```
az storage fs create \
    -n myfilesystem \
    --public-access file 
```

##### Show the properties of file system in ADLS Gen2
```
az storage fs show -n myfilesystem 
```

##### List the properties of file system in ADLS Gen2
```
az storage fs list -n myfilesystem 
```

##### Delete the properties of file system in ADLS Gen2
- Delete a file system with prompt message
```
az storage fs delete -n myfilesystem 
```

- Delete a file system without prompt message
```
az storage fs delete -n myfilesystem -y
```

##### Manage metadata for file system in ADLS Gen2
- Set user-defined metadata for the specified filesystem as one or more name-value pairs.
```
az storage fs metadata uptdate \
    --metdata tag1=value1 tag2=value2 \
    -n myfilesystem
```

- Show all user-defined metadata for the specified filesystem.
```
az storage fs metadata show -n myfilesystem
```

#### Manage Directories in Azure Data Lake Storage Gen2 file system
```
❯ az storage fs directory -h

Group
    az storage fs directory : Manage directories in Azure Data Lake Storage Gen2 account.
        Command group 'storage fs' is in preview. It may be changed/removed in a future
        release.
Commands:
    create : Create a directory in ADLS Gen2 file system.
    delete : Delete a directory in ADLS Gen2 file system.
    exists : Check for the existence of a directory in ADLS Gen2 file system.
    list   : List directories in ADLS Gen2 file system.
    move   : Move a directory in ADLS Gen2 file system.
    show   : Show properties of a directory in ADLS Gen2 file system.
```
##### Check the existence of a directory in ADLS Gen2 file system
- Check the existence of a directory in ADLS Gen2 file system
```
az storage fs directory exists \
    -n mydir
    -f myfilesystem
```

##### Create a directory in ADLS Gen2 file system
- Create a directory in ADLS Gen2 file system
```
az storage fs directory create \
    -n mydir
    -f myfilesystem
```

- Create a directory with specific permissions in ADLS Gen2 file system
```
az storage fs directory create \
    -n mydir \
    -f myfilesystem \
    --permissions rwxrwxrwx
```

##### Show a directory in ADLS Gen2 file system
```
az storage fs directory show \
    -n mydir \
    -f myfilesystem
```

##### List directories in ADLS Gen2 file system
- List all directories in file system
```
az storage fs directory list -f myfilesystem
```

- List all directories under specific path in file system
```
az storage fs directory list \
    -p mydir \
    -f myfilesystem
```

##### Move a directory to a new path in ADLS Gen2 account
- Move a directory "mydir" to "mynewdir" in the same file system "myfilesystem"
```
az storage fs directory move \
    -n mydir \
    -f myfilesystem \
    -new-directory "myfilesystem/mynewdir"
```

- Move a directory "mydir" to another file system "mynewfilesystem" with name "mydir"
```
az storage fs directory move \
    -n mydir \
    -f myfilesystem \
    -new-directory "mymewfilesystem/mydir"
```

##### Delete a directory in ADLS Gen2 file system
- Delete a directory with prompt message
```
az storage fs directory delete \
    -n mydir \
    -f myfilesystem 
```

- Delete a directory without prompt message
```
az storage fs directory delete \
    -n mydir \
    -f myfilesystem \
    -y
```

##### Manage metadata for directory in ADLS Gen2
- Set user-defined metadata for the specified directory as one or more name-value pairs.
```
az storage fs directory metadata uptdate \
    --metdata tag1=value1 tag2=value2 \
    -n mydir \
    -f myfilesystem
```

- Show all user-defined metadata for the specified directory.
```
az storage fs directory metadata show -n mydir -f myfilesystem
```

#### Manage Files in Azure Data Lake Storage Gen2 file system.
```
❯ az storage fs file -h

Group
    az storage fs file : Manage files in Azure Data Lake Storage Gen2 account.
        Command group 'storage fs' is in preview. It may be changed/removed in a future
        release.
Commands:
    append   : Append content to a file in ADLS Gen2 file system.
    create   : Create a new file in ADLS Gen2 file system.
    delete   : Delete a file in ADLS Gen2 file system.
    download : Download a file from the specified path in ADLS Gen2 file system.
    exists   : Check for the existence of a file in ADLS Gen2 file system.
    list     : List files and directories in ADLS Gen2 file system.
    move     : Move a file in ADLS Gen2 Account.
    show     : Show properties of file in ADLS Gen2 file system.
    upload   : Upload a file to a file path in ADLS Gen2 file system.

```
##### Check the existence of a file in ADLS Gen2 file system
- Check the existence of a file path in ADLS Gen2 file system
```
az storage fs file exists \
    -p myfile \
    -f myfilesystem
```

##### Create an empty file in ADLS Gen2 file system
- Create an empty file in ADLS Gen2 file system
```
az storage fs file create \
    -p myfile \
    -f myfilesystem
```

- Create an empty file with specific permissions in ADLS Gen2 file system
```
az storage fs file create \
    -p mydir/myfile \
    -f myfilesystem \
    --permissions rwxrwx---
```

##### Show the properties of a file in ADLS Gen2 file system
```
az storage fs file show \
    -p myfile \
    -f myfilesystem
```

##### Append data to a file in ADLS Gen2 file system
```
az storage fs directory append \
    --content "testdata" \
    -p myfile \
    -f myfilesystem
```

##### Upload a file to ADLS Gen2 file system
- Upload a file to ADLS Gen2 file system
```
az storage fs directory upload \
    -s "src.txt" \
    -p mydir/myfile \
    -f myfilesystem
```

- Upload a file with specific permissions to ADLS Gen2 file system
```
az storage fs directory upload \
    -s "src.txt" \
    -p myfile \
    -f myfilesystem \
    --permissions rwxrwxrwx
```

##### Download a file in ADLS Gen2 file system
- Download a file from ADLS Gen2 file system
```
az storage fs directory download \
    -p myfile \
    -f myfilesystem
```

- Download a file to the specified path from ADLS Gen2 file system
```
az storage fs directory download \
    -p myfile \
    -f myfilesystem \
    -d dir/mylocalfile
```

##### List files and directories in ADLS Gen2 file system
- List files and directories in ADLS Gen2 file system
```
az storage fs file list \
    -f myfilesystem
```

- List files and directories under the specified path in ADLS Gen2 file system
```
az storage fs file list \
    -f myfilesystem \
    --path mydir
```

- List only files in ADLS Gen2 file system
```
az storage fs file list \
    -f myfilesystem \
    --exclude-dir
```

##### Move a file to a new path in  ADLS Gen2 account

- Move a file "myfile" to "mydir/mynewfile" in the same file system "myfilesystem"

```
az storage fs file move \
    -p myfile \
    -f myfilesystem \
    -new-path "myfilesystem/mydir/mynewfile"
```

- Move a file "mydir/myfile" to another file system "mynewfilesystem" with name "mynewfile"

```
az storage fs file move \
    -p mydir/myfile \
    -f myfilesystem \
    -new-path "mymewfilesystem/mynewfile"
```

##### Delete a file in ADLS Gen2 file system
- Delete a file with prompt message
```
az storage fs file delete \
    -p mydir/myfile \
    -f myfilesystem 
```

- Delete a file without prompt message
```
az storage fs file delete \
    -p myfile \
    -f myfilesystem \
    -y
```

##### Manage metadata for file in ADLS Gen2
- Set user-defined metadata for the specified file as one or more name-value pairs.
```
az storage fs file metadata uptdate \
    --metdata tag1=value1 tag2=value2 \
    -p myfile \
    -f myfilesystem
```

- Show all user-defined metadata for the specified file.
```
az storage fs directory metadata show -p myfile -f myfilesystem
```
  
#### Manage Access in Azure Data Lake Storage Gen2 file system.
```
❯ az storage fs access -h

Group
    az storage fs access : Manage file system access and permissions for Azure Data Lake Storage Gen2 account.
        Command group 'storage fs' is in preview. It may be changed/removed in a future
        release.
Commands:
    remove-recursive : Remove the Access Control on a path and sub-paths in Azure Data Lake Storage Gen2 account.
    set              : Set the access control properties of a path(directory or file) in Azure Data Lake Storage Gen2 account.
    set-recursive    : Set the Access Control on a path and sub-paths in Azure Data Lake Storage Gen2 account.
    show             : Show the access control properties of a path (directory or file) in Azure Data Lake Storage Gen2 account.
    update-recursive : Modify the Access Control on a path and sub-paths in Azure Data Lake Storage Gen2 account.
```

##### Set access control list of a path
- Set access control list for a directory
```
az storage fs access set \
    -a "user::rwx,group::r--,other::---" \
    -p mydir \
    -f myfilesystem
```

- Set access control list for a file
```
az storage fs access set \
    -a "user::rwx,group::r--,other::---" \
    -p mydir/myfile \
    -f myfilesystem
```
##### Set permissions of a path
- Set permissions for a directory
```
az storage fs access set \
    --permissions rwxrwxrwx \
    -p mydir \
    -f myfilesystem
```

- Set permissions for a file
```
az storage fs access set \
    --permissions rwxrwxrwx \
    -p mydir/myfile \
    -f myfilesystem
```

##### Set owning user of a path
- Set owning user for a directory
```
az storage fs access set \
    --owner example@microsoft.com \
    -p mydir \
    -f myfilesystem
```

- Set owning user for a file
```
az storage fs access set \
    --owner example@microsoft.com \
    -p mydir/myfile \
    -f myfilesystem
```

##### Set owning group of a path
- Set owning group for a directory
```
az storage fs access set \
    --group 68390a19-a897-236b-b453-488abf67b4dc \
    -p mydir \
    -f myfilesystem
```

- Set owning group for a file
```
az storage fs access set \
    --group 68390a19-a897-236b-b453-488abf67b4dc \
    -p mydir/myfile \
    -f myfilesystem
```

##### Show access control properties of a path in ADLS Gen2 account
- Show access control properties of a directory
```
az storage fs access show \
    -p mydir \
    -f myfilesystem
```

- Show access control properties of a file
```
az storage fs access show \
    -p myfile \
    -f myfilesystem
```

##### Set the Access Control on a path and sub-paths
- Set the Access Control on a path and sub-paths
```
az storage fs access set-recursive \
    --acl "default:user:[id]:rwx"\
    -p mydir \
    -f myfilesystem
```

##### Modify the Access Control on a path and sub-paths
- Modify the Access Control on a path and sub-paths
```
az storage fs access update-recursive \
    --acl "user::r-x"\
    -p mydir \
    -f myfilesystem
```

##### Remove the Access Control on a path and sub-paths
- Remove the Access Control on a path and sub-paths
```
az storage fs access remove-recursive \
    --acl "default:user:21cd756e-e290-4a26-9547-93e8cc1a8923"\
    -p mydir \
    -f myfilesystem
```
