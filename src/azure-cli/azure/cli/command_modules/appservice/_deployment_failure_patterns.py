# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Well-known Kudu deployment failure patterns for az webapp deploy / az functionapp deploy.

Each pattern maps an errorCode to its deployment stage and suggested fixes.
Error codes and messages are sourced from the KuduLite deployment engine.
These patterns are used by the context-enriched error handler to produce actionable diagnostics
instead of generic HTTP status code messages.
"""

DEPLOYMENT_FAILURE_PATTERNS = [
    # -----------------------------------------------------------------------
    # 400 Bad Request — OneDeploy / general request validation
    # -----------------------------------------------------------------------
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
            "Check 'az webapp config show' for the current linuxFxVersion or windowsFxVersion",
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
        "errorCode": "InvalidDeploymentStatus",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Only mark deployments with 'Success' status as active",
            "Verify the deployment completed successfully before setting it as active"
        ]
    },
    {
        "errorCode": "NoFileUploaded",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Ensure a file is included in the deployment request body",
            "Check that the upload did not fail silently due to a network issue",
            "Retry the deployment with the correct file"
        ]
    },
    {
        "errorCode": "UnsupportedFileType",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Only .zip files are supported for QuickDeploy",
            "Package your application as a .zip file before deploying",
            "Use OneDeploy for non-zip artifact types"
        ]
    },
    {
        "errorCode": "QuickDeployPrepareFailed",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Retry the deployment",
            "Check available disk space on the App Service plan",
            "Reduce the deployment artifact size"
        ]
    },
    {
        "errorCode": "QuickDeployInitFailed",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Retry the deployment",
            "Restart the SCM site and try again",
            "Check deployment logs for initialization errors"
        ]
    },
    {
        "errorCode": "InvalidDeploymentId",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Provide a valid GUID format for the deployment ID",
            "Omit the deployment ID to let the system generate one"
        ]
    },
    # -----------------------------------------------------------------------
    # 400 Bad Request — ZipDeploy validation
    # -----------------------------------------------------------------------
    {
        "errorCode": "ZipDeployMalformedUri",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Verify the package URI is well-formed (scheme, host, path)",
            "Test the package URL independently before deploying"
        ]
    },
    {
        "errorCode": "ZipDeployUriInaccessible",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Verify the package URL is reachable from the App Service network",
            "Check SAS token expiration if using Azure Storage",
            "Ensure any firewall rules allow access from App Service"
        ]
    },
    {
        "errorCode": "ZipDeployInsufficientDisk",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Reduce the deployment package size",
            "Scale up the App Service plan for more disk space",
            "Clean up previous deployments or temp files on the app"
        ]
    },
    {
        "errorCode": "ZipDeployRuntimeMismatch",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Ensure the zip package language matches FUNCTIONS_WORKER_RUNTIME",
            "Update FUNCTIONS_WORKER_RUNTIME app setting to match the deployed code",
            "Check 'az functionapp config appsettings list' for FUNCTIONS_WORKER_RUNTIME"
        ]
    },
    {
        "errorCode": "ZipDeployRunFromPackageConflict",
        "stage": "Deployment",
        "httpStatus": 400,
        "suggestedFixes": [
            "Remove or update the WEBSITE_RUN_FROM_PACKAGE app setting pointing to a remote URL",
            "Use 'az webapp config appsettings set' to clear WEBSITE_RUN_FROM_PACKAGE",
            "Deploy directly instead of using run-from-package"
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
    # -----------------------------------------------------------------------
    # 403 Forbidden
    # -----------------------------------------------------------------------
    {
        "errorCode": "ScmDisabled",
        "stage": "Deployment",
        "httpStatus": 403,
        "suggestedFixes": [
            "Enable SCM access in the app settings",
            "Remove any app setting that disables the SCM site",
            "Check 'az webapp config show' for scmType and related settings"
        ]
    },
    # -----------------------------------------------------------------------
    # 404 Not Found
    # -----------------------------------------------------------------------
    {
        "errorCode": "RepositoryNotFound",
        "stage": "Deployment",
        "httpStatus": 404,
        "suggestedFixes": [
            "Perform an initial deployment before attempting redeployment",
            "Verify the app has a git repository initialized on the SCM site"
        ]
    },
    {
        "errorCode": "DeploymentNotFound",
        "stage": "Deployment",
        "httpStatus": 404,
        "suggestedFixes": [
            "Verify the deployment ID is correct",
            "List existing deployments: 'az webapp deployment list'",
            "The deployment may have been cleaned up; redeploy instead"
        ]
    },
    {
        "errorCode": "LogNotFound",
        "stage": "Deployment",
        "httpStatus": 404,
        "suggestedFixes": [
            "Verify the deployment ID and log ID are correct",
            "List deployment logs: 'az webapp log deployment show'"
        ]
    },
    {
        "errorCode": "NoDeploymentsExist",
        "stage": "Deployment",
        "httpStatus": 404,
        "suggestedFixes": [
            "Deploy the website first before requesting a deployment script",
            "Use 'az webapp deploy' to deploy"
        ]
    },
    {
        "errorCode": "CustomDeployScriptInUse",
        "stage": "Deployment",
        "httpStatus": 404,
        "suggestedFixes": [
            "This operation is not supported when a custom deployment script is configured",
            "Remove the custom deployment script (.deployment file) if not needed"
        ]
    },
    {
        "errorCode": "QuickDeployDisabled",
        "stage": "Deployment",
        "httpStatus": 404,
        "suggestedFixes": [
            "Enable the QuickDeploy feature flag on the app",
            "Use standard ZipDeploy or OneDeploy instead"
        ]
    },
    {
        "errorCode": "RouteNotFound",
        "stage": "Deployment",
        "httpStatus": 404,
        "suggestedFixes": [
            "Verify the deployment API endpoint path is correct",
            "Check the Kudu/SCM API documentation for valid routes"
        ]
    },
    # -----------------------------------------------------------------------
    # 409 Conflict
    # -----------------------------------------------------------------------
    {
        "errorCode": "AutoSwapInProgress",
        "stage": "Deployment",
        "httpStatus": 409,
        "suggestedFixes": [
            "Wait for the auto swap operation to complete before deploying",
            "Check slot swap status: 'az webapp deployment slot list'",
            "Retry the deployment after the swap finishes"
        ]
    },
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
            "Remove WEBSITE_RUN_FROM_PACKAGE or WEBSITE_USE_ZIP app setting pointing to a remote URL",
            "Use 'az webapp config appsettings delete --setting-names WEBSITE_RUN_FROM_PACKAGE'",
            "Deploy to a staging slot instead"
        ]
    },
    {
        "errorCode": "DeploymentIdExists",
        "stage": "Deployment",
        "httpStatus": 409,
        "suggestedFixes": [
            "Use a unique deployment ID for each deployment",
            "Omit the deployment ID to let the system generate one",
            "Delete the existing deployment before reusing its ID"
        ]
    },
    {
        "errorCode": "DeploymentLockFailed",
        "stage": "Deployment",
        "httpStatus": 409,
        "suggestedFixes": [
            "Wait and retry — another deployment may be in progress",
            "Restart the SCM site to release stale locks",
            "Check if another CI/CD pipeline is deploying concurrently"
        ]
    },
    # -----------------------------------------------------------------------
    # 499 Client Closed Request
    # -----------------------------------------------------------------------
    {
        "errorCode": "ClientDisconnected",
        "stage": "Deployment",
        "httpStatus": 499,
        "suggestedFixes": [
            "Retry the deployment with a stable network connection",
            "Increase client timeout settings",
            "Use async deployment (--async true) for long-running deploys"
        ]
    },
    # -----------------------------------------------------------------------
    # 500 Internal Server Error
    # -----------------------------------------------------------------------
    {
        "errorCode": "InternalDeploymentError",
        "stage": "Deployment",
        "httpStatus": 500,
        "suggestedFixes": [
            "Retry the deployment",
            "Check deployment logs: 'az webapp log deployment show'",
            "Restart the SCM site and try again",
            "If the problem persists, file an Azure support ticket"
        ]
    },
    {
        "errorCode": "EmptyBranch",
        "stage": "Deployment",
        "httpStatus": 500,
        "suggestedFixes": [
            "Push commits to the target deployment branch",
            "Verify the branch name matches the configured deployment branch",
            "Check 'az webapp deployment source show' for the configured branch"
        ]
    },
    # -----------------------------------------------------------------------
    # Kudu DeployStatus — Pending / Building / Deploying / Failed / Success
    # -----------------------------------------------------------------------
    {
        "errorCode": "KuduBuildFailed",
        "stage": "Building",
        "httpStatus": None,
        "suggestedFixes": [
            "Check build logs: 'az webapp log deployment show'",
            "Ensure the correct build manifest file exists (requirements.txt / package.json)",
            "Set SCM_DO_BUILD_DURING_DEPLOYMENT=false and pre-build artifacts locally"
        ]
    },
    {
        "errorCode": "KuduDeployFailed",
        "stage": "Deploying",
        "httpStatus": None,
        "suggestedFixes": [
            "Check deployment logs: 'az webapp log deployment show'",
            "Verify file permissions and disk space",
            "Retry the deployment"
        ]
    },
]

# Index for O(1) lookup by error code
_PATTERN_INDEX = {p["errorCode"]: p for p in DEPLOYMENT_FAILURE_PATTERNS}


def get_failure_pattern(error_code):
    """Look up a well-known failure pattern by its error code."""
    return _PATTERN_INDEX.get(error_code)


def match_failure_pattern(status_code=None, error_message=None, deployment_status=None):
    """
    Attempt to match an error to a well-known Kudu deployment failure pattern.

    Examines HTTP status codes and error message text to find the most relevant
    failure pattern from the KuduLite deployment engine.

    Returns the matched pattern dict or None.
    """
    if error_message is None:
        error_message = ""

    error_lower = error_message.lower()

    # ----- 400 Bad Request: match on specific Kudu error messages -----
    if status_code == 400:
        # ZipDeploy validation errors (check first — most specific)
        if "zipdeploy validation error" in error_lower:
            if "malformed" in error_lower:
                return get_failure_pattern("ZipDeployMalformedUri")
            if "inaccessible" in error_lower:
                return get_failure_pattern("ZipDeployUriInaccessible")
            if "disk space" in error_lower or "package size" in error_lower:
                return get_failure_pattern("ZipDeployInsufficientDisk")
            if "cannot deploy" in error_lower and "functions" in error_lower:
                return get_failure_pattern("ZipDeployRuntimeMismatch")
            if "website_run_from_package" in error_lower:
                return get_failure_pattern("ZipDeployRunFromPackageConflict")

        # OneDeploy artifact / type errors
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
        if "invalid packageu" in error_lower:
            return get_failure_pattern("InvalidPackageUri")
        if "clean deployments cannot be performed" in error_lower:
            return get_failure_pattern("CleanDeployForbidden")
        if "only successful status can be active" in error_lower:
            return get_failure_pattern("InvalidDeploymentStatus")
        if "no file uploaded" in error_lower:
            return get_failure_pattern("NoFileUploaded")
        if "only .zip files are supported" in error_lower:
            return get_failure_pattern("UnsupportedFileType")
        if "failed to prepare deployment file" in error_lower:
            return get_failure_pattern("QuickDeployPrepareFailed")
        if "failed to initialize deployment" in error_lower:
            return get_failure_pattern("QuickDeployInitFailed")
        if "invalid deployment id" in error_lower:
            return get_failure_pattern("InvalidDeploymentId")

        # Generic 400
        return get_failure_pattern("DeploymentFailed")

    # ----- 403 Forbidden -----
    if status_code == 403:
        return get_failure_pattern("ScmDisabled")

    # ----- 404 Not Found -----
    if status_code == 404:
        if "repository could not be found" in error_lower:
            return get_failure_pattern("RepositoryNotFound")
        if "logid" in error_lower and "not found" in error_lower:
            return get_failure_pattern("LogNotFound")
        if "deployment" in error_lower and "not found" in error_lower:
            return get_failure_pattern("DeploymentNotFound")
        if "need to deploy website" in error_lower:
            return get_failure_pattern("NoDeploymentsExist")
        if "custom deployment script" in error_lower:
            return get_failure_pattern("CustomDeployScriptInUse")
        if "quickdeploy" in error_lower and "disabled" in error_lower:
            return get_failure_pattern("QuickDeployDisabled")
        if "no route registered" in error_lower:
            return get_failure_pattern("RouteNotFound")
        return get_failure_pattern("DeploymentNotFound")

    # ----- 409 Conflict -----
    if status_code == 409:
        if "auto swap" in error_lower:
            return get_failure_pattern("AutoSwapInProgress")
        if "run-from-zip" in error_lower or "website_run_from_package" in error_lower or "website_use_zip" in error_lower:
            return get_failure_pattern("RunFromRemoteZipConfigured")
        if "deployment with id" in error_lower and "exists" in error_lower:
            return get_failure_pattern("DeploymentIdExists")
        if "failed to acquire deployment lock" in error_lower:
            return get_failure_pattern("DeploymentLockFailed")
        # Generic 409 — deployment lock conflict
        return get_failure_pattern("DeploymentInProgress")

    # ----- 499 Client Closed Request -----
    if status_code == 499:
        return get_failure_pattern("ClientDisconnected")

    # ----- 500 Internal Server Error -----
    if status_code == 500:
        if "nothing has been pushed" in error_lower and "branch" in error_lower:
            return get_failure_pattern("EmptyBranch")
        return get_failure_pattern("InternalDeploymentError")

    # ----- Kudu DeployStatus-based matching -----
    if deployment_status == "Failed":
        # Check error message for build vs deploy phase hints
        if "build" in error_lower:
            return get_failure_pattern("KuduBuildFailed")
        return get_failure_pattern("KuduDeployFailed")

    if deployment_status == "Building":
        return get_failure_pattern("KuduBuildFailed")

    # ----- Message-based fallback heuristics (no status code) -----
    if not status_code:
        if "request was aborted" in error_lower or "deployment was cancelled" in error_lower:
            return get_failure_pattern("ClientDisconnected")
        if "auto swap" in error_lower:
            return get_failure_pattern("AutoSwapInProgress")
        if "deployment currently in progress" in error_lower:
            return get_failure_pattern("DeploymentInProgress")
        if "run-from-zip" in error_lower:
            return get_failure_pattern("RunFromRemoteZipConfigured")
        if "cannot be deployed to stack" in error_lower:
            return get_failure_pattern("ArtifactStackMismatch")
        if "repository could not be found" in error_lower:
            return get_failure_pattern("RepositoryNotFound")

    return None
