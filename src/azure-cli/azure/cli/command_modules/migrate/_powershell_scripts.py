# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
PowerShell migration scripts for common scenarios.
These scripts can be executed by the PowerShell executor.
"""

# SQL Server migration assessment script
SQL_SERVER_ASSESSMENT = """
param(
    [string]$ServerName = $env:COMPUTERNAME,
    [string]$InstanceName = "MSSQLSERVER"
)

$assessment = @{
    ServerName = $ServerName
    InstanceName = $InstanceName
    Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Databases = @()
    Configuration = @{}
    Recommendations = @()
}

try {
    # Import SQL Server module if available
    Import-Module SqlServer -ErrorAction SilentlyContinue
    
    # Get SQL Server information
    $sqlConnection = "Server=$ServerName\\$InstanceName;Integrated Security=true;"
    
    # Basic server configuration
    $assessment.Configuration = @{
        Version = (Invoke-Sqlcmd -Query "SELECT @@VERSION as Version" -ConnectionString $sqlConnection).Version
        Edition = (Invoke-Sqlcmd -Query "SELECT SERVERPROPERTY('Edition') as Edition" -ConnectionString $sqlConnection).Edition
        ProductLevel = (Invoke-Sqlcmd -Query "SELECT SERVERPROPERTY('ProductLevel') as ProductLevel" -ConnectionString $sqlConnection).ProductLevel
    }
    
    # Get database information
    $databases = Invoke-Sqlcmd -Query "SELECT name, database_id, create_date, collation_name FROM sys.databases WHERE database_id > 4" -ConnectionString $sqlConnection
    
    foreach ($db in $databases) {
        $dbInfo = @{
            Name = $db.name
            CreateDate = $db.create_date
            Collation = $db.collation_name
            SizeInfo = @{}
        }
        
        # Get database size
        $sizeQuery = "SELECT 
            DB_NAME(database_id) AS DatabaseName,
            SUM(CASE WHEN type_desc = 'ROWS' THEN size END) * 8 / 1024 AS DataFileSizeMB,
            SUM(CASE WHEN type_desc = 'LOG' THEN size END) * 8 / 1024 AS LogFileSizeMB
            FROM sys.master_files 
            WHERE database_id = $($db.database_id)
            GROUP BY database_id"
            
        $sizeResult = Invoke-Sqlcmd -Query $sizeQuery -ConnectionString $sqlConnection
        $dbInfo.SizeInfo = @{
            DataSizeMB = $sizeResult.DataFileSizeMB
            LogSizeMB = $sizeResult.LogFileSizeMB
        }
        
        $assessment.Databases += $dbInfo
    }
    
    # Add recommendations
    $assessment.Recommendations += "Consider Azure SQL Database for databases under 4TB"
    $assessment.Recommendations += "Use Azure SQL Managed Instance for complex dependencies"
    $assessment.Recommendations += "Review collation compatibility with Azure SQL"
    
} catch {
    $assessment.Error = $_.Exception.Message
    $assessment.Recommendations += "SQL Server PowerShell module not available or connection failed"
}

$assessment | ConvertTo-Json -Depth 4
"""

# Hyper-V VM assessment script
HYPERV_VM_ASSESSMENT = """
param(
    [string]$VMName = $null
)

$assessment = @{
    Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    VirtualMachines = @()
    HostInfo = @{}
    Recommendations = @()
}

