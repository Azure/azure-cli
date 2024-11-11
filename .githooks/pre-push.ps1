Write-Host "Running pre-push hook in powershell..." -ForegroundColor Green

# run azdev_active script and capture its output
$scriptPath = Join-Path $PSScriptRoot "azdev_active.ps1"
. $scriptPath
if ($LASTEXITCODE -ne 0) {
    exit 1
}

# Check if azure-cli is installed in editable mode
$pipShowOutput = pip show azure-cli 2>&1
$editableLocation = if ($pipShowOutput) {
    $match = $pipShowOutput | Select-String "Editable project location: (.+)"
    if ($match) {
        $match.Matches.Groups[1].Value
    }
}
if ($editableLocation) {
    # get the parent of parent directory of the editable location
    $AZURE_CLI_FOLDER = Split-Path -Parent (Split-Path -Parent $editableLocation)
} else {
    Write-Host "Error: azure-cli is not installed in editable mode. Please install it in editable mode using `azdev setup`." -ForegroundColor Red
    exit 1
}

# Get extension repo paths and join them with spaces
$Extensions = (azdev extension repo list -o tsv) -join ' '

# Fetch upstream/dev branch
Write-Host "Fetching upstream/dev branch..." -ForegroundColor Green
git fetch upstream dev
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to fetch upstream/dev branch. Please run 'git remote add upstream https://github.com/Azure/azure-cli.git' first." -ForegroundColor Red
    exit 1
}

# Check if current branch needs rebasing
$mergeBase = git merge-base HEAD upstream/dev
$upstreamHead = git rev-parse upstream/dev
if ($mergeBase -ne $upstreamHead) {
    Write-Host ""
    Write-Host "Your branch is not up to date with upstream/dev. Please run the following commands to rebase and setup:" -ForegroundColor Yellow
    Write-Host "+++++++++++++++++++++++++++++++++++++++++++++++++++++++" -ForegroundColor Yellow
    Write-Host "git rebase upstream/dev" -ForegroundColor Yellow
    if ($Extensions) {
        Write-Host "azdev setup -c $AZURE_CLI_FOLDER -r $Extensions" -ForegroundColor Yellow
    } else {
        Write-Host "azdev setup -c $AZURE_CLI_FOLDER" -ForegroundColor Yellow
    }
    Write-Host "+++++++++++++++++++++++++++++++++++++++++++++++++++++++" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "You have 5 seconds to stop the push (Ctrl+C)..." -ForegroundColor Yellow
    for ($i = 5; $i -gt 0; $i--) {
        Write-Host "`rTime remaining: $i seconds..." -NoNewline -ForegroundColor Yellow
        Start-Sleep -Seconds 1
    }
    Write-Host "`rContinuing without rebase..."
}

# get the current branch name
$currentBranch = git branch --show-current

# Run command azdev lint
Write-Host "Running azdev lint..." -ForegroundColor Green
azdev linter --repo ./ --src $currentBranch --tgt upstream/dev
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: azdev lint check failed." -ForegroundColor Red
    exit 1
}

# Run command azdev style
Write-Host "Running azdev style..." -ForegroundColor Green
azdev style --repo ./ --src $currentBranch --tgt upstream/dev
if ($LASTEXITCODE -ne 0) {
    $error_msg = azdev style --repo ./ --src $currentBranch --tgt upstream/dev 2>&1
    if ($error_msg -like "*No modules*") {
        Write-Host "Pre-push hook passed." -ForegroundColor Green
        exit 0
    }
    Write-Host "Error: azdev style check failed." -ForegroundColor Red
    exit 1
}

# Run command azdev test
Write-Host "Running azdev test..." -ForegroundColor Green
azdev test --repo ./ --src $currentBranch --tgt upstream/dev
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: azdev test check failed." -ForegroundColor Red
    exit 1
}

Write-Host "Pre-push hook passed." -ForegroundColor Green
exit 0
