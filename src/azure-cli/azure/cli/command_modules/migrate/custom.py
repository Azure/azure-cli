# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import platform
import sys
from knack.util import CLIError
from knack.log import get_logger
from azure.cli.core.util import run_cmd
from azure.cli.command_modules.migrate._powershell_utils import get_powershell_executor, PowerShellExecutor

logger = get_logger(__name__)

# --------------------------------------------------------------------------------------------
# System Environment Commands
# --------------------------------------------------------------------------------------------


def check_migration_prerequisites(cmd):
    """Check if the system meets migration prerequisites."""
    ps_executor = get_powershell_executor()
    
    try:
        prereqs = ps_executor.check_migration_prerequisites()
        
        logger.info(f"PowerShell Version: {prereqs.get('PowerShell Version', 'Unknown')}")
        logger.info(f"Platform: {prereqs.get('Platform', 'Unknown')}")
        logger.info(f"Edition: {prereqs.get('Edition', 'Unknown')}")
        
        if prereqs.get('Platform') == 'Win32NT':
            if not prereqs.get('IsAdmin', False):
                logger.warning("Running without administrator privileges. Some migration operations may require elevated permissions.")
        
        return prereqs
        
    except Exception as e:
        raise CLIError(f'Failed to check migration prerequisites: {str(e)}')

def setup_migration_environment(cmd, install_powershell=False, check_only=False):
    """Configure the system environment for migration operations."""    
    logger = get_logger(__name__)
    system = platform.system().lower()
    
    setup_results = {
        'platform': system,
        'checks': [],
        'actions_taken': [],
        'recommendations': [],
        'status': 'success'
    }
    
    try:
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 7:
            setup_results['checks'].append({
                'component': 'Python',
                'status': 'passed',
                'version': f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                'message': 'Python version is compatible'
            })
        else:
            setup_results['checks'].append({
                'component': 'Python',
                'status': 'failed',
                'version': f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                'message': 'Python 3.7 or higher is required'
            })
            setup_results['status'] = 'warning'
        
        powershell_check = _check_powershell_availability(system)
        setup_results['checks'].append(powershell_check)
        
        if powershell_check['status'] == 'failed' and install_powershell and not check_only:
            install_result = _install_powershell(system, logger)
            setup_results['actions_taken'].append(install_result)
            
            powershell_recheck = _check_powershell_availability(system)
            setup_results['checks'].append({
                'component': 'PowerShell (after installation)',
                'status': powershell_recheck['status'],
                'version': powershell_recheck.get('version', 'Unknown'),
                'message': powershell_recheck['message']
            })
        
        if system == 'windows':
            setup_results['checks'].extend(_check_windows_tools())
        elif system == 'linux':
            setup_results['checks'].extend(_check_linux_tools())
        elif system == 'darwin':
            setup_results['checks'].extend(_check_macos_tools())
        
        setup_results['recommendations'] = _get_platform_recommendations(system, setup_results['checks'])
        
        failed_checks = [c for c in setup_results['checks'] if c['status'] == 'failed']
        if failed_checks:
            setup_results['status'] = 'failed' if any(c['component'] == 'PowerShell' for c in failed_checks) else 'warning'
        
        return setup_results
        
    except Exception as e:
        raise CLIError(f'Failed to setup migration environment: {str(e)}')


def _check_powershell_availability(system):
    """Check if PowerShell is available on the system."""
    
    try:
        executor = PowerShellExecutor()
        is_available, command = executor.check_powershell_available()
        
        if is_available:
            try:
                if command == 'pwsh':
                    result = run_cmd([command, '--version'], capture_output=True, timeout=10)
                else:
                    result = run_cmd([command, '-Command', '$PSVersionTable.PSVersion.ToString()'], 
                                   capture_output=True, timeout=10)
                
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0] if result.stdout else 'Unknown'
                else:
                    version = 'Available'
            except Exception:
                version = 'Available'
            
            return {
                'component': 'PowerShell',
                'status': 'passed',
                'version': version,
                'command': command,
                'message': f'PowerShell is available via {command}'
            }
    except Exception as e:
        pass
    
    return {
        'component': 'PowerShell',
        'status': 'failed',
        'version': None,
        'command': None,
        'message': 'PowerShell is not available. Install PowerShell Core or ensure Windows PowerShell is accessible.'
    }


def _install_powershell(system, logger):
    """Attempt to install PowerShell on the system."""
    
    install_result = {
        'component': 'PowerShell Installation',
        'status': 'attempted',
        'message': '',
        'commands': []
    }
    
    try:
        if system == 'windows':
            try:
                result = run_cmd(['winget', 'install', 'Microsoft.PowerShell'], 
                                capture_output=True, timeout=300)
                if result.returncode == 0:
                    install_result['status'] = 'success'
                    install_result['message'] = 'PowerShell Core installed via winget'
                    install_result['commands'].append('winget install Microsoft.PowerShell')
                else:
                    install_result['status'] = 'failed'
                    install_result['message'] = 'winget installation failed. Please install manually from https://github.com/PowerShell/PowerShell'
            except Exception:
                install_result['status'] = 'failed'
                install_result['message'] = 'winget not available. Please install PowerShell Core manually from https://github.com/PowerShell/PowerShell'
        
        elif system == 'linux':
            install_result['status'] = 'manual_required'
            install_result['message'] = 'Please install PowerShell Core using your distribution package manager'
            install_result['commands'] = [
                '# Ubuntu/Debian: sudo apt update && sudo apt install -y powershell',
                '# CentOS/RHEL: sudo yum install -y powershell',
                '# Or download from: https://github.com/PowerShell/PowerShell'
            ]
        
        elif system == 'darwin':
            try:
                result = run_cmd(['brew', 'install', 'powershell'], 
                                capture_output=True, timeout=300)
                if result.returncode == 0:
                    install_result['status'] = 'success'
                    install_result['message'] = 'PowerShell Core installed via Homebrew'
                    install_result['commands'].append('brew install powershell')
                else:
                    install_result['status'] = 'failed'
                    install_result['message'] = 'Homebrew installation failed'
            except Exception:
                install_result['status'] = 'manual_required'
                install_result['message'] = 'Homebrew not available. Please install PowerShell Core manually'
                install_result['commands'] = [
                    'brew install powershell',
                    '# Or download from: https://github.com/PowerShell/PowerShell'
                ]
        
        logger.info(f"PowerShell installation result: {install_result['message']}")
        return install_result
        
    except Exception as e:
        install_result['status'] = 'error'
        install_result['message'] = f'Installation attempt failed: {str(e)}'
        return install_result


