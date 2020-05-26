Service Onboarding Guide
======

This article aims to provide a guide for service team to request a feature in Azure CLI.

We encourage you to contact Azure CLI team as early as possible even if the service is not ready yet so that the work can be planned in advance. We officially support three kinds of communication channels, namely Github, email and Teams. The email address of Azure CLI is azpycli@microsoft.com.

The only mandatory action is opening an issue at [Service Team Support Request](https://github.com/Azure/azure-cli/issues/new?assignees=&labels=&template=Service_team_request.md&title=). Fill in the blanks of the issue template as detailed as possible to help Azure CLI team understand the feature request without difficulties and deliver the feature as expected.

Information required from service team:

1. Resource provider. What is the Azure resource provider your feature is part of?
2. Description of feature or work requested. Provide a brief description of the feature or work requested. A link to conceptual documentation may be helpful too.
3. Minimum API version required. What is the minimum API version of your service required to implement your feature?
4. Swagger link. Provide a link to the location of your feature(s) in the REST API specs repo. If your feature(s) has corresponding commit or pull request in the REST API specs repo, provide them. This should be on the master branch of the REST API specs repo.
5. Target date. If you have a target date for release of this feature/work, please provide it. While we can't guarantee these dates, it will help us prioritize your request against other requests.
6. Where do you want the feature locate? Module or Extension? A [Comparision](https://github.com/Azure/azure-cli/blob/dev/doc/onboarding_guide.md#extension-vs-module).
7. Status of the service and swagger. Preview? GA? Is the swagger change merged to master branch?
8. Examples of the feature. Usually REST API specs repo should contain examples. An independent documentation or tutorial is also OK.  
9. Prerequisite to use this feature. Whitelist subscription? Register the feature for subscription? Is it available in public Azure?

The overall workflow is: (1) Swagger and service ready -> (2) Azure Python SDK ready (PyPI) -> (3) Azure CLI commands ready. This is the easiest and most efficient way that Azure CLI collaborates with service team. Service should be well-designed, stable and tested before asking Azure CLI support. However, sometimes, some features are urgent due to some reasons like bad planning. If we wait the previous phase to finish before start the next phase, it could last a very long time to deliver the feature. We support developing Azure CLI commands before the service is ready. The requirements are (1) service is available for testing (2) Azure Python SDK is available. A private build is allowed. Once the service is published and SDK is published in PyPI, we will release CLI commands. Please notice that this is not a recommended way of collaboration because service tends to change even involves breaking changes without cost before this version of service is announced released.

Feel free to contact Azure CLI team at any time through any channels. We are passionate to build the world-class cloud product.
