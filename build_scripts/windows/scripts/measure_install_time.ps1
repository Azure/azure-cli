param ($version, $dir)

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

$download_link = "https://azcliprod.blob.core.windows.net/msi/azure-cli-$version.msi"

Write-Host "Downlaod link:" $download_link 

$InstallArgs = @(
"/i"
"$download_link"
"/q"
"/norestart"
"/l*v"
".\install_logs_$logDate.txt"
)

$install_time=Measure-Command {Start-Process "msiexec.exe" -ArgumentList $InstallArgs -Wait -NoNewWindow} | select -expand TotalSeconds

Write-Host 'Install time(seconds):' $install_time
Stop-Transcript
