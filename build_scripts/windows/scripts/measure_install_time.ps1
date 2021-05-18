param ($version, $dir, $upgradeVersion)

if ($null -eq $version) {
    $version = Read-Host -Prompt "Please enter a version"
}

if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    # Start another Powershell process as Admin and execute this script again
    $params = "-version $version -dir $pwd"
    if ($null -ne $upgradeVersion) {
        $params += " -upgradeVersion $upgradeVersion"
    }
    $arguments = "& '" + $myinvocation.mycommand.definition + "' $params"
    Start-Process powershell -Verb runAs -ArgumentList $arguments 
    # Stop if the PowerShell is not run as Admin
    Break
}

# The following are executed by elevated PowerShell
if ($null -eq $dir) {
    $dir = $pwd
}

$logDate = $(Get-Date -f yyyyMMddHHmmss)
Start-Transcript -Path $dir\msi_install_measure_$logDate.txt
$oldPreference = $ErrorActionPreference

$ErrorActionPreference = 'stop'
$command = 'az'
try {
    if (Get-Command $command) {
        Write-Host "azure-cli already installed. Please remove it first."
        Stop-Transcript
        Exit 1
    }
}
catch {
    Write-Host 'Install version:' $version
}
finally {
    $ErrorActionPreference = $oldPreference
}

if (-not(Test-Path -Path $dir\azure-cli-$version.msi -PathType Leaf)) {
    $downloadLink = "https://azcliprod.blob.core.windows.net/msi/azure-cli-$version.msi"
    Write-Host "Download link:" $downloadLink
    Invoke-WebRequest -Uri $downloadLink -OutFile $dir\azure-cli-$version.msi
}


$InstallArgs = @(
    "/i"
    "$dir\azure-cli-$version.msi"
    "/q"
    "/norestart"
)

$installTime = Measure-Command { Start-Process "msiexec.exe" -ArgumentList $InstallArgs -Wait -NoNewWindow } | Select-Object -expand TotalSeconds

Write-Host 'Install time(seconds):' $installTime

Start-Sleep -s 5

if ($null -eq $upgradeVersion) {
    # Measure uninstall time
    $RemoveArgs = @(
        "/x"
        "$dir\azure-cli-$version.msi"
        "/q"
    )
    $removeTime = Measure-Command { Start-Process "msiexec.exe" -ArgumentList $RemoveArgs -Wait -NoNewWindow } | Select-Object -expand TotalSeconds
    Write-Host 'Uninstall time(seconds):' $removeTime
}
else {
    # Measure upgrade time
    if (-not(Test-Path -Path $dir\azure-cli-$upgradeVersion.msi -PathType Leaf)) {
        $downloadLink = "https://azcliprod.blob.core.windows.net/msi/azure-cli-$upgradeVersion.msi"
        Write-Host "Upgrade link:" $downloadLink
        Invoke-WebRequest -Uri $downloadLink -OutFile $dir\azure-cli-$upGradeVersion.msi
    }
    $UpgradeArgs = @(
        "/i"
        "$dir\azure-cli-$upgradeVersion.msi"
        "/q"
        "/norestart"
    )
    Write-Host 'Upgrade to version:' $upgradeVersion
    $upgrade_time = Measure-Command { Start-Process "msiexec.exe" -ArgumentList $UpgradeArgs -Wait -NoNewWindow } | Select-Object -expand TotalSeconds
    Write-Host 'Upgrade time(seconds):' $upgrade_time
    # Uninstall the upgraded version
    $RemoveArgs = @(
        "/x"
        "$dir\azure-cli-$upgradeVersion.msi"
        "/q"
    )
    $removeTime = Measure-Command { Start-Process "msiexec.exe" -ArgumentList $RemoveArgs -Wait -NoNewWindow } | Select-Object -expand TotalSeconds
    Write-Host 'Uninstall version:' $upgradeVersion
    Write-Host 'Uninstall time(seconds):' $removeTime
}

Stop-Transcript
