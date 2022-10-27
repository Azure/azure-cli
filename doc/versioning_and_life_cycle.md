
## Versioning

The official Azure CLI follows [Semantic Versioning](https://semver.org/) for version numbering. The CLI version consists of three parts `MAJOR.MINOR.PATCH`:
- MAJOR version will be upgraded only when there is a huge revolution. Generally, this version will not be upgraded.
- MINOR version upgraded for new features with the normal release process. All the feature updates must be forward compatible, the breaking changes can only be published in the breaking change window *(Ignite sprint or Build sprint)*.
- PATCH version upgraded for hotfix with the hotfix release process.

## Life Cycle

### Relase States

Different from the three life cycles [(GA, Preview, Private Preview)](https://docs.microsoft.com/en-us/learn/modules/describe-service-life-cycle-microsoft-365/2-private-public-general-availability) of the Azure Service, CLI only uses two states **GA** and **Preview** to make it easier to understand and easier to maintain.

- For the GA state, it means that this feature becomes available to all customers with formal support, and those commands have been mature and stable. We must ensure its forward compatibility and will not easily make breaking changes.
    - Commands that are not tagged with `is_preview` flag are considered as GA commands

- For the Preview state, it means that this feature is still in the preview status, which is released before GA release to allow some customers to experience it in advance and collect their feedback. Therefore, these features are unstable and not finalized, the related commands may make breaking changes in the future.
    - The preview commands need to be tagged with [`is_preview`](https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/authoring_commands.md#preview-commands-and-arguments) flag to let customers aware of these instability.
    - It is generally recommended to put the preview features into CLI extension first and migrate it to official CLI after they are stable and GA. We can also consider moving some preview features from official CLI to CLI extensions if they are proper for moving.

### States Transition

#### Preview to GA
Generally, if the service is stable and the design of the commands will not change, we are confident that these commands will not cause breaking changes in the future, then we can remove the `is_preview` flag and GA those commands.

#### GA to Preview
For the official CLI, it is generally not allowed to downgrade from GA to Preview, because the GA state means that the stability of commands has been promised to customers, and new instability cannot be introduced by downgrade to Preview. Moreover, since Azure CLI is an all-in-one package, users usually upgrade directly to the latest version of CLI. If users skip the intermediate version with those feature downgraded to Preview and directly upgrade to the latest version that has breaking changes, it will make a terrible experience for them.

### Relationship with api-version

At present, CLI sets the api-version according to the Resource Provider granularity, and there are corresponding configurations for different profiles. For most commands, we do not support customers to specify the requested api-version.

- For the GA api-version, if the command itself determines the final design, then we usually make the implemented command also in the GA state.

- For the public preview api-version, the situation is relatively complicated, and we usually divide it into the following cases:
    - if those features are newly onboard RPs, command groups or extensions, we usually mark them as `is_preview`. 
    - If there are some existing commands under these RPs, but only the new features need to be released through the preview api-version, and we need to add some new commands or parameters to support them, then we need to upragde to the preview api-version and only mark `is_preview` on those new commands and parameters, while the existing commands and parameters remain in the GA state. We still need to ensure that the existing commands and parameters are stable without breaking changes.
    - Due to the higher flexibility of CLI extension, we plan to make the release status of extension consistent with the api-version status: if the api-version is preview, the whole extension should be in preview. And we need to add "preview" suffix in extension version number *(comply with [pep-0440](https://peps.python.org/pep-0440/))* to prevent customers from upgrading to preview version automatically. We will add support for `az extension add` and `az upgrade` to allow customers to install/upgrade to stable version as default behavior and to install/upgrade to preview version by specifying extra parameter in the future. 

- For the private preview api-version, we generally do not recommend release those private features in official CLI/CLI extension, so as to avoid premature exposure of private features. It is suggested to use [edge build](https://github.com/Azure/azure-cli/blob/dev/doc/try_new_features_before_release.md) to build the private packages to meet the urgent needs of some customers first.

Since the release states of api-version and CLI commands may be inconsistent, we hope that customers only need to pay attention to the release states *(`is_preview` flag)* of the command itself, rather than the api-version used behind it, which will be easier for customers to understand and use it.


## Breaking Changes

### What is a breaking change
A breaking change is any update to Azure CLI, including official CLI and CLI extensions, that causes a customer's script or automation written in a previous version to fail.
The common examples of breaking changes include:
- Modifying the names of parameters/commands.
- Modifying the input logic of parameters.
- Modifying the format or properties of result output.
- Modifying the current behavior model.
- Adding additional verification that changes CLI behavior.


### When do breaking changes occur
Azure CLI has bi-annual breaking change releases coinciding with Microsoft **Build Event** and **Ignite Event**. Azure CLI usually releases the breaking changes with a unified and centralized manner only in these two breaking change windows, so customers need to plan and migrate deprecated usage for the breaking change windows in advance.

However, there are some special cases that need to be released as soon as possible. In the following cases, it dose not need to wait for the breaking change window to release:
- The critical bugs need hotfix
- The security patch
- If server side has produced a breaking change which is inevitable for users, then CLI side has to adapt it

### How to know the breaking changes in advance
- You can view this document [upcoming-breaking-changes](https://learn.microsoft.com/en-us/cli/azure/upcoming-breaking-changes) to obtain the upcoming major breaking changes 
- Please pay attention to the warning message for deprecated commands/parameters in time
