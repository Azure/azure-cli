
## Versioning

The Azure CLI follows [Semantic Versioning](https://semver.org/) for version numbering. The CLI version consists of three parts `MAJOR.MINOR.PATCH`:
- MAJOR version is upgraded only when there is a huge revolution, such as the core changes that will break commands' behavior globally.
- MINOR version is upgraded for new features with the normal release process. All feature updates must be forward compatible, and breaking changes can only be published in the breaking change window *(Ignite sprint or Build sprint)*.
- PATCH version is upgraded for hotfixes through the hotfix release process.

## Life Cycle

### Release States

Azure CLI differs from the [three life cycles](https://docs.microsoft.com/learn/modules/describe-service-life-cycle-microsoft-365/2-private-public-general-availability) of an Azure Service.  CLI only uses two states, **GA** (Generally Available) and **Preview**, making it easier to understand and maintain.

- The **GA** state means that a feature is mature, stable, available to all customers, and has formal support. A GA feature must be forward compatible and not prone to cause breaking changes.
    - Commands not tagged with the `is_preview` flag are considered as GA commands

- The **Preview** state means a feature is unstable and not finalized. Preview features are released before GA and allow customers to test, experiment, and provide feedback in advance of the GA release. Preview features should not be used in production environments as they aren't stable or finalized and could have breaking changes with each release up to, and including, the feature's GA release.
    - Preview features and commands need to be tagged with the [is_preview](https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/authoring_commands.md#preview-commands-and-arguments) flag to let customers know about instability.
    - It is usually recommended to put the preview features into CLI extension first and migrate it to core CLI after they are stable and GA. We can also consider moving some preview features from core CLI to CLI extensions if they are proper for moving.

### States Transition

#### Preview to GA
Generally, if the service is stable and the design of the commands will not change, we are confident that these commands will not cause breaking changes in the future, then we can remove the `is_preview` flag and GA those commands.

#### GA to Preview
For the core CLI, it is generally not allowed to downgrade from GA to Preview, because the GA state means that the stability of commands has been promised to customers, and new instability cannot be introduced by downgrading to Preview. Moreover, since Azure CLI is an all-in-one package, users usually upgrade directly to the latest version of CLI. If users skip the intermediate version with features having been downgraded to Preview and directly upgrade to the latest version that has breaking changes, it will make a confusing and frustrating experience for them.

### Relationship with api-version

At present, CLI sets the api-version according to the Resource Provider granularity, and there are corresponding configurations for different profiles. For most commands, we do not support customers to specify the requested api-version.

- For the GA api-version, if the command itself determines the final design, then we usually make the implemented command also in the GA state.

- For the public preview api-version, the situation is relatively complicated, and we usually divide it into the following cases:
    1. If those features are newly onboard RPs, command groups or extensions, we usually mark them as `is_preview`. 
    2. If there are some existing commands under these RPs, but only the new features need to be released through the preview api-version, and we need to add some new commands or parameters to support them, then we need to upragde to the preview api-version and only mark `is_preview` on those new commands and parameters, while the existing commands and parameters remain in the GA state. We still need to ensure that the existing commands and parameters are stable without breaking changes.
    3. Due to the higher flexibility of CLI extension, we want customers to use the stable extension version by default, so we plan to make the release state of extension consistent with the api-version state: if the api-version is preview, the whole extension should be in preview state. And we need to add "preview" suffix in extension version number *(comply with [pep-0440](https://peps.python.org/pep-0440/))* to prevent customers from upgrading to preview version automatically. We will add support for `az extension add` and `az upgrade` to allow customers to install/upgrade to stable version as default behavior and to install/upgrade to preview version by specifying extra parameter in the future. 

- For the private preview api-version, we usually do not recommend releasing those private features in the core CLI/CLI extension, so as to avoid premature exposure of private features. It is suggested to use [edge build](https://github.com/Azure/azure-cli/blob/dev/doc/try_new_features_before_release.md) to build the private packages to meet the urgent needs of some customers first.

Since the release states of api-version and CLI commands may be inconsistent, our intent is for customers to only have to pay attention to the release states *(`is_preview` flag)* of the command itself, rather than the api-version used behind it. This will be easier for customers to understand.

## Breaking Changes

### What is a breaking change

A breaking change is any update to Azure CLI, including core CLI and CLI extensions, that causes a customer's script or automation, written in a previous version, to fail.
Common examples of breaking changes include:
- Modifying names of parameters/commands.
- Modifying input logic of parameters.
- Modifying the format or properties of result output.
- Modifying the current behavior model.
- Adding additional verification that changes CLI behavior.
- Removing parameters/commands

All breaking changes for commands will be marked as **\[BREAKING CHANGE\]** in [release notes](https://docs.microsoft.com/cli/azure/release-notes-azure-cli).

### When do breaking changes occur

Azure CLI has bi-annual breaking change releases coinciding with Microsoft **Build** and **Ignite** events. Azure CLI **generally** releases the breaking changes **only** in these two breaking change windows. This approach allows customers to maintain stability, especially in automation scenarios, while keeping up-to-date with the latest and most secure versions of Azure CLI. It also allows customers to plan, test, and migrate Azure CLI commands and features properly when breaking changes are released.

However, under the following circumstances, breaking changes cannot wait the next breaking change release and we will proceed with an out of band breaking change release. We will notify about this change as early as possible in the [upcoming breaking changes](https://learn.microsoft.com/cli/azure/upcoming-breaking-changes) page:

- A critical bug is affecting customers and requires a hot fix.
- A security or data loss related fix is required. 
- A service-side breaking change requires an Azure CLI adjustment to avoid customer interruption.

### Planning for breaking changes

- You can view our [Upcoming Breaking Changes](https://learn.microsoft.com/cli/azure/upcoming-breaking-changes) doc to view the upcoming major breaking changes planned for the next breaking change release cycle.
- Azure CLI places in-tool warning messages in relevant commands when breaking changes are planned in the future. Paying attention to these warnings will keep you informed about major changes to a command or feature. 
