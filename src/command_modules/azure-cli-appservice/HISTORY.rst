.. :changelog:

Release History
===============
0.1.5 (unreleased)
++++++++++++++++++++
* functionapp: add full functionapp supports, including create, show, list, delete, hostname, ssl, etc
* Adding Team Services (vsts) as a continuous delivery option to "appservice web source-control config"
* Create "az webapp" to replace "az appservice web" (for backward compat, "az appservice web" will stay for 2 releases)
* Expose arguments to configure deployment and "runtime stacks" on webapp create
* Expose "webapp list-runtimes"
* support configure connection strings (#2647)

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
