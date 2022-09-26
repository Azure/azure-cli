# How to Bump SDK Version in CLI

This article aims to provide a guide for CLI developers and contributors to bump SDK version in Azure CLI.

## Overview

Developers need to do several things for bumping version:
1. Upgrade the SDK version in CLI dependency
2. Update the used API version if defined in Cli Core
3. Regression test to check if it breaks existing features
4. Make the code changes to
    - fix the regression
    - add new features

We can divide all the work into 2 phases.

## Phase 1 - Trigger Bump Version Pipeline

The [Bump Version Pipeline](https://dev.azure.com/azure-sdk/internal/_build?definitionId=4949) is designed to handle all the repetitive work. It will:
- Upgrade the SDK version in [setup.py](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli/setup.py), [requirements.py3.windows.txt](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli/requirements.py3.windows.txt), [requirements.py3.Linux.txt](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli/requirements.py3.Linux.txt) and [requirements.py3.Darwin.txt](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli/requirements.py3.Darwin.txt)
- Update the API version defined in CLI Core [AZURE_API_PROFILES](https://github.com/Azure/azure-cli/blob/ce74ae358b51aedfdfb6c32042b515d949618e33/src/azure-cli-core/azure/cli/core/profiles/_shared.py#L147) for 'latest' profile
- Run automation full test for all cli command modules in recording mode
- Rerun failed tests of last step in live mode, keep the new recording yaml files for those successful tests during live rerun
- Create a PR to CLI repo with all version changes and new test recordings

To trigger a new execution of Bump Version Pipeline, developers need to fulfill these variables:
- PACKAGE: **Required**. The SDK package name, eg. `azure-mgmt-network`.
- TARGET_PACKAGE_VERSION: **Required**. The SDK new version, eg. `19.3.0`.
- RESOURCE_TYPE: Required if you want to update the API version definition in CLI Core. The resource type enum name define in [CLI Core](https://github.com/Azure/azure-cli/blob/ce74ae358b51aedfdfb6c32042b515d949618e33/src/azure-cli-core/azure/cli/core/profiles/_shared.py#L38), eg. `MGMT_NETWORK`.
- TARGET_API_VERSION: Required if you want to update the API version definition in CLI Core. The new API version or API versions:
    - If the AZURE_API_PROFILES['latest'][RESOURCE_TYPE] definition is `str` type, then just fulfill this variable with new API version. For example, to update API version for [ResourceType.MGMT_NETWORK](https://github.com/Azure/azure-cli/blob/ce74ae358b51aedfdfb6c32042b515d949618e33/src/azure-cli-core/azure/cli/core/profiles/_shared.py#L150), use `2021-10-01` as variable value.
    - If the  AZURE_API_PROFILES['latest'][RESOURCE_TYPE] definition is `SDKProfile` type, then fulfill this variable with 'operation=version' pairs separated by space. For example, to update API version for [ResourceType.MGMT_COMPUTE](https://github.com/Azure/azure-cli/blob/ce74ae358b51aedfdfb6c32042b515d949618e33/src/azure-cli-core/azure/cli/core/profiles/_shared.py#L151-L164), use `default=2022-05-01 snapshots=2022-03-01 gallery_images=2021-12-01` as variable value. `default` means other operations except for explicitly listed ones.

It may take some time for the pipeline execution. After PR created, developers can check the status and test results in linked pipeline.

## Phase 2 - Manual code changes

Developers can review the test failures from pipeline test result report or PR CI checks. These failed test can't pass live run after bumping version.

Developers need to figure out the failure root cause and fix them. After all the tests fixed, feel free to implement new features in the same PR or a separate one.

## See also

- [Authoring Commands](authoring_command_modules/authoring_commands.md)

- [Automating tests for Azure CLI](authoring_tests.md)