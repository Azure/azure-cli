param ($version, $dir, $upgradeVersion)

if ($null -eq $version) {
    $version = Read-Host -Prompt "Please enter a version"
}

if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    # Start another Powershell process as Admin and execute this script again
    $arguments = "& '" +$myinvocation.mycommand.definition + "' -version $version -dir $pwd"
    Start-Process powershell -Verb runAs -ArgumentList $arguments 
    # Stop if the PowerShell is not run as Admin
    Break
}

# The following are executed by elevated PowerShell
if ($null -eq $dir) {
    $dir = $pwd
}

$logDate=$(Get-Date -f yyyyMMddHHmmss)
Start-Transcript -Path $dir\msi_install_measure_$logDate.txt
$oldPreference = $ErrorActionPreference

$ErrorActionPreference = 'stop'
$command = 'az'
try {
    if(Get-Command $command){
        Write-Host "azure-cli already installed. Please remove it first."
        Stop-Transcript
        Exit 1
    }
}
catch {
    Write-Host 'Install version:' $version
}
finally {
    $ErrorActionPreference=$oldPreference
}

if (-not(Test-Path -Path $dir\azure-cli-$version.msi -PathType Leaf)) {
    $download_link = "https://azcliprod.blob.core.windows.net/msi/azure-cli-$version.msi"
    Write-Host "Download link:" $download_link
    Invoke-WebRequest -Uri $download_link -OutFile $dir\azure-cli-$version.msi
}


$InstallArgs = @(
"/i"
"$dir\azure-cli-$version.msi"
"/q"
"/norestart"
)

$install_time=Measure-Command {Start-Process "msiexec.exe" -ArgumentList $InstallArgs -Wait -NoNewWindow} | select -expand TotalSeconds

Write-Host 'Install time(seconds):' $install_time

Start-Sleep -s 5

if ($null -eq $upgradeVersion) {
    $RemoveArgs = @(
    "/x"
    "$dir\azure-cli-$version.msi"
    "/q"
    )
    $remove_time=Measure-Command {Start-Process "msiexec.exe" -ArgumentList $RemoveArgs -Wait -NoNewWindow} | select -expand TotalSeconds
    Write-Host 'Uninstall time(seconds):' $remove_time
} else {
    if (-not(Test-Path -Path $dir\azure-cli-$upgradeVersion.msi -PathType Leaf)) {
        $download_link = "https://azcliprod.blob.core.windows.net/msi/azure-cli-$upgradeVersion.msi"
        Write-Host "Upgrade link:" $download_link
        Invoke-WebRequest -Uri $download_link -OutFile $dir\azure-cli-$upGradeVersion.msi
    }
    $UpgradeArgs = @(
    "/i"
    "$dir\azure-cli-$upgradeVersion.msi"
    "/q"
    "/norestart"
    )
    Write-Host 'Upgrade to version:' $upgradeVersion
    $upgrade_time=Measure-Command {Start-Process "msiexec.exe" -ArgumentList $UpgradeArgs -Wait -NoNewWindow} | select -expand TotalSeconds
    Write-Host 'Upgrade time(seconds):' $upgrade_time

    $RemoveArgs = @(
    "/x"
    "$dir\azure-cli-$upgradeVersion.msi"
    "/q"
    )
    $remove_time=Measure-Command {Start-Process "msiexec.exe" -ArgumentList $RemoveArgs -Wait -NoNewWindow} | select -expand TotalSeconds
    Write-Host 'Uninstall version:' $upgradeVersion
    Write-Host 'Uninstall time(seconds):' $remove_time
}

Stop-Transcript
