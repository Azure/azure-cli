.. :changelog:

Release History
===============
2.0.5 (Unreleased)
^^^^^^^^^^^^^^^^^^
* core: capture exceptions caused by unregistered provider and auto-register it   

2.0.4 (2017-04-28)
^^^^^^^^^^^^^^^^^^
* Fix bytes returned from hex fingerprint -o tsv (#3053)
* Enhanced Key Vault Certificate Download and AAD SP Integration (#3003)
* Add Python location to ‘az —version’ (#2986)
* login: support login when there are no subscriptions (#2929)

2.0.3 (2017-04-17)
^^^^^^^^^^^^^^^^^^
*core: fix a failure when login using a service principal twice (#2800)
*core: Allow file path of accessTokens.json to be configurable through an env var(#2605)
*core: Allow configured defaults to apply on optional args(#2703)
*core: Improved performance
*core: Support for multiple API versions
*core: Custom CA Certs - Support setting REQUESTS_CA_BUNDLE environment variable
*core: Cloud configuration - use 'resource manager' endpoint if 'management' endpoint not set

2.0.2 (2017-04-03)
^^^^^^^^^^^^^^^^^^
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
^^^^^^^^^^^^^^^^^^

* Support setting default values for common arguments like default resource group, default web, default vm
* Fix resource_id parsing to accept 'resourcegroups'
* Mitigate AI SDK's problem with numeric in properties
* Fix KeyError: 'environmentName' on 'az account list'
* Support login to specific tenant

2.0.0 (2017-02-27)
^^^^^^^^^^^^^^^^^^

* GA release


0.1.2rc2 (2017-02-22)
^^^^^^^^^^^^^^^^^^^^^

* Telemetry: Generate unique event ID for each exception.
* Show privacy statement on first invocation of ‘az’ command.


0.1.2rc1 (2017-02-17)
^^^^^^^^^^^^^^^^^^^^^

* Show commands return empty string with exit code 0 for 404 responses
* Fix: Ensure known clouds are always in cloud config
* Handle cloud switching in more user friendly way + remove context
* Add support for prompts for yes / no with -y option
* Remove list output


0.1.1b3 (2017-01-30)
^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^

* Fix argcomplete 'default_completer' error after release of argcomplete 1.8.0.
* [Telemetry] Update instrumentation key for telemetry and use new DataModel.


0.1.1b1 (2017-01-17)
^^^^^^^^^^^^^^^^^^^^

* Improve @file handling logic.
* Telemetry code improvements and readability changes.
* Fix incorrect parsing of argument name when description contains ':'
* Correct endpoints for USGov.


0.1.0b11 (2016-12-12)
^^^^^^^^^^^^^^^^^^^^^

* Preview release.
