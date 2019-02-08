# Azure CLI Help System #

Help authoring for commands is done in a number of places, all of which are contained in the Az code base.  Some help text comes from product code, but it can be overridden using a YAML-based help authoring system.  The YAML-based system is the recommended way to update command and group help text.

## YAML Help Authoring ##

The YAML syntax is described [here](http://www.yaml.org/spec/1.2/spec.html "here").

To override help for a given command:

1. Find the command's module, Example "az account clear".
	1. Search code base for "account clear".
	2. Search result: src/command_modules/azure-cli-**profile**/azure/cli/command_modules/**profile**/commands.py.
	3. Result shows "account clear" is in the "profile" module.
2. Using the module name, find the YAML help file which follows the path pattern.:
	1.  src/command_modules/azure-cli-**[module name]**/azure/cli/command_modules/**[module name]**/_help.py<br>
	    **or** <br>
	    src/command_modules/azure-cli-**[module name]**/azure/cli/command_modules/**[module name]**/help.yaml
	2.  If the file doesn't exist, it can be created.
3.  Find or create a help entry with the name of the command/group you want to document.  See example below.


>  ###Notes: <br>
>  1. If using **_help.py** files for help authoring, the command module's **\_\_init\_\_.py** file must import the **_help.py** file. i.e: <br>
>    `import azure.cli.command_modules.examplemod._help` <br>
>  2. The Help Authoring System now supports **help.yaml** files. Eventually, **_help.py** files will be replaced by **help.yaml**.


### Example YAML help file, _help.py ###

<pre>
#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from knack.help_files import helps

#pylint: disable=line-too-long

helps['account clear'] = """
            type: command
            short-summary: Clear account
            long-summary: Longer summary of clearing account
            parameters: 
                - name: --account-name -n
                  type: string
                  short-summary: 'Account name'
                  long-summary: |
                      Longer summary with newlines preserved.  Preserving newlines is helpful for paragraph breaks.
                  populator-commands: 
                    - az account list
                - name: --another-parameter
                  short-summary: These parameter names must match what is shown in the command's CLI help output, including abbreviation.
            examples:
                - name: Collapse whitespace in YAML
                  text: >
                    The > character collapses multiple lines into a single line, which is good for on-screen wrapping.
            """
</pre>

You can also document groups using the same format.

<pre>
helps['account'] = """
            type: group
            short-summary: The account group
            long-summary: Longer summary of account            
            examples:
                - name: Clear an account 
                  text: Description
                - name: Choose your current account
                  text: az account set...
            """
</pre>


### Example YAML help file, help.yaml (Version 1) ###
<pre>
#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

version: 1

content:

- command:
    name: account clear
    summary: Clear account
    description: Longer summary of how the dummy account clear command works
    links:
      - title: Azure Accounts Webpage
        url: https://azure.microsoft.com/en-us/account/
      - url: https://aka.ms/just-a-url
    arguments:
      - name: --account-name
        summary: Account name
        description: |
          Longer summary with newlines preserved.
          Preserving newlines is helpful for paragraph breaks.
        value-sources:
          - link:
              title: List accounts
              command: az account list
          - link:
              title: Show an accounts details
              command: az account show
          - link:
              title: Azure Accounts Webpage
              url: https://azure.microsoft.com/en-us/account/
          - link:
              title: Azure Billing Documentation
              url: https://docs.microsoft.com/en-us/azure/billing/
          - string:
              "Account name should be lower case with no numbers or special symbol."
    examples:
    - summary: Clear an account
      description: >
        This is a longer description of the example.
        The > character collapses multiple lines into a single line,
        which is good for on-screen wrapping.
      command: |
        az account clear --acount-name myaccount

</pre>

You can also document groups using a similar format.

<pre>

- group:
    name: account
    summary: Manage Azure accounts
    description: Longer summary of the account command group
    links:
      - title: Azure Accounts Webpage
        url: https://azure.microsoft.com/en-us/account/
      - url: https://aka.ms/just-a-url
</pre>

# Tips to write effective help for your command

- Make sure the doc contains all the details that someone unfamiliar with the API needs to use the command.
- Examples are worth a thousand words. Provide examples that cover common use cases.
- Don't use "etc". Sometimes it makes sense to spell out a list completely. Sometimes it works to say "like ..." instead of "..., etc".
- Use active voice. For example, say "Update web app configurations" instead of "Updates web app congfigurations" or "Updating web app configurations".
- Don't use highly formal language. If you imagine that another dev sat down with you and you were telling him what he needs to know to use the command, that's exactly what you need to write, in those words.

# Testing Authored Help #

To verify the YAML help is correctly formatted, the command/group's help command must be executed at runtime.  For example, to verify "az account clear", run the command "az account clear -h" and verify the text.  

Runtime is also when help authoring errors will be reported, such as documenting a parameter that doesn't exist.  Errors will only show when the CLI help is executed, so verifying the CLI help is required to ensure your authoring is correct.   

# Other Help Authoring #

Commands without YAML usually still have help text.  Where does it come from?  These sections briefly outline where Az help text comes from.

Authoring note: it is not recommended to use the product code to author command/group help--YAML is the recommended way (see above).  This information is provided for completeness and may be useful for fixing small typos in existing help text.

## Help Layers ##

Command help starts with its raw SDK docstring text, if available.  Non-SDK commands may have their own docstring.  Code can specify values that replace the SDK/docstring contents.  YAML is the final override for help content and is the recommended way for authoring command and group help.  Note that group help can only be authored via YAML.  

Here are the layers of Project Az help, with each layer overriding the layer below it:

| Help Display                  |
|-------------------------------|
| YAML Authoring via *help.yaml*|
| YAML Authoring via *_help.py* |
| Code Specified                |
| Docstring                     |
| SDK Text                      |

## Page titles for command groups ##

Page titles for your command groups as generated from the source are simply the command syntax, "az vm", but we use friendly titles on the published pages - "Virtual machines - az vm". To do that, ee add the friendly part of the page title to [titlemapping.json](https://github.com/Azure/azure-docs-cli/blob/master/titleMapping.json) in the azure-docs-cli repo. When you add a new command group, make sure to update the mapping.

## Profile specific help ##

The CLI supports multiple profiles. Help can be authored to take advantage of this.  
Commands available, arguments, descriptions and examples all change dynamically based on the profile in use.

The `az cloud update --profile ...` command allows you to switch profiles.  
You can see an example of this by switching profiles and running `az storage account create --help`.

---

Below is some documentation on taking advantage of this in your YAML help files.

In your YAML files, the same `short-summary` and `long-summary` is used for all profiles.

For the command parameters section, any parameters not used by a profile will be ignored and not displayed.

For command examples, you optionally specify the profile the example is for with the `min_profile` and `max_profile` options.

Here's a samply for `storage account create`:  
The first example is only supported on the profile `latest` and above whilst the second example if only supported on `2017-03-09-profile` and below.

### _help.py

```
    examples:
        - name: Create a storage account MyStorageAccount in resource group MyResourceGroup in the West US region with locally redundant storage.
          text: az storage account create -n MyStorageAccount -g MyResourceGroup -l westus --sku Standard_LRS
          min_profile: latest
        - name: Create a storage account MyStorageAccount in resource group MyResourceGroup in the West US region with locally redundant storage.
          text: az storage account create -n MyStorageAccount -g MyResourceGroup -l westus --account-type Standard_LRS
          max_profile: 2017-03-09-profile
```

### help.yaml

```
    examples:
        - summary: Create a storage account MyStorageAccount in resource group MyResourceGroup in the West US region with locally redundant storage.
          command: az storage account create -n MyStorageAccount -g MyResourceGroup -l westus --sku Standard_LRS
          min_profile: latest
        - summary: Create a storage account MyStorageAccount in resource group MyResourceGroup in the West US region with locally redundant storage.
          command: az storage account create -n MyStorageAccount -g MyResourceGroup -l westus --account-type Standard_LRS
          max_profile: 2017-03-09-profile
```

Here is how this looks in CLI `--help`:

On profile `latest`.
```
Examples
    Create a storage account MyStorageAccount in resource group MyResourceGroup in the West US
    region with locally redundant storage.
        az storage account create -n MyStorageAccount -g MyResourceGroup -l westus --sku
        Standard_LRS
```

On profile `2017-03-09-profile`.
```
Examples
    Create a storage account MyStorageAccount in resource group MyResourceGroup in the West US
    region with locally redundant storage.
        az storage account create -n MyStorageAccount -g MyResourceGroup -l westus --account-type
        Standard_LRS
```

## Online Reference Documentation ##

The help that you author above will be available online as reference documentation.

https://docs.microsoft.com/en-us/cli/azure/reference-index

If you are not satisfied with the heading that is automatically provided, please create a PR to update the following file:

https://github.com/Azure/azure-docs-cli/blob/master/titleMapping.json