try {
    # Check if Hyper-V module is available
    Import-Module Hyper-V -ErrorAction Stop
    
    # Get host information
    $assessment.HostInfo = @{
        ComputerName = $env:COMPUTERNAME
        HyperVVersion = (Get-WindowsFeature -Name Hyper-V).InstallState
        ProcessorCount = (Get-WmiObject -Class Win32_Processor).NumberOfCores
        TotalMemoryGB = [math]::Round((Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
    }
    
    # Get VM information
    $vms = if ($VMName) { Get-VM -Name $VMName } else { Get-VM }
    
    foreach ($vm in $vms) {
        $vmInfo = @{
            Name = $vm.Name
            State = $vm.State
            Generation = $vm.Generation
            ProcessorCount = $vm.ProcessorCount
            MemoryAssignedGB = [math]::Round($vm.MemoryAssigned / 1GB, 2)
            MemoryMinimumGB = [math]::Round($vm.MemoryMinimum / 1GB, 2)
            MemoryMaximumGB = [math]::Round($vm.MemoryMaximum / 1GB, 2)
            DynamicMemoryEnabled = $vm.DynamicMemoryEnabled
            Path = $vm.Path
            ConfigurationLocation = $vm.ConfigurationLocation
            HardDrives = @()
            NetworkAdapters = @()
        }
        
        # Get hard drive information
        $hardDrives = Get-VMHardDiskDrive -VM $vm
        foreach ($hd in $hardDrives) {
            $vmInfo.HardDrives += @{
                ControllerType = $hd.ControllerType
                ControllerNumber = $hd.ControllerNumber
                ControllerLocation = $hd.ControllerLocation
                Path = $hd.Path
            }
        }
        
        # Get network adapter information
        $netAdapters = Get-VMNetworkAdapter -VM $vm
        foreach ($adapter in $netAdapters) {
            $vmInfo.NetworkAdapters += @{
                Name = $adapter.Name
                SwitchName = $adapter.SwitchName
                MacAddress = $adapter.MacAddress
                DynamicMacAddressEnabled = $adapter.DynamicMacAddressEnabled
            }
        }
        
        $assessment.VirtualMachines += $vmInfo
    }
    
    # Add recommendations
    $assessment.Recommendations += "Generation 2 VMs are recommended for Azure migration"
    $assessment.Recommendations += "Consider Azure VM sizes based on current resource allocation"
    $assessment.Recommendations += "Review network configuration for Azure compatibility"
    
} catch {
    $assessment.Error = $_.Exception.Message
    $assessment.Recommendations += "Hyper-V PowerShell module not available or insufficient permissions"
}

$assessment | ConvertTo-Json -Depth 4
"""

# File system migration assessment script
FILESYSTEM_ASSESSMENT = """
param(
    [string]$Path = "C:\\"
)

$assessment = @{
    Path = $Path
    Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    StorageInfo = @{}
    FileTypeAnalysis = @{}
    Recommendations = @()
}

try {
    # Get storage information
    $drive = Get-WmiObject -Class Win32_LogicalDisk | Where-Object { $_.DeviceID -eq (Split-Path $Path -Qualifier) }
    if ($drive) {
        $assessment.StorageInfo = @{
            DriveLetter = $drive.DeviceID
            TotalSizeGB = [math]::Round($drive.Size / 1GB, 2)
            FreeSpaceGB = [math]::Round($drive.FreeSpace / 1GB, 2)
            UsedSpaceGB = [math]::Round(($drive.Size - $drive.FreeSpace) / 1GB, 2)
            FileSystem = $drive.FileSystem
        }
    }
    
    # Analyze file types and sizes
    if (Test-Path $Path) {
        $files = Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue | 
                 Select-Object Extension, Length | 
                 Group-Object Extension
        
        $fileTypeStats = @{}
        foreach ($group in $files) {
            $extension = if ($group.Name) { $group.Name } else { "No Extension" }
            $fileTypeStats[$extension] = @{
                Count = $group.Count
                TotalSizeMB = [math]::Round(($group.Group | Measure-Object Length -Sum).Sum / 1MB, 2)
            }
        }
        $assessment.FileTypeAnalysis = $fileTypeStats
    }
    
    # Add recommendations
    $assessment.Recommendations += "Consider Azure Files for file shares migration"
    $assessment.Recommendations += "Use Azure Storage Explorer for data transfer"
    $assessment.Recommendations += "Review file permissions and security settings"
    
} catch {
    $assessment.Error = $_.Exception.Message
}

$assessment | ConvertTo-Json -Depth 3
"""

# Network configuration assessment
NETWORK_ASSESSMENT = """
$assessment = @{
    Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    NetworkAdapters = @()
    RoutingTable = @()
    DNSConfiguration = @{}
    FirewallStatus = @{}
    Recommendations = @()
}

try {
    # Get network adapter information
    $adapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' }
    foreach ($adapter in $adapters) {
        $adapterInfo = @{
            Name = $adapter.Name
            InterfaceDescription = $adapter.InterfaceDescription
            LinkSpeed = $adapter.LinkSpeed
            MacAddress = $adapter.MacAddress
            IPAddresses = @()
        }
        
        # Get IP configuration
        $ipConfig = Get-NetIPAddress -InterfaceIndex $adapter.InterfaceIndex -ErrorAction SilentlyContinue
        foreach ($ip in $ipConfig) {
            $adapterInfo.IPAddresses += @{
                IPAddress = $ip.IPAddress
                AddressFamily = $ip.AddressFamily
                PrefixLength = $ip.PrefixLength
            }
        }
        
        $assessment.NetworkAdapters += $adapterInfo
    }
    
    # Get routing table
    $routes = Get-NetRoute | Where-Object { $_.RouteMetric -lt 1000 }
    foreach ($route in $routes) {
        $assessment.RoutingTable += @{
            DestinationPrefix = $route.DestinationPrefix
            NextHop = $route.NextHop
            RouteMetric = $route.RouteMetric
            InterfaceIndex = $route.InterfaceIndex
        }
    }
    
    # Get DNS configuration
    $dnsServers = Get-DnsClientServerAddress | Where-Object { $_.ServerAddresses.Count -gt 0 }
    $assessment.DNSConfiguration = @{
        Servers = $dnsServers.ServerAddresses
        SearchSuffixes = (Get-DnsClientGlobalSetting).SuffixSearchList
    }
    
    # Check Windows Firewall status
    $firewallProfiles = Get-NetFirewallProfile
    foreach ($profile in $firewallProfiles) {
        $assessment.FirewallStatus[$profile.Name] = @{
            Enabled = $profile.Enabled
            DefaultInboundAction = $profile.DefaultInboundAction
            DefaultOutboundAction = $profile.DefaultOutboundAction
        }
    }
    
    # Add recommendations
    $assessment.Recommendations += "Review network security groups in Azure"
    $assessment.Recommendations += "Plan for Azure Virtual Network configuration"
    $assessment.Recommendations += "Consider ExpressRoute for hybrid connectivity"
    
} catch {
    $assessment.Error = $_.Exception.Message
}

$assessment | ConvertTo-Json -Depth 3
"""
