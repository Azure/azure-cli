Authoring Command Modules
=========================

The document provides instructions and guidelines on how to author command modules. For other help, please see the following:

**On-boarding Guide**:<br>https://github.com/Azure/azure-cli/blob/dev/doc/onboarding_guide.md

**Module Authoring**:<br>You are here!

**Command Authoring**:<br>https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/authoring_commands.md

**Command Guidelines**:<br>https://github.com/Azure/azure-cli/blob/dev/doc/command_guidelines.md

**Help Authoring**:<br>https://github.com/Azure/azure-cli/blob/dev/doc/authoring_help.md

**Test Authoring**:<br>https://github.com/Azure/azure-cli/blob/dev/doc/authoring_tests.md

**Generating Documentation**:<br>https://review.docs.microsoft.com/help/onboard/admin/reference/cli/azure-cli-ci?branch=master#documenting-a-new-azure-cli-module

<a name="heading_set_up"></a>Set Up
------

Create your dev environment if you haven't already. This is how to do that.  

Clone the repo, enter the repo directory then create your virtual environment.  

For example:
```
git clone https://github.com/Azure/azure-cli.git
git clone https://github.com/Azure/azure-cli-extensions.git
python -m venv env
source env/bin/activate
azdev setup -c azure-cli -r azure-cli-extensions
```
For more information, see https://github.com/Azure/azure-cli-dev-tools#setting-up-your-development-environment.

After this, you should be able to run the CLI with `az`.

