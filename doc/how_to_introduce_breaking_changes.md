# How to introduce Breaking Changes in service command

Azure CLI has bi-annual breaking change releases coinciding with Microsoft **Build** and **Ignite**. Limiting breaking changes to twice a year provides a stable experience for customers while being able to keep up to date with the latest versions of Azure CLI and plan accordingly for announced breaking changes.

## Breaking Changes in Azure CLI

A breaking change refers to a modification that disrupts backward compatibility with previous versions. The breaking changes could cause a customer's script or automation written in a previous version to fail.

The common examples of breaking changes include:
* Modifying the names of parameters/commands.
* Modifying the input logic of parameters.
* Modifying the format or properties of result output.
* Modifying the current behavior model.
* Adding additional verification that changes CLI behavior.

To mitigate the impact of breaking changes, Azure CLI delays breaking changes and coordinates half-yearly **Breaking Change Releases** that bundle multiple breaking changes together. This approach helps users plan ahead and adapt to the modifications effectively.

### Breaking Change Window

The breaking change window is a designated sprint that **permits** the merging of service command breaking changes. Any Pull Request merged during this sprint will be included in the subsequent Breaking Change Release.

The timing of the breaking change window in Azure CLI aligns with [Microsoft Build](https://build.microsoft.com/) and [Microsoft Ignite](https://ignite.microsoft.com/). It normally occurs in May for Build and November for Ignite. So please prepare beforehand to align command breaking changes with Azure CLI team accordingly. 

You could find the next Breaking Change Release plan in our [milestones](https://github.com/Azure/azure-cli/milestones).

> It's highlighted that the introduction of breaking changes is typically prohibited within non-breaking-change window, based on what we stated above for consistency and stable tooling experience.
> 
> Exceptions to this policy may be considered under extraordinary circumstances. We understand and would like to help out. There would be high-graded justifications required to provide the info Azure CLI can access.
> 
> Please note that providing the required info for assessment does not mean it will be assured to be green-lighted for breaking changes. Team will still make the decision based on the overall impact.

### Pre-announce Breaking Changes

All breaking changes **must** be pre-announced two sprints ahead Release. It give users the buffer time ahead to mitigate for better command experience. There are two approaches to inform both interactive users and automatic users about the breaking changes.

1. (**Mandatory**) Breaking Changes must be pre-announced through Warning Log while executing.
2. (*Automatic*) Breaking Changes would be collected automatically and listed in [Upcoming Breaking Change](https://learn.microsoft.com/en-us/cli/azure/upcoming-breaking-changes) Document.

## Workflow

### Overview

* CLI Owned Module
  * Service Team should create an Issue that requests CLI Team to create the pre-announcement several sprints ahead Breaking Change Window. The issue should include the label `Breaking Change`. The CLI team will look at the issue and evaluate if it will be accepted in the next breaking change release.
    * Please ensure sufficient time for CLI Team to finish the pre-announcement.
  * The pre-announcement should be released ahead of Breaking Change Window.
* Service Owned Module
  * Service Team should create a Pull Request that create the pre-announcement several sprints ahead Breaking Change Window.
  * The pre-announcement should be released ahead of Breaking Change Window.
* After releasing the pre-announcement, a pipeline would be triggered, and the Upcoming Breaking Change Documentation would be updated.
* At the start of Breaking Change window, the CLI team would notify Service Teams to adopt Breaking Changes.
* Breaking Changes should be adopted within Breaking Change Window. Any unfinished pre-announcements of breaking changes targeting this release will be deleted by the CLI team.

### Pre-announce Breaking Changes

The breaking change pre-announcement must be released at least two sprints before the breaking change itself. It is strongly recommended to follow the best practice of providing the new behavior along with the pre-announcement. This allows customers to take action as soon as they discover the pre-announcement.

We provide several interfaces to pre-announce different types of breaking changes.

To pre-announce breaking changes, such as modifications to default argument values, please add an entry to the `_breaking_change.py` file within the relevant module. If this file does not exist, create `_breaking_change.py` and insert the following lines.

```python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
```

You can then pre-announce breaking changes for different command groups or commands. Multiple breaking changes on the same command are accepted.

```python
from azure.cli.core.breaking_change import register_required_flag_breaking_change, register_default_value_breaking_change, register_other_breaking_change

register_required_flag_breaking_change('bar foo', '--name')
register_default_value_breaking_change('bar foo baz', '--foobar', 'A', 'B')
register_other_breaking_change('bar foo baz', 'During May 2024, another Breaking Change would happen in Build Event.')
```

All related breaking changes will be displayed while executing the command. For example, in the above declarations, the following warnings will be output when executing the command:

```shell
# The azure command
az bar foo baz

# =====Warning output=====
# The argument '--name' will become required in next breaking change release(2.61.0).
# The default value of '--foobar' will be changed to 'B' from 'A' in next breaking change release(2.61.0).
# During May 2024, another Breaking Change would happen in Build Event.
```

There are several types of breaking changes defined in `breaking_change.py`. You should use any of them to declare breaking changes in `_breaking_change.py`.

**Deprecate**

Declaring deprecation in `_breaking_change.py` is similar to deprecation when authoring commands. It is recommended to use this method rather than declaring `deprecate_info` when defining a command or argument. You can use the following method to declare deprecation: 

* `register_command_group_deprecate`: Deprecating a command group. 
* `register_command_deprecate`: Deprecating a command.
* `register_argument_deprecate`: Deprecating an argument or option.

> **Note:** Avoid marking an item with both a deprecation and another breaking change. A command group, command, or argument cannot be deprecated while also undergoing other breaking changes.

They share similar arguments:

* `command_group/command`: The name of the command group or command.
* `argument`: The name of the argument or option to be deprecated. If it is one of the options in `options_list`, the declaration will deprecate the option instead of the entire argument.
* `redirect`: This is the alternative that should be used in lieu of the deprecated thing. If not provided, the item is expected to be removed in the future with no replacement.
* `hide`: Hide the deprecated item from the help system, reducing discoverability, but still allow it to be used. Accepts either the boolean `True` to immediately hide the item or a core CLI version. If a version is supplied, the item will appear until the core CLI rolls to the specified value, after which it will be hidden.
* `target_version`: The version when the deprecated item should be removed. This version will be communicated in all warning messages. The `target_version` is the next breaking change window by default. The deprecated item will still function at the input version.

```python
from azure.cli.core.breaking_change import register_command_group_deprecate, register_command_deprecate, register_argument_deprecate

register_command_group_deprecate('bar', redirect='baz')
# Warning Message: This command group has been deprecated and will be removed in next breaking change release(2.67.0). Use `baz` instead.

register_command_deprecate('bar foo', redirect='baz foo', hide=True)
# Warning Message: This command has been deprecated and will be removed in next breaking change release(2.67.0). Use `baz foo` instead.

register_argument_deprecate('bar foo', '--name', target_version='2.70.0')
# Warning Message: Option `--name` has been deprecated and will be removed in 2.70.0.
```

> Note: The declared deprecation would be transformed into `knack.deprecation.Deprecated` item during runtime. The `tag_func` and `message_func` will remain effective. However, due to the timing of the transformation, the `expiration` will not take effect.

**Remove**

To declare the removal of an item, use the deprecation method instead.

```python
from azure.cli.core.breaking_change import register_argument_deprecate

register_argument_deprecate('bar foo', '--name', target_version='2.70.0')
# Warning Message: Option `--name` has been deprecated and will be removed in 2.70.0.
```

**Rename**

To declare the renaming of an item, use the deprecation method.

```python
from azure.cli.core.breaking_change import register_argument_deprecate

register_argument_deprecate('bar foo', '--name', '--new-name')
# Warning Message: Option `--name` has been deprecated and will be removed in next breaking change release(2.67.0). Use `--new-name` instead.
```

**Output Change**

Declare breaking changes that affect the output of a command. This ensures users are aware of modifications to the command’s output format or content.

* `command`: The name of the command group or command. If it is a command group, the warning would show in the execution of all commands in the group. 
* `description`: The description of the breaking change. The description will display in warning messages.
* `target_version`: The version when the deprecated item should be removed. The `target_version` is the next breaking change window by default.
* `guide`: The guide that customers could take action to prepare for the future breaking change.
* `doc_link`: A link to related documentation, which will be displayed in warning messages.

```python
from azure.cli.core.breaking_change import register_output_breaking_change

register_output_breaking_change('bar foo', description='Reduce the output field `baz`',
                                guide='You could retrieve this field through `az another command`.')
# The output will be changed in next breaking change release(2.61.0). Reduce the output field `baz`. You could retrieve this field through `az another command`.
```

**Logic Change**

Declare breaking changes in the logic of the command.

* `command`: The name of the command.
* `summary`: Summary of the breaking change, which will be displayed in warning messages.
* `target_version`: The version when the breaking change should happen. The `target_version` is the next breaking change window by default.
* `detail`: A detailed description of the breaking change, including the actions customers should take.
* `doc_link`: A link to related documentation, which will be displayed in warning messages.

```python
from azure.cli.core.breaking_change import register_logic_breaking_change

register_logic_breaking_change('bar foo', 'Update the validator', detail='The xxx will not be accepted.')
# Update the validator in next breaking change release(2.61.0). The xxx will not be accepted.
```

**Default Change**

Declare breaking changes caused by changes in default values. This ensures users are aware of modifications to default values.

* `command`: The name of the command.
* `arg`: The name of the argument or one of its options. The default change warning will display whether the argument is used or not.
* `current_default`: The current default value of the argument.
* `new_default`: The new default value of the argument.
* `target_version`: The version in which the breaking change should happen. By default, this is set to the next breaking change window.
* `target`: Use this field to overwrite the argument display in warning messages.
* `doc_link`: A link to related documentation, which will be displayed in warning messages.

```python
from azure.cli.core.breaking_change import register_default_value_breaking_change

register_default_value_breaking_change('bar foo', '--type', 'TypeA', 'TypeB')
# The default value of `--type` will be changed to `TypeB` from `TypeA` in next breaking change release(2.61.0).
```

**Be Required**

Declare breaking changes that will make an argument required in a future release. This ensures users are aware of upcoming mandatory parameters.

* `command`: The name of the command.
* `arg`: The name of the argument that will become required.
* `target_version`: The version in which the argument will become required. By default, this is set to the next breaking change window.
* `target`: Use this field to overwrite the argument display in warning messages.
* `doc_link`: A link to related documentation, which will be displayed in warning messages.

```python
from azure.cli.core.breaking_change import register_required_flag_breaking_change

register_required_flag_breaking_change('bar foo', '--type')
# The argument `--type` will become required in next breaking change release(2.61.0).
```

**Other Changes**

Declare other custom breaking changes that do not fall into the predefined categories. This allows for flexibility in communicating various types of breaking changes to users.

* `command`: The name of the command.
* `message`: A description of the breaking change.
* `arg`: The name of the argument associated with the breaking change. If arg is not None, the warning message will only be displayed when the argument is used.
* `target_version`: The version in which the breaking change will occur. By default, this is set to the next breaking change window. This value won't display in warning message but is used to generate upcoming breaking change document.

```python
from azure.cli.core.breaking_change import register_other_breaking_change

register_other_breaking_change('bar foo', 'During May 2024, another Breaking Change would happen in Build Event.')
# During May 2024, another Breaking Change would happen in Build Event.
```

**Conditional Breaking Change**

To enhance flexibility, the CLI supports using a designated tag to specify a Breaking Change Pre-announcement. This method avoids reliance on the default automatic warning display and allows the warning to be shown whenever `print_manual_breaking_change` is called.

**Note:** We strongly recommend using this method to display breaking change warnings under specific conditions instead of using `logger.warning` directly. This approach enables centralized documentation of breaking changes and assists in automating customer notifications.

```python
# src/azure-cli/azure/cli/command_modules/vm/custom.py
from azure.cli.core.breaking_change import register_conditional_breaking_change, AzCLIOtherChange

register_conditional_breaking_change(tag='SpecialBreakingChangeA', breaking_change=(
  'vm create', 'This is special Breaking Change Warning A. This breaking change is happend in "vm create" command.'))
register_conditional_breaking_change(tag='SpecialBreakingChangeB', breaking_change=(
  'vm', 'This is special Breaking Change Warning B. This breaking change is happend in "vm" command group.'))


# src/azure-cli/azure/cli/command_modules/vm/custom.py
def create_vm(cmd, vm_name, **):
  from azure.cli.core.breaking_change import print_conditional_breaking_change
  if some_condition:
    print_conditional_breaking_change(cmd.cli_ctx, tag='SpecialBreakingChangeA', custom_logger=logger)
    print_conditional_breaking_change(cmd.cli_ctx, tag='SpecialBreakingChangeB', custom_logger=logger)
```

This way, the pre-announcement wouldn't be display unless running into the branch, but still could be collected into the upcoming breaking change documentation.

### Check Your Breaking Change Pre-Announcement

Before you publish the breaking changes, you need to make sure that the announcement is ready for the Upcoming Breaking Change Documentation. To do that, run this command:

```commandline
azdev genereate-breaking-change-report
```

If your breaking change is not for the next breaking change window, you can see all the announcements by using `--target-version None` like this:

```commandline
azdev genereate-breaking-change-report --target-version None
```

The output should be a json object including the pre-announcement you made.

### Adopt Breaking Changes

Breaking changes should be released with the announced CLI version, typically during the next breaking change window. The breaking change Pull Request must be reviewed by a CLI team member and merged before the sprint’s code freeze day.

**Note:** Ensure the breaking change pre-announcement is removed in the same Pull Request.

## Upcoming Breaking Change Documentation

The Upcoming Breaking Change Documentation is released every sprint. This document lists the expected breaking changes for the next Breaking Change Release. However, due to the implementation’s dependency on the Service Team, not all the listed Breaking Changes may be adopted.

The Upcoming Breaking Change Documentation includes:
* The deprecation targeted at the next Breaking Change Release;
* The pre-announcement declared in `_breaking_change.py`.

The documentation is generated through `azdev` tool. You can preview the documentation locally through the following command.

```commandline
azdev genereate-breaking-change-report CLI --output-format markdown
```
