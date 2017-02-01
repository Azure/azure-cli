# Project AZ Help System #

Help authoring for commands is done in a number of places, all of which are contained in the Az code base.  Some help text comes from product code, but it can be overridden using a YAML-based help authoring system.  The YAML-based system is the recommended way to update command and group help text.

## YAML Help Authoring ##

The YAML syntax is described [here](http://www.yaml.org/spec/1.2/spec.html "here").

To override help for a given command:

1. Find the command's module, Example "az account clear".
	1. Search code base for "account clear".
	2. Search result: src/command_modules/azure-cli-**profile**/azure/cli/command_modules/**profile**/commands.py.
	3. Result shows "account clear" is in the "profile" module.
2. Using the module name, find the YAML help file which follows the path pattern:
	1.  src/command_modules/azure-cli-**[module name]**/azure/cli/command_modules/**[module name]**/_help.py.
	2.  If the file doesn't exist, it can be created.
3.  Find or create a help entry with the name of the command/group you want to document.  See example below.

### Example YAML help file, _help.py ###

<pre>
#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.help_files import helps

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
                  - These indicate where values can be retrieved for input to this command
                - name: --another-parameter
                  short-summary: These parameter names must match what is shown in the command's CLI help output, including abbreviation.
            examples:
                - name: Document a parameter that doesn't exist
                  text: >
                    You will get an error when you show help for the command stating there is an extra parameter.
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

# Tips to write effective help for your command

- Make sure the doc contains all the details that someone unfamiliar with the API needs to use the command.
- Examples are worth a thousand words. Provide examples that cover common use cases.
- Don't use "etc". Sometimes it makes sense to spell out a list completely. Sometimes it works to say "like ..." instead of "..., etc".
- The short summary for a group should start with "Commands to...".
- Use active voice. For example, say "Update web app configurations" instead of "Updates web app congfigurations" or "Updating web app configurations".
- Refer to the CLI as "Azure CLI 2.0 (Preview)". We'll drop "(Preview)" when the CLI GAs.
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

| Help Display   |
|----------------|
| YAML Authoring |
| Code Specified |
| Docstring      |
| SDK Text       |

## Page titles for command groups ##

Page titles for your command groups as generated from the source are simply the command syntax, "az vm", but we use friendly titles on the published pages - "Virtual machines - az vm". To do that, ee add the friendly part of the page title to [titlemapping.json](https://github.com/Azure/azure-docs-cli-python/blob/master/titleMapping.json) in the azure-docs-cli-python repo. When you add a new command group, make sure to update the mapping.
