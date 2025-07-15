# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import platform
from knack.util import CLIError
from knack.log import get_logger
from azure.cli.command_modules.migrate._powershell_utils import get_powershell_executor

logger = get_logger(__name__)


def check_migration_prerequisites(cmd):
    """Check if the system meets migration prerequisites."""
    ps_executor = get_powershell_executor()
    
    try:
        prereqs = ps_executor.check_migration_prerequisites()
        
        # Display prerequisite information
        logger.info(f"PowerShell Version: {prereqs.get('PowerShellVersion', 'Unknown')}")
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
    import platform
    import subprocess
    import sys
    from knack.util import CLIError
    from knack.log import get_logger
    
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
        # Check Python version
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
        
        # Check PowerShell availability
        powershell_check = _check_powershell_availability(system)
        setup_results['checks'].append(powershell_check)
        
        if powershell_check['status'] == 'failed' and install_powershell and not check_only:
            # Attempt to install PowerShell
            install_result = _install_powershell(system, logger)
            setup_results['actions_taken'].append(install_result)
            
            # Re-check after installation attempt
            powershell_recheck = _check_powershell_availability(system)
            setup_results['checks'].append({
                'component': 'PowerShell (after installation)',
                'status': powershell_recheck['status'],
                'version': powershell_recheck.get('version', 'Unknown'),
                'message': powershell_recheck['message']
            })
        
        # Check for specific tools based on platform
        if system == 'windows':
            setup_results['checks'].extend(_check_windows_tools())
        elif system == 'linux':
            setup_results['checks'].extend(_check_linux_tools())
        elif system == 'darwin':
            setup_results['checks'].extend(_check_macos_tools())
        
        # Add platform-specific recommendations
        setup_results['recommendations'] = _get_platform_recommendations(system, setup_results['checks'])
        
        # Determine overall status
        failed_checks = [c for c in setup_results['checks'] if c['status'] == 'failed']
        if failed_checks:
            setup_results['status'] = 'failed' if any(c['component'] == 'PowerShell' for c in failed_checks) else 'warning'
        
        return setup_results
        
    except Exception as e:
        raise CLIError(f'Failed to setup migration environment: {str(e)}')


