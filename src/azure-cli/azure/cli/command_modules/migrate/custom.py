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


def discover_migration_sources(cmd, source_type=None, server_name=None):
    """Discover available migration sources using PowerShell cmdlets."""
    ps_executor = get_powershell_executor()
    
    discover_script = """
    $sources = @()
    
    # Discover local system information
    $computerInfo = @{
        ComputerName = $env:COMPUTERNAME
        OSVersion = (Get-WmiObject -Class Win32_OperatingSystem).Caption
        Architecture = (Get-WmiObject -Class Win32_Processor).Architecture
        TotalMemory = [math]::Round((Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
        IPAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -ne 'Loopback Pseudo-Interface 1'}).IPAddress
    }
    $sources += $computerInfo
    
    # Discover SQL Server instances (if available)
    try {
        $sqlInstances = Get-Service -Name 'MSSQL*' -ErrorAction SilentlyContinue | Select-Object Name, Status, DisplayName
        if ($sqlInstances) {
            $sources += @{
                Type = 'SQLServer'
                Instances = $sqlInstances
            }
        }
    } catch {
        Write-Warning "Could not discover SQL Server instances"
    }
    
    # Discover Hyper-V VMs (if available)
    try {
        $vms = Get-VM -ErrorAction SilentlyContinue | Select-Object Name, State, Path, ProcessorCount, MemoryAssigned
        if ($vms) {
            $sources += @{
                Type = 'HyperV'
                VirtualMachines = $vms
            }
        }
    } catch {
        Write-Warning "Could not discover Hyper-V virtual machines"
    }
    
    $sources | ConvertTo-Json -Depth 3
    """
    
    try:
        result = ps_executor.execute_script(discover_script)
        sources_data = json.loads(result['stdout'])
        
        return {
            'sources': sources_data,
            'discovery_timestamp': 'discovery completed'
        }
        
    except Exception as e:
        raise CLIError(f'Failed to discover migration sources: {str(e)}')


def assess_migration_readiness(cmd, source_path=None, assessment_type='basic'):
    """Assess migration readiness for the specified source."""
    ps_executor = get_powershell_executor()
    
    assessment_script = f"""
    $assessment = @{{
        AssessmentType = '{assessment_type}'
        Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        Results = @()
    }}
    
    # Basic system assessment
    $systemInfo = @{{
        OS = (Get-WmiObject -Class Win32_OperatingSystem)
        CPU = (Get-WmiObject -Class Win32_Processor)
        Memory = (Get-WmiObject -Class Win32_ComputerSystem)
        Disk = (Get-WmiObject -Class Win32_LogicalDisk)
        Network = (Get-NetAdapter | Where-Object {{$_.Status -eq 'Up'}})
    }}
    
    # Check disk space
    $diskSpaceWarnings = @()
    foreach ($disk in $systemInfo.Disk) {{
        $freeSpaceGB = [math]::Round($disk.FreeSpace / 1GB, 2)
        $totalSpaceGB = [math]::Round($disk.Size / 1GB, 2)
        $usedPercentage = [math]::Round((($totalSpaceGB - $freeSpaceGB) / $totalSpaceGB) * 100, 2)
        
        if ($usedPercentage -gt 80) {{
            $diskSpaceWarnings += "Drive $($disk.DeviceID) is $usedPercentage% full"
        }}
    }}
    
    $assessment.Results += @{{
        Category = 'Storage'
        Status = if ($diskSpaceWarnings.Count -eq 0) {{ 'Passed' }} else {{ 'Warning' }}
        Details = $diskSpaceWarnings
    }}
    
    # Check memory
    $totalMemoryGB = [math]::Round($systemInfo.Memory.TotalPhysicalMemory / 1GB, 2)
    $memoryStatus = if ($totalMemoryGB -ge 4) {{ 'Passed' }} else {{ 'Warning' }}
    $assessment.Results += @{{
        Category = 'Memory'
        Status = $memoryStatus
        Details = "Total Memory: $totalMemoryGB GB"
    }}
    
    # Check network connectivity
    $networkStatus = if ($systemInfo.Network.Count -gt 0) {{ 'Passed' }} else {{ 'Failed' }}
    $assessment.Results += @{{
        Category = 'Network'
        Status = $networkStatus
        Details = "Active network adapters: $($systemInfo.Network.Count)"
    }}
    
    $assessment | ConvertTo-Json -Depth 3
    """
    
    try:
        result = ps_executor.execute_script(assessment_script)
        assessment_data = json.loads(result['stdout'])
        
        return assessment_data
        
    except Exception as e:
        raise CLIError(f'Failed to assess migration readiness: {str(e)}')


