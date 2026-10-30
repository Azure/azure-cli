param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Seed', 'Target', 'SecondTarget', 'Permissions', 'Write')]
    [string] $Mode,
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string] $SqlUsername,
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string] $SqlPassword
)

$ErrorActionPreference = 'Stop'
$securePassword = ConvertTo-SecureString $SqlPassword -AsPlainText -Force
$securePassword.MakeReadOnly()
$sqlCredential = New-Object System.Data.SqlClient.SqlCredential($SqlUsername, $securePassword)

function Invoke-TestSql([string] $Query) {
    $connection = New-Object System.Data.SqlClient.SqlConnection(
        'Server=lpc:localhost;Database=master;Integrated Security=false;Encrypt=true;TrustServerCertificate=true')
    $connection.Credential = $sqlCredential
    try {
        $connection.Open()
        $command = $connection.CreateCommand()
        $command.CommandTimeout = 300
        $command.CommandText = $Query
        [void] $command.ExecuteNonQuery()
    }
    finally {
        $connection.Dispose()
    }
}

Invoke-TestSql @"
IF ISNULL(IS_SRVROLEMEMBER(N'sysadmin'), 0) <> 1
    THROW 51000, 'SQL snapshot setup requires the test SQL login to be a SQL sysadmin.', 1;
"@

if ($Mode -eq 'Seed') {
    $disks = @(Get-Disk | Where-Object PartitionStyle -eq 'RAW' | Sort-Object Number)
    if ($disks.Count -ne 2) {
        throw "Expected exactly two new data disks; found $($disks.Count)."
    }
    $letters = @('F', 'G')
    for ($index = 0; $index -lt 2; $index++) {
        $letter = $letters[$index]
        if (Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue) {
            throw "Source volume ${letter}: must not exist before test setup."
        }
        $disks[$index] | Initialize-Disk -PartitionStyle GPT -PassThru |
            New-Partition -UseMaximumSize -DriveLetter $letter |
            Format-Volume -FileSystem NTFS -AllocationUnitSize 65536 -Confirm:$false | Out-Null
        New-Item -ItemType Directory -Path "${letter}:\SqlSnapshotTest" | Out-Null
        & icacls "${letter}:\SqlSnapshotTest" /grant 'NT SERVICE\MSSQLSERVER:(OI)(CI)F'
        if ($LASTEXITCODE -ne 0) { throw 'Could not grant SQL Server access to the data directory.' }
    }
    foreach ($database in @('clitestdb1', 'clitestdb2')) {
        Invoke-TestSql @"
CREATE DATABASE [$database]
ON PRIMARY (NAME = N'${database}_data', FILENAME = N'F:\SqlSnapshotTest\$database.mdf', SIZE = 16MB)
LOG ON (NAME = N'${database}_log', FILENAME = N'G:\SqlSnapshotTest\$database.ldf', SIZE = 16MB);
"@
        Invoke-TestSql @"
ALTER DATABASE [$database] SET RECOVERY FULL;
USE [$database];
CREATE TABLE dbo.SnapshotTest (Id int IDENTITY PRIMARY KEY, Payload nvarchar(200) NOT NULL);
INSERT dbo.SnapshotTest (Payload) VALUES (N'before snapshot');
"@
    }
}
elseif ($Mode -eq 'Permissions') {
    Invoke-TestSql @"
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'NT SERVICE\AzureWLBackupPluginSvc')
    CREATE LOGIN [NT SERVICE\AzureWLBackupPluginSvc] FROM WINDOWS;
ALTER SERVER ROLE [sysadmin] ADD MEMBER [NT SERVICE\AzureWLBackupPluginSvc];
"@
}
elseif ($Mode -eq 'Target' -or $Mode -eq 'SecondTarget') {
    $letters = if ($Mode -eq 'Target') { @('X', 'Y') } else { @('U', 'V') }
    foreach ($letter in $letters) {
        if (Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue) {
            throw "Restore volume ${letter}: is already in use."
        }
    }
    Invoke-TestSql 'SELECT 1;'
}
elseif ($Mode -eq 'Write') {
    foreach ($database in @('clitestdb1', 'clitestdb2')) {
        Invoke-TestSql "USE [$database]; INSERT dbo.SnapshotTest (Payload) VALUES (N'after snapshot');"
    }
}

Write-Output "SQLSNAP-SETUP-OK:$Mode"
