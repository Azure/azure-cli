Publishing
==========

Once you have your `.whl`, share that as you wish.

For example, you could upload it to Azure Blob storage and share the download link with your users.

Then, users can then install it with the `--source` argument.

`az extension add --source https://contoso.com/myextension.whl`.

Alternatively, you can add the extension to the index so it is available with these CLI commands:
- `az extension add --name NAME` - Allows users to add an extension by name
- `az extension list-available` - Allows users to list the available extensions in the index
- `az extension update --name NAME` - Allows users to update an extension

If you would like to make it publicly available in the index, see [extensions index.json](https://github.com/Azure/azure-cli-extensions#about-indexjson).
