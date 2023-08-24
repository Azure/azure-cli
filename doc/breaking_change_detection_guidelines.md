# Breaking Change Detection for Azure CLI

## Overview

Azure cli provides command line tool to help users and developers check cli changes: [command-change](https://github.com/Azure/azure-cli-extensions/blob/main/src/command-change/README.md) 

There are two categories of breaking change detection users can check for Azure CLI: [version-diff](https://github.com/Azure/azure-cli-extensions/blob/main/src/command-change/README.md#version-diff) and [meta-diff](https://github.com/Azure/azure-cli-extensions/blob/main/src/command-change/README.md#meta-diff) .

#### Prerequisite

Install cli extension `command-change`

```
az extension add --name command-change
```

### version-diff

Users can check the differences between two cli releases, like `2.47.0` and `2.49.0`, by typing following command:
```
az command-change version-diff --base-version 2.47.0 --diff-version 2.49.0
```

If specific module is targeted, like `monitor`, users can add `--target-module` following above command:
```
az command-change version-diff --base-version 2.47.0 --diff-version 2.49.0 --target-module monitor
```

Normally, the pulled list of version diffs is quite long, so a better usage way is redirecting the result to a local file like `filename-a`, with the `--output-type` set as `csv`:
```
az command-change version-diff --base-version 2.47.0 --diff-version 2.49.0 --target-module monitor --output-type csv --version-diff-file filename-a
```

When `version-diff` command runs, it will download the corresponding metadata files of all modules for chosen cli versions and store them in current working directory, one module a file called `az_module_meta.json`, which can be used in the following `meta-diff` command


### meta-diff

Using the downloaded metadata files from `version-diff` command, users can get various versions for the target module metadata. `meta-diff` can be used to diff between two versions of a specific module, as below:

```
az command-change meta-diff --base-meta-file fileA --diff-meta-file fileB
```

By the way, both these two commands can add `--only-break` to just pull the break change list if needed.


### Analysis

The diff result will be organized as a combination of following basic structure:
```
{
    "cmd_name": "command name",
    "is_break": false or true,
    "module": "module name",
    "rule_id": "1xxx",
    "rule_link_url": "https://github.com/Azure/azure-cli/blob/dev/doc/breaking_change_rules/1xxx.md",
    "rule_message": "",
    "rule_name": "",
    "suggest_message": ""
}
```

- `cmd_name`: the command or subgroup name of detected changes
- `is_break`: whether it will cause a break in current commands' functionality
- `module`: the module name
- `rule_id`: corresponding change rule ids
- `rule_link_url`: corresponding change rule docs. For full rule doc, please refer to [this link](https://github.com/Azure/azure-cli/tree/dev/doc/breaking_change_rules)
- `rule_message`: detailed change info message
- `rule_name`: abbreviation of rules
- `suggest_message`: it's used for developers of CI when a pull request is made to cli code repo.

