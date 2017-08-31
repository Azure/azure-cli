.. :changelog:

Release History
===============

1.0.8 (2017-08-31)
++++++++++++++++++
* Deprecating all commands in favor of Service Fabric CLI (sfctl)

1.0.7 (2017-08-28)
++++++++++++++++++
* Simplified registry user/pass rules for command.
* Fixed password prompt for user even after passing in the param.
* Supports None registry_cred.

1.0.6 (2017-08-11)
++++++++++++++++++
* minor fixes

1.0.5 (2017-07-07)
++++++++++++++++++
* Fixes an issue with large files in applications being truncated on upload (#3666)

1.0.4 (2017-06-21)
++++++++++++++++++
* No changes.

1.0.3 (2017-06-13)
++++++++++++++++++
* Adding tests for Service Fabric commands and fixing some arugment parsing logic (#3424)

1.0.2 (2017-05-30)
++++++++++++++++++

* Fix numerous Service Fabric commands (#3234)

1.0.1 (2017-05-09)
++++++++++++++++++

* Minor fixes.

1.0.0 (2017-05-05)
++++++++++++++++++

* Initial release of Service Fabric module. This corresponds to 5.6 Service Fabric product release.
* Fixing certain commands that were previously reporting syntax errors even though the combination of arguments was valid.
* Adding tests for custom commands including recordings for some commands.
