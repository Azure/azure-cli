Installing Nightly Builds
=========================

Try out our latest bits with our nightly builds!

Install via pip with:

```shell
    pip install --pre azure-cli --extra-index-url https://azureclinightly.blob.core.windows.net/packages
```

- Builds happen at 21:00:00 PDT each night.
    They are published shortly afterwards.

- Whilst all command modules are built each nightly, not all are are included on install.
    Install additional components with:
    ```shell
        export AZURE_COMPONENT_PACKAGE_INDEX_URL=https://azureclinightly.blob.core.windows.net/packages
        az component update --additional-component <component_name> --private
    ```
    To view the list of installed packages, run `az component list`.

- There is no cURL install link available for nightly builds.
    We recommend creating a virtual environment and running the `pip` command above.

- [Creating a virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/)
