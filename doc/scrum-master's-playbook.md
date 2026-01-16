The Scrum Master role of CLI is primarily release-focused, but also includes several ongoing responsibilities:
- Host the weekly sync meeting every Thursday.
- Attend office hours held on Tuesday and Friday.
  - Join this [channel](https://teams.microsoft.com/l/chat/19:e4bb31fd84ab4f2f9375ad848e8a80fa@thread.v2/conversations?context=%7B%22contextType%22%3A%22chat%22%7D). If there is any topic related to CLI requested, make sure to join the call. Request product manager to add you to the meeting series.
- Monitor Batched CI on a regular basis:

  ![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/batched-ci.png)
  - Ensure that Batched CI is in a normal state before the release. If there are any failures, coordinate with the corresponding engineer to resolve them.

The Azure CLI release process is highly automated **with some manual intervention steps** and has evolved to use both Azure DevOps and GitHub Actions.

## Release is about to happen
You can find key dates for each sprint in the Azure CLI [milestones](https://github.com/Azure/azure-cli/milestones). For each sprint, a few days before the release starts, remind the relevant teammates to complete and merge the required pull requests.

Schedule release meetings in advance and involve the Azure CLI Dev distribution list:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/calendar-sample.png)
- Phase 1: will take place on a Tuesday, make sure that is scheduled after the code complete time.
- Phase 1.5: will take place on the next coming Wednesday.
- Phase 2: will take place on next Tuesday.

Overall, these phases span seven weekdays across two working weeks.

## Phase 1
1. Triggering [Prepare for Release Build](https://dev.azure.com/azclitools/release/_release?definitionId=12) pipeline.
2. Reviewing the Release PR to verify release history and its correctness.

Trigger **Prepare for Release Build** pipeline. Enter the release number and create a release:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase1-1.png)

It will create a new release in azure-cli and a new PR to merge into `dev` branch. Verify the correctness of the changelog together with colleagues. [Sample](https://github.com/Azure/azure-cli/pull/32410).

After PR gets merged, resume the **Prepare for Release Build** pipeline for completion.

It will trigger [CI pipeline](https://dev.azure.com/azclitools/release/_build?definitionId=757) on the release branch. Make sure that is successfully completed and the build number, e.g., #20251111.1 is needed in Phase 1.5 for verification.

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase1-2.png)

## Phase 1.5
1. Triggering [Azure CLI Release-Corp](https://dev.azure.com/azclitools/release/_release?definitionId=27) pipeline.
2. Starting [Azure CLI Release-AME](https://msazure.visualstudio.com/One/_release?definitionId=67158) pipeline.
3. Inform Azure Cloud Shell team via email about the new release artifact availability for their consumption.

Trigger **Azure CLI Release-Corp** pipeline, enter the details:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase1.5-1.png)

There is a task which will create a PR in `MicrosoftDocs/azure-docs`. [Sample](https://github.com/MicrosoftDocs/azure-docs-cli/pull/5626):

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase1.5-2.png)

There is a task with instructions on how to trigger **Azure CLI Release-AME** pipeline:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase1.5-3.png)

Sample instructions and input the details during **Azure CLI Release-AME** pipeline creation:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase1.5-4.png)
![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase1.5-5.png)

Once it is created, resume the task in **Azure CLI Release-Corp** pipeline.

There is a task "Deliver to Cloud Shell". Once it turns successfully, let's send an email to Cloud Shell team:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase1.5-6.png)

The task gives you the email text, please replace the release number details. E.g., please refer to the following screenshot:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase1.5-7.png)

Currently, ownership of this email-sending task rotates between CLI and PowerShell teams. Please coordinate accordingly.

Make sure that **Azure CLI Release-Corp** and **Azure CLI Release-AME** pipelines execute until "Wait Until Tuesday" task:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase1.5-8.png)

## Phase 2
Resume the following tasks in **Azure CLI Release-Corp** pipeline:
1. Wait Until Tuesday.
2. Release Notes (after merge).

Resume **Azure CLI Release-AME** pipeline and wait for its completion. Once the pipeline is done, resume the following task for completion:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase2-1.png)

"Publish Windows Artifacts" involves updating links inside aka.ms. Follow the instructions listed in the task and resume the task to completion:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase2-2.png)

As part of "Release Notes" task perform the instructions. Manually complete the changelog from "Core" and review/approve/merge (squash) the release notes PR to main branch.

As part of "Make Doc Live", a PR gets created to merge main branch to live branch. Wait for the following 2 commits appear (typically takes ~2 hours). [Sample](https://github.com/MicrosoftDocs/azure-docs-cli/pull/5637):

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase2-3.png)

Review and merge (do not squash) the above PR:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase2-4.png)

As part of "Publish to Homebrew", a PR gets created in [homebrew-core](https://github.com/Homebrew/homebrew-core). Wait for that PR to get approved and merged by community and resume this task to completion:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase2-7.png)

Once all of above tasks are completed. The final step is to send communication to partner teams:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase2-5.png)

The task gives you the email text, please replace the release number details:

![](https://raw.githubusercontent.com/Azure/azure-cli/refs/heads/dev/doc/assets/phase2-6.png)
