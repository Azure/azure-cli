.. :changelog:

Release History
===============

0.1.9
+++++
* Minor fixes.

0.1.8
+++++
* Minor fixes.

0.1.7
+++++
* BC: Removed the `az eventgrid topic event-subscription` commands. The corresponding `az eventgrid event-subscription` commands can now be used to manage event subscriptions for topics.
* BC: Removed the `az eventgrid resource event-subscription` commands. The corresponding `az eventgrid event-subscription` commands can now be used to manage event subscriptions for Azure resources.
* BC: Removed the `az eventgrid event-subscription show-endpoint-url` command. This can now be achieved using `az eventgrid event-subscription show` command with the --include-full-endpoint-url parameter.
* Added a new command `az eventgrid topic update`.
* Added a new command `az eventgrid event-subscription update`.
* Added --ids parameter for `az eventgrid topic` commands.
* Added tab completion support for topic names.

0.1.6
+++++
* minor fixes

0.1.5
+++++
* minor fixes

0.1.4 (2017-09-22)
++++++++++++++++++

* Using 0.2.0 of Python SDK

0.1.3 (2017-08-28)
++++++++++++++++++
* minor fixes

0.1.2 (2017-08-15)
++++++++++++++++++

* Added SDK dependencies.

0.1.1 (2017-08-11)
++++++++++++++++++

* Initial release.

