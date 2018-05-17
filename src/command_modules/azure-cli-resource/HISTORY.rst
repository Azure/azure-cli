.. :changelog:

Release History
===============

2.0.29
++++++
* Minor changes


2.0.28
++++++
* Minor changes

2.0.27
++++++
* `policy definition create`: Add support for `--metadata`.
* `policy definition update`: Add support for `--metadata`, `--set`, `--add`, `--remove`.
* `sdist` is now compatible with wheel 0.31.0

2.0.26
++++++
provider operation list/show: (breaking change)`api-version` is no longer required to run the command

2.0.25
++++++
* Support Autorest 3.0 based SDKs

2.0.24
++++++
* `group deployment export`: On failure, command will now output a partial template and any failures.

2.0.23
++++++
* feature: bring back 'feature show' command

2.0.22
++++++
* `deployment create/validate`: Fix bug where warning was incorrectly displayed when a template 'type' field contained
                                uppercase values.

2.0.21
++++++
* Helpfile changes

2.0.20
++++++
* Update for CLI core changes.

2.0.19
++++++
* `resource show`: expose `--include-response-body` to show the response body in the output

2.0.18
++++++
* --resource parameter, resource-level locks now support resource-ids.

2.0.17
++++++
* `group export`: Fixed incompatibility with most recent version of msrest dependency.
* `az policy assignment create`: policy assignment create command to work with built in policy definitions and policy set definitions.

2.0.16 (2017-10-09)
+++++++++++++++++++
* group: permit --resource-group/-g options for resource group name.
* `account lock`: lock commands to work specifically with subscription level locks
* `group lock`: lock commands to work specifically with group level locks
* `resource lock`: lock command to work specifically with resource level locks

2.0.15 (2017-09-22)
+++++++++++++++++++
* policy: support to show built-in policy definition.
* policy: support mode parameter for creating policy definitions.
* policy: add policy set definition commands.
* policy: add sku and policysetdefinition parameters when creating policy assignment
* managedapp definition: support to create managedapp definition using create-ui-definition and main-template.
* BREAKING CHANGE: managedapp: Update to latest ARM package, which includes changing resource type from appliances to applications and applianceDefinitions to applicationDefinitions.
* resource invoke-action: supports ability to invoke any action onto resource, also supports user-specified url to post.

2.0.14 (2017-09-11)
+++++++++++++++++++
* Allows passing in resource policy parameter definitions in 'policy definition create', and 'policy definition update'.
* Allows passing in parameter values for 'policy assignment create'.
* In all cases params can be provided either via json or file.
* Incremented API version.
* Support '--ids' parameter to refer to locks
* Various lock command bug fixes

2.0.12 (2017-08-11)
+++++++++++++++++++
* minor fixes

2.0.13 (2017-08-28)
+++++++++++++++++++
* `group deployment create`: Fixes issue where templates which lacked "parameters" or "resources" failed to deploy.

2.0.11 (2017-07-27)
+++++++++++++++++++
* minor fixes

2.0.10 (2017-07-07)
+++++++++++++++++++
* `group deployment create`: Improve prompting for missing parameters. Improve parsing of `--parameters KEY=VALUE` syntax.

2.0.9 (2017-06-21)
++++++++++++++++++
* `group deployment create`: Fixes issue where some parameter files were no longer recognized using @<file> syntax.
* `resource\managedapp` commands: Support `--ids` argument.


2.0.8 (2017-06-13)
++++++++++++++++++
* Fix up some parsing and error messages. (#3584)
* Fix --resource-type parsing for the lock command to accept <resource-namespace>/<resource-type>
* Add parameter checking for template link templates (#3629)
* Add support for specifying deployment parameters using KEY=VALUE syntax.

2.0.7 (2017-05-30)
++++++++++++++++++
* Minor fixes.

2.0.6 (2017-05-09)
++++++++++++++++++
* Change ARM api-version default to latest, update ARM SDK (#3256)

2.0.5 (2017-05-05)
++++++++++++++++++
* Add managedapp and managedapp definition commands (#2985)

2.0.4 (2017-04-28)
++++++++++++++++++
* Support 'provider operation' commands (#2908)
* Support generic resource create (#2606)

2.0.3 (2017-04-17)
++++++++++++++++++

* Fix resource parsing and api version lookup. (#2781)
* Add docs for az lock update. (#2702)
* Error out if you try to list resources for a group that doesn't exist. (#2769)
* [Compute] Fix issues with VMSS and VM availability set update. (#2773)
* Add some more error checking/handling. (#2768)
* Make argument parameters match up. (#2717)
* Fix lock create and delete if parent-resource-path is None (#2742)
* Apply core changes required for API profile support (#2834) & JSON string parsing from shell (#2705)


2.0.2 (2017-04-03)
++++++++++++++++++

* Add better error messages if --namespace is missing. (#2652)
* Make --parameters repeatable, and merge arguments. (#2656)
* resource: support resource id for generic resource update (#2640)
* Add prompting for missing template parameters. (#2364)

2.0.1 (2017-03-13)
++++++++++++++++++

* Improve docs to point at template deployments command. (#2466)
* core: support setting default values for common arguments like default resource group, default web, default vm (#2414)
* Add some docs for az lock, remove an unused flag, rename another. (#2382)


2.0.0 (2017-02-27)
++++++++++++++++++

* GA release


0.1.2rc2 (2017-02-22)
+++++++++++++++++++++

* Documentation updates.

0.1.2rc1 (2017-02-17)
+++++++++++++++++++++

* Add support for resource links
* Prompts for yes / no use the -y option rather than --force
* Resource delete return the server response
* Show commands return empty string with exit code 0 for 404 responses

0.1.1b2 (2017-01-30)
+++++++++++++++++++++

* Support for management locks.
* Add path expansion to file type parameters.
* Support Python 3.6.

0.1.1b1 (2017-01-17)
+++++++++++++++++++++

* Add --operation-ids to 'az resource group deployment operations show'.

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
