.. :changelog:

Release History
===============

0.3.0
+++++
* Added New cmdlets for Service Bus Standard to Premium namespace:
    'az servicebus migration start', 'az servicebus migration show', 'az servicebus migration complete', 'az servicebus migration stop',
    'az servicebus migration delete'

* Added new optional properties to Service Bus queue and Subscription
    - enable_batched_operations and dead_lettering_on_filter_evaluation_exceptions in queue
    - dead_lettering_on_filter_evaluation_exceptions in subscriptions

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

