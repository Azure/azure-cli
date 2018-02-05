Onboarding Best Practices
=========================

You'll have a dev contact on the CLI team. Early and frequent communication with this contact is essential to ensuring a smooth onboarding.

Suggested timeline:

- **Initial Kickoff:** Reach out to your contact on the CLI team. Set up a short 30 minute Skype call to discuss initial questions.

- **Initial Review:** Create a few commands. Schedule a short 30 minute Skype screen-share to demo your commands. This is crucial! Teams have created entire modules using anti-patterns, resulting in comment-filled PRs and last-minute rework! A quick command review would have prevented this.

- **During command authoring:** Run *check_style --module {your module}* frequently to ensure you are staying on type of style issues that will stall your build when you submit a PR.

- **Period Command Review:** As practical.

- **Just before opening PR:** Run *check_style --ci* and *run_tests* to address issues before the CI finds them.

- **2 weeks before desired release date:** Open PR in CLI repo (public or private depending on your service). Request your CLI contact as the reviewer for the PR.

- **1 week prior to desired release date:** Hopefully, PR is merged! Download the edge build and try it out. Submit follow-up PRs to address any small issues. Anything caught before release is not a breaking change!

Inital Pull Request Guidance
============================

Reviewing a new command module is very difficult, so the PR shouldn't be the first time we see your module! The two most important things for your initial PR are:

1. Recorded Scenario Tests for **all** new commands. This lets us know that your commands *work*.
2. The help output of:

   - all groups and subgroups (i.e. `az vm -h`)
   
   - all non-trivial commands (commands except `list`, `show`, `delete`)
   
If you and your CLI contact have been doing regular command reviews, the PR should merely be a formality. If you haven't been conducting regular reviews, the help output allows us to quickly identify holes and anti-patterns to get you on the right track. Most teams post the help output in the PR comments. You can also put them in a TXT document if you choose.

Lessons Learned
===============

1. If you have a supporting resource (say your resource takes a reference to a VNet), do not expose a bunch of parameters like `--vnet-name`, `--vnet-rg`, `--vnet-id`. Instead, expose a single parameter: `--vnet` which will accept either the VNet name or the VNet ARM ID. The ARM ID is required for all cross-RG and cross-subscription scenarios!
2. Avoid accepting JSON objects! They are confusing to users, who often struggle with where to find the proper format. If you feel like JSON is the best solution, reach out to your CLI contact!
