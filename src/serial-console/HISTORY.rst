Release History
===============
1.0.0b4
++++++
* Fixed `az serial-console connect` crashing with `ValueError: No value for given attribute` when the VM's boot diagnostics storage account is not accessible in the current subscription.

1.0.0b3
++++++
* Fixed an issue where admin commands were not being sent when the VM was using a custom boot diagnostics storage account.

1.0.0b2
++++++
* Changed to 2024 API version, fixes Disable API to track "properties". Essentially return to 2018 format

1.0.0b1
++++++
* Migrated to a new authentication flow to enhance overall security

0.1.8
++++++
* Changed first message flow, fixed typo

0.1.7
++++++
* Preparation for the new websocket authentication mechanism

0.1.6
++++++
* Fix pair region mapping for eastus to westus

0.1.5
++++++
* Fix resource group for custom storage account

0.1.4
++++++
* Fix repeating loading message
* Bump websocket-client version

0.1.3
++++++
* Change to use different region for url calls when custom storage account firewalls are enabled

0.1.2
++++++
* Change to make custom boot diagnostics optional

0.1.1
++++++
* Change to require custom boot diagnostics

0.1.0
++++++
* Initial release.
