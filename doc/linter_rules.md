# Azure CLI Linter Rule Summary #
This document lists the set of linter rules that would be applied to each PR in CI system.

## Index
* [Severity]()

## Severity

## Linter Rules

#### Command Group Rules
#### Command Rules
#### Help Rules
#### Parameter Rules

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