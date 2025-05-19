GitHub Codespace gets you up and coding faster with fully configured, secure cloud development environments native to GitHub.

## Create a codespace
Currently, the dev container is available in [azure-cli-extensions](https://github.com/Azure/azure-cli-extensions), as it's the repository that our contributors mainly contribute to. However, we can still contribute codes to [azure-cli](https://github.com/Azure/azure-cli) based on it.

In the repository of GitHub, we can create a codespace as follows:
![](/doc/assets/dev_container_entry.png)

## Login account of GitHub
Once codespace is started (take a couple of minutes), we will see the following prompt in the integrated terminal:
![](/doc/assets/github_account_login.png)

It will help us log in to our account in an interactive way, after logging in, we don't need to do it again in the fresh terminals:
![](/doc/assets/github_already_login.png)

## Run ./easy_setup
As we can see, Python virtual environment has been automatically activated. We can directly execute the script to setup the development environment:
```bash
$ ./easy_setup
```

Usually the whole process will take several minutes. When the following prompt is displayed, it means the whole setup process has been completed:
![](/doc/assets/dev_container_finished.png)

## Fundamentals of codegen tool
Once the development environment is setup, we can launch the codegen tool via:
```bash
$ aaz-dev run -c azure-cli -e azure-cli-extensions -s azure-rest-api-specs -a aaz
```
> Above 4 parameters are the paths of the repositories, please feel free to modify them if you have other needs, e.g., your swagger source is `azure-rest-api-specs-pr`.

We can refer to the full document of codegen tool at https://azure.github.io/aaz-dev-tools/. However, the following will briefly introduce the 2 pages that we often interact with.

### Workspace Editor
[Workspace Editor](https://azure.github.io/aaz-dev-tools/pages/usage/workspace-editor/) is usually the start page to develop our command modules. We can open or create a workspace at:
![](/doc/assets/codegen_workspace_editor_1.png)

If everything is selected correctly, we will be redirected to the following UI. We can interactively edit our ideal command line interface based on that.
![](/doc/assets/codegen_workspace_editor_2.png)

### CLI Generator
When we have completed all the editing in Workspace Editor and clicked EXPORT in its upper right corner. It's ready to switch to [CLI Generator](https://azure.github.io/aaz-dev-tools/pages/usage/cli-generator/) to generate code of Azure CLI.

First, we need to select the target for generating code. If you don't know where to generate the code, usually Azure CLI Extension is all you need.
![](/doc/assets/codegen_cli_generator_1.png)

Next, we can find the commands that we modified before in the following UI. Check the corresponding checkboxes, then click GENERATE in the upper right corner, and the code will be generated.
![](/doc/assets/codegen_cli_generator_2.png)

> More advanced guides, such as [testing](https://azure.github.io/aaz-dev-tools/pages/usage/command-usage-testing/) and [customization](https://azure.github.io/aaz-dev-tools/pages/usage/customization/), are also explained in the full document.
