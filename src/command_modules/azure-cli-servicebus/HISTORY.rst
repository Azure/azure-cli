.. :changelog:

Release History
===============

0.2.2
+++++
* Minor fixes

0.2.1
+++++
* Added migration command group to migrate a namespace from Service Bus Standard to Premium

* Added new optional properties to Service Bus queue and Subscription
    --enable-batched-operations and --enable-dead-lettering-on-message-expiration in queue
    --dead-letter-on-filter-exceptions in subscriptions

0.2.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.

0.1.3
++++++
* Minor fixes.

0.1.2
++++++

* Fix package wheel
* `sdist` is now compatible with wheel 0.31.0

0.1.1
+++++
* Suppress the service bus extension from being loaded now.


0.1.0
+++++

* Initial release.

