.. :changelog:

Release History
===============

0.4.2
+++++
Minor fixes.

0.4.1
+++++
* ams streaming-endpoint [start | stop | create | update] : added 'wait' command
* ams live-event [create | start | stop | reset] : added 'wait' command

0.4.0
+++++
* BREAKING CHANGE: asset group command `ams asset get-streaming-locators` renamed `ams asset list-streaming-locators`.
* BREAKING CHANGE: streaming-locator group command `ams streaming-locator get-content-keys` renamed `ams streaming-locator list-content-keys`.

0.3.2
+++++
* Minor fixes

0.3.1
+++++
* Minor fixes

0.3.0
+++++
* New command groups added:
    `ams account-filter`
    `ams asset-filter`
    `ams content-key-policy`
    `ams live-event`
    `ams live-output`
    `ams streaming-endpoint`
    `ams mru`
* New commands to existing groups added:
    `ams account check-name`
    `ams job update`
    `ams asset get-encryption-key`
    `ams asset get-streaming-locators`
    `ams streaming-locator get-content-keys`
* Encryption parameters support in `ams streaming-policy create` command added.
* `ams transform output remove` now can be performed by passing the output index to remove.
* `--correlation-data` and `--label` arguments added for `ams job` command group.
* `--storage-account` and `--container` arguments added for `ams asset` command group.
* Default values for expiry time (Now+23h) and permissions (Read) in `ams asset get-sas-url` command added.
* BREAKING CHANGE: `ams streaming locator` base command replaced with `ams streaming-locator`.
* BREAKING CHANGE: `--content-keys` argument from `ams streaming locator` command updated.
* BREAKING CHANGE: `--content-policy-name` renamed to `--content-key-policy-name` in `ams streaming locator` command.
* BREAKING CHANGE: `ams streaming policy` base command replaced with `ams streaming-policy`.
* BREAKING CHANGE: `--preset-names` argument replaced with `--preset` in `ams transform` command group. Now you can only set 1 output/preset at a time (to add more you have to run `ams transform output add`). Also, you can set custom StandardEncoderPreset by passing the path to your custom JSON.
* BREAKING CHANGE: `--output-asset-names ` renamed to `--output-assets` in `ams job start` command. Now it accepts a space-separated list of assets in 'assetName=label' format. An asset without label can be sent like this: 'assetName='.

0.2.4
+++++
* Minor fixes

0.2.3
+++++
* Minor fixes

0.2.2
+++++
* Minor changes

0.2.1
+++++
* Consuming multi api azure.mgmt.authorization package

0.2.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.

0.1.1
+++++
* Minor changes

0.1.0
+++++
* Initial release of module.
