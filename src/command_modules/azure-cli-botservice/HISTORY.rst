.. :changelog:

Release History
===============

* Add "discontinued support"/"maintenance mode"-warning messages for commands that support the v3 SDK

0.2.1
+++++
* Allow all casing for `--lang` parameters for commands
* Update description for command module

0.2.0
+++++
* [Breaking Change]: `az bot create -v v4 -k webapp` now creates an empty Web App Bot by default (i.e. no bot is deployed to the App Service).
    * To use the Echo Bot template that was always deployed in the past, use the new `--echo` flag when creating a v4 Web App Bot.
    * `v3` bot creation does not support using the `--echo` flag.
* [Breaking Change]: The default value for `--version` is now `v4`, not `v3` (except for `az bot prepare-publish`).
* [Breaking Change]: `--lang` no longer defaults to `Csharp`. If the command requires `--lang` and it is not provided, the command will error out.
* [Breaking Change]: The `--appid` and `--password` args for `az bot create` are now required and can be created via `az ad app create`.
    * Add `--appid` and `--password` validations
* [Breaking Change]: `az bot create -v v4` does not create or use a Storage Account or Application Insights.
* [Breaking Change]: Instead of mapping Application Insights regions for `az bot create -v v3`, the command only accepts regions where Application Insights is creatable.
* [Breaking Change]: `az bot update` is no longer a generic update command, but instead can affect specific properties of a bot.
* [Breaking Change]: All --lang flags now accept `Javascript` instead of `Node`. `Node` as a `--lang` value is no longer supported.
* [Breaking Change]: `az bot create -v v4 -k webapp` no longer sets `SCM_DO_BUILD_DURING_DEPLOYMENT` to true. All deployments through Kudu will act according to their default behavior.
* `az bot download` for bots without .bot files now create the language-specific configuration file with values from the Application Settings for the bot.
* Add `Typescript` support to `az bot prepare-deploy`
* Add warning message to `az bot prepare-deploy` for `Javascript` and `Typescript` bots.
    * This message only appears if the `--code-dir` doesn't contain a package.json.
* `az bot prepare-deploy` returns `true` if successful and has helpful verbose logging.
* Add more available Application Insights regions to `az bot create -v v3`

0.1.10
++++++
* Minor fixes

0.1.9
+++++
* Add `az bot prepare-deploy` to prepare for deploying bots via `az webapp`
* Have `az bot create --kind registration` show password if the password is not provided
* Have `--endpoint` in `az bot create --kind registration` default empty string instead of being required

0.1.8
+++++
* Add "SCM_DO_BUILD_DURING_DEPLOYMENT" to ARM template's Application Settings for v4 Web App Bots
* Add "Microsoft-BotFramework-AppId" and "Microsoft-BotFramework-AppPassword" to ARM template's Application Settings for v4 Web App Bots
* Remove single quotes from `az bot publish` command output at end of `az bot create`
* Use async zipdeploy API for deploying bots via `az bot publish`

0.1.7
+++++
* Suppress latest `botservice (0.4.3)` extension, this functionality has been rolled into the core CLI

0.1.6
+++++
* Improve UX around `az bot publish`
* Add warning for timeouts when running `npm install` during `az bot publish`
* Remove invalid char "." from `--name`  in `az bot create`
* Stop randomizing resource names when creating Azure Storage, App Service Plan, Function/Web App and Application Insights
* Code cleanup in BotTemplateDeployer
* Deprecate `--proj-name` argument for `--proj-file-path`
* Update old `--proj-file` messages to instead use `--proj-file-path`
* `az bot publish` now removes fetched IIS Node.js deployment files if they did not already exist
  * The command does not remove any local IIS Node.js files if detected when command is initiated.
* Add `--keep-node-modules` to `az bot publish` to not delete node_modules folder on App Service
* Add `"publishCommand"` key-value pair to output from `az bot create` when creating an Azure Function or Web App bot.
  * The value of `"publishCommand"` is an `az bot publish` command prepopulated with the required parameters to publish the newly created bot.
* Update `"WEBSITE_NODE_DEFAULT_VERSION"` in ARM template for v4 SDK bots to use 10.14.1 instead of 8.9.4

0.1.5
+++++
* Minor fixes

0.1.4
+++++
* Add deployment status updates to `az bot create`

0.1.3
+++++
* Add support for .bot file parsing when calling `az bot show`
* Fix AppInsights provisioning bug
* Fix whitespace bug when dealing with file paths
* Reduce Kudu network calls
* Additional UX improvements

0.1.2
+++++
* Major refactoring
* Improvements to test coverage

0.1.1
+++++
* Minor fixes

0.1.0
+++++
* Initial Bot Service CLI Release