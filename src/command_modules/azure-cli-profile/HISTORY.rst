.. :changelog:

Release History
===============
2.0.25
++++++
* minor changes

2.0.24
++++++
* `disk create`: fix a bug that source detection is not accurate
* BREAKING CHANGE: remove --msi-port/--identity-port as they are no longer used

2.0.23
++++++
* Fix typo in `az account get-access-token` short summary.

2.0.22
++++++
* account list: handle accounts which come from CLI 1.0/ASM mode
* (Breaking change): remove `--msi` & `--msi-port` which were tagged `deprecating` 2 releases ago
* `sdist` is now compatible with wheel 0.31.0

2.0.21
++++++
* az login: warn on using --identity-port/--msi-port as they become useless with imds support

2.0.20
++++++
* az login: use `--identity` and deprecate `--msi`
* enable login/logout commands in cloud shell

2.0.19
++++++
* Enable `az login` in from interactive mode.

2.0.18
++++++
* ensure 'get-access-token' work inside a VM with identity

2.0.17
++++++
* Update for CLI core changes.

2.0.16
++++++
* support login with user assigned identities

2.0.15
++++++
* minor fixes

2.0.14 (2017-10-09)
+++++++++++++++++++
* minor fixes

2.0.13 (2017-09-22)
+++++++++++++++++++
* minor fixes

2.0.12 (2017-09-11)
+++++++++++++++++++
* minor fixes

2.0.11 (2017-08-28)
+++++++++++++++++++
* login: expose `--msi` and `--msi-port` to login using Virtual machine's identity

2.0.10 (2017-08-11)
+++++++++++++++++++
* account list: add `--refresh` to sycn up the latest subscriptions from server

2.0.9 (2017-07-27)
++++++++++++++++++
support login inside a VM with a managed identity

2.0.8 (2017-07-07)
++++++++++++++++++
account show: support output in SDK auth file format

2.0.7 (2017-06-21)
++++++++++++++++++
* No changes.

2.0.6 (2017-06-13)
++++++++++++++++++
* Minor fixes.

2.0.5 (2017-05-30)
++++++++++++++++++
* Output deprecating information on using '--expanded-view'
* Add get-access-token command to provide raw AAD token
* Support login with a user account with no associated subscriptions

2.0.4 (2017-04-28)
++++++++++++++++++
* Support login when there are no subscriptions found (#2560)
* Support short param name in az account set --subscription (#2980)

2.0.3 (2017-04-17)
++++++++++++++++++

* API Profile Support (#2834)
* Fix #2839. (#2844)
* [Network] Make DNS Zone record imports relative (#2825)
* [Network] VPN-connection shared key fixes (#2798)
* [Network] Support active-active VNet gateways (#2751)
* [Network] Remove nulls from VPN connection show/list output (#2748)
* Alter JSON string parsing from shell (#2705)

2.0.2 (2017-04-03)
++++++++++++++++++

* account: do not show not enabled subscription by default (#2664)
* core: support login using service principal with a cert (#2457)

2.0.1 (2017-03-13)
++++++++++++++++++

* Fix KeyError: 'environmentName' on 'az account list' (#2358)
* Core: Support login to specific tenant (#2327)


2.0.0 (2017-02-27)
++++++++++++++++++

* GA release.


0.1.2rc2 (2017-02-22)
+++++++++++++++++++++

* Documentation updates.


0.1.2rc1 (2017-02-17)
+++++++++++++++++++++

* Fixes KeyError: 'environmentName' after log in
* Handle cloud switching in more user friendly way

0.1.1b2 (2017-01-30)
+++++++++++++++++++++

* Add subscription id to ‘az account list’ table format.
* Support Python 3.6.

0.1.1b1 (2017-01-17)
+++++++++++++++++++++

* Preview release (no source code changes since previous version).

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
