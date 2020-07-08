# Azure CLI Linter Rule Summary #
This document lists the set of linter rules that would be applied to each PR in CI system.

## Index
* [Severity](#severity)
* [Linter Rules](#linter-rules)
* [Contributions](#contributions)
* [Rule Descriptions](#rule-descriptions)

## Severity
Linter rule has three kinds of severity: High, Medium and Low.

Rule with **high** severity is mandatory and must be passed in a PR. If you want bypass this linter rule, please contact corresponding reviewer or contact [AzCLIDev](AzCLIDev@microsoft.com).

Rule with **medium** severity is not mandatory for a PR. But we recommend author following the guidance since they are best practice for Azure CLI.

Rule with **low** severity is not mandatory for a PR. We use this severity as reminder or we are just onboarding this rule and do some tests.

## Linter Rules
#### Command Group Rules

| Id | Rule Name | Severity |
| --- | --- | --- |
| [R1001](#r1001) | [Missing Group Help](#r1001) | High |
| [R1002](#r1002) | [Expired Command Group](#r1002) | High |
| [R1003](#r1003) | [Require Wait Command If No Wait](#r1003) | Medium |

#### Command Rules

| Id | Rule Name | Severity |
| --- | --- | --- |
| [R2001](#r2001) | [Missing Command Help](#r2001) | High |
| [R2002](#r2002) | [No --ids For List Commands](#r2002) | High |
| [R2003](#r2003) | [Expired Command](#r2003) | High |
| [R2004](#r2004) | [Delete Command Should Have Confirmation](#r2004) | Low |

#### Parameter Rules

| Id | Rule Name | Severity |
| --- | --- | --- |
| [R3001](#r3001) | [Missing Parameter Help](#r3001) | High |
| [R3002](#r3002) | [Expired Parameter](#r3002) | High |
| [R3003](#r3003) | [Expired Parameter Option](#r3003) | High |
| [R3004](#r3004) | [Bad Short Option](#r3004) | High |
| [R3005](#r3005) | [Parameter Should Not End In Resource Group](#r3005) | High |
| [R3006](#r3006) | [No Positional Parameters](#r3006) | High |
| [R3007](#r3007) | [No Parameter Defaults For Update Commands](#r3007) | High |
| [R3008](#r3008) | [No Required Location Parameter](#r3008) | Medium |
| [R3009](#r3009) | [Id Parameters Only For GUID](#r3009) | Low |

#### Help Rules

| Id | Rule Name | Severity |
| --- | --- | --- |
| [R4001](#r4001) | [Unrecognized Help Entry](#r4001) | High |
| [R4002](#r4002) | [Faulty Help Type](#r4002) | High |
| [R4003](#r4003) | [Expired Parameter Option](#r4003) | High |
| [R4004](#r4004) | [Faulty Help Example](#r4004) | High |
| [R4005](#r4005) | [Faulty Help Example Parameters](#r4005) | High |


## Contributions
To onboard a new rule, generally we need the following steps.
- Propose a new rule and have an internal discussion.
- Develop the rule and open a PR.
- Review the PR and get approval.
- Exclude or fix all existing commands which violate the new rule in both [Azure/azure-cli](https://github.com/Azure/azure-cli) and [Azure/azure-cli-extensions](https://github.com/Azure/azure-cli-extensions)
- Merge the PR and release new version of azdev.

Better to make new rule in Medium or Low severity first and collect some telemetry to see whether we need this rule as high or not.

## Rule Descriptions

### <a name="r1001" />R1001 Missing Group Help
**Category** : Command Group

**Severity** : High

**Output Message**: Command-Group: `{command_group}` - Missing help.

**Description**: Each command group must have help message.

**Why the rule is important**: For better user experience, each command group must have help message.

**How to fix the violation**: Add help message into help file for this command group.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r1002" />R1002 Expired Command Group
**Category** : Command Group

**Severity** : High

**Output Message**: Command-Group: `{command_group}` - Deprecated command group is expired and should be removed.

**Description**: If this command group has been deprecated and expired, it should be removed.

**Why the rule is important**: User might cannot use the deprecated command which is expired. It's deprecated by design and they should not appear to users.

**How to fix the violation**: Remove the command group and all related codes.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r1003" />R1003 Require Wait Command If No Wait
**Category** : Command Group

**Severity** : Medium

**Output Message**: Command-Group: `{command_group}` - Group does not have a 'wait' command, yet `{command}` exposes `--no-wait`.

**Description**: If one command in this command group exposes `--no-wait`, there should be a `wait` command for customers.

**Why the rule is important**: If customers can call a command in async mode and use `--no-wait`, they need the `wait` command to wait for the final result of the previous command.

**How to fix the violation**: Add wait command into this command group.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r2001" />R2001 Missing Command Help
**Category** : Command

**Severity** : High

**Output Message**: Command: `{command}` - Missing help.

**Description**: Each command must have help message.

**Why the rule is important**: For better user experience, each command must have help message.

**How to fix the violation**: Add help message into help file for this command.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r2002" />R2002 No --ids For List Commands
**Category** : Command

**Severity** : High

**Output Message**: Command: `{command}` - List commands should not expose --ids argument.

**Description**: List command should not expose `--ids` argument

**Why the rule is important**: Usually `list` command would list all resources under one resource group or subscription. `--ids` is used for parallel executions. It doesn't make sense to expose `--ids` for `list` command.

**How to fix the violation**: Set all parameter's `id_part=None` for `list` command.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r2003" />R2003 Expired Command
**Category** : Command

**Severity** : High

**Output Message**: Command: `{command}` - Deprecated command is expired and should be removed.

**Description**: If this command has been deprecated and expired, it should be removed.

**Why the rule is important**: User might cannot use the deprecated command which is expired. It's deprecated by design and they should not appear to users.

**How to fix the violation**: Remove the command and all related codes.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r2004" />R2004 Delete Command Should Have Confirmation
**Category** : Command

**Severity** : Low

**Output Message**: Command: `{command}` - If this command deletes a collection, or group of resources. Please make sure to ask for confirmation.

**Description**: If this command has been deprecated and expired, it should be removed.

**Why the rule is important**: User might cannot use the deprecated command which is expired. It's deprecated by design and they should not appear to users.

**How to fix the violation**: Remove the command and all related codes.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r3001" />R3001 Missing Parameter Help
**Category** : Parameter

**Severity** : High

**Output Message**: Parameter: `{parameter}` - Missing help.

**Description**: Each parameter must have help message.

**Why the rule is important**: For better user experience, each parameter must have help message.

**How to fix the violation**: Add help message into help file for this parameter.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r3002" />R3002 Expired Parameter
**Category** : Parameter

**Severity** : High

**Output Message**: Parameter: `{parameter}` - Deprecated parameter is expired and should be removed.

**Description**: If this parameter has been deprecated and expired, it should be removed.

**Why the rule is important**: User might cannot use the deprecated parameter which is expired. It's deprecated by design and they should not appear to users.

**How to fix the violation**: Remove the parameter and all related codes.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r3003" />R3003 Expired Parameter Option
**Category** : Parameter

**Severity** : High

**Output Message**: Parameter: `{parameter}` - Deprecated options `{options}` are expired and should be removed.

**Description**: If this parameter's option has been deprecated and expired, it should be removed.

**Why the rule is important**: User might cannot use the deprecated parameter's option which is expired. It's deprecated by design and they should not appear to users.

**How to fix the violation**: Remove the parameter's option and all related codes.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r3004" />R3004 Bad Short Option
**Category** : Parameter

**Severity** : High

**Output Message**: Parameter: `{parameter}` - Found multi-character short options: `{options}`. Use a single character or convert to a long-option.

**Description**: Short option(`-s, -n, -g`) should just use a single character.

**Why the rule is important**: It's a common design in Azure CLI. For consistent user experience, short option should just use a single character.

**How to fix the violation**: Use a single character or convert to a long-option.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r3005" />R3005 Parameter Should Not End In Resource Group
**Category** : Parameter

**Severity** : High

**Output Message**: Parameter: `{parameter}` - A command should only have `--resource-group` as its resource group parameter. However options `{options}` in command `{command}` end with `resource-group` or similar.

**Description**: Parameter should not end in `--resourge-group`, `resourcegroup` or `resource-group-name` except for `--resource-group` argument.

**Why the rule is important**: It's a common design in Azure CLI. Other kinds of resource group doesn't make sense to users.

**How to fix the violation**: Parameter's name should be re-design.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r3006" />R3006 No Positional Parameters
**Category** : Parameter

**Severity** : High

**Output Message**: Parameter: `{parameter}` - CLI commands should have optional parameters instead of positional parameters. However parameter `{parameter}` in command `{command}` is a positional.

**Description**: Parameter should not have positional parameters.

**Why the rule is important**: It's a common design in Azure CLI. Positional parameter is reserved for command registration. Positional parameter would cause bad effect on Azure CLI.

**How to fix the violation**: Use optional parameters instead of positional parameters.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r3007" />R3007 No Parameter Defaults For Update Commands
**Category** : Parameter

**Severity** : High

**Output Message**: Parameter: `{parameter}` - Update commands should not have parameters with default values. Parameter `{parameter}` in command `{command}` has a default value of `{value}`

**Description**: Update commands should not have parameters with default values.

**Why the rule is important**: If users don't input this argument, it represents that users don't want to change this property. But default value would violate users' willing and change the property implicitly.

**How to fix the violation**: Remove the default value and set it to None

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r3008" />R3008 No Required Location Parameter
**Category** : Parameter

**Severity** : Medium

**Output Message**: Parameter: `{parameter}` - Location parameters should not be required. However, Parameter `{parameter}` in command `{command}` is required. Please make it optional and default to the location of the resource group.

**Description**: Location parameters should not be required.

**Why the rule is important**: It's a common design in Azure CLI. For better user experience, location parameter should be default to the location of the resource group.

**How to fix the violation**: Use `get_default_location_from_resource_group` to set default value for location parameter.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r3009" />R3009 Id Parameters Only For GUID
**Category** : Parameter

**Severity** : Low

**Output Message**: Parameter: `{parameter}` - Arguments ending with `-id` must be guids/uuids and not resource ids. An option `{option}` ends with `-id`.

**Description**: Arguments ending with `-id` must be guids/uuids and not resource ids.

**Why the rule is important**: It's a common design in Azure CLI. We hope make naming part clear enough.

**How to fix the violation**: Parameter's name should be re-design.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r4001" />R4001 Unrecognized Help Entry
**Category** : Help-Entry

**Severity** : High

**Output Message**:  Help-Entry: `{entry}` - Not a recognized command or command-group.

**Description**: Help entry in help file doesn't exist and not correct.

**Why the rule is important**: It would cause the missing of help message for customers.

**How to fix the violation**: Check the help file and fix the help entry

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r4002" />R4002 Faulty Help Type
**Category** : Help-Entry

**Severity** : High

**Output Message**:  Help-Entry: `{entry}` - Command-group should be of help-type `group` or Command should be of help-type `command`.

**Description**: Help entry and its type are mismatch

**Why the rule is important**: It would cause the missing of help message for customers.

**How to fix the violation**: Check the help file and fix the help type.

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r4003" />R4003 Unrecognized Help Parameter
**Category** : Help-Entry

**Severity** : High

**Output Message**:  Help-Entry: `{entry}` - The following parameter help names are invalid: `{parameter}`

**Description**: Parameter help names don't exist and not correct.

**Why the rule is important**: It would cause the missing of help message for customers.

**How to fix the violation**: Check the help file and fix the parameter help names

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r4004" />R4004 Faulty Help Example
**Category** : Help-Entry

**Severity** : High

**Output Message**:  Help-Entry: `{entry}` - The following example entry indices do not include the command: `{command}`

**Description**: Example entry indices doesn't match this help entry.

**Why the rule is important**: It would cause the missing of help message for customers.

**How to fix the violation**: Check the help file and fix the example entry indices

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)

### <a name="r4005" />R4005 Faulty Help Example Parameters
**Category** : Help-Entry

**Severity** : High

**Output Message**:  Help-Entry: `{entry}` - There is a violation: `{violation_msg}`.

**Description**: Help example doesn't match this command or command group.

**Why the rule is important**: It would cause wrong guidance for customers.

**How to fix the violation**: Check the help file and fix the help example

Links: [Index](#index) | [Severity](#severity) | [Linter Rules](#linter-rules)