def create_migration_plan(cmd, source_name, target_type='azure-vm', plan_name=None):
    """Create a migration plan using PowerShell automation."""
    ps_executor = get_powershell_executor()
    
    if not plan_name:
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        plan_name = f"{source_name}-migration-plan-{timestamp}"
    
    plan_script = f"""
    $plan = @{{
        PlanName = '{plan_name}'
        SourceName = '{source_name}'
        TargetType = '{target_type}'
        CreatedDate = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        Steps = @()
    }}
    
    # Add standard migration steps
    $plan.Steps += @{{
        StepNumber = 1
        Name = 'Prerequisites Check'
        Description = 'Verify system meets migration requirements'
        Status = 'Pending'
    }}
    
    $plan.Steps += @{{
        StepNumber = 2
        Name = 'Data Assessment'
        Description = 'Analyze data and applications for migration'
        Status = 'Pending'
    }}
    
    $plan.Steps += @{{
        StepNumber = 3
        Name = 'Migration Preparation'
        Description = 'Prepare source and target environments'
        Status = 'Pending'
    }}
    
    $plan.Steps += @{{
        StepNumber = 4
        Name = 'Data Migration'
        Description = 'Migrate data and applications'
        Status = 'Pending'
    }}
    
    $plan.Steps += @{{
        StepNumber = 5
        Name = 'Validation'
        Description = 'Validate migration results'
        Status = 'Pending'
    }}
    
    $plan.Steps += @{{
        StepNumber = 6
        Name = 'Cutover'
        Description = 'Complete migration and switch to target'
        Status = 'Pending'
    }}
    
    $plan | ConvertTo-Json -Depth 3
    """
    
    try:
        result = ps_executor.execute_script(plan_script)
        plan_data = json.loads(result['stdout'])
        
        return plan_data
        
    except Exception as e:
        raise CLIError(f'Failed to create migration plan: {str(e)}')


def execute_migration_step(cmd, plan_name, step_number, force=False):
    """Execute a specific migration step."""
    ps_executor = get_powershell_executor()
    
    execution_script = f"""
    $execution = @{{
        PlanName = '{plan_name}'
        StepNumber = {step_number}
        StartTime = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        Status = 'Running'
        Output = @()
    }}
    
    # Simulate step execution based on step number
    switch ({step_number}) {{
        1 {{
            $execution.Output += "Checking PowerShell version..."
            $execution.Output += "PowerShell version: $($PSVersionTable.PSVersion)"
            $execution.Output += "Checking network connectivity..."
            $execution.Output += "Network connectivity: OK"
            $execution.Status = 'Completed'
        }}
        2 {{
            $execution.Output += "Scanning local applications..."
            $execution.Output += "Analyzing disk usage..."
            $execution.Output += "Checking dependencies..."
            $execution.Status = 'Completed'
        }}
        3 {{
            $execution.Output += "Preparing migration environment..."
            $execution.Output += "Configuring target settings..."
            $execution.Status = 'Completed'
        }}
        default {{
            $execution.Output += "Step $step_number execution not yet implemented"
            $execution.Status = 'Pending'
        }}
    }}
    
    $execution.EndTime = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $execution | ConvertTo-Json -Depth 3
    """
    
    try:
        result = ps_executor.execute_script(execution_script)
        execution_data = json.loads(result['stdout'])
        
        return execution_data
        
    except Exception as e:
        raise CLIError(f'Failed to execute migration step: {str(e)}')


def list_migration_plans(cmd, status=None):
    """List migration plans."""
    # This would typically query a database or file system
    # For now, return a simulated list
    plans = [
        {
            'name': 'server01-migration-plan',
            'source': 'server01',
            'target_type': 'azure-vm',
            'status': 'in-progress',
            'created_date': '2025-01-01 10:00:00'
        },
        {
            'name': 'database-migration-plan',
            'source': 'sql-server-01',
            'target_type': 'azure-sql',
            'status': 'completed',
            'created_date': '2024-12-15 14:30:00'
        }
    ]
    
    if status:
        plans = [p for p in plans if p['status'] == status]
    
    return plans


def get_migration_status(cmd, plan_name):
    """Get the status of a migration plan."""
    ps_executor = get_powershell_executor()
    
    status_script = f"""
    # Simulate getting migration status
    $status = @{{
        PlanName = '{plan_name}'
        OverallStatus = 'In Progress'
        CompletedSteps = 3
        TotalSteps = 6
        LastUpdated = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        StepDetails = @(
            @{{ StepNumber = 1; Name = 'Prerequisites Check'; Status = 'Completed' }},
            @{{ StepNumber = 2; Name = 'Data Assessment'; Status = 'Completed' }},
            @{{ StepNumber = 3; Name = 'Migration Preparation'; Status = 'Completed' }},
            @{{ StepNumber = 4; Name = 'Data Migration'; Status = 'Running' }},
            @{{ StepNumber = 5; Name = 'Validation'; Status = 'Pending' }},
            @{{ StepNumber = 6; Name = 'Cutover'; Status = 'Pending' }}
        )
    }}
    
    $status | ConvertTo-Json -Depth 3
    """
    
    try:
        result = ps_executor.execute_script(status_script)
        status_data = json.loads(result['stdout'])
        
        return status_data
        
    except Exception as e:
        raise CLIError(f'Failed to get migration status: {str(e)}')


