GitHub Codespace is a great option for developers who prefer to work in containerized cloud environments and avoid installing tools or dependencies locally.

## Create a codespace
1. In your browser, navigate to the [Official Repository of Azure CLI](https://github.com/Azure/azure-cli).
2. Above the file list, click **Code** > **Codespaces** > **Create codespace on dev**.
![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/codespace_entry.png)

## Authenticate with GitHub
Once codespace is created (takes a while), you will see the following prompt in the integrated terminal:
![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/codespace_login.png)

It helps login to your GitHub account interactively; after logging in, you won't need to do it again in a fresh terminal:
![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/codespace_logged.png)

Furthermore, all dependencies will be installed automatically, and once a similar prompt appears, you can start development:
```commandline
Elapsed time: 3m 26s.

Finished setup! Please launch the codegen tool via: aaz-dev run
```

## Introduction to development workflow
Once the environment is set up, you can proceed with the standard development process of Azure CLI.

**Generate Azure CLI module in seconds!** E.g.,
```bash
aaz-dev cli generate --spec chaos --module chaos
```
It will convert the specification from https://github.com/Azure/azure-rest-api-specs/tree/main/specification/chaos
 into an Azure CLI module named `chaos`.

> Generate code effortlessly. If the result isn't what you expected, use the UI to fine-tune it.

### Prune command-line interface
Typically, the interface generated directly from the specification isn’t ideal. You can refine it in the [Workspace Editor](https://azure.github.io/aaz-dev-tools/pages/usage/workspace-editor/) to make it meet our requirements. You can open or create a workspace at:
![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/codespace_workspace_editor_1.png)

If everything is selected correctly, you will be redirected to the following UI. You can interactively edit our ideal command line interface based on that:
![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/codespace_workspace_editor_2.png)

When you have completed all the editing in Workspace Editor and clicked EXPORT in its upper right corner. It's ready to switch to [CLI Generator](https://azure.github.io/aaz-dev-tools/pages/usage/cli-generator/) to generate code of Azure CLI:
1. You need to select the target for generating code. If you don't know where to generate the code, usually Azure CLI Extension is all you need:
    ![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/codespace_cli_generator_1.png)
2. You can find the commands that you modified before in the following UI. Check the corresponding checkboxes, then click GENERATE in the upper right corner, and the code will be generated:
    ![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/codespace_cli_generator_2.png)

### Implement custom logic (optional)
Sometimes, the generated code may not fully meet the requirements. In such cases, you'll need to make some customizations based on it. This process can be relatively complex, so please refer to the [relevant documentation](https://azure.github.io/aaz-dev-tools/pages/usage/customization/).

### Test via real-world scenarios
You understand your test scenarios best. Please refer to the [relevant documentation](https://azure.github.io/aaz-dev-tools/pages/usage/command-usage-testing/) to author your own tests.

### Provide meaningful examples
While the codegen tool provides some initial examples, their quality directly impacts the quality of future documentation. Therefore, you should strive for continuous improvement. Please refine your command examples in the Workspace Editor.

Once everything is ready, you can raise pull requests in [Azure/azure-cli-extensions](https://github.com/Azure/azure-cli-extensions) and [Azure/aaz](https://github.com/Azure/aaz).
