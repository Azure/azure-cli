.. :changelog:

Release History
===============

0.0.14
++++++
* Be more resilient to system error when removing an extension.

0.0.13
++++++
* Pin version of `wheel` so extensions can get metadata shown again.

0.0.12
++++++
* Linux distro check message should be output to debug instead of warning.
* `sdist` is now compatible with wheel 0.31.0

0.0.11
++++++
* Preview extensions: Show message on `az extension add` if extension is in preview
* BC: `az extension list-available` - The full extension data is now available with `--show-details`
* `az extension list-available` - A simplified view of the extensions available is now shown by default

0.0.10
+++++++
* Added check to warn user if used distro is different then the one stored in package source file, as this may lead into errors. 

0.0.9
++++++
* Added support for --pip-proxy parameter to az extension add/update commands.
* Added support for --pip-extra-index-urls argument to az extension add and update commands.

0.0.8
++++++
Minor fixes

0.0.7
++++++
* Update for CLI core changes.

0.0.6
+++++

* `az extension add --name NAME` - Allows users to add an extension by name
* `az extension list-available` - Allows users to list the available extensions in the index
* `az extension update --name NAME` - Allows users to update an extension

0.0.5
+++++

* minor fixes

0.0.4 (2017-10-09)
++++++++++++++++++

* minor fixes

0.0.3 (2017-09-22)
++++++++++++++++++

* minor fixes

0.0.2 (2017-09-11)
++++++++++++++++++

* Initial Release.