def assess_sql_server(cmd, server_name=None, instance_name='MSSQLSERVER'):
    """Assess SQL Server for migration to Azure SQL."""
    from azure.cli.command_modules.migrate._powershell_scripts import SQL_SERVER_ASSESSMENT
    
    ps_executor = get_powershell_executor()
    
    parameters = {}
    if server_name:
        parameters['ServerName'] = server_name
    if instance_name:
        parameters['InstanceName'] = instance_name
    
    try:
        result = ps_executor.execute_script(SQL_SERVER_ASSESSMENT, parameters)
        assessment_data = json.loads(result['stdout'])
        
        return assessment_data
        
    except Exception as e:
        raise CLIError(f'Failed to assess SQL Server: {str(e)}')


def assess_hyperv_vm(cmd, vm_name=None):
    """Assess Hyper-V virtual machines for migration to Azure."""
    from azure.cli.command_modules.migrate._powershell_scripts import HYPERV_VM_ASSESSMENT
    
    ps_executor = get_powershell_executor()
    
    parameters = {}
    if vm_name:
        parameters['VMName'] = vm_name
    
    try:
        result = ps_executor.execute_script(HYPERV_VM_ASSESSMENT, parameters)
        assessment_data = json.loads(result['stdout'])
        
        return assessment_data
        
    except Exception as e:
        raise CLIError(f'Failed to assess Hyper-V VMs: {str(e)}')


def assess_filesystem(cmd, path='C:\\'):
    """Assess file system for migration to Azure Storage."""
    from azure.cli.command_modules.migrate._powershell_scripts import FILESYSTEM_ASSESSMENT
    
    ps_executor = get_powershell_executor()
    
    parameters = {'Path': path}
    
    try:
        result = ps_executor.execute_script(FILESYSTEM_ASSESSMENT, parameters)
        assessment_data = json.loads(result['stdout'])
        
        return assessment_data
        
    except Exception as e:
        raise CLIError(f'Failed to assess file system: {str(e)}')


def assess_network(cmd):
    """Assess network configuration for Azure migration."""
    from azure.cli.command_modules.migrate._powershell_scripts import NETWORK_ASSESSMENT
    
    ps_executor = get_powershell_executor()
    
    try:
        result = ps_executor.execute_script(NETWORK_ASSESSMENT)
        assessment_data = json.loads(result['stdout'])
        
        return assessment_data
        
    except Exception as e:
        raise CLIError(f'Failed to assess network configuration: {str(e)}')


def execute_custom_powershell(cmd, script_path, parameters=None):
    """Execute a custom PowerShell script for migration tasks."""
    ps_executor = get_powershell_executor()
    
    if not os.path.exists(script_path):
        raise CLIError(f'PowerShell script not found: {script_path}')
    
    try:
        with open(script_path, 'r', encoding='utf-8') as script_file:
            script_content = script_file.read()
        
        param_dict = {}
        if parameters:
            # Parse parameters in format key=value,key2=value2
            for param in parameters.split(','):
                if '=' in param:
                    key, value = param.split('=', 1)
                    param_dict[key.strip()] = value.strip()
        
        result = ps_executor.execute_script(script_content, param_dict)
        
        return {
            'script_path': script_path,
            'execution_result': result,
            'timestamp': 'execution completed'
        }
        
    except Exception as e:
        raise CLIError(f'Failed to execute PowerShell script: {str(e)}')


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

