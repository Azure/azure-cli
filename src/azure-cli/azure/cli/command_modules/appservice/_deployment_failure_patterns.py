# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

DEPLOYMENT_FAILURE_PATTERNS = [
    # 400 Bad Request — OneDeploy / general request validation
    {
        "errorCode": "DeploymentFailed",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Check the deployment request body and packageUri for correctness",
            "Verify the artifact is a valid deployment package",
            "Check deployment logs: 'az webapp log deployment show'"
        ]
    },
    {
        "errorCode": "InvalidArtifactType",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Use a supported artifact type: zip, war, jar, ear, lib, startup, static, script",
            "Check the 'type' query parameter in the deploy request"
        ]
    },
    {
        "errorCode": "ArtifactStackMismatch",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Ensure the artifact type matches the app's runtime stack (e.g., war requires Tomcat)",
            "Check 'az webapp config show' for the current linuxFxVersion",
            "Update the runtime stack via 'az webapp config set --linux-fx-version'"
        ]
    },
    {
        "errorCode": "MissingDeployPath",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Provide the 'path' query parameter for type=lib, type=script, or type=static",
            "Review the OneDeploy API documentation for required parameters"
        ]
    },
    {
        "errorCode": "InvalidDeployPath",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Remove trailing '/' from the deploy path",
            "Use an absolute path; do not include '..' path segments",
            "Review the deploy path for correct format"
        ]
    },
    {
        "errorCode": "InvalidPackageUri",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Verify the packageUri is a valid, accessible URL",
            "Ensure the packageUri is not empty or null in the JSON request body",
            "Test the package URL is reachable from your network"
        ]
    },
    {
        "errorCode": "CleanDeployForbidden",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Do not use clean=true when deploying to /home or /home/site",
            "Change the deploy path to a subdirectory (e.g., /home/site/wwwroot)",
            "Remove the 'clean=true' parameter from the deploy request"
        ]
    },
    {
        "errorCode": "UnsupportedArtifactType",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Use a supported artifact type: zip, war, jar, ear, lib, startup, static, script",
            "Check 'az webapp deploy --help' for valid type values"
        ]
    },
    # 409 Conflict
    {
        "errorCode": "DeploymentInProgress",
        "stage": "Deployment",
        "httpStatus": 409,
        "suggestedFixes": [
            "Wait for the current deployment to complete before starting a new one",
            "Check deployment status: 'az webapp deployment show'",
            "If stuck, restart the SCM site to release the deployment lock"
        ]
    },
    {
        "errorCode": "RunFromRemoteZipConfigured",
        "stage": "Deployment",
        "httpStatus": 409,
        "suggestedFixes": [
            "Remove WEBSITE_RUN_FROM_PACKAGE (or legacy WEBSITE_RUN_FROM_ZIP) app setting pointing to a remote URL",
            "Use 'az webapp config appsettings delete --setting-names WEBSITE_RUN_FROM_PACKAGE'",
            "Set WEBSITE_RUN_FROM_PACKAGE to 1 instead of a URL"
        ]
    },
]

# Index for O(1) lookup by error code
_PATTERN_INDEX = {p["errorCode"]: p for p in DEPLOYMENT_FAILURE_PATTERNS}


def get_failure_pattern(error_code):
    return _PATTERN_INDEX.get(error_code)


def match_failure_pattern(status_code=None, error_message=None):  # pylint: disable=too-many-return-statements,too-many-branches
    if error_message is None:
        error_message = ""

    error_lower = error_message.lower()

    if status_code == 400:
        if "not recognized" in error_lower and "type=" in error_lower:
            return get_failure_pattern("InvalidArtifactType")
        if "cannot be deployed to stack" in error_lower:
            return get_failure_pattern("ArtifactStackMismatch")
        if "artifact type" in error_lower and "not supported" in error_lower:
            return get_failure_pattern("UnsupportedArtifactType")
        if "path must be defined" in error_lower:
            return get_failure_pattern("MissingDeployPath")
        if "path cannot end with" in error_lower or "path cannot contain" in error_lower:
            return get_failure_pattern("InvalidDeployPath")
        if "invalid packageurl" in error_lower:
            return get_failure_pattern("InvalidPackageUri")
        if "clean deployments cannot be performed" in error_lower:
            return get_failure_pattern("CleanDeployForbidden")
        # Generic 400 - deployment failed pattern
        return get_failure_pattern("DeploymentFailed")
    if status_code == 409:
        if ("run-from-zip" in error_lower or
                "website_run_from_package" in error_lower or
                "website_use_zip" in error_lower):
            return get_failure_pattern("RunFromRemoteZipConfigured")
        # Generic 409 - deployment lock conflict
        return get_failure_pattern("DeploymentInProgress")
    return None
