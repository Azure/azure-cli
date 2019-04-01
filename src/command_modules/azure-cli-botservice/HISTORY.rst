.. :changelog:

Release History
===============

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