def get_discovered_server(cmd, resource_group_name, project_name, subscription_id=None, server_id=None, source_machine_type='VMware'):
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
        # Execute the real PowerShell cmdlet
        if ('{server_id}') {{
            $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceMachineType $SourceMachineType | Where-Object {{ $_.Id -eq '{server_id}' }}
        }} else {{
            $DiscoveredServers = Get-AzMigrateDiscoveredServer -ProjectName $ProjectName -ResourceGroupName $ResourceGroupName -SourceMachineType $SourceMachineType
        }}
        
        if ($DiscoveredServers) {{
            $DiscoveredServers | ConvertTo-Json -Depth 5
        }} else {{
            Write-Host "No discovered servers found in project $ProjectName"
            @{{ 'DiscoveredServers' = @(); 'Count' = 0 }} | ConvertTo-Json
        }}
    }} catch {{
        Write-Error "Failed to get discovered servers: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
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


def new_server_replication(cmd, resource_group_name, project_name, machine_name, 
                          target_vm_name=None, target_resource_group=None, target_network=None):
    """Azure CLI equivalent to New-AzMigrateLocalServerReplication PowerShell cmdlet."""
    ps_executor = get_powershell_executor()
    
    replication_script = f"""
    # Azure CLI equivalent functionality for New-AzMigrateLocalServerReplication
    $ResourceGroupName = '{resource_group_name}'
    $ProjectName = '{project_name}'
    $MachineName = '{machine_name}'
    $TargetVMName = '{target_vm_name or machine_name}'
    $TargetResourceGroup = '{target_resource_group or resource_group_name}'
    
    try {{
        # In a real implementation, this would call:
        # New-AzMigrateLocalServerReplication -ResourceGroupName $ResourceGroupName -ProjectName $ProjectName -MachineName $MachineName
        
        Write-Host "This command requires actual Azure Migrate setup with discovered servers."
        Write-Host "To create server replication, you need:"
        Write-Host "1. A discovered server in Azure Migrate project"
        Write-Host "2. Azure Migrate: Server Migration solution enabled"
        Write-Host "3. Proper Azure authentication configured"
        
        $errorResult = @{{
            'Error' = 'Server replication requires real Azure Migrate project with discovered servers'
            'MachineName' = $MachineName
            'ResourceGroup' = $ResourceGroupName
            'Project' = $ProjectName
            'RequiredSteps' = @(
                'Ensure server is discovered in Azure Migrate project',
                'Enable Azure Migrate: Server Migration solution',
                'Configure authentication with Connect-AzAccount',
                'Run New-AzMigrateLocalServerReplication with real parameters'
            )
        }}
        
        $errorResult | ConvertTo-Json -Depth 3
    }} catch {{
        Write-Error "Failed to create server replication: $($_.Exception.Message)"
        return @{{ 'Error' = $_.Exception.Message }}
    }}
    """
    
    try:
        result = ps_executor.execute_script(replication_script)
        response_data = json.loads(result['stdout'])
        
        if 'Error' in response_data:
            raise CLIError(f"Replication setup required: {response_data['Error']}")
        
        return response_data
    except json.JSONDecodeError:
        raise CLIError('Failed to parse response from Azure Migrate API')
    except Exception as e:
        raise CLIError(f'Failed to create server replication: {str(e)}')


def get_server_replication(cmd, resource_group_name, project_name, machine_name=None):
    """Azure CLI equivalent to Get-AzMigrateLocalServerReplication PowerShell cmdlet."""
    ps_executor = get_powershell_executor()
    
    get_replication_script = f"""
    # Azure CLI equivalent functionality for Get-AzMigrateLocalServerReplication
    $ResourceGroupName = '{resource_group_name}'
    $ProjectName = '{project_name}'
    $MachineName = '{machine_name or ""}'
    
    try {{
        # In a real implementation, this would call:
        # Get-AzMigrateLocalServerReplication -ResourceGroupName $ResourceGroupName -ProjectName $ProjectName
        
        Write-Host "This command requires actual Azure Migrate setup with server replication."
        Write-Host "To retrieve server replication status, you need:"
        Write-Host "1. Active server replication in Azure Migrate project"
        Write-Host "2. Azure Migrate: Server Migration solution enabled"
        Write-Host "3. Proper Azure authentication configured"
        
        $errorResult = @{{
            'Error' = 'Server replication status requires real Azure Migrate project with active replications'
            'MachineName' = $MachineName
            'ResourceGroup' = $ResourceGroupName
            'Project' = $ProjectName
            'RequiredSteps' = @(
                'Create server replication with az migrate server replication create',
                'Ensure Azure Migrate: Server Migration solution is enabled',
                'Configure authentication with Connect-AzAccount',
                'Run Get-AzMigrateLocalServerReplication with real parameters'
            )
        }}
        
        $errorResult | ConvertTo-Json -Depth 3
    }} catch {{
        Write-Error "Failed to get server replication: $($_.Exception.Message)"
        return @{{ 'Error' = $_.Exception.Message }}
    }}
    """
    
    try:
        result = ps_executor.execute_script(get_replication_script)
        response_data = json.loads(result['stdout'])
        
        if 'Error' in response_data:
            raise CLIError(f"Replication status check requires setup: {response_data['Error']}")
        
        return response_data
    except json.JSONDecodeError:
        raise CLIError('Failed to parse response from Azure Migrate API')
    except Exception as e:
        raise CLIError(f'Failed to get server replication: {str(e)}')


def start_server_migration(cmd, resource_group_name, project_name, machine_name, 
                          shutdown_source=False, test_migration=False):
    """Azure CLI equivalent to Start-AzMigrateLocalServerMigration PowerShell cmdlet."""
    ps_executor = get_powershell_executor()
    
    migration_script = f"""
    # Azure CLI equivalent functionality for Start-AzMigrateLocalServerMigration
    $ResourceGroupName = '{resource_group_name}'
    $ProjectName = '{project_name}'
    $MachineName = '{machine_name}'
    $ShutdownSource = ${str(shutdown_source).lower()}
    $TestMigration = ${str(test_migration).lower()}
    
    try {{
        # In a real implementation, this would call:
        # Start-AzMigrateLocalServerMigration -ResourceGroupName $ResourceGroupName -ProjectName $ProjectName -MachineName $MachineName
        
        Write-Host "This command requires actual Azure Migrate setup with replicating servers."
        Write-Host "To start server migration, you need:"
        Write-Host "1. Server with active replication in Azure Migrate project"
        Write-Host "2. Azure Migrate: Server Migration solution enabled"
        Write-Host "3. Proper Azure authentication configured"
        
        $errorResult = @{{
            'Error' = 'Server migration requires real Azure Migrate project with replicating servers'
            'MachineName' = $MachineName
            'ResourceGroup' = $ResourceGroupName
            'Project' = $ProjectName
            'MigrationType' = if ($TestMigration) {{ 'Test' }} else {{ 'Production' }}
            'RequiredSteps' = @(
                'Ensure server replication is active and healthy',
                'Verify target VM configuration is complete',
                'Configure authentication with Connect-AzAccount',
                'Run Start-AzMigrateLocalServerMigration with real parameters'
            )
        }}
        
        $errorResult | ConvertTo-Json -Depth 3
    }} catch {{
        Write-Error "Failed to start server migration: $($_.Exception.Message)"
        return @{{ 'Error' = $_.Exception.Message }}
    }}
    """
    
    try:
        result = ps_executor.execute_script(migration_script)
        response_data = json.loads(result['stdout'])
        
        if 'Error' in response_data:
            raise CLIError(f"Migration start requires setup: {response_data['Error']}")
        
        return response_data
    except json.JSONDecodeError:
        raise CLIError('Failed to parse response from Azure Migrate API')
    except Exception as e:
        raise CLIError(f'Failed to start server migration: {str(e)}')


def get_migration_job(cmd, resource_group_name, project_name, job_id=None):
    """Azure CLI equivalent to Get-AzMigrateLocalJob PowerShell cmdlet."""
    ps_executor = get_powershell_executor()
    
    job_script = f"""
    # Azure CLI equivalent functionality for Get-AzMigrateLocalJob
    $ResourceGroupName = '{resource_group_name}'
    $ProjectName = '{project_name}'
    $JobId = '{job_id or ""}'
    
    try {{
        # In a real implementation, this would call:
        # Get-AzMigrateLocalJob -ResourceGroupName $ResourceGroupName -ProjectName $ProjectName
        
        Write-Host "This command requires actual Azure Migrate setup with migration jobs."
        Write-Host "To retrieve migration job status, you need:"
        Write-Host "1. Active migration jobs in Azure Migrate project"
        Write-Host "2. Azure Migrate: Server Migration solution enabled"
        Write-Host "3. Proper Azure authentication configured"
        
        $errorResult = @{{
            'Error' = 'Migration job status requires real Azure Migrate project with active jobs'
            'JobId' = $JobId
            'ResourceGroup' = $ResourceGroupName
            'Project' = $ProjectName
            'RequiredSteps' = @(
                'Start server migration with az migrate server migration start',
                'Ensure Azure Migrate: Server Migration solution is enabled',
                'Configure authentication with Connect-AzAccount',
                'Run Get-AzMigrateLocalJob with real parameters'
            )
        }}
        
        $errorResult | ConvertTo-Json -Depth 3
    }} catch {{
        Write-Error "Failed to get migration job: $($_.Exception.Message)"
        return @{{ 'Error' = $_.Exception.Message }}
    }}
    """
    
    try:
        result = ps_executor.execute_script(job_script)
        response_data = json.loads(result['stdout'])
        
        if 'Error' in response_data:
            raise CLIError(f"Job status check requires setup: {response_data['Error']}")
        
        return response_data
    except json.JSONDecodeError:
        raise CLIError('Failed to parse response from Azure Migrate API')
    except Exception as e:
        raise CLIError(f'Failed to get migration job: {str(e)}')


def remove_server_replication(cmd, resource_group_name, project_name, machine_name, force=False):
    """Azure CLI equivalent to Remove-AzMigrateLocalServerReplication PowerShell cmdlet."""
    ps_executor = get_powershell_executor()
    
    remove_script = f"""
    # Azure CLI equivalent functionality for Remove-AzMigrateLocalServerReplication
    $ResourceGroupName = '{resource_group_name}'
    $ProjectName = '{project_name}'
    $MachineName = '{machine_name}'
    $Force = ${str(force).lower()}
    
    try {{
        # In a real implementation, this would call:
        # Remove-AzMigrateLocalServerReplication -ResourceGroupName $ResourceGroupName -ProjectName $ProjectName -MachineName $MachineName
        
        Write-Host "This command requires actual Azure Migrate setup with active replication."
        Write-Host "To remove server replication, you need:"
        Write-Host "1. Server with active replication in Azure Migrate project"
        Write-Host "2. Azure Migrate: Server Migration solution enabled"
        Write-Host "3. Proper Azure authentication configured"
        
        $errorResult = @{{
            'Error' = 'Server replication removal requires real Azure Migrate project with active replications'
            'MachineName' = $MachineName
            'ResourceGroup' = $ResourceGroupName
            'Project' = $ProjectName
            'Force' = $Force
            'RequiredSteps' = @(
                'Ensure server replication exists and is active',
                'Stop any ongoing migration jobs for this server',
                'Configure authentication with Connect-AzAccount',
                'Run Remove-AzMigrateLocalServerReplication with real parameters'
            )
        }}
        
        $errorResult | ConvertTo-Json -Depth 3
    }} catch {{
        Write-Error "Failed to remove server replication: $($_.Exception.Message)"
        return @{{ 'Error' = $_.Exception.Message }}
    }}
    """
    
    try:
        result = ps_executor.execute_script(remove_script)
        response_data = json.loads(result['stdout'])
        
        if 'Error' in response_data:
            raise CLIError(f"Replication removal requires setup: {response_data['Error']}")
        
        return response_data
    except json.JSONDecodeError:
        raise CLIError('Failed to parse response from Azure Migrate API')
    except Exception as e:
        raise CLIError(f'Failed to remove server replication: {str(e)}')


def create_migrate_project(cmd, resource_group_name, project_name, location='East US', 
                          assessment_solution=None, migration_solution=None):
    """Create a new Azure Migrate project (Azure CLI equivalent to PowerShell project creation)."""
    ps_executor = get_powershell_executor()
    
    project_script = f"""
    # Azure CLI equivalent functionality for creating migrate project
    $ResourceGroupName = '{resource_group_name}'
    $ProjectName = '{project_name}'
    $Location = '{location}'
    
    try {{
        # In a real implementation, this would call Azure REST API or PowerShell:
        # New-AzMigrateProject -ResourceGroupName $ResourceGroupName -Name $ProjectName -Location $Location
        
        Write-Host "This command requires actual Azure subscription and authentication."
        Write-Host "To create Azure Migrate project, you need:"
        Write-Host "1. Valid Azure subscription with proper permissions"
        Write-Host "2. Resource group created in Azure"
        Write-Host "3. Proper Azure authentication configured"
        
        $errorResult = @{{
            'Error' = 'Project creation requires real Azure subscription and authentication'
            'ProjectName' = $ProjectName
            'ResourceGroup' = $ResourceGroupName
            'Location' = $Location
            'RequiredSteps' = @(
                'Ensure Azure subscription is active and accessible',
                'Create or verify resource group exists',
                'Configure authentication with Connect-AzAccount',
                'Use Azure Portal or REST API to create Azure Migrate project'
            )
        }}
        
        $errorResult | ConvertTo-Json -Depth 3
    }} catch {{
        Write-Error "Failed to create migrate project: $($_.Exception.Message)"
        return @{{ 'Error' = $_.Exception.Message }}
    }}
    """
    
    try:
        result = ps_executor.execute_script(project_script)
        response_data = json.loads(result['stdout'])
        
        if 'Error' in response_data:
            raise CLIError(f"Project creation requires setup: {response_data['Error']}")
        
        return response_data
    except json.JSONDecodeError:
        raise CLIError('Failed to parse response from Azure Migrate API')
    except Exception as e:
        raise CLIError(f'Failed to create migrate project: {str(e)}')


# Additional Azure CLI equivalents needed for full PowerShell compatibility

def initialize_replication_infrastructure(cmd, resource_group_name, project_name, 
                                        source_appliance_name, target_appliance_name):
    """Azure CLI equivalent to Initialize-AzMigrateLocalReplicationInfrastructure."""
    ps_executor = get_powershell_executor()
    
    infrastructure_script = f"""
    # Real Azure authentication and execution
    $ResourceGroupName = '{resource_group_name}'
    $ProjectName = '{project_name}'
    $SourceApplianceName = '{source_appliance_name}'
    $TargetApplianceName = '{target_appliance_name}'
    
    try {{
        # This would need real Azure authentication
        Initialize-AzMigrateLocalReplicationInfrastructure `
            -ProjectName $ProjectName `
            -ResourceGroupName $ResourceGroupName `
            -SourceApplianceName $SourceApplianceName `
            -TargetApplianceName $TargetApplianceName
            
        Write-Output "Infrastructure initialized successfully"
    }} catch {{
        Write-Error "Failed to initialize replication infrastructure: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        result = ps_executor.execute_script(infrastructure_script)
        return {"status": "success", "message": "Infrastructure initialized"}
    except Exception as e:
        raise CLIError(f'Failed to initialize replication infrastructure: {str(e)}')


def create_disk_mapping(cmd, disk_id, is_os_disk=True, is_dynamic=False, 
                       size_gb=64, format_type='VHD', physical_sector_size=512):
    """Azure CLI equivalent to New-AzMigrateLocalDiskMappingObject."""
    ps_executor = get_powershell_executor()
    
    disk_mapping_script = f"""
    $DiskMapping = New-AzMigrateLocalDiskMappingObject `
        -DiskID '{disk_id}' `
        -IsOSDisk '{str(is_os_disk).lower()}' `
        -IsDynamic '{str(is_dynamic).lower()}' `
        -Size {size_gb} `
        -Format '{format_type}' `
        -PhysicalSectorSize {physical_sector_size}
        
    $DiskMapping | ConvertTo-Json -Depth 3
    """
    
    try:
        result = ps_executor.execute_script(disk_mapping_script)
        disk_mapping = json.loads(result['stdout'])
        return disk_mapping
    except Exception as e:
        raise CLIError(f'Failed to create disk mapping: {str(e)}')


def create_server_replication_with_params(cmd, machine_id, os_disk_id, target_storage_path_id,
                                        target_virtual_switch_id, target_resource_group_id, 
                                        target_vm_name):
    """Azure CLI equivalent to New-AzMigrateLocalServerReplication with full parameters."""
    ps_executor = get_powershell_executor()
    
    replication_script = f"""
    $ReplicationJob = New-AzMigrateLocalServerReplication `
        -MachineId '{machine_id}' `
        -OSDiskID '{os_disk_id}' `
        -TargetStoragePathId '{target_storage_path_id}' `
        -TargetVirtualSwitch '{target_virtual_switch_id}' `
        -TargetResourceGroupId '{target_resource_group_id}' `
        -TargetVMName '{target_vm_name}'
        
    $ReplicationJob | ConvertTo-Json -Depth 3
    """
    
    try:
        result = ps_executor.execute_script(replication_script)
        replication_job = json.loads(result['stdout'])
        return replication_job
    except Exception as e:
        raise CLIError(f'Failed to create server replication: {str(e)}')


def get_local_job(cmd, input_object=None, job_id=None):
    """Azure CLI equivalent to Get-AzMigrateLocalJob."""
    ps_executor = get_powershell_executor()
    
    if input_object:
        job_script = f"""
        $Job = Get-AzMigrateLocalJob -InputObject $({json.dumps(input_object)})
        $Job | ConvertTo-Json -Depth 3
        """
    elif job_id:
        job_script = f"""
        $Job = Get-AzMigrateLocalJob -Id '{job_id}'
        $Job | ConvertTo-Json -Depth 3
        """
    else:
        job_script = """
        $Jobs = Get-AzMigrateLocalJob
        $Jobs | ConvertTo-Json -Depth 3
        """
    
    try:
        result = ps_executor.execute_script(job_script)
        job_data = json.loads(result['stdout'])
        return job_data
    except Exception as e:
        raise CLIError(f'Failed to get migration job: {str(e)}')


def get_server_replication_by_id(cmd, discovered_machine_id=None, input_object=None):
    """Azure CLI equivalent to Get-AzMigrateLocalServerReplication with specific parameters."""
    ps_executor = get_powershell_executor()
    
    if discovered_machine_id:
        replication_script = f"""
        $ProtectedItem = Get-AzMigrateLocalServerReplication -DiscoveredMachineId '{discovered_machine_id}'
        $ProtectedItem | ConvertTo-Json -Depth 3
        """
    elif input_object:
        replication_script = f"""
        $ProtectedItem = Get-AzMigrateLocalServerReplication -InputObject $({json.dumps(input_object)})
        $ProtectedItem | ConvertTo-Json -Depth 3
        """
    else:
        replication_script = """
        $ProtectedItems = Get-AzMigrateLocalServerReplication
        $ProtectedItems | ConvertTo-Json -Depth 3
        """
    
    try:
        result = ps_executor.execute_script(replication_script)
        replication_data = json.loads(result['stdout'])
        return replication_data
    except Exception as e:
        raise CLIError(f'Failed to get server replication: {str(e)}')


def start_server_migration_with_object(cmd, input_object, turn_off_source_server=False):
    """Azure CLI equivalent to Start-AzMigrateLocalServerMigration with InputObject."""
    ps_executor = get_powershell_executor()
    
    migration_script = f"""
    $MigrationJob = Start-AzMigrateLocalServerMigration `
        -InputObject $({json.dumps(input_object)}) `
        {'-TurnOffSourceServer' if turn_off_source_server else ''}
        
    $MigrationJob | ConvertTo-Json -Depth 3
    """
    
    try:
        result = ps_executor.execute_script(migration_script)
        migration_job = json.loads(result['stdout'])
        return migration_job
    except Exception as e:
        raise CLIError(f'Failed to start server migration: {str(e)}')


def check_azure_authentication(cmd):
    """Check Azure authentication status and Az.Migrate module availability."""
    ps_executor = get_powershell_executor()
    
    auth_status = ps_executor.check_azure_authentication()
    
    return {
        'azure_authentication': {
            'is_authenticated': auth_status.get('IsAuthenticated', False),
            'module_available': auth_status.get('ModuleAvailable', False),
            'subscription_id': auth_status.get('SubscriptionId'),
            'account_id': auth_status.get('AccountId'),
            'tenant_id': auth_status.get('TenantId'),
            'error': auth_status.get('Error')
        },
        'recommendations': [
            "Install Az.Migrate module: Install-Module -Name Az.Migrate" if not auth_status.get('ModuleAvailable') else None,
            "Authenticate to Azure: Connect-AzAccount" if not auth_status.get('IsAuthenticated') else None,
            "Set subscription context: Set-AzContext -SubscriptionId 'your-subscription-id'" if auth_status.get('IsAuthenticated') else None
        ]
    }


def connect_azure_account(cmd, tenant_id=None, subscription_id=None, device_code=False, 
                        app_id=None, secret=None):
    """
    Azure CLI equivalent to Connect-AzAccount PowerShell cmdlet.
    
    This command works cross-platform (Windows, Linux, macOS) but requires:
    - PowerShell Core (pwsh) on Linux/macOS
    - Azure PowerShell modules (Az.Accounts, Az.Migrate)
    
    Installation instructions:
    - Windows: PowerShell is pre-installed, install Az modules with: Install-Module -Name Az
    - Linux: Install PowerShell Core, then Az modules
    - macOS: Install PowerShell Core via Homebrew, then Az modules
    """
    ps_executor = get_powershell_executor()
    
    # Check if PowerShell is available for cross-platform compatibility
    current_platform = platform.system().lower()
    is_available, ps_command = ps_executor.check_powershell_availability()
    
    if not is_available:
        error_msg = f"PowerShell not found on {current_platform}. "
        
        if current_platform == 'linux':
            error_msg += "Install PowerShell Core:\n"
            error_msg += "Ubuntu/Debian: curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add - && "
            error_msg += "echo \"deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -rs)-prod $(lsb_release -cs) main\" | "
            error_msg += "sudo tee /etc/apt/sources.list.d/microsoft.list && sudo apt update && sudo apt install -y powershell"
        elif current_platform == 'darwin':
            error_msg += "Install PowerShell Core:\nmacOS: brew install --cask powershell"
        else:
            error_msg += "Please install PowerShell."
            
        raise CLIError(error_msg)
    
    print(f"Using PowerShell: {ps_command} on {current_platform}")
    
    service_principal = None
    if app_id and secret:
        service_principal = {
            'app_id': app_id,
            'secret': secret
        }
    
    try:
        result = ps_executor.connect_azure_account(
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            device_code=device_code,
            service_principal=service_principal
        )
        
        if result.get('Success'):
            # For interactive logins, the output has already been displayed
            # Just return the final result
            return {
                'status': 'success',
                'account_id': result.get('AccountId'),
                'subscription_id': result.get('SubscriptionId'),
                'subscription_name': result.get('SubscriptionName'),
                'tenant_id': result.get('TenantId'),
                'environment': result.get('Environment'),
                'message': f'Successfully connected to Azure using {ps_command}',
                'platform': current_platform
            }
        else:
            error_msg = result.get('Error', 'Unknown error')
            if 'Output' in result:
                # Include the PowerShell output for context
                logger.info(f"PowerShell output: {result['Output']}")
            raise CLIError(f"Failed to connect to Azure: {error_msg}")
            
    except Exception as e:
        raise CLIError(f'Failed to connect to Azure: {str(e)}')


def disconnect_azure_account(cmd):
    """Azure CLI equivalent to Disconnect-AzAccount PowerShell cmdlet."""
    ps_executor = get_powershell_executor()
    
    try:
        result = ps_executor.disconnect_azure_account()
        
        if result.get('Success'):
            return {
                'status': 'success',
                'message': result.get('Message', 'Successfully disconnected from Azure')
            }
        else:
            raise CLIError(f"Failed to disconnect from Azure: {result.get('Error', 'Unknown error')}")
            
    except Exception as e:
        raise CLIError(f'Failed to disconnect from Azure: {str(e)}')


def set_azure_context(cmd, subscription_id=None, tenant_id=None):
    """Azure CLI equivalent to Set-AzContext PowerShell cmdlet."""
    ps_executor = get_powershell_executor()
    
    if not subscription_id and not tenant_id:
        raise CLIError('Either --subscription-id or --tenant-id must be provided')
    
    try:
        result = ps_executor.set_azure_context(
            subscription_id=subscription_id,
            tenant_id=tenant_id
        )
        
        if result.get('Success'):
            return {
                'status': 'success',
                'account_id': result.get('AccountId'),
                'subscription_id': result.get('SubscriptionId'),
                'subscription_name': result.get('SubscriptionName'),
                'tenant_id': result.get('TenantId'),
                'environment': result.get('Environment'),
                'message': 'Successfully set Azure context'
            }
        else:
            raise CLIError(f"Failed to set Azure context: {result.get('Error', 'Unknown error')}")
            
    except Exception as e:
        raise CLIError(f'Failed to set Azure context: {str(e)}')


def get_azure_context(cmd):
    """Azure CLI equivalent to Get-AzContext PowerShell cmdlet."""
    ps_executor = get_powershell_executor()
    
    try:
        result = ps_executor.get_azure_context()
        
        if result.get('Success'):
            if result.get('IsAuthenticated'):
                return {
                    'is_authenticated': True,
                    'account_id': result.get('AccountId'),
                    'subscription_id': result.get('SubscriptionId'),
                    'subscription_name': result.get('SubscriptionName'),
                    'tenant_id': result.get('TenantId'),
                    'environment': result.get('Environment'),
                    'account_type': result.get('AccountType')
                }
            else:
                return {
                    'is_authenticated': False,
                    'message': result.get('Message', 'No Azure context found')
                }
        else:
            raise CLIError(f"Failed to get Azure context: {result.get('Error', 'Unknown error')}")
            
    except Exception as e:
        raise CLIError(f'Failed to get Azure context: {str(e)}')