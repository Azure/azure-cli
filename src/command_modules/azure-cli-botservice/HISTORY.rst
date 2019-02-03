.. :changelog:

Release History
===============
0.1.5
+++++
* Minor fixes

0.1.5
+++++
* Improve UX around `az bot publish`
* Add warning for timeouts when running `npm install` during `az bot publish`
* Remove invalid char "." from `--name`  in `az bot create`
* Stop randomizing resource names when creating Azure Storage, App Service Plan, Function/Web App and Application Insights
* Code cleanup in BotTemplateDeployer
* Deprecate `--proj-name` argument for `--proj-file-path`
* Update old `--proj-file` messages to instead use `--proj-file-path`


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