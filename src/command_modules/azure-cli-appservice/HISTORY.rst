.. :changelog:

Release History
===============
0.1.33
++++++
* webapp/functionapp: improve generic update commands
* webapp/functionapp: webapp deployment source config-zip supports async operation with status updates for long running operation 

0.1.32
++++++
* webapp: fix a bug in `az webapp delete` when `--slot` is provided
* webapp: remove `--runtime-version` from `az webapp auth update` as it's not very public ready
* webapp: az webapp config set support for min_tls_version & https2.0
* webapp: az webapp create support for multicontainers

0.1.31
++++++
* (Breaking change): remove `assign-identity` which was tagged `deprecating` 2 releases ago
* webapp: capture the unhandled exception if the appservice plan doesn't exist
* `sdist` is now compatible with wheel 0.31.0

0.1.30
++++++
* webapp: az webapp update supports httpsOnly
* webapp/functionapp:  slot support for identity assign & identity show

0.1.29
++++++
* webapp/functionapp: author managed identity commands `identity assign/show`, and deprecate `assign-identity`

0.1.28
++++++
* webapp: updating tests/code for sdk update

0.1.27
++++++
* appservice: list-location: Fixes the bug where 'Free' was reported as an invalid SKU

0.1.26
++++++
* webapp backup/restore: Fix issue where restore command fails because of a null reference
* appservice: support default app service plan through `az configure --defaults appserviceplan=my-asp`

0.1.25
++++++
* fix broken webapp log tail/download
* relieve the 'kind' check on webapp/functionapp

0.1.24
++++++
* `webapp config ssl upload`: fix a bug where the hosting_environment_profile was null
* `webapp browse`: adding support for browse to handle custom domain URL
* `webapp log tail`: fixing a bug where support for slots was not working

0.1.23
++++++
* Minor fixes.

0.1.22
++++++
* Minor fixes.
* `webapp config ssl upload`: fix a bug where the hosting_environment_profile was null

0.1.21
++++++
* `webapp config ssl upload`: fix a bug in the cert name generation
* `webapp/functionapp`: ensure list/show display correct set of apps
* webapp: set WEBSITE_NODE_DEFAULT_VERSION in case where runtime is not set

0.1.20
++++++
* webapp: add deployment source config-zip support for webapps and functions apps
* webapp: use azure-mgmt-web 0.34.1
* webapp: add --docker-container-logging
* webapp: removing the 'storage' option from --web-server-logging since this is not working
* `deployment user set`: logged more informative error messages.
* functionapp: add support for creating Linux function apps
* appservice: fix list-locations

0.1.19
++++++
* webapp: fix a bug that downloaded log file might be invalid

0.1.18 (2017-10-09)
+++++++++++++++++++
* webapp: added generic update with new command: 'az webapp update'
* webapp: updating tests/code for sdk update

0.1.17 (2017-09-22)
+++++++++++++++++++
* webapp: able to update and show authentication settings using "az webapp auth update/show"

0.1.16 (2017-09-11)
+++++++++++++++++++
* webapp: able to create a webapp in a resource group other than the service plan's

0.1.15 (2017-08-31)
+++++++++++++++++++
* minor fixes

0.1.14 (2017-08-28)
+++++++++++++++++++
Breaking Change:webapp: fix inconsistencies in the output of "az webapp config appsettings delete/set"
webapp: add a new alias of '-i' for "az webapp config container set --docker-custom-image-name"
webapp: expose 'az webapp log show'
webapp: expose new arguments from 'az webapp delete' to retain app service plan, metrics or dns registration. 
webapp: detect a slot setting correctly 
webapp: add param --docker-container-logging that goes through the same logic as --web-server-logging
webapp: add premium v2 sku
webapp: add new container setting WEBSITES_ENABLE_APP_SERVICE_STORAGE

0.1.13 (2017-08-15)
+++++++++++++++++++
webapp: fix an exception when create a new git based linux webapp

