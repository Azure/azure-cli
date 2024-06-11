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

The timing of the breaking change window in Azure CLI aligns with [Microsoft Build](https://build.microsoft.com/) and [Microsoft Ignite](https://ignite.microsoft.com/). You could find the next Breaking Change Release plan in our [milestones](https://github.com/Azure/azure-cli/milestones).

> It's highlighted that the introduction of breaking changes is typically prohibited within non-breaking-change window, based on what we stated above for consistency and stable tooling experience.
> 
> Exceptions to this policy may be considered under extraordinary circumstances. We understand and would like to help out. There would be high-graded justifications required to provide the info Azure CLI can access.
> 
> Please note that providing the required info for assessment does not mean it will be assured to be green-lighted for breaking changes. Team will still make the decision based on the overall impact.

### Pre-announce Breaking Changes

All breaking changes **must** be pre-announced several sprints ahead Release. There are two approaches to inform both interactive users and automatic users about the breaking changes.

1. (**Mandatory**) Breaking Changes must be pre-announced through Warning Log while executing.
2. (*Automatic*) Breaking Changes would be collected automatically and listed in [Upcoming Breaking Change](https://learn.microsoft.com/en-us/cli/azure/upcoming-breaking-changes).

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
* At the start of Breaking Change window, emails would be sent to notify Service Teams to adopt Breaking Changes.
* Breaking Changes should be adopted within Breaking Change Window.

### Pre-announce Breaking Changes

We recommend different approaches for different types of Breaking Changes.

#### Deprecation

If you would like to deprecate command groups, commands, arguments or options, please following the [deprecation guide](authoring_command_modules/authoring_commands.md#deprecating-commands-and-arguments) to add a pre-announcement.

```Python
from azure.cli.core.breaking_change import NEXT_BREAKING_CHANGE_RELEASE

with self.command_group('test', test_sdk) as g:
  g.command('show-parameters', 'get_params', deprecate_info=g.deprecate(redirect='test show', expiration=NEXT_BREAKING_CHANGE_RELEASE))
```

A warning message would be produced when executing the deprecated command.

```This command has been deprecated and will be removed in version 2.1.0. Use `test show` instead.```

If you would like to break the deprecated usage automatically in a future version, set the `expiration` in deprecation information. The `expiration` should be the breaking change release version in our [milestones](https://github.com/Azure/azure-cli/milestones) if set.

#### Others

To pre-announce custom breaking changes, such as modifications to default argument values, please add an entry to the `_breaking_change.py` file within the relevant module. If this file does not exist, create `_breaking_change.py` and insert the following lines.

```python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.breaking_change import upcoming_breaking_changes
```

Then you could pre-announce breaking changes for different command groups or command, both list and `BreakingChange` object are accepted.

```python
from azure.cli.core.breaking_change import upcoming_breaking_changes, BeRequired, DefaultChange, OtherChange

upcoming_breaking_changes['bar foo'] = BeRequired('--name')
upcoming_breaking_changes['bar foo baz'] = [DefaultChange('--foobar', 'A', 'B'), OtherChange('During May 2024, another Breaking Change would happen in Build Event.')]
```

All related breaking changes would be displayed while executing the command. For example, in the above 

```shell
# The azure command
az bar foo baz

# =====Warning output=====
# The argument `--name` will become required in next breaking change release(2.61.0).
# The default value of `--foobar` will be changed to `B` from `A` in next breaking change release(2.61.0).
# During May 2024, another Breaking Change would happen in Build Event.
```

There are several types of breaking changes defined in `breaking_change`. You should use any of them to declare breaking changes in `_breaking_change.py`.

**Remove**
```python
from azure.cli.core.breaking_change import upcoming_breaking_changes, Remove, NextBreakingChangeWindow

# Remove the command groups, commands or arguments in a future release.
# **It is recommended to utilize `deprecate_info` instead of this class to pre-announce Breaking Change of Removal.**
upcoming_breaking_changes['bar foo'] = Remove('az bar foo', target_version=NextBreakingChangeWindow(), redirect='`az barfoo`')
# `az bar foo` will be removed in next breaking change release(2.61.0). Please use `az barfoo` instead.
```

**Rename**
```python
from azure.cli.core.breaking_change import upcoming_breaking_changes, Rename, NextBreakingChangeWindow

# Rename the command groups, commands or arguments to a new name in a future release.
# **It is recommended to utilize `deprecate_info` instead of this class to pre-announce Breaking Change of Renaming.**
# It is recommended that the old name and the new name should be reserved in few releases.
upcoming_breaking_changes['bar foo'] = Rename('az bar foo', 'az bar baz', target_version=NextBreakingChangeWindow())
# `az bar foo` will be renamed to `az bar baz` in next breaking change release(2.61.0).
```

**OutputChange**
```python
from azure.cli.core.breaking_change import upcoming_breaking_changes, OutputChange, NextBreakingChangeWindow

# The output of the command will be changed in a future release.
upcoming_breaking_changes['bar foo'] = OutputChange('Reduce the output field `baz`', target_version=NextBreakingChangeWindow())
# The output will be changed in next breaking change release(2.61.0). Reduce the output field `baz`. 
```

**LogicChange**
```python
from azure.cli.core.breaking_change import upcoming_breaking_changes, LogicChange, NextBreakingChangeWindow

# There would be a breaking change in the logic of the command in future release.
upcoming_breaking_changes['bar foo'] = LogicChange('Update the validator', target_version=NextBreakingChangeWindow(), detail='The xxx will not be accepted.')
# Update the validator in next breaking change release(2.61.0). The xxx will not be accepted.
```

**DefaultChange**
```python
from azure.cli.core.breaking_change import upcoming_breaking_changes, DefaultChange, NextBreakingChangeWindow

# The default value of an argument would be changed in a future release.
upcoming_breaking_changes['bar foo'] = DefaultChange('--type', 'TypeA', 'TypeB', target_version=NextBreakingChangeWindow())
# The default value of `--type` will be changed to `TypeB` from `TypeA` in next breaking change release(2.61.0).
```

**BeRequired**
```python
from azure.cli.core.breaking_change import upcoming_breaking_changes, BeRequired, NextBreakingChangeWindow

# The argument would become required in a future release.
upcoming_breaking_changes['bar foo'] = BeRequired('--type', target_version=NextBreakingChangeWindow())
# The argument `--type` will become required in next breaking change release(2.61.0).
```

**OtherChange**
```python
from azure.cli.core.breaking_change import upcoming_breaking_changes, OtherChange, NextBreakingChangeWindow
# Other custom breaking changes.
upcoming_breaking_changes['bar foo'] = OtherChange('During May 2024, another Breaking Change would happen in Build Event.', target_version=NextBreakingChangeWindow())
# During May 2024, another Breaking Change would happen in Build Event.
```

To enhance flexibility in using the Breaking Change Pre-announcement, instead of the default automatic warning display prior to command execution, you may opt to specify the pre-announcement using a designated key in the format `{Command}.{NAME}`.

```python
# src/azure-cli/azure/cli/command_modules/vm/_breaking_change.py
from azure.cli.core.breaking_change import upcoming_breaking_changes, BeRequired
upcoming_breaking_changes['bar foo.TYPE_REQUIRED'] = BeRequired('--type')

# src/azure-cli/azure/cli/command_modules/vm/custom.py
# Use the pre-announcement. Replace `vm` with your module
import azure.cli.command_modules.vm._breaking_change  # pylint: disable=unused-import
from azure.cli.core.breaking_change import upcoming_breaking_changes

if not_use_type:
    logger.warn(upcoming_breaking_changes['bar foo.TYPE_REQUIRED'].message)
```

This way, the pre-announcement wouldn't be display unless running into the branch, but still could be collected into the upcoming breaking change documentation.

### Check Your Breaking Change Pre-Announcement

Before you publish the breaking changes, you need to make sure that the announcement is ready for the Upcoming Breaking Change Documentation. To do that, run this command:

```commandline
azdev breaking-change collect
```

If your breaking change is not for the next breaking change window, you can see all the announcements by using `--target-version None` like this:

```commandline
azdev breaking-change collect --target-version None
```

The output should be a json object including the pre-announcement you made.

## Upcoming Breaking Change Documentation

The Upcoming Breaking Change Documentation is released every sprint. This document lists the expected breaking changes for the next Breaking Change Release. However, due to the implementation’s dependency on the Service Team, not all the listed Breaking Changes may be adopted.

The Upcoming Breaking Change Documentation includes:
* The deprecation targeted at the next Breaking Change Release;
* The pre-announcement declared in `_breaking_change.py`.

The documentation is generated through `azdev` tool. You can preview the documentation locally through the following command.

```commandline
azdev breaking-change collect CLI --output-format markdown
```
