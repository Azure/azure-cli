# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Well-known deployment failure patterns for az webapp deploy / az functionapp deploy.

Each pattern maps an errorCode to its deployment stage, common causes, and suggested fixes.
These patterns are used by the context-enriched error handler to produce actionable diagnostics
instead of generic "Status Code: 504" messages.
"""

DEPLOYMENT_FAILURE_PATTERNS = [
    {
        "errorCode": "ZipDeployTimeout",
        "stage": "ZipExtract",
        "commonCauses": [
            "Large node_modules or dependency folder",
            "Slow network between client and App Service",
            "B1 plan under-provisioned for artifact size"
        ],
        "suggestedFixes": [
            "Scale up the App Service plan (e.g., B1 -> P1V2)",
            "Set SCM_DO_BUILD_DURING_DEPLOYMENT=false to disable remote build",
            "Reduce artifact size by excluding dev dependencies",
            "Retry the deployment"
        ]
    },
    {
        "errorCode": "Exit137",
        "stage": "ContainerStartup",
        "commonCauses": [
            "Out-of-memory (OOM) kill during startup",
            "Startup memory spike exceeds plan limits"
        ],
        "suggestedFixes": [
            "Scale up the App Service plan to get more memory",
            "Reduce startup memory footprint",
            "Lazy-load heavy dependencies instead of importing at startup"
        ]
    },
    {
        "errorCode": "OryxBuildFailed",
        "stage": "Build",
        "commonCauses": [
            "Missing requirements.txt or package.json",
            "Oryx build system misconfigured",
            "Incompatible dependency versions"
        ],
        "suggestedFixes": [
            "Ensure the correct build manifest file exists (requirements.txt / package.json)",
            "Set SCM_DO_BUILD_DURING_DEPLOYMENT=false and pre-build artifacts locally",
            "Check Oryx build logs for specific dependency errors"
        ]
    },
    {
        "errorCode": "StartupProbeFailed",
        "stage": "ContainerStartup",
        "commonCauses": [
            "Application not listening on the expected port",
            "Slow initialization exceeding probe timeout"
        ],
        "suggestedFixes": [
            "Increase WEBSITES_CONTAINER_START_TIME_LIMIT (e.g., to 600)",
            "Verify the PORT environment variable and that the app binds to it",
            "Add a /health or /ready endpoint for the startup probe"
        ]
    },
    {
        "errorCode": "AuthFailed",
        "stage": "Deployment",
        "commonCauses": [
            "RBAC role not assigned or misconfigured",
            "Managed identity not enabled on the app"
        ],
        "suggestedFixes": [
            "Ensure the deploying identity has Contributor or Website Contributor role",
            "Enable system-assigned managed identity on the web app",
            "Run 'az role assignment list' to verify permissions"
        ]
    },
    {
        "errorCode": "AppOfflineDetected",
        "stage": "Deployment",
        "commonCauses": [
            "Deployment file lock preventing updates",
            "app_offline.htm file left from a previous deployment"
        ],
        "suggestedFixes": [
            "Remove the app_offline.htm file from wwwroot",
            "Retry the deployment after a brief wait",
            "Restart the app before redeploying"
        ]
    },
    {
        "errorCode": "DockerImagePullFailed",
        "stage": "ContainerStartup",
        "commonCauses": [
            "Invalid image name or tag",
            "Container registry authentication failure",
            "Network connectivity issue to registry"
        ],
        "suggestedFixes": [
            "Verify the image name and tag exist in the registry",
            "Check container registry credentials and permissions",
            "Ensure network connectivity between App Service and the registry"
        ]
    },
    {
        "errorCode": "SCMTimeout",
        "stage": "ZipExtract",
        "commonCauses": [
            "Slow SCM (Kudu) operations under load",
            "Very large deployment artifact"
        ],
        "suggestedFixes": [
            "Split deployment into smaller artifacts",
            "Set SCM_DO_BUILD_DURING_DEPLOYMENT=false to skip build during deploy",
            "Retry the deployment"
        ]
    },
    {
        "errorCode": "ConfigConflict",
        "stage": "ConfigUpdate",
        "commonCauses": [
            "Conflicting settings between portal and CLI/ARM",
            "Stale configuration cached by the platform"
        ],
        "suggestedFixes": [
            "Resolve conflicts manually in the Azure portal",
            "Use an ARM template or Bicep to enforce consistent configuration",
            "Run 'az webapp config show' to review current settings"
        ]
    },
    {
        "errorCode": "RuntimeMismatch",
        "stage": "ContainerStartup",
        "commonCauses": [
            "Runtime version set in config does not match deployed code",
            "Container base image uses a different runtime version"
        ],
        "suggestedFixes": [
            "Update the runtime stack via 'az webapp config set --linux-fx-version'",
            "Rebuild the container image with the correct runtime version",
            "Check 'az webapp config show' for linuxFxVersion or windowsFxVersion"
        ]
    },
    {
        "errorCode": "SSLValidationFailed",
        "stage": "Deployment",
        "commonCauses": [
            "Invalid or expired SSL certificate",
            "Certificate-key mismatch"
        ],
        "suggestedFixes": [
            "Upload a valid SSL certificate with matching private key",
            "Check certificate expiration date",
            "Verify the certificate password is correct"
        ]
    },
    {
        "errorCode": "InsufficientQuota",
        "stage": "Deployment",
        "commonCauses": [
            "App Service plan instance or core limits reached",
            "Subscription quota exhausted"
        ],
        "suggestedFixes": [
            "Upgrade the App Service plan to a higher tier",
            "Free up quota by deleting unused apps",
            "Request a quota increase via Azure support"
        ]
    },
    {
        "errorCode": "PermissionDenied",
        "stage": "Deployment",
        "commonCauses": [
            "Service principal or user lacks required RBAC role",
            "Scope of role assignment is incorrect"
        ],
        "suggestedFixes": [
            "Assign Contributor or Website Contributor role at the correct scope",
            "Run 'az role assignment list --assignee <principal>' to verify",
            "Check if a deny assignment or policy is blocking access"
        ]
    },
    {
        "errorCode": "FileLockError",
        "stage": "ZipExtract",
        "commonCauses": [
            "File in use by a running process during deployment",
            "Antivirus or file lock from another deployment"
        ],
        "suggestedFixes": [
            "Stop the app before deploying: 'az webapp stop'",
            "Retry the deployment after a short delay",
            "Enable MSDEPLOY_RENAME_LOCKED_FILES=1 in app settings"
        ]
    },
    {
        "errorCode": "ColdStartTimeout",
        "stage": "ContainerStartup",
        "commonCauses": [
            "Large dependency tree causing slow cold start",
            "No pre-warmed instances available"
        ],
        "suggestedFixes": [
            "Increase WEBSITES_CONTAINER_START_TIME_LIMIT",
            "Scale up the plan for faster cold starts",
            "Enable Always On to avoid cold starts"
        ]
    },
    {
        "errorCode": "DBConnectionFailed",
        "stage": "ContainerStartup",
        "commonCauses": [
            "Database connection string missing from app settings",
            "Database firewall blocking App Service IP"
        ],
        "suggestedFixes": [
            "Set the connection string via 'az webapp config connection-string set'",
            "Add App Service outbound IPs to the database firewall rules",
            "Use a service connector: 'az webapp connection create'"
        ]
    },
    {
        "errorCode": "WebJobFailed",
        "stage": "WebJobStartup",
        "commonCauses": [
            "Missing runtime for the WebJob",
            "Package or dependency errors in the WebJob"
        ],
        "suggestedFixes": [
            "Check WebJob runtime requirements and logs",
            "Run 'az webapp webjob continuous list' to see WebJob status",
            "Review logs at https://<app>.scm.azurewebsites.net/api/continuouswebjobs"
        ]
    },
    {
        "errorCode": "PortBindingError",
        "stage": "ContainerStartup",
        "commonCauses": [
            "Container not exposing port 80 or 8080",
            "WEBSITES_PORT not set to the correct port"
        ],
        "suggestedFixes": [
            "Set WEBSITES_PORT app setting to match the container's listening port",
            "Ensure the Dockerfile exposes the correct port",
            "Check 'az webapp config appsettings list' for WEBSITES_PORT"
        ]
    },
    {
        "errorCode": "AppSettingsMisconfigured",
        "stage": "ContainerStartup",
        "commonCauses": [
            "Missing required environment variables",
            "Incorrect app setting names or values"
        ],
        "suggestedFixes": [
            "Review app settings: 'az webapp config appsettings list'",
            "Set required environment variables: 'az webapp config appsettings set'",
            "Compare with working configuration or documentation"
        ]
    },
    {
        "errorCode": "StorageMountFailed",
        "stage": "ContainerStartup",
        "commonCauses": [
            "SMB/NFS mount failure due to storage account issues",
            "Incorrect storage credentials or share name"
        ],
        "suggestedFixes": [
            "Verify the storage account name, key, and share exist",
            "Check network connectivity (private endpoints, firewalls)",
            "Run 'az webapp config storage-account list' to review mounts"
        ]
    }
]

# Index for O(1) lookup by error code
_PATTERN_INDEX = {p["errorCode"]: p for p in DEPLOYMENT_FAILURE_PATTERNS}


def get_failure_pattern(error_code):
    """Look up a well-known failure pattern by its error code."""
    return _PATTERN_INDEX.get(error_code)


def match_failure_pattern(status_code=None, error_message=None, deployment_status=None):
    """
    Attempt to match an error to a well-known failure pattern based on heuristics.

    Examines status codes, error messages, and deployment status text to find the
    most relevant failure pattern.

    Returns the matched pattern dict or None.
    """
    if error_message is None:
        error_message = ""

    error_lower = error_message.lower()

    # Status code based matching
    if status_code in (504, 408):
        if "scm" in error_lower or "kudu" in error_lower:
            return get_failure_pattern("SCMTimeout")
        return get_failure_pattern("ZipDeployTimeout")

    if status_code == 401 or status_code == 403:
        if "ssl" in error_lower or "cert" in error_lower:
            return get_failure_pattern("SSLValidationFailed")
        if "permission" in error_lower or "denied" in error_lower:
            return get_failure_pattern("PermissionDenied")
        return get_failure_pattern("AuthFailed")

    if status_code == 409:
        if "lock" in error_lower or "locked" in error_lower:
            return get_failure_pattern("FileLockError")
        if "offline" in error_lower:
            return get_failure_pattern("AppOfflineDetected")

    if status_code == 429 or "quota" in error_lower or "insufficient" in error_lower:
        return get_failure_pattern("InsufficientQuota")

    # Deployment status based matching
    if deployment_status == "BuildFailed":
        if "oryx" in error_lower:
            return get_failure_pattern("OryxBuildFailed")
        return get_failure_pattern("OryxBuildFailed")  # default build failure

    if deployment_status == "RuntimeFailed":
        # Try to narrow down the runtime failure
        if "137" in error_lower or "oom" in error_lower or "out of memory" in error_lower:
            return get_failure_pattern("Exit137")
        if "port" in error_lower or "bind" in error_lower:
            return get_failure_pattern("PortBindingError")
        if "probe" in error_lower or "health" in error_lower:
            return get_failure_pattern("StartupProbeFailed")
        if "image" in error_lower or "pull" in error_lower or "docker" in error_lower:
            return get_failure_pattern("DockerImagePullFailed")
        if "runtime" in error_lower and "mismatch" in error_lower:
            return get_failure_pattern("RuntimeMismatch")
        if "connection" in error_lower and ("db" in error_lower or "database" in error_lower or "sql" in error_lower):
            return get_failure_pattern("DBConnectionFailed")
        if "storage" in error_lower or "mount" in error_lower or "smb" in error_lower:
            return get_failure_pattern("StorageMountFailed")
        if "setting" in error_lower or "env" in error_lower or "environment" in error_lower:
            return get_failure_pattern("AppSettingsMisconfigured")
        if "cold" in error_lower or "startup" in error_lower or "timeout" in error_lower:
            return get_failure_pattern("ColdStartTimeout")
        # Generic runtime failure — use StartupProbeFailed as the closest match
        return get_failure_pattern("StartupProbeFailed")

    # Message-based matching (fallback heuristics)
    if "artifact type" in error_lower and "cannot be deployed to stack" in error_lower:
        return get_failure_pattern("RuntimeMismatch")
    if "webjob" in error_lower:
        return get_failure_pattern("WebJobFailed")
    if "config" in error_lower and "conflict" in error_lower:
        return get_failure_pattern("ConfigConflict")
    if "offline" in error_lower:
        return get_failure_pattern("AppOfflineDetected")
    if "timeout" in error_lower:
        return get_failure_pattern("ZipDeployTimeout")
    if "permission" in error_lower or "denied" in error_lower or "unauthorized" in error_lower:
        return get_failure_pattern("PermissionDenied")
    if "quota" in error_lower or "exceeded" in error_lower:
        return get_failure_pattern("InsufficientQuota")
    if "lock" in error_lower:
        return get_failure_pattern("FileLockError")

    return None