[Author your command module...](#heading_author_command_mod)

If your command module contributes any commands, they should appear when running `az`.
If your commands aren't showing with `az`, use `az --debug` to help debug. There could have been an exception
thrown whilst attempting to load your module.


<a name="heading_author_command_mod"></a>Authoring command modules
------

There are two options to initialize a command module:
1. Use [Azure CLI Code Generator tool](https://github.com/Azure/autorest.az#how-does-azure-cli-code-generator-work) to generate code automatically.
2. [Create a module with `azdev cli create`](https://azurecliprod.blob.core.windows.net/videos/04%20-%20AzdevCliCreate.mp4).

**Create an \_\_init__.py for your module**

In the \_\_init__ file, you will declare a command loader class that inherits from AzCommandsLoader. You will typically override the following three methods:
  - `__init__` - Useful for setting metadata that applies to the entire module. For performance reasons, no heavy processing should be done here. See command authoring for more info.
  - `load_commands_table` - Register command groups and commands here. It is common to store the implementation of this method in
                            a file named `commands.py` but for very small modules this may not be necessary. See command authoring for
                            more info.
  - `load_arguments` - Apply metadata to your command arguments. It is common to store the implementation of this method in a file 
                       named `_params.py` but for very small modules this may not be necessary. See command authoring for more info.

**__init__.py**
```Python
from azure.cli.core import AzCommandsLoader
from azure.cli.command_modules.mymod._help import helps  # pylint: disable=unused-import

class MyModCommandsLoader(AzCommandsLoader):

    def load_command_table(self, args):
      from azure.cli.core.commands import CliCommandType

      mymod_custom = CliCommandType(
        operations_tmpl='azure.mgmt.mymod.operations#MyModOperations.{}',
      )

      with self.command_group('myfoo', mymod_custom) as g:
        g.command('create', 'create_myfoo')

COMMAND_LOADER_CLS = MyModCommandsLoader
```

**custom.py**
```python
def create_myfoo(cmd, myfoo_name, resource_group_name, location=None):
    from azure.mgmt.example.models import MyFoo
    from azure.cli.command_modules.example._client_factory import cf_mymod
    client = cf_mymod(cmd.cli_ctx)

    foo = MyFoo(location=location)
    return client.create_or_update(myfoo_name, resource_group_name, foo)
```

The snippet above shows what it takes to author a basic command.
1. Create a CliCommandType which holds the metadata for your command. 
2. Create a command group in which your command will exist, passing the command type created in the previous step.
3. Register your command with the `command` method, defining first the name of the command and then the name of the method which will execute.
4. Define the callable that will execute:
    The CLI inspects the callable to determine required params, defaults and help text and more.  
    Try out the example to see these in action!

When running the command with the `--help` flag, you should see the command.
You can also now execute the command for yourself.
```
$ az myfoo create --help

Command
    az myfoo create

Arguments
    --myfoo-name          [Required]: The argument that is required.
    --resource-group-name [Required]: Also required.
    --location                      : Optional arg.
...

$ az myfoo create --myfoo-name foo --resource-group-name myrg
{
  "name": "foo",
  "resourceGroup": "myrg",
  "location": None
}
```

Testing
-------

Discover tests

```
azdev test --discover
```

Run all tests in a module:

```
azdev test MODULE [--live] [--series] [--discover] [--dest-file FILENAME]
```

Run an individual test:

```
azdev test TEST [TEST ...] [--live] [--series] [--discover] [--dest-file FILENAME]
```
For example `azdev test test_myfoo`

Run a test when there is a conflict (for example, both 'azure-cli-core' and 'azure-cli-network' have 'test_foo'):
```
azdev test MODULE.TEST [--live]
```

The list of failed tests are displayed at the end of a run and dumped to the file specified with `--dest-file` or `test_failures.txt` if nothing is provided. This allows for conveniently replaying failed tests:

```
azdev test --src-file test_failures.txt [--live] [--series] [--discover]
```

Relying on the default filename, the list of failed tests should grow shorter as you fix the cause of the failures until there are no more failing tests.

Style Checks
------------

```
azdev style --module <module> [--pylint] [--pep8]
```

Submitting Pull Requests
------------------------

### Format PR Title

History notes are auto-generated based on PR titles and descriptions starting from [S165](https://github.com/Azure/azure-cli/milestone/82). Starting from 01/30/2020, we require all the PR titles to follow the below format:
1. [**Mandatory**] Each PR title **MUST** start with `[Component Name]` or `{Component Name}`. 
    * `Component Name` shall be replaced by the real ones such as `Storage`, `Compute`. It could be the name of a command module, but in title case with necessary spaces for better readability, such as `API Management`, `Managed Service`. Other possible component names include but are not limited to: `Packaging`, `Misc.`, `Aladdin`.
    * `[]` means this change is customer-facing and the message will be put into `HISTORY.rst`. `{}` means this change is not customer-facing and the message will **NOT** be included in `HISTORY.rst`.
    * If the component name is `Core`, the message will be written in `src/azure-cli-core/HISTORY.rst`. Otherwise, the message will be written in `src/azure-cli/HISTORY.rst`.
2. [**Mandatory**] If it's a breaking change, the second part should be `BREAKING CHANGE` followed by a colon. In the case of hotfix, put `Hotfix` in this part. If it's related to fixing an issue, put `Fix #number` in this part. For other cases, this part could be empty.
3. [**Recommendation**] If the change can be mapped into a command, then the next part could be the command name starting with `az`, followed by a colon.
4. [**Recommendation**] Use the right verb with **present-tense** in **base form** and **capitalized first letter** to describe what is done:
    * **Add** for new features.
    * **Change** for changes in existing functionality.
    * **Deprecate** for once-stable features removed in upcoming releases.
    * **Remove** for deprecated features removed in this release.
    * **Fix** for any bug fixes.

Examples of customer-facing change PR title:

> [Storage] BREAKING CHANGE: az storage remove: Remove --auth-mode argument  
> [ARM] Fix #10246: az resource tag crashes when the parameter --ids passed in is resource group ID

An example of non-customer-facing change PR title:

> {Aladdin} Add help example for dns

### Format PR Description

Please follow the instruction in the PR template to provide a description of the PR and the testing guide if possible. 

If you would like to write multiple history notes for one PR or overwrite the message in the PR title as a history note, please write the notes under `History Notes` section in the PR description, following the same format described above. The PR template already contains the history note template, just change it if needed. In this case, the PR title could be a summary of all the changes in this PR and will not be put into `HISTORY.rst` in our pipeline. The PR title still needs to start with `[Component Name]`. You can delete the `History Notes` section if not needed.

### Hotfix PR
Step 1: Create a hotfix branch based on `release` branch, then submit a PR to merge the hotfix branch into `release`.

In this PR, the second part of the PR title should be `Hotfix`. If you have customer-facing changes, you need to manually modify `HISTORY.rst` to add history notes. The auto-generated history notes for the next regular release will ignore the PR that contains `Hotfix`.

An example title of hotfix change PR:

> {Packaging} Hotfix: Fix dependency error

Step 2: After the hotfix version is released, submit a PR to merge `release` branch back to `dev` (e.g. [#15505](https://github.com/Azure/azure-cli/pull/15505)).

⚠ Do **NOT** squash merge this PR. After the PR gets approved by code owners, merge `release` to `dev` by creating a **merge commit** on your local machine, then push `dev` to upstream repository. The PR will automatically be marked as **Merged**.
