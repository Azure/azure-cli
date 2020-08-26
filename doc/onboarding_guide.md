Onboarding Best Practices
=========================

As a prerequisite, please contact Carl Shipley first for the [PLR](http://aka.ms/plrcriteria) (Product Launch Readiness) process.

Then reach out to `azpycli@microsoft.com` to get the CLI onboarding process started. You'll be assigned a dev contact on the CLI team. Early and frequent communication with this contact is essential to ensuring a smooth onboarding.

## Extension vs. Module

One of the key decisions you will need to make is whether to create your commands in a CLI module or an extension.

#### Extensions

|                      PROS                      |                         CONS                         |
|:----------------------------------------------:|:----------------------------------------------------:|
| Release separate from the CLI release schedule | Requires dedicated installation (az extension add …) |
| Higher velocity fixes possible                 | Can be broken by changes to the azure-cli-core       |
| Experimental UX is permissible                 |                                                      |
| Leverage CLI code generator to generate code   |                                                      |

#### CLI Modules

|                                   PROS                                  |                                                                             CONS                                                                             |
|:-----------------------------------------------------------------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------:|
| Comes automatically with the CLI. No dedicated installation required.   | Strictly tied to CLI release schedule                                                                                                                        |
| Unlikely to be broken by changes to azure-cli-core (with test coverage) | STRICTLY tied to CLI authoring guidelines. Experimental patterns that may be allowed in extensions could be rejected entirely for inclusion as a CLI module. |

- Common uses for extensions include experimental commands, commands in private or public preview, or to separate between frequently used and rarely used functionality (where infrequently used commands are acquired via extension).
- Note that if you are trying to get commands into the CLI out of step with the normal release cycle, extensions are your **only** option.
- Because non-standard, experimental authoring patterns are permitted for extensions, simply trying to "move an extension into the CLI" is often **not** a trivial process and will necessitate a full review with higher scrutiny from the CLI team. Expect to need to make changes.
- If you want to use CLI code generator to generate CLI code automatically, extension is your **only** option. Please reference [AZ CLI Codegen On boarding](https://github.com/Azure/autorest.az/blob/master/doc/00-onboarding-guide.md) and start from **Step 2** now.

## Initial Timeline and Milestones

- **Initial Kickoff:** Reach out to your contact on the CLI team. Set up a short 30 minute Teams call to discuss initial questions.

- **Initial Review:** Create a few commands. Schedule a short 30 minute Teams screen-share to demo your commands. This is crucial! Teams have created entire modules using anti-patterns, resulting in comment-filled PRs and last-minute rework! A quick command review would have prevented this.

- **During command authoring:** Run checks frequently to ensure you are staying on top of issues that will stall your build when you submit a PR. Use commands like `azdev test <YOURMOD>`, `azdev style <YOURMOD>` and `azdev linter <YOURMOD>`.

- **Periodic Command Review:** As practical.

- **Just before opening PR:** Run `azdev style` and `azdev linter --ci-exclusions` and `azdev test <YOURMOD>` to address issues before the CI finds them.

- **2 weeks before desired release date:** Open PR in CLI repo (public or private depending on your service). Request your CLI contact as the reviewer for the PR.

- **1 week prior to desired release date:** Hopefully, PR is merged! Download the edge build and try it out. Submit follow-up PRs to address any small issues. Anything caught before release is not a breaking change!

## Initial Pull Request Guidance

Reviewing a new command module is very difficult, so the PR shouldn't be the first time we see your module! Some important considerations for your initial PR:

1. Have recorded ScenarioTests for **all** new commands. This lets us know that your commands *work*. [Test Authoring](https://github.com/Azure/azure-cli/blob/dev/doc/authoring_tests.md)
2. If you are creating brand new commands, they should be marked as being in Preview. See: [Preview Commands and Arguments](https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/authoring_commands.md#preview-commands-and-arguments)
3. (OPTIONAL) The help output of:
   - all groups and subgroups (i.e. `az vm -h`)
   - all non-trivial commands (commands except `list`, `show`, `delete`)

If you and your CLI contact have been doing regular command reviews, the PR should merely be a formality. If you haven't been conducting regular reviews, the help output allows us to quickly identify holes and anti-patterns to get you on the right track.
The help output is generally not needed if a command walkthrough has been conducted, but is often a helpful alternative for teams who are in a very different time zone such that scheduling a live review would be highly inconvenient.

## Transition Paths

Nearly all new command modules or extensions begin life in Preview, but will eventually want to transition to being GA. The section describes the review requirements required for various transitions.

#### Preview Extension to GA Extension

This is the easiest to accomplish.

- Underlying service must be GA.
- Existing command UX must be stable.
- Author must acknowledge they will no longer be able to simply make breaking changes but will instead need to follow [deprecation mechanisms](https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/authoring_commands.md#deprecating-commands-and-arguments).

#### Preview Extension to Preview Module

Because extensions are permitted to try experimental things that may be antithetical to the CLI's conventions, it is not automatic that a preview extension can just transition to being a preview module.

- Command review required.
- Commands must conform to CLI standards and may no longer be permitted to do experimental things that they previously could as an extension.

#### Preview Extension/Module to GA Module

This is a significant transition for any service.

- Underlying service must be GA.
- Command review required.
- Command UX must be stable for several releases and conform to CLI standards.
- No deficiencies permitted which would necessitate future breaking changes. Instead, the breaking changes should be made as part of a preview release and allowed to stabilize.
- Minor deficiencies which can be fixed through additive, non-breaking changes are permissible (for example, missing argument completers or missing generic update arguments).
- Author must acknowledge they will no longer be able to simply make breaking changes but will instead need to follow [deprecation mechanisms](https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/authoring_commands.md#deprecating-commands-and-arguments).

#### GA Extension to GA Module

Because extensions are permitted to try experimental things that may be antithetical to the CLI's conventions, no benefit is afforded a GA extension in trying to become a module. In reality, the fact that the extension is GA can actually be more of a hindrance because any breaking changes that may be necessitated to conform with CLI standards will need to go through [deprecation mechanisms](https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/.

- Command review required.
- Commands must conform to CLI standards and may no longer be permitted to do experimental things that they previously could as an extension. This could necessitate breaking changes which will need to be accomplished using
[deprecation mechanisms](https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/authoring_commands.md#deprecating-commands-and-arguments).
- Minor deficiencies which can be fixed through additive, non-breaking changes are permissible (for example, missing argument completers or missing generic update arguments).