def _check_powershell_availability(system):
    """Check if PowerShell is available on the system."""
    from ._powershell_utils import PowerShellExecutor
    import subprocess
    
    # Try to use our PowerShell executor's check method
    try:
        executor = PowerShellExecutor()
        is_available, command = executor.check_powershell_available()
        
        if is_available:
            # Get version information
            try:
                if command == 'pwsh':
                    result = subprocess.run([command, '--version'], capture_output=True, text=True, timeout=10)
                else:
                    result = subprocess.run([command, '-Command', '$PSVersionTable.PSVersion.ToString()'], 
                                          capture_output=True, text=True, timeout=10)
                
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
        # Fallback to original logic if needed
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
    import subprocess
    
    install_result = {
        'component': 'PowerShell Installation',
        'status': 'attempted',
        'message': '',
        'commands': []
    }
    
    try:
        if system == 'windows':
            # Windows - try winget first, then provide manual instructions
            try:
                result = subprocess.run(['winget', 'install', 'Microsoft.PowerShell'], 
                                      capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    install_result['status'] = 'success'
                    install_result['message'] = 'PowerShell Core installed via winget'
                    install_result['commands'].append('winget install Microsoft.PowerShell')
                else:
                    install_result['status'] = 'failed'
                    install_result['message'] = 'winget installation failed. Please install manually from https://github.com/PowerShell/PowerShell'
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                install_result['status'] = 'failed'
                install_result['message'] = 'winget not available. Please install PowerShell Core manually from https://github.com/PowerShell/PowerShell'
        
        elif system == 'linux':
            # Linux - provide distribution-specific instructions
            install_result['status'] = 'manual_required'
            install_result['message'] = 'Please install PowerShell Core using your distribution package manager'
            install_result['commands'] = [
                '# Ubuntu/Debian: sudo apt update && sudo apt install -y powershell',
                '# CentOS/RHEL: sudo yum install -y powershell',
                '# Or download from: https://github.com/PowerShell/PowerShell'
            ]
        
        elif system == 'darwin':
            # macOS - try Homebrew
            try:
                result = subprocess.run(['brew', 'install', 'powershell'], 
                                      capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    install_result['status'] = 'success'
                    install_result['message'] = 'PowerShell Core installed via Homebrew'
                    install_result['commands'].append('brew install powershell')
                else:
                    install_result['status'] = 'failed'
                    install_result['message'] = 'Homebrew installation failed'
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
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
    import subprocess
    
    checks = []
    
    # Check for Windows PowerShell modules
    powershell_modules = [
        'Hyper-V',
        'SqlServer',
        'WindowsFeature',
        'Storage'
    ]
    
    for module in powershell_modules:
        try:
            result = subprocess.run([
                'powershell', '-Command', 
                f'Get-Module -ListAvailable -Name {module} | Select-Object -First 1'
            ], capture_output=True, text=True, timeout=30)
            
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
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            checks.append({
                'component': f'PowerShell Module: {module}',
                'status': 'warning',
                'message': f'Could not check {module} module availability'
            })
    
    return checks


def _check_linux_tools():
    """Check for Linux-specific tools that might be useful for migration."""
    import subprocess
    
    checks = []
    
    # Check for common tools
    tools = [
        ('curl', 'Data transfer tool'),
        ('wget', 'File download tool'),
        ('rsync', 'File synchronization tool'),
        ('ssh', 'Secure shell client')
    ]
    
    for tool, description in tools:
        try:
            result = subprocess.run(['which', tool], capture_output=True, text=True, timeout=5)
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
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            checks.append({
                'component': f'Tool: {tool}',
                'status': 'warning',
                'message': f'Could not check {tool} availability'
            })
    
    return checks


def _check_macos_tools():
    """Check for macOS-specific tools."""
    import subprocess
    
    checks = []
    
    # Check for Homebrew
    try:
        result = subprocess.run(['brew', '--version'], capture_output=True, text=True, timeout=5)
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
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        checks.append({
            'component': 'Homebrew',
            'status': 'warning',
            'message': 'Homebrew not installed. Consider installing from https://brew.sh'
        })
    
    return checks


def _get_platform_recommendations(system, checks):
    """Get platform-specific recommendations based on check results."""
    recommendations = []
    
    # Check if PowerShell is missing
    powershell_checks = [c for c in checks if 'PowerShell' in c['component']]
    if any(c['status'] == 'failed' for c in powershell_checks):
        if system == 'windows':
            recommendations.append("Install PowerShell Core from https://github.com/PowerShell/PowerShell or use 'winget install Microsoft.PowerShell'")
        elif system == 'linux':
            recommendations.append("Install PowerShell Core using your package manager or from https://github.com/PowerShell/PowerShell")
        elif system == 'darwin':
            recommendations.append("Install PowerShell Core using 'brew install powershell' or from https://github.com/PowerShell/PowerShell")
    
    # Platform-specific recommendations
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


# Azure CLI equivalents to PowerShell Az.Migrate commands

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
                Write-Host ""
                Write-Host "Discovered Servers in Project: $ProjectName (Source Type: $SourceMachineType)" -ForegroundColor Green
                Write-Host "=" * 80 -ForegroundColor Gray
                
                # Create table output similar to PowerShell Format-Table
                $DiscoveredServers | Format-Table -Property DisplayName, Name, Type -AutoSize | Out-String
                
                Write-Host ""
                Write-Host "Total discovered servers: $($DiscoveredServers.Count)" -ForegroundColor Cyan
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
                Write-Host ""
                Write-Host "No discovered servers found in project: $ProjectName (Source Type: $SourceMachineType)" -ForegroundColor Yellow
                Write-Host ""
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
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    # This script exactly matches your PowerShell commands
    powershell_script = f"""
    # Exact equivalent of the provided PowerShell commands
    $ProjectName = '{project_name}'
    $ResourceGroupName = '{resource_group_name}'
    $SourceMachineType = '{source_machine_type}'
    
    try {{
        Write-Host ""
        Write-Host "Executing: Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceMachineType $SourceMachineType" -ForegroundColor Cyan
        Write-Host ""
        
        # Your exact PowerShell commands:
        $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceMachineType $SourceMachineType
        Write-Output $DiscoveredServers | Format-Table DisplayName,Name,Type
        
        Write-Host ""
        Write-Host "Total discovered servers: $($DiscoveredServers.Count)" -ForegroundColor Green
        Write-Host ""
        
    }} catch {{
        Write-Error "Failed to execute PowerShell commands: $($_.Exception.Message)"
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "1. Ensure you are authenticated to Azure: az migrate auth login" -ForegroundColor Yellow
        Write-Host "2. Verify the project exists: az migrate project create --resource-group $ResourceGroupName --project-name $ProjectName" -ForegroundColor Yellow
        Write-Host "3. Check if Az.Migrate module is installed: az migrate powershell get-module" -ForegroundColor Yellow
        Write-Host ""
        throw
    }}
    """
    
    try:
        # Use interactive execution to show real-time PowerShell output
        result = ps_executor.execute_script_interactive(powershell_script)
        return {
            'message': 'PowerShell commands executed successfully. Output displayed above.',
            'commands_executed': [
                f'$DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName {project_name} -ResourceGroupName {resource_group_name} -SourceMachineType {source_machine_type}',
                'Write-Output $DiscoveredServers | Format-Table DisplayName,Name,Type'
            ],
            'parameters': {
                'ProjectName': project_name,
                'ResourceGroupName': resource_group_name,
                'SourceMachineType': source_machine_type
            }
        }
        
    except Exception as e:
        raise CLIError(f'Failed to execute PowerShell commands: {str(e)}')


def initialize_replication_infrastructure(cmd, resource_group_name, project_name, source_appliance_name, target_appliance_name, subscription_id=None):
    """
    Azure CLI equivalent to Initialize-AzMigrateLocalReplicationInfrastructure PowerShell cmdlet.
    Initializes the replication infrastructure for Azure Migrate server migration.
    """
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    # PowerShell script that executes the real cmdlet
    infrastructure_script = f"""
    # Azure CLI equivalent functionality for Initialize-AzMigrateLocalReplicationInfrastructure
    $ProjectName = '{project_name}'
    $ResourceGroupName = '{resource_group_name}'
    $SourceApplianceName = '{source_appliance_name}'
    $TargetApplianceName = '{target_appliance_name}'
    
    try {{
        Write-Host ""
        Write-Host "Executing: Initialize-AzMigrateLocalReplicationInfrastructure -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceApplianceName $SourceApplianceName -TargetApplianceName $TargetApplianceName" -ForegroundColor Cyan
        Write-Host ""
        
        # Execute the real PowerShell cmdlet
        $InfrastructureResult = Initialize-AzMigrateLocalReplicationInfrastructure `
            -ProjectName $ProjectName `
            -ResourceGroupName $ResourceGroupName `
            -SourceApplianceName $SourceApplianceName `
            -TargetApplianceName $TargetApplianceName
        
        Write-Host ""
        Write-Host "Replication infrastructure initialization completed successfully!" -ForegroundColor Green
        Write-Host ""
        
        # Display results
        if ($InfrastructureResult) {{
            Write-Host "Infrastructure Details:" -ForegroundColor Yellow
            $InfrastructureResult | Format-List
            
            # Return JSON for programmatic use
            $result = @{{
                'Status' = 'Success'
                'ProjectName' = $ProjectName
                'ResourceGroupName' = $ResourceGroupName
                'SourceApplianceName' = $SourceApplianceName
                'TargetApplianceName' = $TargetApplianceName
                'InfrastructureDetails' = $InfrastructureResult
                'Message' = 'Replication infrastructure initialized successfully'
            }}
            $result | ConvertTo-Json -Depth 5
        }} else {{
            Write-Host "Infrastructure initialization completed but no detailed results returned." -ForegroundColor Yellow
            @{{
                'Status' = 'Completed'
                'ProjectName' = $ProjectName
                'ResourceGroupName' = $ResourceGroupName
                'SourceApplianceName' = $SourceApplianceName
                'TargetApplianceName' = $TargetApplianceName
                'Message' = 'Infrastructure initialization completed'
            }} | ConvertTo-Json
        }}
        
    }} catch {{
        Write-Error "Failed to initialize replication infrastructure: $($_.Exception.Message)"
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "1. Ensure you are authenticated to Azure with proper permissions" -ForegroundColor Yellow
        Write-Host "2. Verify the Azure Migrate project exists and is accessible" -ForegroundColor Yellow
        Write-Host "3. Check that the source and target appliances are properly configured" -ForegroundColor Yellow
        Write-Host "4. Ensure Azure Migrate: Server Migration solution is enabled" -ForegroundColor Yellow
        Write-Host "5. Verify network connectivity between appliances" -ForegroundColor Yellow
        Write-Host ""
        
        $errorResult = @{{
            'Status' = 'Failed'
            'Error' = $_.Exception.Message
            'ProjectName' = $ProjectName
            'ResourceGroupName' = $ResourceGroupName
            'SourceApplianceName' = $SourceApplianceName
            'TargetApplianceName' = $TargetApplianceName
            'TroubleshootingSteps' = @(
                'Verify Azure authentication and permissions',
                'Check Azure Migrate project accessibility',
                'Confirm appliance names and configuration',
                'Ensure Server Migration solution is enabled',
                'Test network connectivity between appliances',
                'Review Azure Migrate documentation for infrastructure requirements'
            )
        }}
        $errorResult | ConvertTo-Json -Depth 3
        throw
    }}
    """
    
    try:
        # Use interactive execution to show real-time PowerShell output
        result = ps_executor.execute_script_interactive(infrastructure_script)
        return {
            'message': 'PowerShell command executed successfully. Output displayed above.',
            'command_executed': f'Initialize-AzMigrateLocalReplicationInfrastructure -ProjectName {project_name} -ResourceGroupName {resource_group_name} -SourceApplianceName {source_appliance_name} -TargetApplianceName {target_appliance_name}',
            'parameters': {
                'ProjectName': project_name,
                'ResourceGroupName': resource_group_name,
                'SourceApplianceName': source_appliance_name,
                'TargetApplianceName': target_appliance_name
            }
        }
        
    except Exception as e:
        raise CLIError(f'Failed to initialize replication infrastructure: {str(e)}')


def initialize_replication_infrastructure(cmd, resource_group_name, project_name, 
                                         target_region, subscription_id=None):
    """Initialize Azure Migrate replication infrastructure."""
    
    # Get PowerShell executor
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    # Build the PowerShell script
    init_script = f"""
    # Initialize Azure Migrate replication infrastructure
    try {{
        Write-Host ""
        Write-Host "🚀 Initializing Azure Migrate Replication Infrastructure..." -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Gray
        Write-Host ""
        Write-Host "📋 Configuration:" -ForegroundColor Yellow
        Write-Host "   Resource Group: {resource_group_name}" -ForegroundColor White
        Write-Host "   Project Name: {project_name}" -ForegroundColor White
        Write-Host "   Target Region: {target_region}" -ForegroundColor White
        Write-Host ""
        
        # Get current subscription context
        $Context = Get-AzContext
        if (-not $Context) {{
            throw "No Azure context found. Please authenticate first."
        }}
        
        Write-Host "   Subscription: $($Context.Subscription.Name)" -ForegroundColor White
        Write-Host "   Account: $($Context.Account.Id)" -ForegroundColor White
        Write-Host ""
        
        Write-Host "⏳ Starting infrastructure initialization..." -ForegroundColor Cyan
        Write-Host ""
        
        # Initialize the replication infrastructure
        $InitResult = Initialize-AzMigrateReplicationInfrastructure `
            -ResourceGroupName "{resource_group_name}" `
            -ProjectName "{project_name}" `
            -Scenario "agentlessVMware" `
            -TargetRegion "{target_region}"
        
        Write-Host ""
        Write-Host "✅ Replication infrastructure initialization completed!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Initialization Results:" -ForegroundColor Yellow
        if ($InitResult) {{
            $InitResult | Format-List
        }}
        Write-Host ""
        Write-Host "💡 Next Steps:" -ForegroundColor Cyan
        Write-Host "   1. You can now create server replications" -ForegroundColor White
        Write-Host "   2. Use: az migrate server create-replication" -ForegroundColor White
        Write-Host "   3. Monitor replication jobs with: az migrate server get-replication-status" -ForegroundColor White
        Write-Host ""
        
        return @{{
            Status = "Success"
            ResourceGroupName = "{resource_group_name}"
            ProjectName = "{project_name}"
            TargetRegion = "{target_region}"
            Message = "Replication infrastructure initialized successfully"
            InitializationResult = $InitResult
        }}
        
    }} catch {{
        Write-Host ""
        Write-Host "❌ Failed to initialize replication infrastructure:" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor White
        Write-Host ""
        Write-Host "🔧 Troubleshooting Steps:" -ForegroundColor Yellow
        Write-Host "   1. Verify you have sufficient permissions on the subscription" -ForegroundColor White
        Write-Host "   2. Check that the Azure Migrate project exists" -ForegroundColor White
        Write-Host "   3. Ensure the target region is valid and available" -ForegroundColor White
        Write-Host "   4. Verify Azure Migrate service is available in your region" -ForegroundColor White
        Write-Host "   5. Check Azure resource quotas in the target region" -ForegroundColor White
        Write-Host ""
        
        @{{
            Status = "Failed"
            Error = $_.Exception.Message
            ResourceGroupName = "{resource_group_name}"
            ProjectName = "{project_name}"
            TargetRegion = "{target_region}"
            Message = "Failed to initialize replication infrastructure"
            TroubleshootingSteps = @(
                "Verify sufficient permissions on subscription",
                "Check Azure Migrate project exists",
                "Ensure target region is valid",
                "Verify Azure Migrate service availability",
                "Check Azure resource quotas"
            )
        }} | ConvertTo-Json -Depth 3
        throw
    }}
    """
    
    try:
        # Use interactive execution to show real-time PowerShell output
        result = ps_executor.execute_script_interactive(init_script)
        return {
            'message': 'Infrastructure initialization completed. See detailed results above.',
            'command_executed': f'Initialize-AzMigrateReplicationInfrastructure for project: {project_name}',
            'parameters': {
                'ResourceGroupName': resource_group_name,
                'ProjectName': project_name,
                'TargetRegion': target_region,
                'Scenario': 'agentlessVMware'
            },
            'next_steps': [
                'Create server replications using: az migrate server create-replication',
                'Monitor replication status using: az migrate server get-replication-status'
            ]
        }
        
    except Exception as e:
        raise CLIError(f'Failed to initialize replication infrastructure: {str(e)}')


def check_replication_infrastructure(cmd, resource_group_name, project_name, subscription_id=None):
    """Check the status of Azure Migrate replication infrastructure."""
    
    # Get PowerShell executor
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    # Build the PowerShell script
    check_script = f"""
    # Check Azure Migrate replication infrastructure status
    try {{
        Write-Host ""
        Write-Host "🔍 Checking Azure Migrate Replication Infrastructure Status..." -ForegroundColor Cyan
        Write-Host "=" * 65 -ForegroundColor Gray
        Write-Host ""
        Write-Host "📋 Configuration:" -ForegroundColor Yellow
        Write-Host "   Resource Group: {resource_group_name}" -ForegroundColor White
        Write-Host "   Project Name: {project_name}" -ForegroundColor White
        Write-Host ""
        
        # Get current subscription context
        $Context = Get-AzContext
        Write-Host "   Subscription: $($Context.Subscription.Name)" -ForegroundColor White
        Write-Host "   Account: $($Context.Account.Id)" -ForegroundColor White
        Write-Host ""
        
        Write-Host "⏳ Checking infrastructure components..." -ForegroundColor Cyan
        Write-Host ""
        
        # Check if the Azure Migrate project exists
        Write-Host "1. Checking Azure Migrate Project..." -ForegroundColor Yellow
        try {{
            $Project = Get-AzResource -ResourceGroupName "{resource_group_name}" -ResourceType "Microsoft.Migrate/MigrateProjects" -Name "{project_name}" -ErrorAction SilentlyContinue
            if ($Project) {{
                Write-Host "   ✅ Azure Migrate Project found" -ForegroundColor Green
                Write-Host "      Name: $($Project.Name)" -ForegroundColor White
                Write-Host "      Location: $($Project.Location)" -ForegroundColor White
            }} else {{
                Write-Host "   ❌ Azure Migrate Project not found" -ForegroundColor Red
            }}
        }} catch {{
            Write-Host "   ⚠️  Could not check project: $($_.Exception.Message)" -ForegroundColor Yellow
        }}
        Write-Host ""
        
        # Check for replication infrastructure resources
        Write-Host "2. Checking Replication Infrastructure Resources..." -ForegroundColor Yellow
        
        # Check for Recovery Services Vaults
        try {{
            $Vaults = Get-AzResource -ResourceGroupName "{resource_group_name}" -ResourceType "Microsoft.RecoveryServices/vaults" -ErrorAction SilentlyContinue
            if ($Vaults) {{
                Write-Host "   ✅ Recovery Services Vault(s) found: $($Vaults.Count)" -ForegroundColor Green
                $Vaults | ForEach-Object {{
                    Write-Host "      - $($_.Name) (Location: $($_.Location))" -ForegroundColor White
                }}
            }} else {{
                Write-Host "   ⚠️  No Recovery Services Vaults found" -ForegroundColor Yellow
            }}
        }} catch {{
            Write-Host "   ⚠️  Could not check Recovery Services Vaults: $($_.Exception.Message)" -ForegroundColor Yellow
        }}
        Write-Host ""
        
        # Check for Storage Accounts (used for replication)
        try {{
            $StorageAccounts = Get-AzStorageAccount -ResourceGroupName "{resource_group_name}" -ErrorAction SilentlyContinue
            if ($StorageAccounts) {{
                Write-Host "   ✅ Storage Account(s) found: $($StorageAccounts.Count)" -ForegroundColor Green
                $StorageAccounts | ForEach-Object {{
                    Write-Host "      - $($_.StorageAccountName) (SKU: $($_.Sku.Name))" -ForegroundColor White
                }}
            }} else {{
                Write-Host "   ⚠️  No Storage Accounts found" -ForegroundColor Yellow
            }}
        }} catch {{
            Write-Host "   ⚠️  Could not check Storage Accounts: $($_.Exception.Message)" -ForegroundColor Yellow
        }}
        Write-Host ""
        
        # Check for Site Recovery resources
        Write-Host "3. Checking Site Recovery Resources..." -ForegroundColor Yellow
        try {{
            $SiteRecoveryResources = Get-AzResource -ResourceGroupName "{resource_group_name}" -ResourceType "Microsoft.RecoveryServices/*" -ErrorAction SilentlyContinue
            if ($SiteRecoveryResources) {{
                Write-Host "   ✅ Site Recovery resources found: $($SiteRecoveryResources.Count)" -ForegroundColor Green
                $SiteRecoveryResources | ForEach-Object {{
                    Write-Host "      - $($_.Name) (Type: $($_.ResourceType))" -ForegroundColor White
                }}
            }} else {{
                Write-Host "   ⚠️  No Site Recovery resources found" -ForegroundColor Yellow
            }}
        }} catch {{
            Write-Host "   ⚠️  Could not check Site Recovery resources: $($_.Exception.Message)" -ForegroundColor Yellow
        }}
        Write-Host ""
        
        # Try to get existing server replications to test if infrastructure is working
        Write-Host "4. Testing Replication Infrastructure..." -ForegroundColor Yellow
        try {{
            $Replications = Get-AzMigrateServerReplication -ProjectName "{project_name}" -ResourceGroupName "{resource_group_name}" -ErrorAction SilentlyContinue
            Write-Host "   ✅ Replication infrastructure is accessible" -ForegroundColor Green
            if ($Replications) {{
                Write-Host "      Existing replications found: $($Replications.Count)" -ForegroundColor White
            }} else {{
                Write-Host "      No existing replications (this is normal for new projects)" -ForegroundColor White
            }}
        }} catch {{
            if ($_.Exception.Message -like "*not initialized*") {{
                Write-Host "   ❌ Replication infrastructure is NOT initialized" -ForegroundColor Red
                Write-Host "      This is the cause of your error!" -ForegroundColor Red
            }} else {{
                Write-Host "   ⚠️  Could not test replication infrastructure: $($_.Exception.Message)" -ForegroundColor Yellow
            }}
        }}
        Write-Host ""
        
        # Provide recommendations
        Write-Host "🔧 Recommendations:" -ForegroundColor Cyan
        Write-Host "   If infrastructure is not initialized, run:" -ForegroundColor White
        Write-Host "   az migrate infrastructure init --resource-group {resource_group_name} --project-name {project_name} --target-region <region>" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   Common target regions: eastus, westus2, centralus, westeurope, eastasia" -ForegroundColor White
        Write-Host ""
        
        return @{{
            Status = "Check completed"
            ResourceGroupName = "{resource_group_name}"
            ProjectName = "{project_name}"
            Message = "Infrastructure status check completed"
        }}
        
    }} catch {{
        Write-Host ""
        Write-Host "❌ Failed to check replication infrastructure:" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor White
        Write-Host ""
        
        @{{
            Status = "Failed"
            Error = $_.Exception.Message
            ResourceGroupName = "{resource_group_name}"
            ProjectName = "{project_name}"
            Message = "Failed to check replication infrastructure"
        }} | ConvertTo-Json -Depth 3
        throw
    }}
    """
    
    try:
        # Use interactive execution to show real-time PowerShell output
        result = ps_executor.execute_script_interactive(check_script)
        return {
            'message': 'Infrastructure status check completed. See detailed results above.',
            'command_executed': f'Infrastructure status check for project: {project_name}',
            'parameters': {
                'ResourceGroupName': resource_group_name,
                'ProjectName': project_name
            }
        }
        
    except Exception as e:
        raise CLIError(f'Failed to check replication infrastructure: {str(e)}')

def connect_azure_account(cmd, subscription_id=None, tenant_id=None, device_code=False, app_id=None, secret=None):
    """
    Connect to Azure account using PowerShell Connect-AzAccount with enhanced visibility.
    Azure CLI equivalent to Connect-AzAccount PowerShell cmdlet.
    """
    ps_executor = get_powershell_executor()
    
    # Build PowerShell connection script with rich visual feedback
    connect_script = """
    try {
        Write-Host ""
        Write-Host "🔗 Connecting to Azure using PowerShell..." -ForegroundColor Cyan
        Write-Host "=" * 50 -ForegroundColor Gray
        Write-Host ""
        
        # Connection parameters
        $connectParams = @{}
        """
    
    if subscription_id:
        connect_script += f"""
        $connectParams['Subscription'] = '{subscription_id}'
        Write-Host "📋 Target Subscription: {subscription_id}" -ForegroundColor Yellow
        """
    
    if tenant_id:
        connect_script += f"""
        $connectParams['Tenant'] = '{tenant_id}'
        Write-Host "🏢 Target Tenant: {tenant_id}" -ForegroundColor Yellow
        """
    
    if device_code:
        connect_script += """
        $connectParams['UseDeviceAuthentication'] = $true
        Write-Host "📱 Using Device Code Authentication" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "⚠️  You will be prompted to:" -ForegroundColor Magenta
        Write-Host "   1. Copy the device code" -ForegroundColor White
        Write-Host "   2. Open https://microsoft.com/devicelogin" -ForegroundColor White
        Write-Host "   3. Enter the code and complete authentication" -ForegroundColor White
        Write-Host ""
        """
    
    if app_id and secret:
        connect_script += f"""
        $securePassword = ConvertTo-SecureString '{secret}' -AsPlainText -Force
        $credential = New-Object System.Management.Automation.PSCredential('{app_id}', $securePassword)
        $connectParams['ServicePrincipal'] = $true
        $connectParams['Credential'] = $credential
        Write-Host "🤖 Using Service Principal Authentication" -ForegroundColor Yellow
        Write-Host "   Application ID: {app_id}" -ForegroundColor White
        """
    
    connect_script += """
        Write-Host ""
        Write-Host "⏳ Initiating Azure connection..." -ForegroundColor Cyan
        Write-Host ""
        
        # Connect to Azure
        $context = Connect-AzAccount @connectParams
        
        if ($context) {
            Write-Host ""
            Write-Host "✅ Successfully connected to Azure!" -ForegroundColor Green
            Write-Host ""
            Write-Host "🔐 Account Details:" -ForegroundColor Yellow
            Write-Host "   Account ID: $($context.Context.Account.Id)" -ForegroundColor White
            Write-Host "   Account Type: $($context.Context.Account.Type)" -ForegroundColor White
            Write-Host "   Subscription: $($context.Context.Subscription.Name)" -ForegroundColor White
            Write-Host "   Subscription ID: $($context.Context.Subscription.Id)" -ForegroundColor White
            Write-Host "   Tenant ID: $($context.Context.Tenant.Id)" -ForegroundColor White
            Write-Host "   Environment: $($context.Context.Environment.Name)" -ForegroundColor White
            Write-Host ""
            
            $result = @{
                'Status' = 'Success'
                'AccountId' = $context.Context.Account.Id
                'AccountType' = $context.Context.Account.Type
                'SubscriptionId' = $context.Context.Subscription.Id
                'SubscriptionName' = $context.Context.Subscription.Name
                'TenantId' = $context.Context.Tenant.Id
                'Environment' = $context.Context.Environment.Name
                'AvailableSubscriptions' = @($allSubscriptions | ForEach-Object { 
                    @{
                        'Name' = $_.Name
                        'Id' = $_.Id
                        'IsCurrent' = ($_.Id -eq $context.Context.Subscription.Id)
                    }
                })
                'Message' = 'Successfully connected to Azure'
            }
            $result | ConvertTo-Json -Depth 4
        } else {
            Write-Host ""
            Write-Host "❌ Failed to connect to Azure" -ForegroundColor Red
            Write-Host "   Connection attempt returned null context" -ForegroundColor White
            Write-Host ""
            
            @{
                'Status' = 'Failed'
                'Error' = 'Connection attempt returned null context'
                'Message' = 'Failed to connect to Azure'
            } | ConvertTo-Json
        }
    } catch {
        Write-Host ""
        Write-Host "❌ Failed to connect to Azure: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "🔧 Troubleshooting Steps:" -ForegroundColor Yellow
        Write-Host "   1. Ensure Azure PowerShell modules are installed:" -ForegroundColor White
        Write-Host "      Install-Module -Name Az" -ForegroundColor Cyan
        Write-Host "   2. Try using device code authentication:" -ForegroundColor White
        Write-Host "      az migrate auth login --use-device-code" -ForegroundColor Cyan
        Write-Host "   3. Check network connectivity and firewall settings" -ForegroundColor White
        Write-Host "   4. Verify your credentials are correct" -ForegroundColor White
        Write-Host ""
        
        @{
            'Status' = 'Failed'
            'Error' = $_.Exception.Message
            'Message' = 'Failed to connect to Azure'
            'TroubleshootingSteps' = @(
                'Install Azure PowerShell modules: Install-Module -Name Az',
                'Try device code authentication: az migrate auth login --use-device-code',
                'Check network connectivity and firewall settings',
                'Verify your credentials are correct'
            )
        } | ConvertTo-Json -Depth 3
        throw
    }
    """
    
    try:
        # Use interactive execution to show real-time authentication progress with full visibility
        result = ps_executor.execute_script_interactive(connect_script)
        return {
            'message': 'Azure connection attempt completed. See detailed results above.',
            'command_executed': 'Connect-AzAccount with specified parameters',
            'help': 'Authentication status and account details are displayed above'
        }
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
        Write-Host ""
        Write-Host "🔌 Disconnecting from Azure..." -ForegroundColor Cyan
        Write-Host "=" * 40 -ForegroundColor Gray
        Write-Host ""
        
        # Check if currently connected
        $currentContext = Get-AzContext -ErrorAction SilentlyContinue
        if (-not $currentContext) {
            Write-Host "ℹ️  Not currently connected to Azure" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "💡 To connect, use: az migrate auth login" -ForegroundColor Cyan
            Write-Host ""
            
            @{
                'Status' = 'NotConnected'
                'IsAuthenticated' = $false
                'Message' = 'Not currently connected to Azure'
                'NextSteps' = @('Connect to Azure: az migrate auth login')
            } | ConvertTo-Json -Depth 3
            return
        }
        
        Write-Host "📋 Current Azure context to be disconnected:" -ForegroundColor Yellow
        Write-Host "   Account: $($currentContext.Account.Id)" -ForegroundColor White
        Write-Host "   Subscription: $($currentContext.Subscription.Name)" -ForegroundColor White
        Write-Host "   Tenant: $($currentContext.Tenant.Id)" -ForegroundColor White
        Write-Host ""
        
        Write-Host "⏳ Disconnecting from Azure..." -ForegroundColor Cyan
        
        # Store context info before disconnecting
        $previousAccountId = $currentContext.Account.Id
        $previousSubscriptionId = $currentContext.Subscription.Id
        $previousSubscriptionName = $currentContext.Subscription.Name
        $previousTenantId = $currentContext.Tenant.Id
        
        # Disconnect from Azure
        Disconnect-AzAccount -Confirm:$false
        
        Write-Host ""
        Write-Host "✅ Successfully disconnected from Azure" -ForegroundColor Green
        Write-Host ""
        Write-Host "🔐 Previous session details:" -ForegroundColor Yellow
        Write-Host "   Account: $previousAccountId" -ForegroundColor White
        Write-Host "   Subscription: $previousSubscriptionName ($previousSubscriptionId)" -ForegroundColor White
        Write-Host "   Tenant: $previousTenantId" -ForegroundColor White
        Write-Host ""
        Write-Host "💡 To reconnect, use: az migrate auth login" -ForegroundColor Cyan
        Write-Host ""
        
        @{
            'Status' = 'Success'
            'IsAuthenticated' = $false
            'PreviousAccountId' = $previousAccountId
            'PreviousSubscriptionId' = $previousSubscriptionId
            'PreviousSubscriptionName' = $previousSubscriptionName
            'PreviousTenantId' = $previousTenantId
            'Message' = 'Successfully disconnected from Azure'
            'NextSteps' = @('To reconnect: az migrate auth login')
        } | ConvertTo-Json -Depth 3
        
    } catch {
        Write-Host ""
        Write-Host "❌ Failed to disconnect from Azure: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
        Write-Host "   1. Check if you have an active PowerShell session" -ForegroundColor White
        Write-Host "   2. Verify Azure PowerShell modules are properly loaded" -ForegroundColor White
        Write-Host "   3. Try clearing PowerShell session and reconnecting" -ForegroundColor White
        Write-Host ""
        
        @{
            'Status' = 'Failed'
            'Error' = $_.Exception.Message
            'Message' = 'Failed to disconnect from Azure'
            'TroubleshootingSteps' = @(
                'Check active PowerShell session',
                'Verify Azure PowerShell modules are loaded',
                'Try clearing PowerShell session and reconnecting'
            )
        } | ConvertTo-Json -Depth 3
        throw
    }
    """
    
    try:
        # Use interactive execution to show real-time disconnect progress with full visibility
        ps_executor.execute_script_interactive(disconnect_script)
        return {
            'message': 'Azure disconnection completed. See detailed results above.',
            'command_executed': 'Disconnect-AzAccount',
            'help': 'Use "az migrate auth login" to reconnect to Azure'
        }
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
        Write-Host ""
        Write-Host "🔄 Setting Azure context..." -ForegroundColor Cyan
        Write-Host "=" * 40 -ForegroundColor Gray
        Write-Host ""
        
        # Check if currently connected
        $currentContext = Get-AzContext -ErrorAction SilentlyContinue
        if (-not $currentContext) {{
            Write-Host "❌ Not currently connected to Azure" -ForegroundColor Red
            Write-Host ""
            Write-Host "💡 Please connect first with: az migrate auth login" -ForegroundColor Cyan
            Write-Host ""
            
            @{{
                'Status' = 'NotConnected'
                'Error' = 'Not authenticated to Azure'
                'Message' = 'Please connect to Azure first'
                'NextSteps' = @('Connect to Azure: az migrate auth login')
            }} | ConvertTo-Json -Depth 3
            return
        }}
        
        Write-Host "📋 Current context:" -ForegroundColor Yellow
        Write-Host "   Account: $($currentContext.Account.Id)" -ForegroundColor White
        Write-Host "   Subscription: $($currentContext.Subscription.Name)" -ForegroundColor White
        Write-Host ""
        
        # Set context parameters
        $contextParams = @{{}}
        """
    
    if subscription_id:
        set_context_script += f"""
        $contextParams['SubscriptionId'] = '{subscription_id}'
        Write-Host "🎯 Target Subscription ID: {subscription_id}" -ForegroundColor Yellow
        """
    elif subscription_name:
        set_context_script += f"""
        $contextParams['SubscriptionName'] = '{subscription_name}'
        Write-Host "🎯 Target Subscription Name: {subscription_name}" -ForegroundColor Yellow
        """
    
    if tenant_id:
        set_context_script += f"""
        $contextParams['TenantId'] = '{tenant_id}'
        Write-Host "🏢 Target Tenant ID: {tenant_id}" -ForegroundColor Yellow
        """
    
    set_context_script += """
        Write-Host ""
        Write-Host "⏳ Setting new Azure context..." -ForegroundColor Cyan
        
        # Set the context
        $newContext = Set-AzContext @contextParams
        
        if ($newContext) {
            Write-Host ""
            Write-Host "✅ Successfully set Azure context!" -ForegroundColor Green
            Write-Host ""
            Write-Host "🔐 New Context Details:" -ForegroundColor Yellow
            Write-Host "   Account: $($newContext.Account.Id)" -ForegroundColor White
            Write-Host "   Account Type: $($newContext.Account.Type)" -ForegroundColor White
            Write-Host "   Subscription: $($newContext.Subscription.Name)" -ForegroundColor White
            Write-Host "   Subscription ID: $($newContext.Subscription.Id)" -ForegroundColor White
            Write-Host "   Tenant: $($newContext.Tenant.Id)" -ForegroundColor White
            Write-Host "   Environment: $($newContext.Environment.Name)" -ForegroundColor White
            Write-Host ""
                        
            $result = @{
                'Status' = 'Success'
                'AccountId' = $newContext.Account.Id
                'AccountType' = $newContext.Account.Type
                'SubscriptionId' = $newContext.Subscription.Id
                'SubscriptionName' = $newContext.Subscription.Name
                'TenantId' = $newContext.Tenant.Id
                'Environment' = $newContext.Environment.Name
                'Message' = 'Successfully set Azure context'
            }
            $result | ConvertTo-Json -Depth 4
        } else {
            Write-Host ""
            Write-Host "❌ Failed to set Azure context" -ForegroundColor Red
            Write-Host "   Set-AzContext returned null" -ForegroundColor White
            Write-Host ""
            
            @{
                'Status' = 'Failed'
                'Error' = 'Set-AzContext returned null'
                'Message' = 'Failed to set Azure context'
            } | ConvertTo-Json
        }
        
    } catch {
        Write-Host ""
        Write-Host "❌ Failed to set Azure context: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "🔧 Troubleshooting Steps:" -ForegroundColor Yellow
        Write-Host "   1. Verify the subscription ID or name is correct" -ForegroundColor White
        Write-Host "   2. Ensure you have access to the specified subscription" -ForegroundColor White
        Write-Host "   3. Check that you're authenticated: az migrate auth check" -ForegroundColor White
        Write-Host "   4. List available subscriptions: az migrate auth show-context" -ForegroundColor White
        Write-Host ""
        
        @{
            'Status' = 'Failed'
            'Error' = $_.Exception.Message
            'Message' = 'Failed to set Azure context'
            'TroubleshootingSteps' = @(
                'Verify the subscription ID or name is correct',
                'Ensure you have access to the specified subscription',
                'Check authentication: az migrate auth check',
                'List subscriptions: az migrate auth show-context'
            )
        } | ConvertTo-Json -Depth 3
        throw
    }
    """
    
    try:
        # Use interactive execution to show real-time context change with full visibility
        result = ps_executor.execute_script_interactive(set_context_script)
        return {
            'message': 'Azure context change completed. See detailed results above.',
            'command_executed': 'Set-AzContext with specified parameters',
            'help': 'Context details and available subscriptions are displayed above'
        }
    except Exception as e:
        raise CLIError(f'Failed to set Azure context: {str(e)}')

# --------------------------------------------------------------------------------------------
# Server Replication Commands
# --------------------------------------------------------------------------------------------

def create_server_replication(cmd, resource_group_name, project_name, target_vm_name, 
                             target_resource_group, target_network, server_name=None, 
                             server_index=None, subscription_id=None):
    """Create replication for a discovered server."""
    
    # Get PowerShell executor
    ps_executor = get_powershell_executor()
    
    # Build the PowerShell script
    replication_script = f"""
    # Create server replication
    try {{
        Write-Host "🚀 Creating server replication..." -ForegroundColor Green
        
        # Get discovered servers first
        $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName {project_name} -ResourceGroupName {resource_group_name} -SourceMachineType VMware
        
        # Select server by index or name
        if ("{server_index}" -ne "None" -and "{server_index}" -ne "") {{
            $ServerIndex = [int]"{server_index}"
            if ($ServerIndex -ge 0 -and $ServerIndex -lt $DiscoveredServers.Count) {{
                $SelectedServer = $DiscoveredServers[$ServerIndex]
                Write-Host "Selected server by index $ServerIndex`: $($SelectedServer.DisplayName)" -ForegroundColor Cyan
            }} else {{
                throw "Server index $ServerIndex is out of range. Total servers: $($DiscoveredServers.Count)"
            }}
        }} elseif ("{server_name}" -ne "None" -and "{server_name}" -ne "") {{
            $SelectedServer = $DiscoveredServers | Where-Object {{ $_.DisplayName -eq "{server_name}" }}
            if (-not $SelectedServer) {{
                throw "Server with name '{server_name}' not found"
            }}
            Write-Host "Selected server by name: $($SelectedServer.DisplayName)" -ForegroundColor Cyan
        }} else {{
            throw "Either server_name or server_index must be provided"
        }}
        
        # Get machine details including disk information
        $MachineId = $SelectedServer.Name
        Write-Host "Machine ID: $MachineId" -ForegroundColor Cyan
        
        # Build the full machine resource path for New-AzMigrateServerReplication
        # The cmdlet expects a full resource path like the one shown in the examples
        $SubscriptionId = (Get-AzContext).Subscription.Id
        $MachineResourcePath = "/subscriptions/$SubscriptionId/resourceGroups/{resource_group_name}/providers/Microsoft.OffAzure/VMwareSites/**/machines/$MachineId"
        
        # Try to get the exact machine resource path by finding the VMware site
        try {{
            Write-Host "Looking up VMware site for full machine path..." -ForegroundColor Cyan
            $Sites = Get-AzResource -ResourceGroupName "{resource_group_name}" -ResourceType "Microsoft.OffAzure/VMwareSites" -ErrorAction SilentlyContinue
            if ($Sites -and $Sites.Count -gt 0) {{
                $SiteName = $Sites[0].Name
                $MachineResourcePath = "/subscriptions/$SubscriptionId/resourceGroups/{resource_group_name}/providers/Microsoft.OffAzure/VMwareSites/$SiteName/machines/$MachineId"
                Write-Host "Full machine path: $MachineResourcePath" -ForegroundColor Cyan
            }} else {{
                Write-Host "Could not find subnets, using default subnet name" -ForegroundColor Yellow
            }}
        }} catch {{
            Write-Host "Could not query VMware sites, using machine ID: $($_.Exception.Message)" -ForegroundColor Yellow
            $MachineResourcePath = $MachineId
        }}
        
        # Get detailed server information to extract disk details
        Write-Host "Getting server disk information..." -ForegroundColor Cyan
        $ServerDetails = Get-AzMigrateDiscoveredServer -ProjectName {project_name} -ResourceGroupName {resource_group_name} -DisplayName $SelectedServer.DisplayName
        
        # Extract OS disk ID from the server details
        $OSDiskId = $null
        if ($ServerDetails.Disk) {{
            $OSDisk = $ServerDetails.Disk | Where-Object {{ $_.IsOSDisk -eq $true }}
            if ($OSDisk) {{
                $OSDiskId = $OSDisk.Uuid
                Write-Host "Found OS Disk ID: $OSDiskId" -ForegroundColor Cyan
            }} else {{
                # If no OS disk found with IsOSDisk flag, take the first disk
                $OSDiskId = $ServerDetails.Disk[0].Uuid
                Write-Host "Using first disk as OS Disk ID: $OSDiskId" -ForegroundColor Cyan
            }}
        }} else {{
            throw "No disk information found for server $($SelectedServer.DisplayName)"
        }}
        
        # Create replication with required parameters including OS disk ID
        Write-Host "Creating replication with OS Disk ID: $OSDiskId" -ForegroundColor Cyan
        
        # Extract subnet name from the target network path or use default
        $TargetNetworkPath = "{target_network}"
        $SubnetName = "default"
        
        # Try to find available subnets in the target network
        try {{
            $NetworkParts = $TargetNetworkPath -split "/"
            $NetworkRG = $NetworkParts[4]  # Resource group from the network path
            $NetworkName = $NetworkParts[-1]  # Network name from the path
            
            Write-Host "Checking subnets in network: $NetworkName (RG: $NetworkRG)" -ForegroundColor Cyan
            $VirtualNetwork = Get-AzVirtualNetwork -ResourceGroupName $NetworkRG -Name $NetworkName -ErrorAction SilentlyContinue
            
            if ($VirtualNetwork -and $VirtualNetwork.Subnets) {{
                # Use the first available subnet
                $SubnetName = $VirtualNetwork.Subnets[0].Name
                Write-Host "Found subnet: $SubnetName" -ForegroundColor Cyan
            }} else {{
                Write-Host "Could not find subnets, using default subnet name" -ForegroundColor Yellow
            }}
        }} catch {{
            Write-Host "Could not query network subnets, using default: $($_.Exception.Message)" -ForegroundColor Yellow
        }}
        
        Write-Host "Using target subnet: $SubnetName" -ForegroundColor Cyan
        Write-Host "Using machine resource path: $MachineResourcePath" -ForegroundColor Cyan
        
        $ReplicationJob = New-AzMigrateServerReplication `
            -MachineId $MachineResourcePath `
            -LicenseType "NoLicenseType" `
            -TargetResourceGroupId "{target_resource_group}" `
            -TargetNetworkId "{target_network}" `
            -TargetSubnetName $SubnetName `
            -TargetVMName "{target_vm_name}" `
            -DiskType "Standard_LRS" `
            -OSDiskID $OSDiskId
        
        Write-Host "✅ Replication created successfully!" -ForegroundColor Green
        Write-Host "Job ID: $($ReplicationJob.JobId)" -ForegroundColor Yellow
        Write-Host "Target VM Name: {target_vm_name}" -ForegroundColor Cyan
        
        return @{{
            JobId = $ReplicationJob.JobId
            TargetVMName = "{target_vm_name}"
            Status = "Started"
            ServerName = $SelectedServer.DisplayName
        }}
        
    }} catch {{
        Write-Host "❌ Error creating replication:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Write-Host ""
        Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
        Write-Host "1. Verify server exists and index is correct" -ForegroundColor White
        Write-Host "2. Check target resource group and network paths" -ForegroundColor White
        Write-Host "3. Ensure replication infrastructure is initialized" -ForegroundColor White
        Write-Host ""
        throw
    }}
    """
    
    try:
        # Use interactive execution to show real-time PowerShell output
        result = ps_executor.execute_script_interactive(replication_script)
        return {
            'message': 'PowerShell command executed successfully. Output displayed above.',
            'command_executed': f'New-AzMigrateServerReplication for target VM: {target_vm_name}',
            'parameters': {
                'ProjectName': project_name,
                'ResourceGroupName': resource_group_name,
                'TargetVMName': target_vm_name,
                'TargetResourceGroup': target_resource_group,
                'TargetNetwork': target_network,
                'ServerName': server_name,
                'ServerIndex': server_index
            }
        }
        
    except Exception as e:
        raise CLIError(f'Failed to create server replication: {str(e)}')


def create_server_replication_by_index(cmd, resource_group_name, project_name, server_index, 
                                      target_vm_name, target_resource_group, target_network, 
                                      subscription_id=None):
    """Create replication for a server by its index in the discovered servers list."""
    return create_server_replication(cmd, resource_group_name, project_name, target_vm_name, 
                                   target_resource_group, target_network, 
                                   server_index=server_index, subscription_id=subscription_id)


def get_discovered_servers_by_display_name(cmd, resource_group_name, project_name, display_name, 
                                          source_machine_type='VMware', subscription_id=None):
    """Find discovered servers by display name."""
    
    # Get PowerShell executor
    ps_executor = get_powershell_executor()
    
    # Build the PowerShell script
    search_script = f"""
    # Find servers by display name
    try {{
        Write-Host "🔍 Searching for servers with display name: {display_name}" -ForegroundColor Green
        
        $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName {project_name} -ResourceGroupName {resource_group_name} -SourceMachineType {source_machine_type}
        $MatchingServers = $DiscoveredServers | Where-Object {{ $_.DisplayName -like "*{display_name}*" }}
        
        if ($MatchingServers) {{
            Write-Host "Found $($MatchingServers.Count) matching server(s):" -ForegroundColor Cyan
            $MatchingServers | Format-Table DisplayName, Name, Type -AutoSize
        }} else {{
            Write-Host "No servers found matching: {display_name}" -ForegroundColor Yellow
        }}
        
        return $MatchingServers
        
    }} catch {{
        Write-Host "❌ Error searching for servers:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        throw
    }}
    """
    
    try:
        # Use interactive execution to show real-time PowerShell output
        result = ps_executor.execute_script_interactive(search_script)
        return {
            'message': 'PowerShell command executed successfully. Output displayed above.',
            'command_executed': f'Get-AzMigrateDiscoveredServer filtered by DisplayName: {display_name}',
            'parameters': {
                'ProjectName': project_name,
                'ResourceGroupName': resource_group_name,
                'DisplayName': display_name,
                'SourceMachineType': source_machine_type
            }
        }
        
    except Exception as e:
        raise CLIError(f'Failed to search for servers: {str(e)}')


def get_replication_job_status(cmd, resource_group_name, project_name, vm_name=None, 
                              job_id=None, subscription_id=None):
    """Get replication job status for a VM or job."""
    
    # Get PowerShell executor
    ps_executor = get_powershell_executor()
    
    # Build the PowerShell script
    status_script = f"""
    # Get replication status
    try {{
        Write-Host "📊 Checking replication status..." -ForegroundColor Green
        
        if ("{vm_name}" -ne "None" -and "{vm_name}" -ne "") {{
            Write-Host "Checking status for VM: {vm_name}" -ForegroundColor Cyan
            $ReplicationStatus = Get-AzMigrateServerReplication -ProjectName {project_name} -ResourceGroupName {resource_group_name} -MachineName "{vm_name}"
        }} elseif ("{job_id}" -ne "None" -and "{job_id}" -ne "") {{
            Write-Host "Checking job status for Job ID: {job_id}" -ForegroundColor Cyan
            $ReplicationStatus = Get-AzMigrateJob -JobId "{job_id}" -ProjectName {project_name} -ResourceGroupName {resource_group_name}
        }} else {{
            Write-Host "Getting all replication jobs..." -ForegroundColor Cyan
            $ReplicationStatus = Get-AzMigrateServerReplication -ProjectName {project_name} -ResourceGroupName {resource_group_name}
        }}
        
        if ($ReplicationStatus) {{
            Write-Host "✅ Status retrieved successfully!" -ForegroundColor Green
            $ReplicationStatus | Format-Table -AutoSize
        }} else {{
            Write-Host "No replication status found" -ForegroundColor Yellow
        }}
        
        return $ReplicationStatus
        
    }} catch {{
        Write-Host "❌ Error getting replication status:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        throw
    }}
    """
    
    try:
        # Use interactive execution to show real-time PowerShell output
        result = ps_executor.execute_script_interactive(status_script)
        return {
            'message': 'PowerShell command executed successfully. Output displayed above.',
            'command_executed': f'Get-AzMigrateServerReplication/Get-AzMigrateJob for VM/Job: {vm_name or job_id}',
            'parameters': {
                'ProjectName': project_name,
                'ResourceGroupName': resource_group_name,
                'VMName': vm_name,
                'JobId': job_id
            }
        }
        
    except Exception as e:
        raise CLIError(f'Failed to get replication status: {str(e)}')


def create_multiple_server_replications(cmd, resource_group_name, project_name, 
                                       server_configs, subscription_id=None):
    """Create replication for multiple servers."""
    
    # Get PowerShell executor
    ps_executor = get_powershell_executor()
    
    # Build the PowerShell script
    bulk_script = f"""
    # Create multiple server replications
    try {{
        Write-Host "🚀 Creating multiple server replications..." -ForegroundColor Green
        
        # Get discovered servers
        $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName {project_name} -ResourceGroupName {resource_group_name} -SourceMachineType VMware
        
        $Results = @()
        
        # Process each server configuration
        $ServerConfigs = '{server_configs}' | ConvertFrom-Json
        
        foreach ($Config in $ServerConfigs) {{
            try {{
                Write-Host "Processing server: $($Config.ServerName)" -ForegroundColor Cyan
                
                # Find the server
                $SelectedServer = $DiscoveredServers | Where-Object {{ $_.DisplayName -eq $Config.ServerName }}
                
                if ($SelectedServer) {{
                    # Create replication
                    $ReplicationJob = New-AzMigrateServerReplication -InputObject $SelectedServer -TargetVMName $Config.TargetVMName -TargetResourceGroup $Config.TargetResourceGroup -TargetNetwork $Config.TargetNetwork
                    
                    $Results += @{{
                        ServerName = $Config.ServerName
                        TargetVMName = $Config.TargetVMName
                        JobId = $ReplicationJob.JobId
                        Status = "Started"
                    }}
                    
                    Write-Host "✅ Replication started for $($Config.ServerName)" -ForegroundColor Green
                }} else {{
                    Write-Host "⚠️ Server not found: $($Config.ServerName)" -ForegroundColor Yellow
                    $Results += @{{
                        ServerName = $Config.ServerName
                        Status = "Server not found"
                    }}
                }}
            }} catch {{
                Write-Host "❌ Failed to create replication for $($Config.ServerName): $($_.Exception.Message)" -ForegroundColor Red
                $Results += @{{
                    ServerName = $Config.ServerName
                    Status = "Failed"
                    Error = $_.Exception.Message
                }}
            }}
        }}
        
        Write-Host "📊 Bulk replication summary:" -ForegroundColor Green
        $Results | Format-Table -AutoSize
        
        return $Results
        
    }} catch {{
        Write-Host "❌ Error in bulk replication:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        throw
    }}
    """
    
    try:
        # Use interactive execution to show real-time PowerShell output
        result = ps_executor.execute_script_interactive(bulk_script)
        return {
            'message': 'PowerShell command executed successfully. Output displayed above.',
            'command_executed': 'New-AzMigrateServerReplication (bulk operation)',
            'parameters': {
                'ProjectName': project_name,
                'ResourceGroupName': resource_group_name,
                'ServerConfigs': server_configs
            }
        }
        
    except Exception as e:
        raise CLIError(f'Failed to create multiple server replications: {str(e)}')


def set_replication_target_properties(cmd, resource_group_name, project_name, vm_name, 
                                     target_vm_size=None, target_disk_type=None, 
                                     target_network=None, subscription_id=None):
    """Update replication target properties."""
    
    # Get PowerShell executor
    ps_executor = get_powershell_executor()
    
    # Build the PowerShell script
    update_script = f"""
    # Update replication properties
    try {{
        Write-Host "🔧 Updating replication properties for VM: {vm_name}" -ForegroundColor Green
        
        # Get current replication
        $Replication = Get-AzMigrateServerReplication -ProjectName {project_name} -ResourceGroupName {resource_group_name} -MachineName "{vm_name}"
        
        if ($Replication) {{
            $UpdateParams = @{{}}
            
            if ("{target_vm_size}" -ne "None" -and "{target_vm_size}" -ne "") {{
                $UpdateParams.TargetVMSize = "{target_vm_size}"
                Write-Host "Setting target VM size: {target_vm_size}" -ForegroundColor Cyan
            }}
            
            if ("{target_disk_type}" -ne "None" -and "{target_disk_type}" -ne "") {{
                $UpdateParams.TargetDiskType = "{target_disk_type}"
                Write-Host "Setting target disk type: {target_disk_type}" -ForegroundColor Cyan
            }}
            
            if ("{target_network}" -ne "None" -and "{target_network}" -ne "") {{
                $UpdateParams.TargetNetworkId = "{target_network}"
                Write-Host "Setting target network: {target_network}" -ForegroundColor Cyan
            }}
            
            if ($UpdateParams.Count -gt 0) {{
                $UpdateJob = Set-AzMigrateServerReplication -InputObject $Replication @UpdateParams
                Write-Host "✅ Replication properties updated successfully!" -ForegroundColor Green
                Write-Host "Update Job ID: $($UpdateJob.JobId)" -ForegroundColor Yellow
            }} else {{
                Write-Host "No properties to update" -ForegroundColor Yellow
            }}
        }} else {{
            throw "Replication not found for VM: {vm_name}"
        }}
        
    }} catch {{
        Write-Host "❌ Error updating replication properties:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        throw
    }}
    """
    
    try:
        # Use interactive execution to show real-time PowerShell output
        result = ps_executor.execute_script_interactive(update_script)
        return {
            'message': 'PowerShell command executed successfully. Output displayed above.',
            'command_executed': f'Set-AzMigrateServerReplication for VM: {vm_name}',
            'parameters': {
                'ProjectName': project_name,
                'ResourceGroupName': resource_group_name,
                'VMName': vm_name,
                'TargetVMSize': target_vm_size,
                'TargetDiskType': target_disk_type,
                'TargetNetwork': target_network
            }
        }
        
    except Exception as e:
        raise CLIError(f'Failed to update replication properties: {str(e)}')


# --------------------------------------------------------------------------------------------
# Azure Stack HCI Local Migration Commands
# --------------------------------------------------------------------------------------------

def create_local_disk_mapping(cmd, disk_id, is_os_disk=True, is_dynamic=False, 
                             size_gb=64, format_type='VHD', physical_sector_size=512):
    """
    Azure CLI equivalent to New-AzMigrateLocalDiskMappingObject PowerShell cmdlet.
    Creates a disk mapping object for Azure Stack HCI local migration.
    """
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    disk_mapping_script = f"""
    # Azure CLI equivalent functionality for New-AzMigrateLocalDiskMappingObject
    try {{
        Write-Host ""
        Write-Host "💾 Creating Local Disk Mapping Object..." -ForegroundColor Cyan
        Write-Host "=" * 50 -ForegroundColor Gray
        Write-Host ""
        Write-Host "📋 Disk Configuration:" -ForegroundColor Yellow
        Write-Host "   Disk ID: {disk_id}" -ForegroundColor White
        Write-Host "   Is OS Disk: {str(is_os_disk).lower()}" -ForegroundColor White
        Write-Host "   Is Dynamic: {str(is_dynamic).lower()}" -ForegroundColor White
        Write-Host "   Size (GB): {size_gb}" -ForegroundColor White
        Write-Host "   Format: {format_type}" -ForegroundColor White
        Write-Host "   Physical Sector Size: {physical_sector_size}" -ForegroundColor White
        Write-Host ""
        
        # Execute the real PowerShell cmdlet - equivalent to your provided command
        $DiskMapping = New-AzMigrateLocalDiskMappingObject `
            -DiskID "{disk_id}" `
            -IsOSDisk '{str(is_os_disk).lower()}' `
            -IsDynamic '{str(is_dynamic).lower()}' `
            -Size {size_gb} `
            -Format '{format_type}' `
            -PhysicalSectorSize {physical_sector_size}
        
        if ($DiskMapping) {{
            Write-Host "✅ Disk mapping object created successfully!" -ForegroundColor Green
            Write-Host ""
            Write-Host "📊 Disk Mapping Details:" -ForegroundColor Yellow
            $DiskMapping | Format-List
            Write-Host ""
            
            # Return JSON for programmatic use
            $result = @{{
                'DiskMapping' = $DiskMapping
                'DiskID' = "{disk_id}"
                'IsOSDisk' = {str(is_os_disk).lower()}
                'IsDynamic' = {str(is_dynamic).lower()}
                'SizeGB' = {size_gb}
                'Format' = "{format_type}"
                'PhysicalSectorSize' = {physical_sector_size}
                'Message' = 'Disk mapping object created successfully'
            }}
            $result | ConvertTo-Json -Depth 3
            
        }} else {{
            Write-Host "❌ Failed to create disk mapping object" -ForegroundColor Red
            Write-Host ""
            
            @{{
                'DiskMapping' = $null
                'Created' = $false
                'DiskID' = "{disk_id}"
                'Message' = 'Failed to create disk mapping object'
            }} | ConvertTo-Json
        }}
        
    }} catch {{
        Write-Host ""
        Write-Host "❌ Failed to create disk mapping: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
        Write-Host "1. Check authentication: az migrate auth check" -ForegroundColor White
        Write-Host "2. Verify disk ID format is correct" -ForegroundColor White
        Write-Host "3. Ensure disk size and format values are valid" -ForegroundColor White
        Write-Host "4. Check that Az.Migrate module supports local operations" -ForegroundColor White
        Write-Host ""
        
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
        # Use interactive execution to show real-time PowerShell output
        result = ps_executor.execute_script_interactive(disk_mapping_script)
        return {
            'message': 'PowerShell command executed successfully. Output displayed above.',
            'command_executed': f'New-AzMigrateLocalDiskMappingObject for disk: {disk_id}',
            'parameters': {
                'DiskID': disk_id,
                'IsOSDisk': is_os_disk,
                'IsDynamic': is_dynamic,
                'SizeGB': size_gb,
                'Format': format_type,
                'PhysicalSectorSize': physical_sector_size
            }
        }
        
    except Exception as e:
        raise CLIError(f'Failed to create disk mapping object: {str(e)}')


def create_local_server_replication(cmd, resource_group_name, project_name, server_index, 
                                   target_vm_name, target_storage_path_id, target_virtual_switch_id, 
                                   target_resource_group_id, disk_size_gb=64, disk_format='VHD', 
                                   is_dynamic=False, physical_sector_size=512, subscription_id=None):
    """
    Azure CLI equivalent to New-AzMigrateLocalServerReplication PowerShell cmdlet.
    Creates replication for Azure Stack HCI local migration.
    """
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    local_replication_script = f"""
    # Azure CLI equivalent functionality for New-AzMigrateLocalServerReplication
    try {{
        Write-Host ""
        Write-Host "🚀 Creating Local Server Replication (Azure Stack HCI)..." -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Gray
        Write-Host ""
        Write-Host "📋 Configuration:" -ForegroundColor Yellow
        Write-Host "   Resource Group: {resource_group_name}" -ForegroundColor White
        Write-Host "   Project Name: {project_name}" -ForegroundColor White
        Write-Host "   Server Index: {server_index}" -ForegroundColor White
        Write-Host "   Target VM Name: {target_vm_name}" -ForegroundColor White
        Write-Host ""
        Write-Host "🎯 Target Configuration:" -ForegroundColor Yellow
        Write-Host "   Storage Path: {target_storage_path_id}" -ForegroundColor White
        Write-Host "   Virtual Switch: {target_virtual_switch_id}" -ForegroundColor White
        Write-Host "   Resource Group: {target_resource_group_id}" -ForegroundColor White
        Write-Host ""
        Write-Host "💾 Disk Configuration:" -ForegroundColor Yellow
        Write-Host "   Size: {disk_size_gb} GB" -ForegroundColor White
        Write-Host "   Format: {disk_format}" -ForegroundColor White
        Write-Host "   Dynamic: {str(is_dynamic).lower()}" -ForegroundColor White
        Write-Host "   Sector Size: {physical_sector_size}" -ForegroundColor White
        Write-Host ""
        
        # Get discovered servers
        Write-Host "⏳ Getting discovered servers..." -ForegroundColor Cyan
        $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName {project_name} -ResourceGroupName {resource_group_name} -SourceMachineType VMware
        
        if (-not $DiscoveredServers -or $DiscoveredServers.Count -eq 0) {{
            throw "No discovered servers found in project {project_name}"
        }}
        
        # Select server by index
        $ServerIndex = {server_index}
        if ($ServerIndex -ge 0 -and $ServerIndex -lt $DiscoveredServers.Count) {{
            $DiscoveredServer = $DiscoveredServers[$ServerIndex]
            Write-Host "✅ Selected server: $($DiscoveredServer.DisplayName)" -ForegroundColor Green
            Write-Host "   Server ID: $($DiscoveredServer.Id)" -ForegroundColor White
            Write-Host ""
        }} else {{
            throw "Server index $ServerIndex is out of range. Total servers: $($DiscoveredServers.Count)"
        }}
        
        # Get OS disk information
        Write-Host "💾 Getting disk information..." -ForegroundColor Cyan
        if ($DiscoveredServer.Disk -and $DiscoveredServer.Disk.Count -gt 0) {{
            $OSDisk = $DiscoveredServer.Disk | Where-Object {{ $_.IsOSDisk -eq $true }}
            if (-not $OSDisk) {{
                $OSDisk = $DiscoveredServer.Disk[0]
            }}
            $OSDiskID = $OSDisk.Uuid
            Write-Host "   OS Disk ID: $OSDiskID" -ForegroundColor White
        }} else {{
            throw "No disk information found for server $($DiscoveredServer.DisplayName)"
        }}
        Write-Host ""
        
        # Create disk mapping object
        Write-Host "🔧 Creating disk mapping object..." -ForegroundColor Cyan
        $DiskMappings = New-AzMigrateLocalDiskMappingObject `
            -DiskID $OSDiskID `
            -IsOSDisk $true `
            -IsDynamic ${'$true' if is_dynamic else '$false'} `
            -Size {disk_size_gb} `
            -Format '{disk_format}' `
            -PhysicalSectorSize {physical_sector_size}
        
        Write-Host "✅ Disk mapping created successfully" -ForegroundColor Green
        Write-Host ""
        
        # Create local server replication
        Write-Host "🚀 Starting local server replication..." -ForegroundColor Cyan
        $ReplicationJob = New-AzMigrateLocalServerReplication `
            -MachineId $DiscoveredServer.Id `
            -OSDiskID $OSDiskID `
            -TargetStoragePathId "{target_storage_path_id}" `
            -TargetVirtualSwitchId "{target_virtual_switch_id}" `
            -TargetResourceGroupId "{target_resource_group_id}" `
            -TargetVMName "{target_vm_name}"
        
        Write-Host ""
        Write-Host "✅ Local server replication created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Replication Job Details:" -ForegroundColor Yellow
        if ($ReplicationJob) {{
            Write-Host "   Job ID: $($ReplicationJob.JobId)" -ForegroundColor White
            Write-Host "   Job Type: $($ReplicationJob.Type)" -ForegroundColor White
            Write-Host "   Status: $($ReplicationJob.Status)" -ForegroundColor White
            Write-Host "   Target VM: {target_vm_name}" -ForegroundColor White
            Write-Host "   Source Server: $($DiscoveredServer.DisplayName)" -ForegroundColor White
        }}
        Write-Host ""
        Write-Host "💡 Next Steps:" -ForegroundColor Cyan
        Write-Host "   1. Monitor replication progress with: az migrate server show-replication-status" -ForegroundColor White
        Write-Host "   2. Check job status with: az migrate server show-replication-status --job-id <job-id>" -ForegroundColor White
        Write-Host ""
        
        # Return JSON for programmatic use
        $result = @{{
            'ReplicationJob' = $ReplicationJob
            'JobId' = $ReplicationJob.JobId
            'TargetVMName' = "{target_vm_name}"
            'SourceServerName' = $DiscoveredServer.DisplayName
            'SourceServerId' = $DiscoveredServer.Id
            'OSDiskID' = $OSDiskID
            'TargetStoragePathId' = "{target_storage_path_id}"
            'TargetVirtualSwitchId' = "{target_virtual_switch_id}"
            'TargetResourceGroupId' = "{target_resource_group_id}"
            'DiskConfiguration' = @{{
                'SizeGB' = {disk_size_gb}
                'Format' = "{disk_format}"
                'IsDynamic' = {str(is_dynamic).lower()}
                'PhysicalSectorSize' = {physical_sector_size}
            }}
            'Status' = 'Started'
            'Message' = 'Local server replication created successfully'
        }}
        $result | ConvertTo-Json -Depth 4
        
    }} catch {{
        Write-Host ""
        Write-Host "❌ Failed to create local server replication:" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor White
        Write-Host ""
        Write-Host "🔧 Troubleshooting Steps:" -ForegroundColor Yellow
        Write-Host "   1. Verify server index is correct (0-based)" -ForegroundColor White
        Write-Host "   2. Check Azure Stack HCI resource paths are valid" -ForegroundColor White
        Write-Host "   3. Ensure target storage container exists" -ForegroundColor White
        Write-Host "   4. Verify target virtual switch is available" -ForegroundColor White
        Write-Host "   5. Check permissions on target resource group" -ForegroundColor White
        Write-Host "   6. Ensure Az.Migrate module supports local operations" -ForegroundColor White
        Write-Host ""
        Write-Host "💡 Common Issues:" -ForegroundColor Cyan
        Write-Host "   • Invalid storage path: Check Azure Stack HCI storage container path" -ForegroundColor White
        Write-Host "   • Network issues: Verify logical network path is correct" -ForegroundColor White
        Write-Host "   • Permissions: Ensure contributor access to target resources" -ForegroundColor White
        Write-Host ""
        
        @{{
            'Status' = 'Failed'
            'Error' = $_.Exception.Message
            'ServerIndex' = {server_index}
            'TargetVMName' = "{target_vm_name}"
            'Message' = 'Failed to create local server replication'
            'TroubleshootingSteps' = @(
                'Verify server index is correct',
                'Check Azure Stack HCI resource paths',
                'Ensure target storage container exists',
                'Verify target virtual switch availability',
                'Check permissions on target resource group'
            )
        }} | ConvertTo-Json -Depth 3
        throw
    }}
    """
    
    try:
        # Use interactive execution to show real-time PowerShell output
        result = ps_executor.execute_script_interactive(local_replication_script)
        return {
            'message': 'Azure Stack HCI local replication created successfully. See detailed results above.',
            'command_executed': f'New-AzMigrateLocalServerReplication for target VM: {target_vm_name}',
            'parameters': {
                'ResourceGroupName': resource_group_name,
                'ProjectName': project_name,
                'ServerIndex': server_index,
                'TargetVMName': target_vm_name,
                'TargetStoragePathId': target_storage_path_id,
                'TargetVirtualSwitchId': target_virtual_switch_id,
                'TargetResourceGroupId': target_resource_group_id,
                'DiskConfiguration': {
                    'SizeGB': disk_size_gb,
                    'Format': disk_format,
                    'IsDynamic': is_dynamic,
                    'PhysicalSectorSize': physical_sector_size
                }
            },
            'next_steps': [
                'Monitor replication: az migrate server show-replication-status',
                'Check job status: az migrate server show-replication-status --job-id <job-id>'
            ]
        }
        
    except Exception as e:
        raise CLIError(f'Failed to create local server replication: {str(e)}')


def create_local_server_replication_advanced(cmd, resource_group_name, project_name, 
                                           server_name, target_vm_name, target_storage_path_id, 
                                           target_virtual_switch_id, target_resource_group_id,
                                           disk_mappings=None, subscription_id=None):
    """
    Azure CLI equivalent with advanced disk mapping support.
    Creates replication for Azure Stack HCI local migration with custom disk mappings.
    """
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    # Parse disk mappings if provided
    disk_mappings_param = disk_mappings or "[]"
    
    advanced_replication_script = f"""
    # Azure CLI equivalent functionality for New-AzMigrateLocalServerReplication with advanced options
    try {{
        Write-Host ""
        Write-Host "🚀 Creating Advanced Local Server Replication..." -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Gray
        Write-Host ""
        Write-Host "📋 Configuration:" -ForegroundColor Yellow
        Write-Host "   Resource Group: {resource_group_name}" -ForegroundColor White
        Write-Host "   Project Name: {project_name}" -ForegroundColor White
        Write-Host "   Server Name: {server_name}" -ForegroundColor White
        Write-Host "   Target VM Name: {target_vm_name}" -ForegroundColor White
        Write-Host ""
        
        # Get discovered servers
        Write-Host "⏳ Finding server by name..." -ForegroundColor Cyan
        $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName {project_name} -ResourceGroupName {resource_group_name} -SourceMachineType VMware
        $DiscoveredServer = $DiscoveredServers | Where-Object {{ $_.DisplayName -eq "{server_name}" }}
        
        if (-not $DiscoveredServer) {{
            throw "Server with name '{server_name}' not found in project {project_name}"
        }}
        
        Write-Host "✅ Found server: $($DiscoveredServer.DisplayName)" -ForegroundColor Green
        Write-Host "   Server ID: $($DiscoveredServer.Id)" -ForegroundColor White
        Write-Host ""
        
        # Process disk mappings
        $DiskMappingsArray = @()
        $CustomMappings = '{disk_mappings_param}' | ConvertFrom-Json -ErrorAction SilentlyContinue
        
        if ($CustomMappings -and $CustomMappings.Count -gt 0) {{
            Write-Host "🔧 Creating custom disk mappings..." -ForegroundColor Cyan
            foreach ($mapping in $CustomMappings) {{
                $diskMapping = New-AzMigrateLocalDiskMappingObject `
                    -DiskID $mapping.DiskID `
                    -IsOSDisk $mapping.IsOSDisk `
                    -IsDynamic $mapping.IsDynamic `
                    -Size $mapping.Size `
                    -Format $mapping.Format `
                    -PhysicalSectorSize $mapping.PhysicalSectorSize
                $DiskMappingsArray += $diskMapping
                Write-Host "   ✅ Created mapping for disk: $($mapping.DiskID)" -ForegroundColor Green
            }}
        }} else {{
            Write-Host "🔧 Creating default disk mapping for OS disk..." -ForegroundColor Cyan
            if ($DiscoveredServer.Disk -and $DiscoveredServer.Disk.Count -gt 0) {{
                $OSDisk = $DiscoveredServer.Disk | Where-Object {{ $_.IsOSDisk -eq $true }}
                if (-not $OSDisk) {{
                    $OSDisk = $DiscoveredServer.Disk[0]
                }}
                $OSDiskID = $OSDisk.Uuid
                
                $diskMapping = New-AzMigrateLocalDiskMappingObject `
                    -DiskID $OSDiskID `
                    -IsOSDisk $true `
                    -IsDynamic $false `
                    -Size 64 `
                    -Format 'VHD' `
                    -PhysicalSectorSize 512
                $DiskMappingsArray += $diskMapping
                Write-Host "   ✅ Created default mapping for OS disk: $OSDiskID" -ForegroundColor Green
            }} else {{
                throw "No disk information found for server {server_name}"
            }}
        }}
        Write-Host ""
        
        # Create local server replication
        Write-Host "🚀 Starting local server replication..." -ForegroundColor Cyan
        $ReplicationJob = New-AzMigrateLocalServerReplication `
            -MachineId $DiscoveredServer.Id `
            -OSDiskID $DiskMappingsArray[0].DiskID `
            -TargetStoragePathId "{target_storage_path_id}" `
            -TargetVirtualSwitchId "{target_virtual_switch_id}" `
            -TargetResourceGroupId "{target_resource_group_id}" `
            -TargetVMName "{target_vm_name}"
        
        Write-Host ""
        Write-Host "✅ Advanced local server replication created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Results:" -ForegroundColor Yellow
        if ($ReplicationJob) {{
            Write-Host "   Job ID: $($ReplicationJob.JobId)" -ForegroundColor White
            Write-Host "   Target VM: {target_vm_name}" -ForegroundColor White
            Write-Host "   Source: $($DiscoveredServer.DisplayName)" -ForegroundColor White
            Write-Host "   Disk Mappings: $($DiskMappingsArray.Count)" -ForegroundColor White
        }}
        Write-Host ""
        
        return @{{
            'JobId' = $ReplicationJob.JobId
            'TargetVMName' = "{target_vm_name}"
            'SourceServerName' = $DiscoveredServer.DisplayName
            'DiskMappings' = $DiskMappingsArray.Count
            'Status' = 'Started'
        }}
        
    }} catch {{
        Write-Host ""
        Write-Host "❌ Failed to create advanced local server replication:" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor White
        Write-Host ""
        throw
    }}
    """
    
    try:
        # Use interactive execution to show real-time PowerShell output
        result = ps_executor.execute_script_interactive(advanced_replication_script)
        return {
            'message': 'Advanced Azure Stack HCI local replication created successfully. See detailed results above.',
            'command_executed': f'New-AzMigrateLocalServerReplication (advanced) for target VM: {target_vm_name}',
            'parameters': {
                'ResourceGroupName': resource_group_name,
                'ProjectName': project_name,
                'ServerName': server_name,
                'TargetVMName': target_vm_name,
                'TargetStoragePathId': target_storage_path_id,
                'TargetVirtualSwitchId': target_virtual_switch_id,
                'TargetResourceGroupId': target_resource_group_id,
                'CustomDiskMappings': disk_mappings_param != "[]"
            }
        }
        
    except Exception as e:
        raise CLIError(f'Failed to create advanced local server replication: {str(e)}')


def get_local_replication_job(cmd, job_id=None, input_object=None, subscription_id=None):
    """
    Azure CLI equivalent to Get-AzMigrateLocalJob.
    Gets the status and details of a local replication job.
    """
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
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
            
            # Method 1: Try with -Id parameter
            try {{
                $Job = Get-AzMigrateLocalJob -Id "{job_id}" -ErrorAction SilentlyContinue
                Write-Host "✅ Found job using -Id parameter" -ForegroundColor Green
            }} catch {{
                Write-Host "⚠️ -Id parameter failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }}
            
            # Method 2: Try with -Name parameter if -Id failed
            if (-not $Job) {{
                try {{
                    $Job = Get-AzMigrateLocalJob -Name "{job_id}" -ErrorAction SilentlyContinue
                    Write-Host "✅ Found job using -Name parameter" -ForegroundColor Green
                }} catch {{
                    Write-Host "⚠️ -Name parameter failed: $($_.Exception.Message)" -ForegroundColor Yellow
                }}
            }}
            
            # Method 3: Try listing all jobs and filtering if previous methods failed
            if (-not $Job) {{
                try {{
                    Write-Host "🔍 Getting all jobs and filtering..." -ForegroundColor Cyan
                    $AllJobs = Get-AzMigrateLocalJob -ErrorAction SilentlyContinue
                    $Job = $AllJobs | Where-Object {{ $_.Id -like "*{job_id}*" -or $_.Name -like "*{job_id}*" }}
                    
                    if ($Job) {{
                        Write-Host "✅ Found job by filtering all jobs" -ForegroundColor Green
                    }} else {{
                        Write-Host "⚠️ No job found with ID containing: {job_id}" -ForegroundColor Yellow
                        Write-Host "Available jobs:" -ForegroundColor Cyan
                        $AllJobs | ForEach-Object {{ Write-Host "   - $($_.Id) ($($_.Name))" -ForegroundColor White }}
                    }}
                }} catch {{
                    Write-Host "⚠️ Failed to list all jobs: $($_.Exception.Message)" -ForegroundColor Yellow
                }}
            }}
        }} else {{
            # Get all jobs if no specific job ID provided
            Write-Host "🔍 Getting all local replication jobs..." -ForegroundColor Cyan
            $Job = Get-AzMigrateLocalJob
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
                                               source_appliance_name, target_appliance_name, 
                                               subscription_id=None):
    """
    Azure CLI equivalent to Initialize-AzMigrateLocalReplicationInfrastructure.
    Initializes the local replication infrastructure for Azure Stack HCI migrations.
    """
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    initialize_script = f"""
    # Azure CLI equivalent functionality for Initialize-AzMigrateLocalReplicationInfrastructure
    try {{
        Write-Host ""
        Write-Host "🚀 Initializing Local Replication Infrastructure..." -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Gray
        Write-Host ""
        Write-Host "📋 Configuration:" -ForegroundColor Yellow
        Write-Host "   Resource Group: {resource_group_name}" -ForegroundColor White
        Write-Host "   Project Name: {project_name}" -ForegroundColor White
        Write-Host "   Source Appliance: {source_appliance_name}" -ForegroundColor White
        Write-Host "   Target Appliance: {target_appliance_name}" -ForegroundColor White
        Write-Host ""
        
        # Initialize the local replication infrastructure
        Write-Host "⏳ Setting up replication infrastructure..." -ForegroundColor Cyan
        $Result = Initialize-AzMigrateLocalReplicationInfrastructure `
            -ProjectName "{project_name}" `
            -ResourceGroupName "{resource_group_name}" `
            -SourceApplianceName "{source_appliance_name}" `
            -TargetApplianceName "{target_appliance_name}"
        
        Write-Host ""
        Write-Host "✅ Local replication infrastructure initialized successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Infrastructure Details:" -ForegroundColor Yellow
        if ($Result) {{
            Write-Host "   Status: Initialized" -ForegroundColor White
            Write-Host "   Project: {project_name}" -ForegroundColor White
            Write-Host "   Source Appliance: {source_appliance_name}" -ForegroundColor White
            Write-Host "   Target Appliance: {target_appliance_name}" -ForegroundColor White
        }}
        Write-Host ""
        
        return @{{
            'Status' = 'Initialized'
            'ProjectName' = "{project_name}"
            'ResourceGroupName' = "{resource_group_name}"
            'SourceApplianceName' = "{source_appliance_name}"
            'TargetApplianceName' = "{target_appliance_name}"
        }}
        
    }} catch {{
        Write-Host ""
        Write-Host "❌ Failed to initialize local replication infrastructure:" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor White
        Write-Host ""
        throw
    }}
    """
    
    try:
        result = ps_executor.execute_script_interactive(initialize_script)
        return {
            'message': 'Local replication infrastructure initialized successfully. See detailed results above.',
            'command_executed': f'Initialize-AzMigrateLocalReplicationInfrastructure',
            'parameters': {
                'ResourceGroupName': resource_group_name,
                'ProjectName': project_name,
                'SourceApplianceName': source_appliance_name,
                'TargetApplianceName': target_appliance_name
            }
        }
        
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