0.1.12 (2017-08-11)
+++++++++++++++++++
* minor fixes

0.1.11 (2017-07-27)
+++++++++++++++++++
* webapp: Add generate container CI URL for Web App
* webapp: fix the bug that listing linux webapp returns nothing
* webapp: setting runtime is mandatory for linux
* webapp: use only linux-fx-version instead of CUSTOM_DOCKER_IMAGE_NAME

0.1.10 (2017-07-07)
+++++++++++++++++++
* webapp: support to retrieve creds from acr

0.1.9 (2017-06-21)
++++++++++++++++++
* BC: webapp: remove all commands under 'az appservice web'

0.1.8 (2017-06-13)
++++++++++++++++++
* webapp: mask docker registry passwords from 'webapp appsettings/container' commands' output (#3656)
* webapp: ensure default browser is used on osx and w/o error on launching (#3623)
* webapp: improve the help of 'az webapp log tail/download' (#3624)
* webapp: expose traffic-routing command to configure static routing (#3566)

0.1.7 (2017-05-30)
++++++++++++++++++++
* webapp: add reliability fixes in configuring source control (#3245)
* BC: az webapp config update: Remove unsupported --node-version argument for Windows webapps. Instead use "az webapp config appsettings set" with the WEBSITE_NODE_DEFAULT_VERSION key.

0.1.6 (2017-05-09)
++++++++++++++++++++
* webapp: fix broken log tail commands

0.1.5 (2017-05-05)
++++++++++++++++++++
* functionapp: add full functionapp supports, including create, show, list, delete, hostname, ssl, etc
* Adding Team Services (vsts) as a continuous delivery option to "appservice web source-control config"
* Create "az webapp" to replace "az appservice web" (for backward compat, "az appservice web" will stay for 2 releases)
* Expose arguments to configure deployment and "runtime stacks" on webapp create
* Expose "webapp list-runtimes"
* support configure connection strings (#2647)
* support slot swap with preview

0.1.4 (2017-04-28)
++++++++++++++++++++

* Rename arg of '-n/--name' to '--hostname', and wire up default webapp name (#2946, #2947, #2949)
* Polish errors from appservice commands (#2948)
* New packaging system.

0.1.3 (2017-04-17)
++++++++++++++++++++
* Use the app service plan's resource group for cert operations (#2750)

0.1.2 (2017-04-03)
++++++++++++++++++++

* appservice: rollback the change of auto creating plans (#2671)
* Check sku when creating linux ASP (#2651)
* appservice: include site config on cloning slot (#2644)
* appservice: support to get external ip address used for DNS A records (#2627)
* appservice: support binding wildcard certificates (#2625)
* appservice:improve table output format of web show/list (#2614)
* appservice: support list publishing profiles (#2504)

0.1.1b6 (2017-03-13)
++++++++++++++++++++

* AppService - Trigger source control sync after config (#2326)
* Misc bug fixes(locations, trace when browse, polish error) (#2407)
* Remove tab completion from 'appservice plan create --name'. (#2404)
* Fix a bug on detecting argument value for site configs (#2392)
* Fix slot related bugs


0.1.1b5 (2017-02-27)
++++++++++++++++++++

* Expose git token reset command and add more test coverage


0.1.1b4 (2017-02-22)
++++++++++++++++++++

* Documentation fixes.


0.1.1b3 (2017-02-17)
++++++++++++++++++++

* Add backup and restore commands
* Add App Service SSL commands
* Fixes bug with adding hostname to web app
* Prompts for yes / no use the -y option rather than --force
* Show commands return empty string with exit code 0 for 404 responses


0.1.1b2 (2017-01-30)
++++++++++++++++++++

* Add user path expansion to file type parameters.
* Add confirmation prompt to 'appservice plan delete'.
* Support Python 3.6.

0.1.1b1 (2017-01-17)
+++++++++++++++++++++

* Add webapp start

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