def _check_windows_tools():
    """Check for Windows-specific migration tools."""
    
    checks = []    
    powershell_modules = [
        'Hyper-V',
        'SqlServer',
        'WindowsFeature',
        'Storage'
    ]
    
    for module in powershell_modules:
        try:
            result = run_cmd([
                'powershell', '-Command', 
                f'Get-Module -ListAvailable -Name {module} | Select-Object -First 1'
            ], capture_output=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                checks.append({
                    'component': f'PowerShell Module: {module}',
                    'status': 'passed',
                    'message': f'{module} module is available'
                })
            else:
                checks.append({
                    'component': f'PowerShell Module: {module}',
                    'status': 'warning',
                    'message': f'{module} module not found (optional for some migrations)'
                })
        except Exception:
            checks.append({
                'component': f'PowerShell Module: {module}',
                'status': 'warning',
                'message': f'Could not check {module} module availability'
            })
    
    return checks


def _check_linux_tools():
    """Check for Linux-specific tools that might be useful for migration."""
    
    checks = []    
    tools = [
        ('curl', 'Data transfer tool'),
        ('wget', 'File download tool'),
        ('rsync', 'File synchronization tool'),
        ('ssh', 'Secure shell client')
    ]
    
    for tool, description in tools:
        try:
            result = run_cmd(['which', tool], capture_output=True, timeout=5)
            if result.returncode == 0:
                checks.append({
                    'component': f'Tool: {tool}',
                    'status': 'passed',
                    'message': f'{description} is available'
                })
            else:
                checks.append({
                    'component': f'Tool: {tool}',
                    'status': 'warning',
                    'message': f'{description} not found (may be useful for some migrations)'
                })
        except Exception:
            checks.append({
                'component': f'Tool: {tool}',
                'status': 'warning',
                'message': f'Could not check {tool} availability'
            })
    
    return checks


def _check_macos_tools():
    """Check for macOS-specific tools."""
    
    checks = []    
    try:
        result = run_cmd(['brew', '--version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            checks.append({
                'component': 'Homebrew',
                'status': 'passed',
                'message': 'Package manager available for installing additional tools'
            })
        else:
            checks.append({
                'component': 'Homebrew',
                'status': 'warning',
                'message': 'Homebrew not available (useful for installing additional tools)'
            })
    except Exception:
        checks.append({
            'component': 'Homebrew',
            'status': 'warning',
            'message': 'Homebrew not installed. Consider installing from https://brew.sh'
        })
    
    return checks


def _get_platform_recommendations(system, checks):
    """Get platform-specific recommendations based on check results."""
    recommendations = []
    
    powershell_checks = [c for c in checks if 'PowerShell' in c['component']]
    if any(c['status'] == 'failed' for c in powershell_checks):
        if system == 'windows':
            recommendations.append("Install PowerShell Core from https://github.com/PowerShell/PowerShell or use 'winget install Microsoft.PowerShell'")
        elif system == 'linux':
            recommendations.append("Install PowerShell Core using your package manager or from https://github.com/PowerShell/PowerShell")
        elif system == 'darwin':
            recommendations.append("Install PowerShell Core using 'brew install powershell' or from https://github.com/PowerShell/PowerShell")
    
    if system == 'windows':
        recommendations.extend([
            "Consider installing Hyper-V PowerShell module for VM migrations: Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-Management-PowerShell",
            "For SQL Server migrations, install SQL Server PowerShell module: Install-Module -Name SqlServer",
            "Ensure you have appropriate permissions for accessing system resources"
        ])
    elif system == 'linux':
        recommendations.extend([
            "Install common migration tools: sudo apt install curl wget rsync openssh-client (Ubuntu/Debian)",
            "For database migrations, consider installing database client tools",
            "Ensure Docker is available if containerization is part of your migration strategy"
        ])
    elif system == 'darwin':
        recommendations.extend([
            "Install Homebrew for easy tool management: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"",
            "Consider installing common migration tools via Homebrew: brew install curl wget rsync"
        ])
    
    return recommendations

# --------------------------------------------------------------------------------------------
# Authentication and Discovery Commands
# --------------------------------------------------------------------------------------------

def get_discovered_server(cmd, resource_group_name, project_name, subscription_id=None, server_id=None, source_machine_type='VMware', output_format='json', display_fields=None):
    """Azure CLI equivalent to Get-AzMigrateDiscoveredServer PowerShell cmdlet."""
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    discover_script = f"""
    # Azure CLI equivalent functionality for Get-AzMigrateDiscoveredServer
    $ResourceGroupName = '{resource_group_name}'
    $ProjectName = '{project_name}'
    $SourceMachineType = '{source_machine_type}'
    
    try {{
        # Execute the real PowerShell cmdlet - equivalent to your provided commands
        if ('{server_id}') {{
            $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceMachineType $SourceMachineType | Where-Object {{ $_.Id -eq '{server_id}' }}
        }} else {{
            $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceMachineType $SourceMachineType
        }}
        
        if ($DiscoveredServers) {{
            # Format output similar to Write-Output $DiscoveredServers | Format-Table DisplayName,Name,Type
            if ('{output_format}' -eq 'table') {{
                $DiscoveredServers | Format-Table -Property DisplayName, Name, Type -AutoSize | Out-String
            }} else {{
                # Return JSON for programmatic use
                $result = @{{
                    'DiscoveredServers' = $DiscoveredServers
                    'Count' = $DiscoveredServers.Count
                    'ProjectName' = $ProjectName
                    'ResourceGroupName' = $ResourceGroupName
                    'SourceMachineType' = $SourceMachineType
                }}
                $result | ConvertTo-Json -Depth 5
            }}
        }} else {{
            if ('{output_format}' -eq 'table') {{
                Write-Host "No discovered servers found in project: $ProjectName (Source Type: $SourceMachineType)"
            }} else {{
                @{{ 
                    'DiscoveredServers' = @()
                    'Count' = 0
                    'ProjectName' = $ProjectName
                    'ResourceGroupName' = $ResourceGroupName
                    'SourceMachineType' = $SourceMachineType
                    'Message' = 'No discovered servers found'
                }} | ConvertTo-Json
            }}
        }}
    }} catch {{
        Write-Error "Failed to get discovered servers: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        if output_format == 'table':
            # For table output, use interactive execution to show PowerShell formatting
            result = ps_executor.execute_script_interactive(discover_script)
            return {'message': 'Table output displayed above', 'format': 'table'}
        else:
            # For JSON output, use regular execution
            result = ps_executor.execute_azure_authenticated_script(discover_script, subscription_id=subscription_id)
            
            # Extract JSON from PowerShell output (may have other text mixed in)
            stdout_content = result.get('stdout', '').strip()
            if not stdout_content:
                raise CLIError('No output received from PowerShell command')
            
            # Find JSON content (starts with { and ends with })
            json_start = stdout_content.find('{')
            json_end = stdout_content.rfind('}')
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_content = stdout_content[json_start:json_end + 1]
                try:
                    discovered_data = json.loads(json_content)
                    
                    # If display_fields is specified, filter the output
                    if display_fields and discovered_data.get('DiscoveredServers'):
                        fields = [field.strip() for field in display_fields.split(',')]
                        filtered_servers = []
                        for server in discovered_data['DiscoveredServers']:
                            filtered_server = {}
                            for field in fields:
                                if field in server:
                                    filtered_server[field] = server[field]
                            filtered_servers.append(filtered_server)
                        discovered_data['DiscoveredServers'] = filtered_servers
                        discovered_data['DisplayFields'] = fields
                    
                    return discovered_data
                except json.JSONDecodeError as je:
                    raise CLIError(f'Failed to parse JSON from PowerShell output: {str(je)}')
            else:
                # No JSON found, return raw output for debugging
                return {
                    'raw_output': stdout_content,
                'message': 'No JSON structure found in PowerShell output',
                'stderr': result.get('stderr', '')
            }
            
    except Exception as e:
        raise CLIError(f'Failed to get discovered servers: {str(e)}')

def get_discovered_servers_table(cmd, resource_group_name, project_name, source_machine_type='VMware', subscription_id=None):
    """
    Exact Azure CLI equivalent to the PowerShell commands:
    $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceMachineType <'HyperV' or 'VMware'>
    Write-Output $DiscoveredServers | Format-Table DisplayName,Name,Type
    """
    ps_executor = get_powershell_executor()
    
    powershell_script = f"""
    # Exact equivalent of the provided PowerShell commands
    $ProjectName = '{project_name}'
    $ResourceGroupName = '{resource_group_name}'
    $SourceMachineType = '{source_machine_type}'
    
    try {{
        # Your exact PowerShell commands:
        $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceMachineType $SourceMachineType
        Write-Output $DiscoveredServers | Format-Table DisplayName,Name,Type
        
    }} catch {{
        Write-Error "Failed to execute PowerShell commands: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        # Use interactive execution to show real-time PowerShell output
        ps_executor.execute_script_interactive(powershell_script)
    except Exception as e:
        raise CLIError(f'Failed to execute PowerShell commands: {str(e)}')

def initialize_replication_infrastructure(cmd, resource_group_name, project_name, target_region):
    """Initialize Azure Migrate replication infrastructure."""
    
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    init_script = f"""
    # Initialize Azure Migrate replication infrastructure
    try {{
        # Initialize the replication infrastructure
        $InitResult = Initialize-AzMigrateReplicationInfrastructure `
            -ResourceGroupName "{resource_group_name}" `
            -ProjectName "{project_name}" `
            -Scenario "agentlessVMware" `
            -TargetRegion "{target_region}"
        
        if ($InitResult) {{
            $InitResult | Format-List
        }}
        
    }} catch {{
        Write-Error "Failed to initialize replication infrastructure: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(init_script)    
    except Exception as e:
        raise CLIError(f'Failed to initialize replication infrastructure: {str(e)}')


def check_replication_infrastructure(cmd, resource_group_name, project_name):
    """Check the status of Azure Migrate replication infrastructure."""
    
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    check_script = f"""
    # Check Azure Migrate replication infrastructure status
    try {{
        # Check if the Azure Migrate project exists
        $Project = Get-AzResource -ResourceGroupName "{resource_group_name}" -ResourceType "Microsoft.Migrate/MigrateProjects" -Name "{project_name}" -ErrorAction SilentlyContinue
        if (-Not $Project) {{
            Write-Host "Azure Migrate Project not found"
        }}
        
        # Check for replication infrastructure resources
        $Vaults = Get-AzResource -ResourceGroupName "{resource_group_name}" -ResourceType "Microsoft.RecoveryServices/vaults" -ErrorAction SilentlyContinue
        if (-Not $Vaults) {{
            Write-Host "No Recovery Services Vault(s) found"
        }}
        
        # Check for Storage Accounts (used for replication)
        $StorageAccounts = Get-AzStorageAccount -ResourceGroupName "{resource_group_name}" -ErrorAction SilentlyContinue
        if (-Not $StorageAccounts) {{
            Write-Host "No Storage Account(s) found"
        }}
        
        # Try to get existing server replications to test if infrastructure is working
        try {{
            $Replications = Get-AzMigrateServerReplication -ProjectName "{project_name}" -ResourceGroupName "{resource_group_name}" -ErrorAction SilentlyContinue
            Write-Host "Replication infrastructure is accessible"
            if (-Not $Replications) {{
                Write-Host "No existing replications found"
            }}
        }} catch {{
            if ($_.Exception.Message -like "*not initialized*") {{
                Write-Host "Replication infrastructure is NOT initialized"
            }} else {{
                Write-Host "Could not test replication infrastructure: $($_.Exception.Message)"
            }}
        }}
        
    }} catch {{
        Write-Error "Failed to check replication infrastructure: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        # Use interactive execution to show real-time PowerShell output
        ps_executor.execute_script_interactive(check_script)
        
    except Exception as e:
        raise CLIError(f'Failed to check replication infrastructure: {str(e)}')

def connect_azure_account(cmd, subscription_id=None, tenant_id=None, device_code=False, app_id=None, secret=None):
    """
    Connect to Azure account using PowerShell Connect-AzAccount with enhanced visibility.
    Azure CLI equivalent to Connect-AzAccount PowerShell cmdlet.
    """
    ps_executor = get_powershell_executor()
    
    connect_script = """
    try {
        # Connection parameters
        $connectParams = @{}
        """
    
    if subscription_id:
        connect_script += f"""
        $connectParams['Subscription'] = '{subscription_id}'
        """
    
    if tenant_id:
        connect_script += f"""
        $connectParams['Tenant'] = '{tenant_id}'
        """
    
    if device_code:
        connect_script += """
        $connectParams['UseDeviceAuthentication'] = $true
        Write-Host "To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code displayed below to authenticate."
        """
    
    if app_id and secret:
        connect_script += f"""
        $securePassword = ConvertTo-SecureString '{secret}' -AsPlainText -Force
        $credential = New-Object System.Management.Automation.PSCredential('{app_id}', $securePassword)
        $connectParams['ServicePrincipal'] = $true
        $connectParams['Credential'] = $credential
        """
    
    connect_script += """
        # Connect to Azure
        $context = Connect-AzAccount @connectParams
        
        if ($context) {
            Write-Host ""
            Write-Host "Successfully connected to Azure"
            Write-Host ""
        } else {
            Write-Host ""
            Write-Host "Failed to connect to Azure"
            Write-Host ""
        }
    } catch {
        Write-Error "Failed to connect to Azure: $($_.Exception.Message)"
        
        @{
            'Status' = 'Failed'
            'Error' = $_.Exception.Message
            'Message' = 'Failed to connect to Azure'
        } | ConvertTo-Json -Depth 3
        throw
    }
    """
    
    try:
        # Use interactive execution to show real-time authentication progress with full visibility
        ps_executor.execute_script_interactive(connect_script)
    except Exception as e:
        raise CLIError(f'Failed to connect to Azure: {str(e)}')

def disconnect_azure_account(cmd):
    """
    Disconnect from Azure account using PowerShell Disconnect-AzAccount with enhanced visibility.
    Azure CLI equivalent to Disconnect-AzAccount PowerShell cmdlet.
    """
    ps_executor = get_powershell_executor()
    
    disconnect_script = """
    try {
        # Check if currently connected
        $currentContext = Get-AzContext -ErrorAction SilentlyContinue

        Write-Host "Disconnecting from Azure..."
        Write-Host "Current account: $($currentContext.Account.Id)"
        
        # Store context info before disconnecting
        $previousAccountId = $currentContext.Account.Id
        $previousSubscriptionId = $currentContext.Subscription.Id
        $previousSubscriptionName = $currentContext.Subscription.Name
        $previousTenantId = $currentContext.Tenant.Id
        
        # Disconnect from Azure
        Disconnect-AzAccount -Confirm:$false
        
        Write-Host "Successfully disconnected from Azure"
        
    } catch {
        Write-Error "Failed to disconnect from Azure: $($_.Exception.Message)"
    }
    """
    
    try:
        ps_executor.execute_script_interactive(disconnect_script)
    except Exception as e:
        raise CLIError(f'Failed to disconnect from Azure: {str(e)}')

def set_azure_context(cmd, subscription_id=None, subscription_name=None, tenant_id=None):
    """
    Set the current Azure context using PowerShell Set-AzContext with enhanced visibility.
    Azure CLI equivalent to Set-AzContext PowerShell cmdlet.
    """
    ps_executor = get_powershell_executor()
    
    if not subscription_id and not subscription_name:
        raise CLIError('Either subscription_id or subscription_name must be provided')
    
    set_context_script = f"""
    try {{ 
        $currentContext = Get-AzContext -ErrorAction SilentlyContinue
        if (-not $currentContext) {{
            Write-Host "Not currently connected to Azure. Please connect first with: az migrate auth login"
        }}
        
        # Set context parameters
        $contextParams = @{{}}
        """
    
    if subscription_id:
        set_context_script += f"""
        $contextParams['SubscriptionId'] = '{subscription_id}'
        """
    elif subscription_name:
        set_context_script += f"""
        $contextParams['SubscriptionName'] = '{subscription_name}'
        """
    
    if tenant_id:
        set_context_script += f"""
        $contextParams['TenantId'] = '{tenant_id}'
        """
    
    set_context_script += """
        $newContext = Set-AzContext @contextParams
        
        if ($newContext) {
            Write-Host "Azure context updated successfully"
        }}
    } catch {
        Write-Error "Failed to set Azure context: $($_.Exception.Message)"
    }
    """
    
    try:
        ps_executor.execute_script_interactive(set_context_script)
    except Exception as e:
        raise CLIError(f'Failed to set Azure context: {str(e)}')

# --------------------------------------------------------------------------------------------
# Server Replication Commands
# --------------------------------------------------------------------------------------------

def create_server_replication(cmd, resource_group_name, project_name, target_vm_name, 
                             target_resource_group, target_network, server_name=None, 
                             server_index=None):
    """Create replication for a discovered server."""
    
    ps_executor = get_powershell_executor()    
    replication_script = f"""
    # Create server replication
    try {{        
        $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName {project_name} -ResourceGroupName {resource_group_name} -SourceMachineType VMware
        
        if ("{server_index}" -ne "None" -and "{server_index}" -ne "") {{
            $ServerIndex = [int]"{server_index}"
            if ($ServerIndex -ge 0 -and $ServerIndex -lt $DiscoveredServers.Count) {{
                $SelectedServer = $DiscoveredServers[$ServerIndex]
                Write-Host "Selected server by index $ServerIndex`: $($SelectedServer.DisplayName)"
            }} else {{
                throw "Server index $ServerIndex is out of range. Total servers: $($DiscoveredServers.Count)"
            }}
        }} elseif ("{server_name}" -ne "None" -and "{server_name}" -ne "") {{
            $SelectedServer = $DiscoveredServers | Where-Object {{ $_.DisplayName -eq "{server_name}" }}
            if (-not $SelectedServer) {{
                throw "Server with name '{server_name}' not found"
            }}
            Write-Host "Selected server by name: $($SelectedServer.DisplayName)"
        }} else {{
            throw "Either server_name or server_index must be provided"
        }}
        
        # Get machine details including disk information
        $MachineId = $SelectedServer.Name
        Write-Host "Machine ID: $MachineId"
        
        # Build the full machine resource path for New-AzMigrateServerReplication
        $SubscriptionId = (Get-AzContext).Subscription.Id
        $MachineResourcePath = "/subscriptions/$SubscriptionId/resourceGroups/{resource_group_name}/providers/Microsoft.OffAzure/VMwareSites/**/machines/$MachineId"
        
        # Try to get the exact machine resource path by finding the VMware site
        try {{
            $Sites = Get-AzResource -ResourceGroupName "{resource_group_name}" -ResourceType "Microsoft.OffAzure/VMwareSites" -ErrorAction SilentlyContinue
            if ($Sites -and $Sites.Count -gt 0) {{
                $SiteName = $Sites[0].Name
                $MachineResourcePath = "/subscriptions/$SubscriptionId/resourceGroups/{resource_group_name}/providers/Microsoft.OffAzure/VMwareSites/$SiteName/machines/$MachineId"
                Write-Host "Full machine path: $MachineResourcePath"
            }}
        }} catch {{
            $MachineResourcePath = $MachineId
        }}
        
        # Get detailed server information to extract disk details
        $ServerDetails = Get-AzMigrateDiscoveredServer -ProjectName {project_name} -ResourceGroupName {resource_group_name} -DisplayName $SelectedServer.DisplayName
        
        # Extract OS disk ID from the server details
        $OSDiskId = $null
        if ($ServerDetails.Disk) {{
            $OSDisk = $ServerDetails.Disk | Where-Object {{ $_.IsOSDisk -eq $true }}
            if ($OSDisk) {{
                $OSDiskId = $OSDisk.Uuid
            }} else {{
                # If no OS disk found with IsOSDisk flag, take the first disk
                $OSDiskId = $ServerDetails.Disk[0].Uuid
            }}
        }} else {{
            throw "No disk information found for server $($SelectedServer.DisplayName)"
        }}
        
        Write-Host "OS Disk ID: $OSDiskId"
        
        # Extract subnet name from the target network path or use default
        $TargetNetworkPath = "{target_network}"
        $SubnetName = "default"
        
        # Try to find available subnets in the target network
        try {{
            $NetworkParts = $TargetNetworkPath -split "/"
            $NetworkRG = $NetworkParts[4]  # Resource group from the network path
            $NetworkName = $NetworkParts[-1]  # Network name from the path
            
            $VirtualNetwork = Get-AzVirtualNetwork -ResourceGroupName $NetworkRG -Name $NetworkName -ErrorAction SilentlyContinue
            
            if ($VirtualNetwork -and $VirtualNetwork.Subnets) {{
                # Use the first available subnet
                $SubnetName = $VirtualNetwork.Subnets[0].Name
                Write-Host "Using subnet: $SubnetName"
            }}
        }} catch {{
            # Use default subnet name
        }}
        
        # Create replication with required parameters including OS disk ID
        $ReplicationJob = New-AzMigrateServerReplication `
            -MachineId $MachineResourcePath `
            -LicenseType "NoLicenseType" `
            -TargetResourceGroupId "{target_resource_group}" `
            -TargetNetworkId "{target_network}" `
            -TargetSubnetName $SubnetName `
            -TargetVMName "{target_vm_name}" `
            -DiskType "Standard_LRS" `
            -OSDiskID $OSDiskId
        
        Write-Host "Replication created successfully"
        Write-Host "Job ID: $($ReplicationJob.JobId)"
        Write-Host "Target VM Name: {target_vm_name}"
        
    }} catch {{
        Write-Error "Error creating replication: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(replication_script)       
    except Exception as e:
        raise CLIError(f'Failed to create server replication: {str(e)}')


def get_discovered_servers_by_display_name(cmd, resource_group_name, project_name, display_name, source_machine_type='VMware'):
    """Find discovered servers by display name."""
    
    ps_executor = get_powershell_executor()
    
    search_script = f"""
    # Find servers by display name
    try {{
        $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName {project_name} -ResourceGroupName {resource_group_name} -SourceMachineType {source_machine_type}
        $MatchingServers = $DiscoveredServers | Where-Object {{ $_.DisplayName -like "*{display_name}*" }}
        
        if ($MatchingServers) {{
            Write-Host "Found $($MatchingServers.Count) matching server(s):"
            $MatchingServers | Format-Table DisplayName, Name, Type -AutoSize
        }} else {{
            Write-Host "No servers found matching: {display_name}"
        }}
        
        return $MatchingServers
        
    }} catch {{
        Write-Error "Error searching for servers: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(search_script)
    except Exception as e:
        raise CLIError(f'Failed to search for servers: {str(e)}')


def get_replication_job_status(cmd, resource_group_name, project_name, vm_name=None, 
                              job_id=None, subscription_id=None):
    """Get replication job status for a VM or job."""
    
    ps_executor = get_powershell_executor()
    
    status_script = f"""
    # Get replication status
    try {{
        if ("{vm_name}" -ne "None" -and "{vm_name}" -ne "") {{
            Write-Host "Checking status for VM: {vm_name}"
            $ReplicationStatus = Get-AzMigrateServerReplication -ProjectName {project_name} -ResourceGroupName {resource_group_name} -MachineName "{vm_name}"
        }} elseif ("{job_id}" -ne "None" -and "{job_id}" -ne "") {{
            Write-Host "Checking job status for Job ID: {job_id}"
            $ReplicationStatus = Get-AzMigrateJob -JobId "{job_id}" -ProjectName {project_name} -ResourceGroupName {resource_group_name}
        }} else {{
            Write-Host "Getting all replication jobs..."
            $ReplicationStatus = Get-AzMigrateServerReplication -ProjectName {project_name} -ResourceGroupName {resource_group_name}
        }}
        
        if ($ReplicationStatus) {{
            $ReplicationStatus | Format-Table -AutoSize
        }} else {{
            Write-Host "No replication status found"
        }}
        
        return $ReplicationStatus
        
    }} catch {{
        Write-Error "Error getting replication status: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(status_script)
    except Exception as e:
        raise CLIError(f'Failed to get replication status: {str(e)}')


def set_replication_target_properties(cmd, resource_group_name, project_name, vm_name, 
                                     target_vm_size=None, target_disk_type=None, target_network=None):
    """Update replication target properties."""
    
    ps_executor = get_powershell_executor()    
    update_script = f"""
    # Update replication properties
    try {{
        # Get current replication
        $Replication = Get-AzMigrateServerReplication -ProjectName {project_name} -ResourceGroupName {resource_group_name} -MachineName "{vm_name}"
        
        if ($Replication) {{
            $UpdateParams = @{{}}
            
            if ("{target_vm_size}" -ne "None" -and "{target_vm_size}" -ne "") {{
                $UpdateParams.TargetVMSize = "{target_vm_size}"
                Write-Host "Setting target VM size: {target_vm_size}"
            }}
            
            if ("{target_disk_type}" -ne "None" -and "{target_disk_type}" -ne "") {{
                $UpdateParams.TargetDiskType = "{target_disk_type}"
                Write-Host "Setting target disk type: {target_disk_type}"
            }}
            
            if ("{target_network}" -ne "None" -and "{target_network}" -ne "") {{
                $UpdateParams.TargetNetworkId = "{target_network}"
                Write-Host "Setting target network: {target_network}"
            }}
            
            if ($UpdateParams.Count -gt 0) {{
                $UpdateJob = Set-AzMigrateServerReplication -InputObject $Replication @UpdateParams
                Write-Host "Replication properties updated successfully"
                Write-Host "Update Job ID: $($UpdateJob.JobId)"
            }} else {{
                Write-Host "No properties to update"
            }}
        }} else {{
            throw "Replication not found for VM: {vm_name}"
        }}
        
    }} catch {{
        Write-Error "Error updating replication properties: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(update_script)     
    except Exception as e:
        raise CLIError(f'Failed to update replication properties: {str(e)}')


# --------------------------------------------------------------------------------------------
# Azure Local Migration Commands
# --------------------------------------------------------------------------------------------

def create_local_disk_mapping(cmd, disk_id, is_os_disk=True, is_dynamic=False, 
                             size_gb=64, format_type='VHD', physical_sector_size=512):
    """
    Azure CLI equivalent to New-AzMigrateLocalDiskMappingObject PowerShell cmdlet.
    Creates a disk mapping object for Azure Local migration.
    """
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    disk_mapping_script = f"""
    # Azure CLI equivalent functionality for New-AzMigrateLocalDiskMappingObject
    try {{
        # Execute the real PowerShell cmdlet - equivalent to your provided command
        $DiskMapping = New-AzMigrateLocalDiskMappingObject `
            -DiskID "{disk_id}" `
            -IsOSDisk '{str(is_os_disk).lower()}' `
            -IsDynamic '{str(is_dynamic).lower()}' `
            -Size {size_gb} `
            -Format '{format_type}' `
            -PhysicalSectorSize {physical_sector_size}
        
        if ($DiskMapping) {{
            Write-Host "Disk mapping object created successfully"
            $DiskMapping | Format-List
        }} else {{
            Write-Host "Failed to create disk mapping object"
        }}
        
    }} catch {{
        Write-Error "Failed to create disk mapping: $($_.Exception.Message)"
        
        @{{
            'Status' = 'Failed'
            'Error' = $_.Exception.Message
            'DiskID' = "{disk_id}"
            'Message' = 'Failed to create disk mapping object'
        }} | ConvertTo-Json -Depth 3
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(disk_mapping_script)   
    except Exception as e:
        raise CLIError(f'Failed to create disk mapping object: {str(e)}')


def create_local_server_replication(cmd, resource_group_name, project_name, server_index, 
                                   target_vm_name, target_storage_path_id, target_virtual_switch_id, 
                                   target_resource_group_id, disk_size_gb=64, disk_format='VHD', 
                                   is_dynamic=False, physical_sector_size=512):
    """
    Azure CLI equivalent to New-AzMigrateLocalServerReplication PowerShell cmdlet.
    Creates replication for Azure Stack HCI local migration.
    """
    ps_executor = get_powershell_executor()
    
    local_replication_script = f"""
    try {{
        $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName {project_name} -ResourceGroupName {resource_group_name} -SourceMachineType VMware
        
        if (-not $DiscoveredServers -or $DiscoveredServers.Count -eq 0) {{
            throw "No discovered servers found in project {project_name}"
        }}
        
        # Select server by index
        $ServerIndex = {server_index}
        if ($ServerIndex -ge 0 -and $ServerIndex -lt $DiscoveredServers.Count) {{
            $DiscoveredServer = $DiscoveredServers[$ServerIndex]
            Write-Host "Selected server: $($DiscoveredServer.DisplayName)"
            Write-Host "Server ID: $($DiscoveredServer.Id)"
        }} else {{
            throw "Server index $ServerIndex is out of range. Total servers: $($DiscoveredServers.Count)"
        }}
        
        # Get OS disk information
        if ($DiscoveredServer.Disk -and $DiscoveredServer.Disk.Count -gt 0) {{
            $OSDisk = $DiscoveredServer.Disk | Where-Object {{ $_.IsOSDisk -eq $true }}
            if (-not $OSDisk) {{
                $OSDisk = $DiscoveredServer.Disk[0]
            }}
            $OSDiskID = $OSDisk.Uuid
        }} else {{
            throw "No disk information found for server $($DiscoveredServer.DisplayName)"
        }}
        
        # Create disk mapping object
        $DiskMappings = New-AzMigrateLocalDiskMappingObject `
            -DiskID $OSDiskID `
            -IsOSDisk $true `
            -IsDynamic '${'$true' if is_dynamic else '$false'}' `
            -Size {disk_size_gb} `
            -Format '{disk_format}' `
            -PhysicalSectorSize {physical_sector_size}
        
        # Create local server replication
        $ReplicationJob = New-AzMigrateLocalServerReplication `
            -MachineId $DiscoveredServer.Id `
            -OSDiskID $OSDiskID `
            -TargetStoragePathId "{target_storage_path_id}" `
            -TargetVirtualSwitchId "{target_virtual_switch_id}" `
            -TargetResourceGroupId "{target_resource_group_id}" `
            -TargetVMName "{target_vm_name}"
        
        Write-Host "Local server replication created successfully"
        Write-Host "Job ID: $($ReplicationJob.JobId)"
        Write-Host "Target VM: {target_vm_name}"
        Write-Host "Source: $($DiscoveredServer.DisplayName)"
    }} catch {{
        Write-Error "Failed to create local server replication: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(local_replication_script)
    except Exception as e:
        raise CLIError(f'Failed to create local server replication: {str(e)}')

def get_local_replication_job(cmd, resource_group_name, project_name, job_id=None, input_object=None, subscription_id=None):
    """
    Azure CLI equivalent to Get-AzMigrateLocalJob.
    Gets the status and details of a local replication job.
    """
    ps_executor = get_powershell_executor()
    
    # Determine which parameter to use
    if input_object:
        param_script = f'$InputObject = {input_object}'
        job_param = '-InputObject $InputObject'
    elif job_id:
        param_script = f'$JobId = "{job_id}"'
        job_param = '-JobId $JobId'
    else:
        raise CLIError('Either job_id or input_object must be provided')
    
    get_job_script = f"""
    # Azure CLI equivalent functionality for Get-AzMigrateLocalJob
    try {{
        {param_script}
        
        # Try different approaches to get the job
        $Job = $null
        
        if ("{job_id}" -ne "None" -and "{job_id}" -ne "") {{
            # Method 1: Try with -ID parameter
            try {{
                $Job = Get-AzMigrateLocalJob -ResourceGroupName "{resource_group_name}" -ProjectName "{project_name}" -ID "{job_id}"
                Write-Host "Found job using -ID parameter"
            }} catch {{
                # Silent catch
            }}
            
            # Method 2: Try with -Name parameter if -ID failed
            if (-not $Job) {{
                try {{
                    $Job = Get-AzMigrateLocalJob -ResourceGroupName "{resource_group_name}" -ProjectName "{project_name}" -Name "{job_id}"
                    Write-Host "Found job using -Name parameter"
                }} catch {{
                    # Silent catch
                }}
            }}
            
            # Method 3: Try listing all jobs and filtering if previous methods failed
            if (-not $Job) {{
                try {{
                    $AllJobs = Get-AzMigrateLocalJob -ResourceGroupName "{resource_group_name}" -ProjectName "{project_name}"
                    
                    if ($AllJobs) {{
                        Write-Host "Found $($AllJobs.Count) total jobs, searching for match..."
                        $Job = $AllJobs | Where-Object {{ $_.Id -like "*{job_id}*" -or $_.Name -like "*{job_id}*" }}
                        
                        if ($Job) {{
                            Write-Host "Found job by filtering all jobs"
                        }} else {{
                            Write-Host "No job found with ID containing: {job_id}"
                            Write-Host "Available jobs:"
                            $AllJobs | ForEach-Object {{ Write-Host "  - $($_.Id) ($($_.Name))" }}
                        }}
                    }} else {{
                        Write-Host "No jobs found in project"
                    }}
                }} catch {{
                    # Silent catch
                }}
            }}
        }} else {{
            # Get all jobs if no specific job ID provided
            Write-Host "Getting all local replication jobs..."
            $Job = Get-AzMigrateLocalJob -ResourceGroupName "{resource_group_name}" -ProjectName "{project_name}"
        }}
        
        if ($Job) {{
            Write-Host "Job found!"
            
            if ($Job -is [array] -and $Job.Count -gt 1) {{
                Write-Host "Found multiple jobs ($($Job.Count))"
                $Job | ForEach-Object {{
                    Write-Host "Job: $($_.Id)"
                    Write-Host "  State: $($_.Property.State)"
                    Write-Host "  Display Name: $($_.Property.DisplayName)"
                    Write-Host ""
                }}
            }} else {{
                if ($Job -is [array]) {{ $Job = $Job[0] }}
                Write-Host "Job ID: $($Job.Id)"
                Write-Host "State: $($Job.Property.State)"
                Write-Host "Start Time: $($Job.Property.StartTime)"
                if ($Job.Property.EndTime) {{
                    Write-Host "End Time: $($Job.Property.EndTime)"
                }}
                Write-Host "Display Name: $($Job.Property.DisplayName)"
            }}
        }} else {{
            throw "Job not found with ID: {job_id}"
        }}
        
    }} catch {{
        Write-Error "Failed to get job details: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(get_job_script)
        
    except Exception as e:
        raise CLIError(f'Failed to get local replication job: {str(e)}')

def list_resource_groups(cmd, subscription_id=None):
    """
    Azure CLI equivalent to Get-AzResourceGroup.
    Lists all resource groups in the current subscription.
    """
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    list_rg_script = f"""
    # Azure CLI equivalent functionality for Get-AzResourceGroup
    try {{
        # Get all resource groups
        $ResourceGroups = Get-AzResourceGroup
        
        Write-Host "Found $($ResourceGroups.Count) resource group(s)"
        $ResourceGroups | Format-Table ResourceGroupName, Location, ProvisioningState -AutoSize
        
        return $ResourceGroups | ForEach-Object {{
            @{{
                'ResourceGroupName' = $_.ResourceGroupName
                'Location' = $_.Location
                'ProvisioningState' = $_.ProvisioningState
                'ResourceId' = $_.ResourceId
            }}
        }}
        
    }} catch {{
        Write-Error "Failed to list resource groups: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        result = ps_executor.execute_script_interactive(list_rg_script)
        return {
            'message': 'Resource groups listed successfully. See detailed results above.',
            'command_executed': 'Get-AzResourceGroup'
        }
        
    except Exception as e:
        raise CLIError(f'Failed to list resource groups: {str(e)}')


def check_powershell_module(cmd, module_name='Az.Migrate', subscription_id=None):
    """
    Azure CLI equivalent of Get-InstalledModule -Name Az.Migrate
    Checks if the required PowerShell module is installed.
    """
    ps_executor = get_powershell_executor()
    
    module_check_script = f"""
    try {{
        Write-Host "🔍 Checking PowerShell module: {module_name}" -ForegroundColor Cyan
        Write-Host "=" * 50 -ForegroundColor Gray
        
        $Module = Get-InstalledModule -Name "{module_name}" -ErrorAction SilentlyContinue
        
        if ($Module) {{
            Write-Host "✅ Module found:" -ForegroundColor Green
            Write-Host "   Name: $($Module.Name)" -ForegroundColor White
            Write-Host "   Version: $($Module.Version)" -ForegroundColor White
            Write-Host "   Author: $($Module.Author)" -ForegroundColor White
            Write-Host "   Description: $($Module.Description)" -ForegroundColor White
            Write-Host ""
            
            return @{{
                'IsInstalled' = $true
                'Name' = $Module.Name
                'Version' = $Module.Version.ToString()
                'Author' = $Module.Author
                'Description' = $Module.Description
            }}
        }} else {{
            Write-Host "❌ Module '{module_name}' is not installed" -ForegroundColor Red
            Write-Host "💡 Install with: Install-Module -Name {module_name} -Force" -ForegroundColor Yellow
            Write-Host ""
            
            return @{{
                'IsInstalled' = $false
                'Name' = '{module_name}'
                'InstallCommand' = 'Install-Module -Name {module_name} -Force'
            }}
        }}
        
    }} catch {{
        Write-Host "❌ Error checking module:" -ForegroundColor Red
        Write-Host "   $($_.Exception.Message)" -ForegroundColor White
        throw
    }}
    """
    
    try:
        result = ps_executor.execute_script_interactive(module_check_script)
        return {
            'message': f'PowerShell module check completed for {module_name}',
            'command_executed': f'Get-InstalledModule -Name {module_name}',
            'module_name': module_name
        }
        
    except Exception as e:
        raise CLIError(f'Failed to check PowerShell module {module_name}: {str(e)}')


def get_local_replication_job(cmd, resource_group_name, project_name, job_id=None, input_object=None, subscription_id=None):
    """
    Azure CLI equivalent to Get-AzMigrateLocalJob.
    Gets the status and details of a local replication job.
    """
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    # Temporarily disabled for testing
    # auth_status = ps_executor.check_azure_authentication()
    # if not auth_status.get('IsAuthenticated', False):
    #     raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    # Determine which parameter to use
    if input_object:
        param_script = f'$InputObject = {input_object}'
        job_param = '-InputObject $InputObject'
    elif job_id:
        param_script = f'$JobId = "{job_id}"'
        job_param = '-JobId $JobId'
    else:
        raise CLIError('Either job_id or input_object must be provided')
    
    get_job_script = f"""
    # Azure CLI equivalent functionality for Get-AzMigrateLocalJob
    try {{
        Write-Host ""
        Write-Host "🔍 Getting Local Replication Job Details..." -ForegroundColor Cyan
        Write-Host "=" * 50 -ForegroundColor Gray
        Write-Host ""
        Write-Host "📋 Configuration:" -ForegroundColor Yellow
        Write-Host "   Resource Group: {resource_group_name}" -ForegroundColor White
        Write-Host "   Project Name: {project_name}" -ForegroundColor White
        Write-Host "   Job ID: {job_id or 'All jobs'}" -ForegroundColor White
        Write-Host ""
        
        # First, let's check what parameters are available for Get-AzMigrateLocalJob
        Write-Host "📋 Checking cmdlet parameters..." -ForegroundColor Yellow
        $cmdletInfo = Get-Command Get-AzMigrateLocalJob -ErrorAction SilentlyContinue
        if ($cmdletInfo) {{
            Write-Host "Available parameters:" -ForegroundColor Cyan
            $cmdletInfo.Parameters.Keys | ForEach-Object {{ Write-Host "   - $_" -ForegroundColor White }}
            Write-Host ""
        }}
        
        {param_script}
        
        # Try different approaches to get the job
        $Job = $null
        
        if ("{job_id}" -ne "None" -and "{job_id}" -ne "") {{
            Write-Host "🔍 Trying to get job with ID: {job_id}" -ForegroundColor Cyan
            
            # Method 1: Try with -ID parameter (capital ID based on cmdlet info)
            try {{
                $Job = Get-AzMigrateLocalJob -ResourceGroupName "{resource_group_name}" -ProjectName "{project_name}" -ID "{job_id}"
                Write-Host "✅ Found job using -ID parameter" -ForegroundColor Green
            }} catch {{
                Write-Host "⚠️ -ID parameter failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }}
            
            # Method 2: Try with -Name parameter if -ID failed
            if (-not $Job) {{
                try {{
                    $Job = Get-AzMigrateLocalJob -ResourceGroupName "{resource_group_name}" -ProjectName "{project_name}" -Name "{job_id}"
                    Write-Host "✅ Found job using -Name parameter" -ForegroundColor Green
                }} catch {{
                    Write-Host "⚠️ -Name parameter failed: $($_.Exception.Message)" -ForegroundColor Yellow
                }}
            }}
            
            # Method 3: Try listing all jobs and filtering if previous methods failed
            if (-not $Job) {{
                try {{
                    Write-Host "🔍 Getting all jobs and filtering..." -ForegroundColor Cyan
                    $AllJobs = Get-AzMigrateLocalJob -ResourceGroupName "{resource_group_name}" -ProjectName "{project_name}"
                    
                    if ($AllJobs) {{
                        Write-Host "Found $($AllJobs.Count) total jobs, searching for match..." -ForegroundColor Cyan
                        $Job = $AllJobs | Where-Object {{ $_.Id -like "*{job_id}*" -or $_.Name -like "*{job_id}*" }}
                        
                        if ($Job) {{
                            Write-Host "✅ Found job by filtering all jobs" -ForegroundColor Green
                        }} else {{
                            Write-Host "⚠️ No job found with ID containing: {job_id}" -ForegroundColor Yellow
                            Write-Host "Available jobs:" -ForegroundColor Cyan
                            $AllJobs | ForEach-Object {{ Write-Host "   - $($_.Id) ($($_.Name))" -ForegroundColor White }}
                        }}
                    }} else {{
                        Write-Host "⚠️ No jobs found in project" -ForegroundColor Yellow
                    }}
                }} catch {{
                    Write-Host "⚠️ Failed to list all jobs: $($_.Exception.Message)" -ForegroundColor Yellow
                }}
            }}
        }} else {{
            # Get all jobs if no specific job ID provided
            Write-Host "🔍 Getting all local replication jobs..." -ForegroundColor Cyan
            $Job = Get-AzMigrateLocalJob -ResourceGroupName "{resource_group_name}" -ProjectName "{project_name}"
        }}
        
        if ($Job) {{
            Write-Host "✅ Job found!" -ForegroundColor Green
            Write-Host ""
            Write-Host "📊 Job Details:" -ForegroundColor Yellow
            
            if ($Job -is [array] -and $Job.Count -gt 1) {{
                Write-Host "   Found multiple jobs ($($Job.Count))" -ForegroundColor White
                $Job | ForEach-Object {{
                    Write-Host "   Job: $($_.Id)" -ForegroundColor White
                    Write-Host "      State: $($_.Property.State)" -ForegroundColor White
                    Write-Host "      Display Name: $($_.Property.DisplayName)" -ForegroundColor White
                    Write-Host ""
                }}
            }} else {{
                if ($Job -is [array]) {{ $Job = $Job[0] }}
                Write-Host "   Job ID: $($Job.Id)" -ForegroundColor White
                Write-Host "   State: $($Job.Property.State)" -ForegroundColor White
                Write-Host "   Start Time: $($Job.Property.StartTime)" -ForegroundColor White
                if ($Job.Property.EndTime) {{
                    Write-Host "   End Time: $($Job.Property.EndTime)" -ForegroundColor White
                }}
                Write-Host "   Display Name: $($Job.Property.DisplayName)" -ForegroundColor White
                Write-Host ""
                Write-Host "🔍 Job State: $($Job.Property.State)" -ForegroundColor Cyan
                Write-Host ""
            }}
            
            return @{{
                'Id' = $Job.Id
                'State' = $Job.Property.State
                'DisplayName' = $Job.Property.DisplayName
                'StartTime' = $Job.Property.StartTime
                'EndTime' = $Job.Property.EndTime
                'ActivityId' = $Job.Property.ActivityId
            }}
        }} else {{
            throw "Job not found with ID: {job_id}"
        }}
        
    }} catch {{
        Write-Host ""
        Write-Host "❌ Failed to get job details:" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor White
        Write-Host ""
        Write-Host "💡 Troubleshooting:" -ForegroundColor Yellow
        Write-Host "   1. Verify the job ID is correct" -ForegroundColor White
        Write-Host "   2. Check if the job exists in the current project" -ForegroundColor White
        Write-Host "   3. Ensure you have access to the job" -ForegroundColor White
        Write-Host ""
        throw
    }}
    """
    
    try:
        result = ps_executor.execute_script_interactive(get_job_script)
        return {
            'message': 'Local replication job details retrieved successfully. See detailed results above.',
            'command_executed': f'Get-AzMigrateLocalJob',
            'parameters': {
                'JobId': job_id,
                'InputObject': input_object is not None
            }
        }
        
    except Exception as e:
        raise CLIError(f'Failed to get local replication job: {str(e)}')


def initialize_local_replication_infrastructure(cmd, resource_group_name, project_name, 
                                               source_appliance_name, target_appliance_name):
    """
    Azure CLI equivalent to Initialize-AzMigrateLocalReplicationInfrastructure.
    Initializes the local replication infrastructure for Azure Stack HCI migrations.
    """
    ps_executor = get_powershell_executor()
    
    initialize_script = f"""
    # Azure CLI equivalent functionality for Initialize-AzMigrateLocalReplicationInfrastructure
    try {{
        # Initialize the local replication infrastructure
        $Result = Initialize-AzMigrateLocalReplicationInfrastructure `
            -ProjectName "{project_name}" `
            -ResourceGroupName "{resource_group_name}" `
            -SourceApplianceName "{source_appliance_name}" `
            -TargetApplianceName "{target_appliance_name}"
        
    }} catch {{
        Write-Host ""
        Write-Host "❌ Failed to initialize local replication infrastructure:" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor White
        Write-Host ""
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(initialize_script)
    except Exception as e:
        raise CLIError(f'Failed to initialize local replication infrastructure: {str(e)}')


def list_resource_groups(cmd, subscription_id=None):
    """
    Azure CLI equivalent to Get-AzResourceGroup.
    Lists all resource groups in the current subscription.
    """
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    list_rg_script = f"""
    # Azure CLI equivalent functionality for Get-AzResourceGroup
    try {{
        Write-Host ""
        Write-Host "📋 Listing Resource Groups..." -ForegroundColor Cyan
        Write-Host "=" * 40 -ForegroundColor Gray
        Write-Host ""
        
        # Get all resource groups
        $ResourceGroups = Get-AzResourceGroup
        
        Write-Host "✅ Found $($ResourceGroups.Count) resource group(s)" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Resource Groups:" -ForegroundColor Yellow
        
        $ResourceGroups | Format-Table ResourceGroupName, Location, ProvisioningState -AutoSize
        
        return $ResourceGroups | ForEach-Object {{
            @{{
                'ResourceGroupName' = $_.ResourceGroupName
                'Location' = $_.Location
                'ProvisioningState' = $_.ProvisioningState
                'ResourceId' = $_.ResourceId
            }}
        }}
        
    }} catch {{
        Write-Host ""
        Write-Host "❌ Failed to list resource groups:" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor White
        Write-Host ""
        throw
    }}
    """
    
    try:
        result = ps_executor.execute_script_interactive(list_rg_script)
        return {
            'message': 'Resource groups listed successfully. See detailed results above.',
            'command_executed': 'Get-AzResourceGroup'
        }
        
    except Exception as e:
        raise CLIError(f'Failed to list resource groups: {str(e)}')


def check_powershell_module(cmd, module_name='Az.Migrate', subscription_id=None):
    """
    Azure CLI equivalent of Get-InstalledModule -Name Az.Migrate
    Checks if the required PowerShell module is installed.
    """
    ps_executor = get_powershell_executor()
    
    module_check_script = f"""
    try {{
        Write-Host "🔍 Checking PowerShell module: {module_name}" -ForegroundColor Cyan
        Write-Host "=" * 50 -ForegroundColor Gray
        
        $Module = Get-InstalledModule -Name "{module_name}" -ErrorAction SilentlyContinue
        
        if ($Module) {{
            Write-Host "✅ Module found:" -ForegroundColor Green
            Write-Host "   Name: $($Module.Name)" -ForegroundColor White
            Write-Host "   Version: $($Module.Version)" -ForegroundColor White
            Write-Host "   Author: $($Module.Author)" -ForegroundColor White
            Write-Host "   Description: $($Module.Description)" -ForegroundColor White
            Write-Host ""
            
            return @{{
                'IsInstalled' = $true
                'Name' = $Module.Name
                'Version' = $Module.Version.ToString()
                'Author' = $Module.Author
                'Description' = $Module.Description
            }}
        }} else {{
            Write-Host "❌ Module '{module_name}' is not installed" -ForegroundColor Red
            Write-Host "💡 Install with: Install-Module -Name {module_name} -Force" -ForegroundColor Yellow
            Write-Host ""
            
            return @{{
                'IsInstalled' = $false
                'Name' = '{module_name}'
                'InstallCommand' = 'Install-Module -Name {module_name} -Force'
            }}
        }}
        
    }} catch {{
        Write-Host "❌ Error checking module:" -ForegroundColor Red
        Write-Host "   $($_.Exception.Message)" -ForegroundColor White
        throw
    }}
    """
    
    try:
        result = ps_executor.execute_script_interactive(module_check_script)
        return {
            'message': f'PowerShell module check completed for {module_name}',
            'command_executed': f'Get-InstalledModule -Name {module_name}',
            'module_name': module_name
        }
        
    except Exception as e:
        raise CLIError(f'Failed to check PowerShell module {module_name}: {str(e)}')
