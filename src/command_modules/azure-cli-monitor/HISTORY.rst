.. :changelog:

Release History
===============

0.0.14
++++++
* Update for CLI core changes.

0.0.13
++++++
* Update managed SDK reference to 0.4.0
* Remove data plane SDK reference
* BREAKING CHANGE: Add multi-dimension support to metrics command

0.0.12
++++++
* Add activity-log alert commands
* Minor fixes.

0.0.11
++++++
* Add action-group commands

0.0.10 (2017-09-22)
+++++++++++++++++++
* minor fixes

0.0.9 (2017-08-28)
++++++++++++++++++
* minor fixes

0.0.8 (2017-07-07)
++++++++++++++++++
* minor fixes

0.0.7 (2017-06-21)
++++++++++++++++++
* No changes.

0.0.6 (2017-06-13)
++++++++++++++++++
* Minor fixes.

0.0.5 (2017-05-30)
+++++++++++++++++++++

* Include autoscale template file to fix `az monitor autoscale-settings get-parameters-template` command (#3349)
* BC: `monitor alert-rule-incidents list` renamed `monitor alert list-incidents`
* BC: `monitor alert-rule-incidents show` renamed `monitor alert show-incident`
* BC: `monitor metric-defintions list` renamed `monitor metrics list-definitions`
* BC: `monitor alert-rules` renamed `monitor alert`
* BC: `monitor alert create` completely revamped. `condition` and `action` no longer accepts JSON. 
	  Adds numerous parameters to simplify the rule creation process. `location` no longer required.
	  Added name or ID support for target.
	  `--alert-rule-resource-name` removed. `is-enabled` renamed `enabled` and no longer required.
	  `description` defaults based on the supplied condition. Added examples to help clarifiy the
	  new format.
* BC: Support names or IDs for `monitor metric` commands.
* `monitor alert rule update` - Added numerous convenience arguments to improve usability. Added
  examples to explain usage of the new arguments.

0.0.4 (2017-05-09)
+++++++++++++++++++++

* Minor fixes.

0.0.3 (2017-04-28)
+++++++++++++++++++++

* Bug Fix: Modeling `--actions` of `az alert-rules create` to consume JSON string (#3009)
* Bug fix - diagnostic settings create does not accept logs/metrics from show commands (#2913)

0.0.2 (2017-04-17)
+++++++++++++++++++++

* Apply core changes required for JSON string parsing from shell (#2705)

0.0.1 (2017-04-03)
+++++++++++++++++++++

* Preview release.
