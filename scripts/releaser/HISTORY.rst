.. :changelog:

Release History
===============


0.1.6 (2017-09-21)
++++++++++++++++++

* Script to create new Homebrew formula for Azure CLI that PRs can be created from.

0.1.5 (2017-09-11)
++++++++++++++++++

* Fix RPM script to print the Python upload script instead of automatically uploading as we need to sign first.

0.1.4 (2017-09-07)
++++++++++++++++++

* Add release script for RPM releases.

0.1.3 (2017-08-18)
++++++++++++++++++

* Fix 'packaged release archive' creation step. We now clone the repo again after pushing tags so we can use the new tags.

0.1.2 (2017-08-15)
++++++++++++++++++

* Fix Debian release script failing due to double quotes in printing the status url after the build.

0.1.1 (2017-07-31)
++++++++++++++++++

* Support releasing a module that hasn't been released before.
* Support Docker password with special characters.

0.1.0 (2017-07-05)
++++++++++++++++++

* First release.
* Push modules to Git.
* Publish all modules to PyPI.
* Create GitHub releases.
* Create and Publish packaged release archive.
* Create and Publish Docker image.
* Create and Publish Debian package.
