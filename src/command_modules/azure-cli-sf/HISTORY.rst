.. :changelog:

Release History
===============
1.0.3 (2017-06-13)
^^^^^^^^^^^^^^^^^^
* Remove useless line-too-long suppression
* Fix various pylint disable rules
* Eliminating too-many-arguments pylint disable rule (#3583)
* Adding tests for Service Fabric commands and fixing some arugment parsing logic (#3424)
* Remove various pylint disable statements

1.0.2 (2017-05-30)
++++++++++++++++++

* Fix numerous Service Fabric commands (#3234)

1.0.1 (2017-05-09)
++++++++++++++++++

* Minor fixes.

1.0.0 (2017-05-05)
++++++++++++++++++

* Initial release of Service Fabric module. This corresponds to 5.6 Service
Fabric product release.

Unreleased
++++++++++

* Fixing certain commands that were previously reporting syntax errors even though
the combination of arguments was valid.
* Adding tests for custom commands including recordings for some commands.
