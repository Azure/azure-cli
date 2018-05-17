.. :changelog:

Release History
===============

2.0.33
++++++
* core: ignore FileNotFoundError error on expanding `@`

2.0.32
++++++
* auth: fix a unhandled exception when retrieve secrets from a service principal account with cert
* auth: improve the logic of detecting msi based account
* Added limited support for positional arguments.
* Fix issue where `--query` could not be used with `--ids`. [#5591](https://github.com/Azure/azure-cli/issues/5591)
* Improves piping scenarios from commands when using `--ids`. Supports `-o tsv` with a query specified or `-o json`
  without specifying a query.
* Display command suggestions on error if users have typo in their commands
* More friendly error when users type `az ''`
* Support custom resource types for command modules and extensions

2.0.31
++++++
* Allow other sources to add additional tab completion choices via event hook
* `sdist` is now compatible with wheel 0.31.0

2.0.30
++++++
* Show message for extensions marked as preview on -h.

2.0.29
++++++
* Support Autorest 3.0 based SDKs
* Support mechanism for a command module to suppress the loading of particular extensions.

2.0.28
++++++
* Fix issue that required extension to use `client_arg_name` keyword argument. This is no longer necessary.
* Allow extensions to send telemetry with custom instrumentation key
* Enable HTTP logging with --debug

2.0.27
++++++
* auth: key on both subscription id and name on msi login
* Add events module in core for EVENT_INVOKER_PRE_CMD_TBL_TRUNCATE

2.0.26
++++++
* Support raw token retrival in MSI context
* Remove polling indicator string after finishing LRO on Windows cmd.exe
* Warning that appears when using a configured default has been changed to an INFO level entry. Use --verbose to see.
* Add a progress indicator for wait command

2.0.25
++++++
* Minor fixes

2.0.24
++++++
* Minor fixes

2.0.23
++++++
* Minor fixes

2.0.22
++++++
* Minor fixes
* Modified the AZURE_US_GOV_CLOUD's AAD authority endpoint from login.microsoftonline.com to login.microsoftonline.us.
* Introduce SDKProfile to support azure-mgmt-compute 3.1.0rc1 and integrated profile support.
* Improve telemetry: remove inifinity retry loop from SynchronousSender.

2.0.21
++++++
* Minor fixes

2.0.20
++++++
* 2017-03-09-profile is updated to consume MGMT_STORAGE API version '2016-01-01'

2.0.19
++++++
* skipped version to align package versions with azure-cli

2.0.18 (2017-10-09)
+++++++++++++++++++
* Azure Stack: handle adfs authority url with a trailing slash

2.0.17 (2017-09-22)
+++++++++++++++++++
* minor fixes
* Address problems with 'AzureCloud' clouds.config file in concurrent scenarios
* More user-friendly handling of invalid cloud configurations
* `availability-set create`: Fixed issue where this command would not work on Azure Stack.

2.0.16 (2017-09-11)
+++++++++++++++++++
* Enable command module to set its own correlation ID in telemetry
* Fix json dump issue when telemetry is set to diagnostics mode

2.0.15 (2017-08-31)
+++++++++++++++++++
* minor fixes

2.0.14 (2017-08-28)
+++++++++++++++++++

* Add legal note to --version

2.0.13 (2017-08-11)
+++++++++++++++++++
* fixes issue where `three_state_flag` would not work correctly if custom labels were used.

2.0.12 (2017-07-27)
+++++++++++++++++++
* output sdk auth info for service principals with certificates

2.0.11 (2017-07-07)
+++++++++++++++++++
* minor fixes

2.0.10 (2017-06-21)
+++++++++++++++++++
* Fix deployment progress exceptions

2.0.9 (2017-06-14)
++++++++++++++++++
* use arm endpoint from the current cloud to create subscription client

2.0.8 (2017-06-13)
++++++++++++++++++
* Improve concurrent handling of clouds.config file (#3636)
* Refresh client request id for each command execution.
* core: Create subscription clients with right SDK profile (#3635)
* Progress Reporting for template deployments (#3510)
* output: add support for picking table output fields through jmespath query  (#3581)
* Improves the muting of parse args + appends history with gestures (#3434)
* Create subscription clients with right SDK profile
* Move all existing recording files to latest folder
* [VM/VMSS] Fix idempotency for VM/VMSS create (#3586)

2.0.7 (2017-05-30)
++++++++++++++++++
* Command paths are no longer case sensitive.
* Certain boolean-type parameters are no longer case sensitive.
* Support login to ADFS on prem server like Azure Stack
* Fix concurrent writes to clouds.config (#3255)

2.0.6 (2017-05-09)
++++++++++++++++++
* RP Auto-Reg: capture missing subscription registration error on LRO (#3268)

2.0.5 (2017-05-05)
++++++++++++++++++
* core: capture exceptions caused by unregistered provider and auto-register it
* login: avoid the bad exception when the user account has no subscription and no tenants
* perf: persist adal token cache in memory till process exits (#2603)

2.0.4 (2017-04-28)
++++++++++++++++++
* Fix bytes returned from hex fingerprint -o tsv (#3053)
* Enhanced Key Vault Certificate Download and AAD SP Integration (#3003)
* Add Python location to az —version (#2986)
* login: support login when there are no subscriptions (#2929)

2.0.3 (2017-04-17)
++++++++++++++++++
* core: fix a failure when login using a service principal twice (#2800)
* core: Allow file path of accessTokens.json to be configurable through an env var(#2605)
* core: Allow configured defaults to apply on optional args(#2703)
* core: Improved performance
* core: Support for multiple API versions
* core: Custom CA Certs - Support setting REQUESTS_CA_BUNDLE environment variable
* core: Cloud configuration - use 'resource manager' endpoint if 'management' endpoint not set

2.0.2 (2017-04-03)
++++++++++++++++++
* Avoid loading azure.storage simply to getting an internal string to be used in exceptional cases when trying to instantiate a storage data plane client. (#2673)
* [KeyVault] KeyVault create fix (#2648)
* Azure DevTest Lab command module in CLI (#2631)
* Allow = in generic update values. (#2638)
* Allowing command module authors to inject formatter class. (#2622)
* Login: skip erroneous tenant (#2634)
* Removed duplicate sql utils code (#2629)
* Refactoring SDK reflaction utils into core.sdk (#2599)
* Add blank line after each example. (#2574)
* login: set default subscription to one with the state of "Enabled" (#2575)
* Add wait commands and --no-wait support (#2524)
* choice list outside of named arguments (#2521)
* core: support login using service principal with a cert (#2457)
* Revert "get choices for completion (#2476)" (#2516)
* Add prompting for missing template parameters. (#2364)
* [KeyVault] Command fixes (#2474)
* get choices for completion (#2476)
* Fix issue with "single tuple" options_list (#2495)

2.0.1 (2017-03-13)
++++++++++++++++++

* Support setting default values for common arguments like default resource group, default web, default vm
* Fix resource_id parsing to accept 'resourcegroups'
* Mitigate AI SDK's problem with numeric in properties
* Fix KeyError: 'environmentName' on 'az account list'
* Support login to specific tenant

2.0.0 (2017-02-27)
++++++++++++++++++

* GA release


0.1.2rc2 (2017-02-22)
+++++++++++++++++++++

* Telemetry: Generate unique event ID for each exception.
* Show privacy statement on first invocation of ‘az’ command.


0.1.2rc1 (2017-02-17)
+++++++++++++++++++++

* Show commands return empty string with exit code 0 for 404 responses
* Fix: Ensure known clouds are always in cloud config
* Handle cloud switching in more user friendly way + remove context
* Add support for prompts for yes / no with -y option
* Remove list output


0.1.1b3 (2017-01-30)
++++++++++++++++++++

* Support Python 3.6.
* Support prompt for confirmations.
* Ensure booleans are lowercase in tsv.
* Handle bom on reading file.
* Catch exceptions whilst trying to check if PyPI module is available.
* Fix TSV output unable to decode non-ascii characters.
* Return empty array '[]' instead of nothing for json output.
* Table alphabetical sort if no query or table transformer set.
* Add user path expansion to file type parameters.
* Print parse errors before usage statement.


0.1.1b2 (2017-01-19)
++++++++++++++++++++

* Fix argcomplete 'default_completer' error after release of argcomplete 1.8.0.
* [Telemetry] Update instrumentation key for telemetry and use new DataModel.


0.1.1b1 (2017-01-17)
++++++++++++++++++++

* Improve @file handling logic.
* Telemetry code improvements and readability changes.
* Fix incorrect parsing of argument name when description contains ':'
* Correct endpoints for USGov.


0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
