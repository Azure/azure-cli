.. :changelog:

Release History
===============

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
