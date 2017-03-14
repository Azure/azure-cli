.. :changelog:

Release History
===============

0.1.1 (2017-03-13)
++++++++++++++++++

* Return 200 if webhook is skipped by the bot instead of 400.
* Create release on async thread to prevent GitHub webhook timeouts.
* Clone and tag the correct commit to prevent race conditions with multiple merges to the repo at once.

0.1.0 (2017-01-13)
++++++++++++++++++

* First release.
* Uploads source code, .tar.gz and .whl assets to the GitHub release.
* Bot comments on opened Release PR with checklist
* Bot comments if release successful or not
* Bot applies 'Release' label automatically
* Bot creates a GitHub release
