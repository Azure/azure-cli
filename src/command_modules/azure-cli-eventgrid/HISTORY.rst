.. :changelog:

Release History
===============

0.2.1
+++++
* Added support for specifying deadletter destination for an event subscription.
* Added support for using storage queue as a destination for an event subscription.
* Added support for using hybrid connection as a destination for an event subscription.
* Added support for specify retry policy parameters for an event subscription.
* Added a warning message for manual handshake validation when Webhook as destination is used for an event subscription.
* Added source-resource-id parameter for all event subscription related commands and mark all other source resource related parameters as deprecated.
* Enhance the event subscription list commands to resolve usability issues.

0.2.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.

0.1.13
++++++
* Minor fixes.

0.1.12
++++++
* `sdist` is now compatible with wheel 0.31.0

0.1.11
++++++
* Minor fixes.

0.1.10
++++++
* Minor fixes.

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

