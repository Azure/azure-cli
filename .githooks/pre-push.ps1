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
Write-Host "Initial mergeBase: $mergeBase" -ForegroundColor Cyan

if ($mergeBase -ne $upstreamHead) {
    Write-Host ""
    Write-Host "Your branch is not up to date with upstream/dev." -ForegroundColor Yellow
    Write-Host "Would you like to automatically rebase and setup? [Y/n]" -ForegroundColor Yellow

    try {
        $reader = [System.IO.StreamReader]::new("CON")
        $input = $reader.ReadLine()
    } catch {
        Write-Host "Error reading input. Aborting push..." -ForegroundColor Red
        exit 1
    }

    if ($input -match '^[Yy]$') {
        Write-Host "Rebasing with upstream/dev..." -ForegroundColor Green
        git rebase upstream/dev
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Rebase failed. Please resolve conflicts and try again." -ForegroundColor Red
            exit 1
        }
        Write-Host "Rebase completed successfully." -ForegroundColor Green
        $mergeBase = git merge-base HEAD upstream/dev
        Write-Host "Updated mergeBase: $mergeBase" -ForegroundColor Cyan

        Write-Host "Running azdev setup..." -ForegroundColor Green
        if ($Extensions) {
            azdev setup -c $AZURE_CLI_FOLDER -r $Extensions
        } else {
            azdev setup -c $AZURE_CLI_FOLDER
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Host "azdev setup failed. Please check your environment." -ForegroundColor Red
            exit 1
        }
        Write-Host "Setup completed successfully." -ForegroundColor Green
    } elseif ($input -match '^[Nn]$') {
        Write-Host "Skipping rebase and setup. Continue push..." -ForegroundColor Red
    } else {
        Write-Host "Invalid input. Aborting push..." -ForegroundColor Red
        exit 1
    }
}

# get the current branch name
$currentBranch = git branch --show-current

# Run command azdev lint
Write-Host "Running azdev lint..." -ForegroundColor Green
azdev linter --min-severity medium --repo ./ --src $currentBranch --tgt $mergeBase
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: azdev lint check failed." -ForegroundColor Red
    exit 1
}

# Run command azdev style
Write-Host "Running azdev style..." -ForegroundColor Green
azdev style --repo ./ --src $currentBranch --tgt $mergeBase
if ($LASTEXITCODE -ne 0) {
    $error_msg = azdev style --repo ./ --src $currentBranch --tgt $mergeBase 2>&1
    if ($error_msg -like "*No modules*") {
        Write-Host "Pre-push hook passed." -ForegroundColor Green
        exit 0
    }
    Write-Host "Error: azdev style check failed." -ForegroundColor Red
    exit 1
}

# Run command azdev test
Write-Host "Running azdev test..." -ForegroundColor Green
azdev test --repo ./ --src $currentBranch --tgt $mergeBase --discover --no-exitfirst --xml-path test_results.xml 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: azdev test check failed." -ForegroundColor Red
    exit 1
} else {
    # remove test_results.xml file
    Remove-Item test_results.xml
}

Write-Host "Pre-push hook passed." -ForegroundColor Green
exit 0
