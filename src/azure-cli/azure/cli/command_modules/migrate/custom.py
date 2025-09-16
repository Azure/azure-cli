# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import platform
from knack.util import CLIError
from knack.log import get_logger
from azure.cli.command_modules.migrate._powershell_utils import get_powershell_executor

logger = get_logger(__name__)

# --------------------------------------------------------------------------------------------
# System Environment Commands
# --------------------------------------------------------------------------------------------

def check_migration_prerequisites(cmd):
    """Check if the system meets migration prerequisites."""
    import platform
    
    prereqs = {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'python_version': platform.python_version(),
        'powershell_available': False,
        'powershell_version': None,
        'azure_powershell_available': False,
        'recommendations': []
    }
    
    try:
        ps_executor = get_powershell_executor()
        if ps_executor:
            is_available, _ = ps_executor.check_powershell_availability()
            if is_available:
                prereqs['powershell_available'] = True
                try:
                    # Check PowerShell version
                    result = ps_executor.execute_script('$PSVersionTable.PSVersion.ToString()')
                    prereqs['powershell_version'] = result.get('stdout', '').strip()
                    
                    # Check Azure PowerShell modules
                    module_result = ps_executor.execute_script('Get-Module -ListAvailable Az.* | Select-Object -First 1')
                    if module_result.get('stdout'):
                        prereqs['azure_powershell_available'] = True
                    
                except Exception:
                    prereqs['recommendations'].append('Azure PowerShell modules may not be installed')
            else:
                prereqs['recommendations'].append('PowerShell is not available')
        else:
            prereqs['recommendations'].append('PowerShell executor could not be initialized')
            
    except Exception as e:
        prereqs['powershell_error'] = str(e)
        prereqs['recommendations'].append('PowerShell is not available or not configured properly')
    
    # Platform-specific recommendations
    if not prereqs['powershell_available']:
        if prereqs['platform'] == 'Windows':
            prereqs['recommendations'].append('Install PowerShell Core from https://github.com/PowerShell/PowerShell')
        elif prereqs['platform'] == 'Linux':
            prereqs['recommendations'].append('Install PowerShell Core: sudo apt install powershell (Ubuntu) or sudo yum install powershell (RHEL)')
        elif prereqs['platform'] == 'Darwin':
            prereqs['recommendations'].append('Install PowerShell Core: brew install powershell')
    
    if not prereqs['azure_powershell_available'] and prereqs['powershell_available']:
        prereqs['recommendations'].append('Install Azure PowerShell: Install-Module -Name Az -Force')
    
    # Display results
    logger.info(f"Platform: {prereqs['platform']} {prereqs.get('platform_version', 'Unknown')}")
    logger.info(f"Python Version: {prereqs['python_version']}")
    logger.info(f"PowerShell Available: {prereqs['powershell_available']}")
    if prereqs['powershell_version']:
        logger.info(f"PowerShell Version: {prereqs['powershell_version']}")
    logger.info(f"Azure PowerShell Available: {prereqs['azure_powershell_available']}")
    
    if prereqs['recommendations']:
        logger.warning("Recommendations:")
        for rec in prereqs['recommendations']:
            logger.warning(f"  - {rec}")
    
    return prereqs

def check_azure_authentication(cmd):
    """Check Azure authentication status."""
    try:
        ps_executor = get_powershell_executor()
        if not ps_executor:
            raise CLIError('PowerShell is not available. Cannot check Azure authentication.')
        
        # Check if authenticated to Azure
        auth_result = ps_executor.execute_script(
            'if (Get-AzContext) { @{IsAuthenticated=$true; AccountId=(Get-AzContext).Account.Id} | ConvertTo-Json } else { @{IsAuthenticated=$false; Error="Not authenticated"} | ConvertTo-Json }'
        )
        
        if auth_result.get('returncode') == 0:
            try:
                auth_data = json.loads(auth_result.get('stdout', '{}'))
                if auth_data.get('IsAuthenticated'):
                    logger.info(f"Authenticated as: {auth_data.get('AccountId', 'Unknown')}")
                    return auth_data
                else:
                    logger.warning("Not authenticated to Azure")
                    return auth_data
            except json.JSONDecodeError:
                logger.error("Failed to parse authentication status")
                return {'IsAuthenticated': False, 'Error': 'Failed to parse response'}
        else:
            error_msg = auth_result.get('stderr', 'Unknown error')
            logger.error(f"Authentication check failed: {error_msg}")
            return {'IsAuthenticated': False, 'Error': error_msg}
            
    except Exception as e:
        logger.error(f"Failed to check authentication: {str(e)}")
        return {'IsAuthenticated': False, 'Error': str(e)}

def setup_migration_environment(cmd, install_powershell=False, check_only=False):
    """Configure the system environment for migration operations."""    
    logger = get_logger(__name__)
    system = platform.system().lower()
    
    setup_results = {
        'platform': system,
        'checks': [],
        'actions_taken': [],
        'cross_platform_ready': False,
        'powershell_status': 'not_checked'
    }
    
    logger.info(f"Setting up migration environment for {system}")
    
    # 1. Check PowerShell availability
    try:
        ps_executor = get_powershell_executor()
        is_available, ps_cmd = ps_executor.check_powershell_availability()
        
        if is_available:
            setup_results['powershell_status'] = 'available'
            setup_results['powershell_command'] = ps_cmd
            setup_results['checks'].append('PowerShell is available')
            
            # Check PowerShell version compatibility
            try:
                version_result = ps_executor.execute_script('$PSVersionTable.PSVersion.Major')
                major_version = int(version_result.get('stdout', '0').strip())
                
                if major_version >= 7:  # PowerShell Core 7+
                    setup_results['checks'].append('PowerShell Core 7+ detected (cross-platform compatible)')
                    setup_results['cross_platform_ready'] = True
                elif major_version >= 5 and system == 'windows':
                    setup_results['checks'].append('Windows PowerShell 5+ detected (Windows only)')
                    setup_results['cross_platform_ready'] = False
                else:
                    setup_results['checks'].append('PowerShell version too old')
                    setup_results['cross_platform_ready'] = False
                    
            except Exception as e:
                setup_results['checks'].append(f'Could not determine PowerShell version: {e}')
                
        else:
            setup_results['powershell_status'] = 'not_available'
            setup_results['checks'].append('PowerShell is not available')
            
            if install_powershell and not check_only:
                # Attempt automatic installation
                install_result = _attempt_powershell_installation(system)
                setup_results['actions_taken'].append(install_result)
            else:
                setup_results['checks'].append(_get_powershell_install_instructions(system))
                
    except Exception as e:
        setup_results['powershell_status'] = 'error'
        setup_results['checks'].append(f'PowerShell check failed: {str(e)}')
    
    # 2. Check Azure PowerShell modules
    if setup_results['powershell_status'] == 'available':
        try:
            ps_executor = get_powershell_executor()
            az_check = ps_executor.execute_script('Get-Module -ListAvailable Az.Migrate | Select-Object -First 1')
            
            if az_check.get('stdout', '').strip():
                setup_results['checks'].append('Az.Migrate module is available')
            else:
                setup_results['checks'].append('Az.Migrate module is not installed')
                if not check_only:
                    setup_results['checks'].append('Install with: Install-Module -Name Az.Migrate -Force')
                    
        except Exception as e:
            setup_results['checks'].append(f'Could not check Azure modules: {str(e)}')
    
    # 3. Platform-specific environment checks
    platform_checks = _perform_platform_specific_checks(system)
    setup_results['checks'].extend(platform_checks)
    
    # Display results
    logger.info("Environment Setup Results:")
    for check in setup_results['checks']:
        logger.info(f"  {check}")
    
    if setup_results['actions_taken']:
        logger.info("Actions taken:")
        for action in setup_results['actions_taken']:
            logger.info(f"  {action}")
    
    return setup_results

def _get_powershell_install_instructions(system):
    """Get platform-specific PowerShell installation instructions."""
    instructions = {
        'windows': 'Install PowerShell Core: winget install Microsoft.PowerShell or visit https://github.com/PowerShell/PowerShell',
        'linux': 'Install PowerShell Core: sudo apt install powershell (Ubuntu) or sudo yum install powershell (RHEL)',
        'darwin': 'Install PowerShell Core: brew install powershell'
    }
    return instructions.get(system, instructions['linux'])

def _attempt_powershell_installation(system):
    """Attempt to automatically install PowerShell (platform-dependent)."""
    if system == 'windows':
        try:
            # Try winget first
            import subprocess
            result = subprocess.run(['winget', 'install', 'Microsoft.PowerShell'], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                return 'PowerShell Core installed via winget'
            else:
                return f'winget installation failed: {result.stderr}'
        except Exception as e:
            return f'Automatic installation failed: {str(e)}'
    
    elif system == 'linux':
        # Note: This would require sudo, so we just provide instructions
        return 'Automatic installation requires sudo. Please run: sudo apt install powershell'
    
    elif system == 'darwin':
        try:
            import subprocess
            result = subprocess.run(['brew', 'install', 'powershell'], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                return 'PowerShell Core installed via Homebrew'
            else:
                return f'Homebrew installation failed: {result.stderr}'
        except Exception as e:
            return f'Automatic installation failed: {str(e)}'
    
    return 'Automatic installation not supported for this platform'

def _perform_platform_specific_checks(system):
    """Perform platform-specific environment checks."""
    checks = []
    
    if system == 'windows':
        checks.append('Windows detected - native PowerShell support')
        
        # Check if running as administrator
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if is_admin:
                checks.append('Running with administrator privileges')
            else:
                checks.append('Not running as administrator - some operations may require elevation')
        except Exception:
            checks.append('Could not determine administrator status')
            
    elif system == 'linux':
        checks.append('Linux detected - PowerShell Core required')
        
        # Check common package managers
        import shutil
        if shutil.which('apt'):
            checks.append('APT package manager available')
        elif shutil.which('yum'):
            checks.append('YUM package manager available')
        elif shutil.which('dnf'):
            checks.append('DNF package manager available')
        else:
            checks.append('No common package manager detected')
            
    elif system == 'darwin':
        checks.append('macOS detected - PowerShell Core required')
        
        # Check if Homebrew is available
        import shutil
        if shutil.which('brew'):
            checks.append('Homebrew available for PowerShell installation')
        else:
            checks.append('Homebrew not found - install from https://brew.sh/')
    
    else:
        checks.append(f'Unsupported platform: {system}')
    
    return checks

# --------------------------------------------------------------------------------------------
# Authentication and Discovery Commands
# --------------------------------------------------------------------------------------------

def verify_migrate_setup(cmd, resource_group_name, project_name):
    """
    Verify Azure Migrate project setup and permissions.
    This command helps diagnose common issues before running migration commands.
    """
    ps_executor = get_powershell_executor()
    
    # Check Azure authentication first
    auth_status = ps_executor.check_azure_authentication()
    if not auth_status.get('IsAuthenticated', False):
        raise CLIError(f"Azure authentication required: {auth_status.get('Error', 'Unknown error')}")
    
    verify_script = f"""
    try {{
        Write-Host "Azure Migrate Setup Verification"
        Write-Host ""
        
        # Get current context
        $context = Get-AzContext
        Write-Host "Current Azure Context:"
        Write-Host "  Subscription: $($context.Subscription.Name) ($($context.Subscription.Id))"
        Write-Host "  Account: $($context.Account.Id)"
        Write-Host "  Tenant: $($context.Tenant.Id)"
        Write-Host ""
        
        $allChecks = @()
        $errors = @()
        
        # 1. Check resource group
        Write-Host "1. Checking resource group..."
        try {{
            $rg = Get-AzResourceGroup -Name '{resource_group_name}' -ErrorAction Stop
            Write-Host "   ✓ Resource group '{resource_group_name}' found in $($rg.Location)"
            $allChecks += "Resource group exists"
        }} catch {{
            Write-Host "   ✗ Resource group '{resource_group_name}' not found or not accessible"
            $errors += "Resource group not found"

            Write-Host "   Available resource groups:"
            Get-AzResourceGroup | Select-Object ResourceGroupName, Location | Format-Table -AutoSize
        }}
        
        # 2. Check Azure Migrate project
        Write-Host "2. Checking Azure Migrate project..."
        try {{
            $project = Get-AzResource -ResourceGroupName '{resource_group_name}' -ResourceType "Microsoft.Migrate/MigrateProjects" -Name '{project_name}' -ErrorAction Stop
            Write-Host "   ✓ Azure Migrate project '{project_name}' found"
            $allChecks += "Azure Migrate project exists"
        }} catch {{
            Write-Host "   ✗ Azure Migrate project '{project_name}' not found"
            $errors += "Azure Migrate project not found"

            Write-Host "   Available Migrate projects in resource group:"
            $migrateProjects = Get-AzResource -ResourceGroupName '{resource_group_name}' -ResourceType "Microsoft.Migrate/MigrateProjects" -ErrorAction SilentlyContinue
            if ($migrateProjects) {{
                $migrateProjects | Select-Object Name, Location | Format-Table -AutoSize
            }} else {{
                Write-Host "   No Azure Migrate projects found in this resource group"
            }}
        }}
        
        # 3. Check Azure Migrate solutions
        Write-Host "3. Checking Azure Migrate solutions..."
        try {{
            $solutions = Get-AzMigrateSolution -SubscriptionId $context.Subscription.Id -ResourceGroupName '{resource_group_name}' -MigrateProjectName '{project_name}' -ErrorAction Stop
            
            if ($solutions) {{
                Write-Host "   Found $($solutions.Count) solution(s) in project"
                $allChecks += "Azure Migrate solutions found"

                Write-Host "   Available solutions:"
                $solutions | Select-Object Tool, Status, @{{Name='Details';Expression={{$_.Details.ExtendedDetails}}}} | Format-Table -AutoSize
                
                # Check for Server Discovery specifically
                $serverDiscovery = $solutions | Where-Object {{ $_.Tool -eq "ServerDiscovery" }}
                if ($serverDiscovery) {{
                    Write-Host "   ✓ Server Discovery solution found (Status: $($serverDiscovery.Status))"
                    $allChecks += "Server Discovery solution exists"
                }} else {{
                    Write-Host "   ⚠ Server Discovery solution not found"
                    $errors += "Server Discovery solution not configured"
                }}
            }} else {{
                Write-Host "   ⚠ No solutions found in project"
                $errors += "No migration solutions configured"
            }}
        }} catch {{
            Write-Host "   ✗ Failed to check solutions: $($_.Exception.Message)"
            $errors += "Cannot access migration solutions"
        }}
        
        # 4. Check PowerShell modules
        Write-Host "4. Checking PowerShell modules..."
        $azMigrate = Get-Module -ListAvailable Az.Migrate | Sort-Object Version -Descending | Select-Object -First 1
        if ($azMigrate) {{
            Write-Host "   ✓ Az.Migrate module found (Version: $($azMigrate.Version))"
            $allChecks += "Az.Migrate module available"
        }} else {{
            Write-Host "   ✗ Az.Migrate module not found"
            $errors += "Az.Migrate module not installed"
        }}
        
        # 5. Test actual discovery command (only if basic checks pass)
        if ($errors.Count -eq 0) {{
            Write-Host "5. Testing server discovery..."
            try {{
                $testServers = Get-AzMigrateDiscoveredServer -ProjectName '{project_name}' -ResourceGroupName '{resource_group_name}' -SourceMachineType VMware -ErrorAction Stop
                Write-Host "   ✓ Successfully retrieved discovered servers (Count: $($testServers.Count))"
                $allChecks += "Server discovery working"
            }} catch {{
                Write-Host "   ✗ Server discovery test failed: $($_.Exception.Message)"
                $errors += "Server discovery not working"
            }}
        }} else {{
            Write-Host "5. Skipping server discovery test due to previous errors"
        }}
        
        # Summary
        Write-Host ""
        Write-Host "Verification Summary:"
        
        if ($errors.Count -eq 0) {{
            Write-Host "✓ All checks passed! Your Azure Migrate setup appears to be working correctly."
        }} else {{
            Write-Host "✗ Found $($errors.Count) issue(s) that need to be resolved:"
            foreach ($error in $errors) {{
                Write-Host "  - $error"
            }}
            
            Write-Host ""
            Write-Host "Recommended actions:"
            Write-Host "1. Ensure you have proper permissions on the resource group and subscription"
            Write-Host "2. Verify the Azure Migrate project exists and is properly configured"
            Write-Host "3. Configure discovery tools in the Azure Migrate project portal"
            Write-Host "4. Install required PowerShell modules: Install-Module Az.Migrate -Force"
        }}
        
        # Return structured result
        return @{{
            Success = ($errors.Count -eq 0)
            ChecksPassed = $allChecks
            ErrorsFound = $errors
            ResourceGroup = '{resource_group_name}'
            ProjectName = '{project_name}'
            SubscriptionId = $context.Subscription.Id
        }}
        
    }} catch {{
        Write-Error "Verification failed: $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(verify_script)
    except Exception as e:
        raise CLIError(f'Failed to verify Azure Migrate setup: {str(e)}')

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
        # First, verify the resource group exists and is accessible
        Write-Host "Checking resource group accessibility..."
        $rg = Get-AzResourceGroup -Name $ResourceGroupName -ErrorAction SilentlyContinue
        if (-not $rg) {{
            Write-Error "Resource group '$ResourceGroupName' not found or not accessible."
            Write-Host "Available resource groups in current subscription:"
            Get-AzResourceGroup | Select-Object ResourceGroupName, Location | Format-Table -AutoSize
            throw "Resource group validation failed"
        }}
        Write-Host "✓ Resource group '$ResourceGroupName' found"
        
        # Check if Azure Migrate project exists
        Write-Host "Checking Azure Migrate project..."
        try {{
            $project = Get-AzResource -ResourceGroupName $ResourceGroupName -ResourceType "Microsoft.Migrate/MigrateProjects" -Name $ProjectName -ErrorAction SilentlyContinue
            if (-not $project) {{
                Write-Error "Azure Migrate project '$ProjectName' not found in resource group '$ResourceGroupName'."
                Write-Host "Available Migrate projects in resource group:"
                $migrateProjects = Get-AzResource -ResourceGroupName $ResourceGroupName -ResourceType "Microsoft.Migrate/MigrateProjects"
                if ($migrateProjects) {{
                    $migrateProjects | Select-Object Name, Location | Format-Table -AutoSize
                }} else {{
                    Write-Host "No Azure Migrate projects found in this resource group."
                    Write-Host "You may need to create an Azure Migrate project first."
                }}
                throw "Azure Migrate project validation failed"
            }}
            Write-Host "✓ Azure Migrate project '$ProjectName' found"
        }} catch {{
            Write-Error "Failed to validate Azure Migrate project: $($_.Exception.Message)"
            throw "Azure Migrate project validation failed"
        }}
        
        # Check for Server Discovery Solution
        Write-Host "Checking Server Discovery Solution..."
        try {{
            $solution = Get-AzMigrateSolution -SubscriptionId (Get-AzContext).Subscription.Id -ResourceGroupName $ResourceGroupName -MigrateProjectName $ProjectName -ErrorAction SilentlyContinue
            $serverDiscoverySolution = $solution | Where-Object {{ $_.Tool -eq "ServerDiscovery" }}
            if (-not $serverDiscoverySolution) {{
                Write-Error "Server Discovery Solution not found in project '$ProjectName'."
                Write-Host "Available solutions in project:"
                if ($solution) {{
                    $solution | Select-Object Tool, Status | Format-Table -AutoSize
                }} else {{
                    Write-Host "No solutions found. Please configure discovery tools in Azure Migrate project."
                }}
                throw "Server Discovery Solution not found"
            }}
            Write-Host "Server Discovery Solution found"
        }} catch {{
            Write-Error "Failed to check Server Discovery Solution: $($_.Exception.Message)"
            throw "Server Discovery Solution validation failed"
        }}
        
        # Execute the real PowerShell cmdlet - equivalent to your provided commands
        Write-Host "Retrieving discovered servers..."
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
        $errorMessage = $_.Exception.Message
        Write-Host "Error Details:"
        Write-Host "  Error: $errorMessage"

        # Provide troubleshooting guidance based on the error
        if ($errorMessage -like "*not found*" -or $errorMessage -like "*could not be found*") {{
            Write-Host ""
            Write-Host "Troubleshooting Steps:"
            Write-Host "1. Verify the resource group name: '$ResourceGroupName'"
            Write-Host "2. Verify the project name: '$ProjectName'"
            Write-Host "3. Check if you have proper permissions on the resource group"
            Write-Host "4. Ensure the Azure Migrate project exists and is properly configured"
            Write-Host "5. Check if discovery tools are configured in the Azure Migrate project"
            Write-Host ""
            Write-Host "Current Context:"
            $context = Get-AzContext
            Write-Host "  Subscription: $($context.Subscription.Name) ($($context.Subscription.Id))"
            Write-Host "  Account: $($context.Account.Id)"
            Write-Host "  Tenant: $($context.Tenant.Id)"
        }}
        
        Write-Error "Failed to get discovered servers: $errorMessage"
        throw $errorMessage
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
    
    set_context_script = """
try { 
    $currentContext = Get-AzContext -ErrorAction SilentlyContinue
    if (-not $currentContext) {
        Write-Host "Not currently connected to Azure. Please connect first with: az migrate auth login"
        throw "No Azure context found"
    }
    
    # Set context parameters
    $contextParams = @{}
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
        Write-Host "Current subscription: $($newContext.Subscription.Name) ($($newContext.Subscription.Id))"
        Write-Host "Current tenant: $($newContext.Tenant.Id)"
    } else {
        throw "Failed to set Azure context"
    }
} catch {
    Write-Error "Failed to set Azure context: $($_.Exception.Message)"
    throw
}
"""
    
    try:
        result = ps_executor.execute_script_interactive(set_context_script)
        if result['returncode'] != 0:
            raise CLIError(f'Failed to set Azure context: {result.get("stderr", "Unknown error")}')
        
        print("Azure context set successfully")
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
            -IsDynamic {'$true' if is_dynamic else '$false'} `
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

def check_powershell_module(cmd, module_name='Az.Migrate', subscription_id=None):
    """
    Checks if the required PowerShell module is installed.
    """
    ps_executor = get_powershell_executor()
    
    module_check_script = f"""
    try {{
        Write-Host "Checking PowerShell module: {module_name}"
        
        Get-InstalledModule -Name "{module_name}" -ErrorAction SilentlyContinue
    }} catch {{
        Write-Host "Error checking module:"
        Write-Host "   $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(module_check_script) 
    except Exception as e:
        raise CLIError(f'Failed to check PowerShell module {module_name}: {str(e)}')

def update_powershell_modules(cmd, modules=None, force=False, include_dependencies=True, allow_prerelease=False):
    """
    Update Azure PowerShell modules to the latest version.
    This command installs or updates the specified Azure PowerShell modules.
    
    Args:
        modules: List of specific modules to update (default: all Az modules)
        force: Force update even if modules are already installed
        include_dependencies: Include dependency modules during update
        allow_prerelease: Allow installation of prerelease versions
    """
    ps_executor = get_powershell_executor()
    
    # Default modules for Azure Migrate functionality
    if not modules:
        modules = [
            'Az.Accounts',
            'Az.Profile', 
            'Az.Resources',
            'Az.Migrate',
            'Az.Storage',
            'Az.RecoveryServices'
        ]
    elif isinstance(modules, str):
        modules = [modules]
    
    # Convert Python booleans to PowerShell booleans
    ps_force = '$true' if force else '$false'
    ps_allow_prerelease = '$true' if allow_prerelease else '$false'
    
    # Create the modules array string for PowerShell
    modules_str = ', '.join([f'"{module}"' for module in modules])
    
    update_script = f"""
    try {{
        Write-Host "Azure PowerShell Module Update Utility"
        Write-Host ""
        
        # Check PowerShell execution policy
        $policy = Get-ExecutionPolicy -Scope CurrentUser
        if ($policy -eq 'Restricted') {{
            Write-Host "Setting PowerShell execution policy to RemoteSigned for current user..."
            Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        }}
        
        # Ensure PowerShell Gallery is trusted
        Write-Host "Configuring PowerShell Gallery as trusted repository..."
        Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
        
        # Check if PowerShellGet is up to date
        Write-Host "Checking PowerShellGet module..."
        $psGet = Get-Module -ListAvailable PowerShellGet | Sort-Object Version -Descending | Select-Object -First 1
        if ($psGet.Version -lt [version]"2.2.5") {{
            Write-Host "Updating PowerShellGet module..."
            Install-Module -Name PowerShellGet -Force -AllowClobber -Scope CurrentUser
            Write-Host "Please restart PowerShell and run this command again for best results."
        }}
        
        # Update each module
        $modules = @({modules_str})
        $updateResults = @()
        
        foreach ($moduleName in $modules) {{
            Write-Host "Processing module: $moduleName"
            
            try {{
                # Check if module is already installed
                $installedModule = Get-InstalledModule -Name $moduleName -ErrorAction SilentlyContinue
                $availableModule = Find-Module -Name $moduleName -ErrorAction SilentlyContinue
                
                if (-not $availableModule) {{
                    Write-Host "   Module '$moduleName' not found in PowerShell Gallery"
                    $updateResults += @{{
                        Module = $moduleName
                        Status = "NotFound"
                        Error = "Module not found in PowerShell Gallery"
                    }}
                    continue
                }}
                
                $installParams = @{{
                    Name = $moduleName
                    Scope = 'CurrentUser'
                    Force = {ps_force}
                    AllowClobber = $true
                }}
                
                if ({ps_allow_prerelease}) {{
                    $installParams['AllowPrerelease'] = $true
                }}
                
                if ($installedModule) {{
                    Write-Host "   Current version: $($installedModule.Version)"
                    Write-Host "   Available version: $($availableModule.Version)"
                    
                    if ($installedModule.Version -lt $availableModule.Version -or {ps_force}) {{
                        Write-Host "   Updating module..."
                        Install-Module @installParams
                        
                        # Verify update
                        $newModule = Get-InstalledModule -Name $moduleName | Sort-Object Version -Descending | Select-Object -First 1
                        Write-Host "   Successfully updated to version: $($newModule.Version)"
                        
                        $updateResults += @{{
                            Module = $moduleName
                            Status = "Updated"
                            OldVersion = $installedModule.Version.ToString()
                            NewVersion = $newModule.Version.ToString()
                        }}
                    }} else {{
                        Write-Host "   Module is already up to date"
                        $updateResults += @{{
                            Module = $moduleName
                            Status = "UpToDate"
                            Version = $installedModule.Version.ToString()
                        }}
                    }}
                }} else {{
                    Write-Host "   Installing module..."
                    Install-Module @installParams
                    
                    # Verify installation
                    $newModule = Get-InstalledModule -Name $moduleName
                    Write-Host "   Successfully installed version: $($newModule.Version)"
                    
                    $updateResults += @{{
                        Module = $moduleName
                        Status = "Installed"
                        Version = $newModule.Version.ToString()
                    }}
                }}
                
            }} catch {{
                Write-Host "   Error processing module '$moduleName': $($_.Exception.Message)"
                $updateResults += @{{
                    Module = $moduleName
                    Status = "Error"
                    Error = $_.Exception.Message
                }}
            }}
            
            Write-Host ""
        }}
        
        # Summary
        Write-Host "Update Summary:"
        
        $updated = ($updateResults | Where-Object {{ $_.Status -eq "Updated" }}).Count
        $installed = ($updateResults | Where-Object {{ $_.Status -eq "Installed" }}).Count
        $upToDate = ($updateResults | Where-Object {{ $_.Status -eq "UpToDate" }}).Count
        $errors = ($updateResults | Where-Object {{ $_.Status -eq "Error" -or $_.Status -eq "NotFound" }}).Count
        
        Write-Host "   Updated: $updated modules"
        Write-Host "   Newly Installed: $installed modules"
        Write-Host "   Already Up-to-Date: $upToDate modules"
        Write-Host "   Errors: $errors modules"
        Write-Host ""
        
        if ($errors -eq 0) {{
            Write-Host "All Azure PowerShell modules are now up to date!"
        }} else {{
            Write-Host "Some modules encountered errors. Check the output above for details."
        }}
        
        # Return results
        return @{{
            Success = ($errors -eq 0)
            UpdatedModules = $updated
            InstalledModules = $installed
            UpToDateModules = $upToDate
            ErrorCount = $errors
            Results = $updateResults
        }}
        
    }} catch {{
        Write-Host "Error during module update process:"
        Write-Host "   $($_.Exception.Message)"
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(update_script)
    except Exception as e:
        raise CLIError(f'Failed to update PowerShell modules: {str(e)}')

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
        Write-Host "Getting Local Replication Job Details..."
        Write-Host ""
        Write-Host "Configuration:"
        Write-Host "   Resource Group: {resource_group_name}"
        Write-Host "   Project Name: {project_name}"
        Write-Host "   Job ID: {job_id or 'All jobs'}"
        Write-Host ""
        
        # First, let's check what parameters are available for Get-AzMigrateLocalJob
        Write-Host "Checking cmdlet parameters..."
        $cmdletInfo = Get-Command Get-AzMigrateLocalJob -ErrorAction SilentlyContinue
        if ($cmdletInfo) {{
            Write-Host "Available parameters:"
            $cmdletInfo.Parameters.Keys | ForEach-Object {{ Write-Host "   - $_" }}
            Write-Host ""
        }}
        
        {param_script}
        
        # Try different approaches to get the job
        $Job = $null
        
        if ("{job_id}" -ne "None" -and "{job_id}" -ne "") {{
            Write-Host "Trying to get job with ID: {job_id}"
            
            # Method 1: Try with -ID parameter (capital ID based on cmdlet info)
            try {{
                $Job = Get-AzMigrateLocalJob -ResourceGroupName "{resource_group_name}" -ProjectName "{project_name}" -ID "{job_id}"
                Write-Host "Found job using -ID parameter"
            }} catch {{
                Write-Host "-ID parameter failed: $($_.Exception.Message)"
            }}
            
            # Method 2: Try with -Name parameter if -ID failed
            if (-not $Job) {{
                try {{
                    $Job = Get-AzMigrateLocalJob -ResourceGroupName "{resource_group_name}" -ProjectName "{project_name}" -Name "{job_id}"
                    Write-Host "Found job using -Name parameter"
                }} catch {{
                    Write-Host "-Name parameter failed: $($_.Exception.Message)"
                }}
            }}
            
            # Method 3: Try listing all jobs and filtering if previous methods failed
            if (-not $Job) {{
                try {{
                    Write-Host "Getting all jobs and filtering..."
                    $AllJobs = Get-AzMigrateLocalJob -ResourceGroupName "{resource_group_name}" -ProjectName "{project_name}"
                    
                    if ($AllJobs) {{
                        Write-Host "Found $($AllJobs.Count) total jobs, searching for match..."
                        $Job = $AllJobs | Where-Object {{ $_.Id -like "*{job_id}*" -or $_.Name -like "*{job_id}*" }}
                        
                        if ($Job) {{
                            Write-Host "Found job by filtering all jobs"
                        }} else {{
                            Write-Host "No job found with ID containing: {job_id}"
                            Write-Host "Available jobs:"
                            $AllJobs | ForEach-Object {{ Write-Host "   - $($_.Id) ($($_.Name))" }}
                        }}
                    }} else {{
                        Write-Host "No jobs found in project"
                    }}
                }} catch {{
                    Write-Host "Failed to list all jobs: $($_.Exception.Message)"
                }}
            }}
        }} else {{
            # Get all jobs if no specific job ID provided
            Write-Host "Getting all local replication jobs..."
            $Job = Get-AzMigrateLocalJob -ResourceGroupName "{resource_group_name}" -ProjectName "{project_name}"
        }}
        
        if ($Job) {{
            Write-Host "Job found!"
            Write-Host ""
            Write-Host "Job Details:"
            
            if ($Job -is [array] -and $Job.Count -gt 1) {{
                Write-Host "   Found multiple jobs ($($Job.Count))"
                $Job | ForEach-Object {{
                    Write-Host "   Job: $($_.Id)"
                    Write-Host "      State: $($_.Property.State)"
                    Write-Host "      Display Name: $($_.Property.DisplayName)"
                    Write-Host ""
                }}
            }} else {{
                if ($Job -is [array]) {{ $Job = $Job[0] }}
                Write-Host "   Job ID: $($Job.Id)"
                Write-Host "   State: $($Job.Property.State)"
                Write-Host "   Start Time: $($Job.Property.StartTime)"
                if ($Job.Property.EndTime) {{
                    Write-Host "   End Time: $($Job.Property.EndTime)"
                }}
                Write-Host "   Display Name: $($Job.Property.DisplayName)"
                Write-Host ""
                Write-Host "Job State: $($Job.Property.State)" 
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
        Write-Host "Failed to get job details:"
        Write-Host "   Error: $($_.Exception.Message)"
        Write-Host ""
        Write-Host "Troubleshooting:"
        Write-Host "   1. Verify the job ID is correct"
        Write-Host "   2. Check if the job exists in the current project"
        Write-Host "   3. Ensure you have access to the job"
        Write-Host ""
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(get_job_script)
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
        Write-Host "Failed to initialize local replication infrastructure:"
        Write-Host "   Error: $($_.Exception.Message)"
        Write-Host ""
        throw
    }}
    """
    
    try:
        ps_executor.execute_script_interactive(initialize_script)
    except Exception as e:
        raise CLIError(f'Failed to initialize local replication infrastructure: {str(e)}')
    
# --------------------------------------------------------------------------------------------
# Cross-Platform Helper Functions
# --------------------------------------------------------------------------------------------

def _get_platform_capabilities():
    """Get platform-specific capabilities and limitations."""
    system = platform.system().lower()
    
    capabilities = {
        'windows': {
            'powershell_native': True,
            'powershell_core_supported': True,
            'azure_powershell_compatible': True,
            'limitations': [],
            'recommendations': [
                'Use PowerShell Core for best cross-platform compatibility',
                'Consider Windows PowerShell 5.1 as fallback'
            ]
        },
        'linux': {
            'powershell_native': False,
            'powershell_core_supported': True,
            'azure_powershell_compatible': True,
            'limitations': [
                'Requires PowerShell Core installation',
                'Some Windows-specific cmdlets may not work'
            ],
            'recommendations': [
                'Install PowerShell Core 7+',
                'Use package manager for installation'
            ]
        },
        'darwin': {
            'powershell_native': False,
            'powershell_core_supported': True,
            'azure_powershell_compatible': True,
            'limitations': [
                'Requires PowerShell Core installation',
                'Some Windows-specific cmdlets may not work'
            ],
            'recommendations': [
                'Install PowerShell Core via Homebrew',
                'Ensure Xcode command line tools are installed'
            ]
        }
    }
    
    return capabilities.get(system, capabilities['linux'])

def _validate_cross_platform_environment():
    """Validate that the environment is properly configured for cross-platform operations."""
    system = platform.system().lower()
    validation_results = {
        'platform': system,
        'is_supported': True,
        'powershell_available': False,
        'azure_modules_available': False,
        'warnings': [],
        'errors': []
    }
    
    try:
        # Check PowerShell availability
        ps_executor = get_powershell_executor()
        is_available, ps_cmd = ps_executor.check_powershell_availability()
        
        validation_results['powershell_available'] = is_available
        
        if is_available:
            # Check PowerShell version
            try:
                version_result = ps_executor.execute_script('$PSVersionTable.PSVersion.ToString()')
                ps_version = version_result.get('stdout', '').strip()
                validation_results['powershell_version'] = ps_version
                
                # Check if it's PowerShell Core (cross-platform)
                platform_result = ps_executor.execute_script('$PSVersionTable.PSEdition')
                ps_edition = platform_result.get('stdout', '').strip()
                
                if ps_edition == 'Core':
                    validation_results['warnings'].append('PowerShell Core detected (cross-platform compatible)')
                elif ps_edition == 'Desktop' and system == 'windows':
                    validation_results['warnings'].append('Windows PowerShell detected (Windows-only)')
                
            except Exception as e:
                validation_results['warnings'].append(f'Could not determine PowerShell version: {e}')
            
            # Check Azure modules
            try:
                az_result = ps_executor.execute_script('Get-Module -ListAvailable Az.Migrate | Select-Object -First 1 | ConvertTo-Json')
                if az_result.get('stdout', '').strip():
                    validation_results['azure_modules_available'] = True
                    validation_results['warnings'].append('Az.Migrate module available')
                else:
                    validation_results['warnings'].append('Az.Migrate module not found')
                    
            except Exception as e:
                validation_results['warnings'].append(f'Could not check Azure modules: {e}')
                
        else:
            validation_results['errors'].append('PowerShell is not available')
            validation_results['is_supported'] = False
            
    except Exception as e:
        validation_results['errors'].append(f'Environment validation failed: {e}')
        validation_results['is_supported'] = False
    
    return validation_results

def validate_cross_platform_environment_cmd(cmd):
    """
    CLI command to validate cross-platform environment for Azure Migrate operations.
    This command checks PowerShell availability and Azure module prerequisites.
    """
    from azure.cli.core import telemetry
    
    try:
        # Run comprehensive environment validation
        results = _validate_cross_platform_environment()
        
        # Display results in a user-friendly format
        print("\nAzure Migrate Cross-Platform Environment Check")
        
        # Platform information
        print(f"\n📍 Platform Information:")
        print(f"   Operating System: {results['platform'].title()}")
        
        # PowerShell availability
        print(f"\n🔧 PowerShell Status:")
        if results['powershell_available']:
            print("   PowerShell Available")
            if 'powershell_version' in results:
                print(f"   Version: {results['powershell_version']}")
        else:
            print("   PowerShell Not Available")
        
        # Azure modules
        print(f"\nAzure Module Status:")
        if results['azure_modules_available']:
            print("   Az.Migrate Module Available")
        else:
            print("   Az.Migrate Module Not Found")
        
        # Platform capabilities
        capabilities = _get_platform_capabilities()
        print(f"\nPlatform Capabilities:")
        print(f"   Native PowerShell: {'✅' if capabilities['powershell_native'] else '❌'}")
        print(f"   PowerShell Core Support: {'✅' if capabilities['powershell_core_supported'] else '❌'}")
        print(f"   Azure PowerShell Compatible: {'✅' if capabilities['azure_powershell_compatible'] else '❌'}")
        
        # Warnings and recommendations
        if results['warnings']:
            print(f"\nStatus Messages:")
            for warning in results['warnings']:
                print(f"   {warning}")
        
        if capabilities['limitations']:
            print(f"\n🚧 Platform Limitations:")
            for limitation in capabilities['limitations']:
                print(f"   • {limitation}")
        
        if capabilities['recommendations']:
            print(f"\nRecommendations:")
            for recommendation in capabilities['recommendations']:
                print(f"   • {recommendation}")
        
        # Errors
        if results['errors']:
            print(f"\nIssues Found:")
            for error in results['errors']:
                print(f"   • {error}")
        
        # Installation instructions if needed
        if not results['powershell_available']:
            system = platform.system().lower()
            install_guide = _get_powershell_install_instructions(system)
            print(f"\n Installation Instructions:")
            print(f"   {install_guide}")
        
        if not results['azure_modules_available'] and results['powershell_available']:
            print(f"\n Azure Module Installation:")
            print(f"   Run in PowerShell: Install-Module -Name Az.Migrate -Force")
            print(f"   Run in PowerShell: Install-Module -Name Az.StackHCI -Force")
        
        # Overall status
        print(f"\nOverall Status:")
        if results['is_supported']:
            print("   Environment is ready for Azure Migrate operations")
        else:
            print("   Environment requires setup before using Azure Migrate")
                
        # Return results for programmatic access
        return results
        
    except Exception as e:
        telemetry.set_exception(e, 'validate-environment-failed')
        raise CLIError(f"Failed to validate environment: {str(e)}")

def _get_powershell_install_instructions(system):
    """Get platform-specific PowerShell installation instructions."""
    instructions = {
        'windows': "Install PowerShell Core: winget install Microsoft.PowerShell",
        'linux': "Install PowerShell Core: sudo apt install powershell (Ubuntu) or sudo yum install powershell (RHEL/CentOS)",
        'darwin': "Install PowerShell Core: brew install powershell"
    }
    
    return instructions.get(system, instructions['linux'])

def create_local_nic_mapping(cmd, nic_id, target_virtual_switch_id, create_at_target=True):
    """Create NIC mapping object for Azure Local migration (equivalent to New-AzMigrateLocalNicMappingObject)."""
    try:
        ps_executor = get_powershell_executor()
        if not ps_executor:
            raise CLIError("PowerShell is not available. Please install PowerShell Core.")
        
        # Build the New-AzMigrateLocalNicMappingObject command
        create_at_target_str = 'true' if create_at_target else 'false'
        
        script = f"""
        try {{
            $nicMapping = New-AzMigrateLocalNicMappingObject `
                -NicID '{nic_id}' `
                -TargetVirtualSwitchId '{target_virtual_switch_id}' `
                -CreateAtTarget '{create_at_target_str}'
            
            $result = @{{
                'Success' = $true
                'NicMapping' = $nicMapping
                'NicID' = '{nic_id}'
                'TargetVirtualSwitchId' = '{target_virtual_switch_id}'
                'CreateAtTarget' = '{create_at_target_str}'
            }}
            
            $result | ConvertTo-Json -Depth 5
        }} catch {{
            $errorResult = @{{
                'Success' = $false
                'Error' = $_.Exception.Message
                'ErrorType' = $_.Exception.GetType().Name
            }}
            $errorResult | ConvertTo-Json -Depth 3
        }}
        """
        
        result = ps_executor.execute_script(script)
        
        if result.get('returncode') == 0:
            output = result.get('stdout', '').strip()
            if output:
                try:
                    parsed_result = json.loads(output)
                    if parsed_result.get('Success'):
                        logger.info("Successfully created NIC mapping object")
                        return parsed_result
                    else:
                        raise CLIError(f"Failed to create NIC mapping: {parsed_result.get('Error', 'Unknown error')}")
                except json.JSONDecodeError:
                    logger.warning("Could not parse PowerShell output as JSON")
                    return {"Success": True, "Output": output}
        
        error_msg = result.get('stderr', 'Unknown PowerShell error')
        raise CLIError(f"PowerShell execution failed: {error_msg}")
        
    except Exception as e:
        logger.error(f"Failed to create NIC mapping: {str(e)}")
        raise CLIError(f"Failed to create NIC mapping: {str(e)}")

def start_azure_local_server_migration(cmd, input_object=None, target_object_id=None,
                                      turn_off_source_server=False):
    """Start Azure Local server migration (equivalent to Start-AzMigrateLocalServerMigration)."""
    try:
        ps_executor = get_powershell_executor()
        if not ps_executor:
            raise CLIError("PowerShell is not available. Please install PowerShell Core.")
        
        # Build the Start-AzMigrateLocalServerMigration command
        turn_off_param = "-TurnOffSourceServer" if turn_off_source_server else ""
        
        if input_object:
            script = f"""
            try {{
                $inputObj = '{input_object}' | ConvertFrom-Json
                $migrationJob = Start-AzMigrateLocalServerMigration `
                    -InputObject $inputObj {turn_off_param}
                
                $result = @{{
                    'Success' = $true
                    'MigrationJob' = $migrationJob
                    'TurnOffSourceServer' = {str(turn_off_source_server).lower()}
                }}
                
                $result | ConvertTo-Json -Depth 7
            }} catch {{
                $errorResult = @{{
                    'Success' = $false
                    'Error' = $_.Exception.Message
                    'ErrorType' = $_.Exception.GetType().Name
                }}
                $errorResult | ConvertTo-Json -Depth 3
            }}
            """
        elif target_object_id:
            script = f"""
            try {{
                # First get the protected item
                $protectedItem = Get-AzMigrateLocalServerReplication -InputObject @{{ Id = '{target_object_id}' }}
                
                $migrationJob = Start-AzMigrateLocalServerMigration `
                    -InputObject $protectedItem {turn_off_param}
                
                $result = @{{
                    'Success' = $true
                    'TargetObjectId' = '{target_object_id}'
                    'MigrationJob' = $migrationJob
                    'TurnOffSourceServer' = {str(turn_off_source_server).lower()}
                }}
                
                $result | ConvertTo-Json -Depth 7
            }} catch {{
                $errorResult = @{{
                    'Success' = $false
                    'Error' = $_.Exception.Message
                    'ErrorType' = $_.Exception.GetType().Name
                }}
                $errorResult | ConvertTo-Json -Depth 3
            }}
            """
        else:
            raise CLIError("Either input_object or target_object_id must be provided")
        
        result = ps_executor.execute_script(script)
        
        if result.get('returncode') == 0:
            output = result.get('stdout', '').strip()
            if output:
                try:
                    parsed_result = json.loads(output)
                    if parsed_result.get('Success'):
                        logger.info("Successfully started Azure Local server migration")
                        return parsed_result
                    else:
                        raise CLIError(f"Failed to start migration: {parsed_result.get('Error', 'Unknown error')}")
                except json.JSONDecodeError:
                    logger.warning("Could not parse PowerShell output as JSON")
                    return {"Success": True, "Output": output}
        
        error_msg = result.get('stderr', 'Unknown PowerShell error')
        raise CLIError(f"PowerShell execution failed: {error_msg}")
        
    except Exception as e:
        logger.error(f"Failed to start Azure Local server migration: {str(e)}")
        raise CLIError(f"Failed to start Azure Local server migration: {str(e)}")

def remove_azure_local_server_replication(cmd, input_object=None, target_object_id=None):
    """Remove Azure Local server replication (equivalent to Remove-AzMigrateLocalServerReplication)."""
    try:
        ps_executor = get_powershell_executor()
        if not ps_executor:
            raise CLIError("PowerShell is not available. Please install PowerShell Core.")
        
        # Build the Remove-AzMigrateLocalServerReplication command
        if input_object:
            script = f"""
            try {{
                $inputObj = '{input_object}' | ConvertFrom-Json
                $removeJob = Remove-AzMigrateLocalServerReplication -InputObject $inputObj
                
                $result = @{{
                    'Success' = $true
                    'RemoveJob' = $removeJob
                    'Message' = 'Replication removal initiated successfully'
                }}
                
                $result | ConvertTo-Json -Depth 7
            }} catch {{
                $errorResult = @{{
                    'Success' = $false
                    'Error' = $_.Exception.Message
                    'ErrorType' = $_.Exception.GetType().Name
                }}
                $errorResult | ConvertTo-Json -Depth 3
            }}
            """
        elif target_object_id:
            script = f"""
            try {{
                $removeJob = Remove-AzMigrateLocalServerReplication -TargetObjectID '{target_object_id}'
                
                $result = @{{
                    'Success' = $true
                    'TargetObjectId' = '{target_object_id}'
                    'RemoveJob' = $removeJob
                    'Message' = 'Replication removal initiated successfully'
                }}
                
                $result | ConvertTo-Json -Depth 7
            }} catch {{
                $errorResult = @{{
                    'Success' = $false
                    'Error' = $_.Exception.Message
                    'ErrorType' = $_.Exception.GetType().Name
                }}
                $errorResult | ConvertTo-Json -Depth 3
            }}
            """
        else:
            raise CLIError("Either input_object or target_object_id must be provided")
        
        result = ps_executor.execute_script(script)
        
        if result.get('returncode') == 0:
            output = result.get('stdout', '').strip()
            if output:
                try:
                    parsed_result = json.loads(output)
                    if parsed_result.get('Success'):
                        logger.info("Successfully removed Azure Local server replication")
                        return parsed_result
                    else:
                        raise CLIError(f"Failed to remove replication: {parsed_result.get('Error', 'Unknown error')}")
                except json.JSONDecodeError:
                    logger.warning("Could not parse PowerShell output as JSON")
                    return {"Success": True, "Output": output}
        
        error_msg = result.get('stderr', 'Unknown PowerShell error')
        raise CLIError(f"PowerShell execution failed: {error_msg}")
        
    except Exception as e:
        logger.error(f"Failed to remove Azure Local server replication: {str(e)}")
        raise CLIError(f"Failed to remove Azure Local server replication: {str(e)}")

def get_azure_local_job(cmd, resource_group_name, project_name, job_id=None, input_object=None, subscription_id=None):
    """Retrieve Azure Local migration jobs (equivalent to Get-AzMigrateLocalJob)."""
    try:
        ps_executor = get_powershell_executor()
        if not ps_executor:
            raise CLIError("PowerShell is not available. Please install PowerShell Core.")
        
        # Build the Get-AzMigrateLocalJob command
        if job_id:
            script = f"""
            try {{
                $job = Get-AzMigrateLocalJob `
                    -ProjectName '{project_name}' `
                    -ResourceGroupName '{resource_group_name}' `
                    -JobId '{job_id}'
                
                $result = @{{
                    'Success' = $true
                    'ProjectName' = '{project_name}'
                    'ResourceGroupName' = '{resource_group_name}'
                    'JobId' = '{job_id}'
                    'Job' = $job
                }}
                
                $result | ConvertTo-Json -Depth 7
            }} catch {{
                $errorResult = @{{
                    'Success' = $false
                    'Error' = $_.Exception.Message
                    'ErrorType' = $_.Exception.GetType().Name
                }}
                $errorResult | ConvertTo-Json -Depth 3
            }}
            """
        elif input_object:
            script = f"""
            try {{
                $inputObj = '{input_object}' | ConvertFrom-Json
                $job = Get-AzMigrateLocalJob -InputObject $inputObj
                
                $result = @{{
                    'Success' = $true
                    'InputObject' = $inputObj
                    'Job' = $job
                }}
                
                $result | ConvertTo-Json -Depth 7
            }} catch {{
                $errorResult = @{{
                    'Success' = $false
                    'Error' = $_.Exception.Message
                    'ErrorType' = $_.Exception.GetType().Name
                }}
                $errorResult | ConvertTo-Json -Depth 3
            }}
            """
        else:
            # List all jobs in the project
            script = f"""
            try {{
                $jobs = Get-AzMigrateLocalJob `
                    -ProjectName '{project_name}' `
                    -ResourceGroupName '{resource_group_name}'
                
                $result = @{{
                    'Success' = $true
                    'ProjectName' = '{project_name}'
                    'ResourceGroupName' = '{resource_group_name}'
                    'Jobs' = $jobs
                }}
                
                $result | ConvertTo-Json -Depth 7
            }} catch {{
                $errorResult = @{{
                    'Success' = $false
                    'Error' = $_.Exception.Message
                    'ErrorType' = $_.Exception.GetType().Name
                }}
                $errorResult | ConvertTo-Json -Depth 3
            }}
            """
        
        result = ps_executor.execute_script(script)
        
        if result.get('returncode') == 0:
            output = result.get('stdout', '').strip()
            if output:
                try:
                    parsed_result = json.loads(output)
                    if parsed_result.get('Success'):
                        logger.info("Successfully retrieved Azure Local job(s)")
                        return parsed_result
                    else:
                        raise CLIError(f"Failed to get job: {parsed_result.get('Error', 'Unknown error')}")
                except json.JSONDecodeError:
                    logger.warning("Could not parse PowerShell output as JSON")
                    return {"Success": True, "Output": output}
        
        error_msg = result.get('stderr', 'Unknown PowerShell error')
        raise CLIError(f"PowerShell execution failed: {error_msg}")
        
    except Exception as e:
        logger.error(f"Failed to get Azure Local job: {str(e)}")
        raise CLIError(f"Failed to get Azure Local job: {str(e)}")

def new_azure_local_server_replication_with_mappings(cmd, resource_group_name, project_name, 
                                                    discovered_machine_id, target_storage_path_id,
                                                    target_resource_group_id, target_vm_name,
                                                    disk_mappings=None, nic_mappings=None,
                                                    source_appliance_name=None, target_appliance_name=None):
    """Create Azure Local server replication with disk and NIC mappings (enhanced New-AzMigrateLocalServerReplication)."""
    try:
        ps_executor = get_powershell_executor()
        if not ps_executor:
            raise CLIError("PowerShell is not available. Please install PowerShell Core.")
        
        # Build the New-AzMigrateLocalServerReplication command with mappings
        if disk_mappings and nic_mappings:
            # Convert mappings to PowerShell objects
            disk_mappings_json = json.dumps(disk_mappings) if isinstance(disk_mappings, (list, dict)) else str(disk_mappings)
            nic_mappings_json = json.dumps(nic_mappings) if isinstance(nic_mappings, (list, dict)) else str(nic_mappings)
            
            script = f"""
            try {{
                # Parse disk and NIC mappings
                $diskMappings = '{disk_mappings_json}' | ConvertFrom-Json
                $nicMappings = '{nic_mappings_json}' | ConvertFrom-Json
                
                $replicationJob = New-AzMigrateLocalServerReplication `
                    -MachineId '{discovered_machine_id}' `
                    -TargetStoragePathId '{target_storage_path_id}' `
                    -TargetResourceGroupId '{target_resource_group_id}' `
                    -TargetVMName '{target_vm_name}' `
                    -DiskToInclude $diskMappings `
                    -NicToInclude $nicMappings"""
            
            if source_appliance_name:
                script += f" `\n                    -SourceApplianceName '{source_appliance_name}'"
            if target_appliance_name:
                script += f" `\n                    -TargetApplianceName '{target_appliance_name}'"
            
            script += f"""
                
                $result = @{{
                    'Success' = $true
                    'MachineId' = '{discovered_machine_id}'
                    'TargetVMName' = '{target_vm_name}'
                    'ReplicationJob' = $replicationJob
                }}
                
                $result | ConvertTo-Json -Depth 7
            }} catch {{
                $errorResult = @{{
                    'Success' = $false
                    'Error' = $_.Exception.Message
                    'ErrorType' = $_.Exception.GetType().Name
                }}
                $errorResult | ConvertTo-Json -Depth 3
            }}
            """
        else:
            # Basic replication without custom mappings
            script = f"""
            try {{
                $replicationJob = New-AzMigrateLocalServerReplication `
                    -MachineId '{discovered_machine_id}' `
                    -TargetStoragePathId '{target_storage_path_id}' `
                    -TargetResourceGroupId '{target_resource_group_id}' `
                    -TargetVMName '{target_vm_name}'"""
            
            if source_appliance_name:
                script += f" `\n                    -SourceApplianceName '{source_appliance_name}'"
            if target_appliance_name:
                script += f" `\n                    -TargetApplianceName '{target_appliance_name}'"
            
            script += f"""
                
                $result = @{{
                    'Success' = $true
                    'MachineId' = '{discovered_machine_id}'
                    'TargetVMName' = '{target_vm_name}'
                    'ReplicationJob' = $replicationJob
                }}
                
                $result | ConvertTo-Json -Depth 7
            }} catch {{
                $errorResult = @{{
                    'Success' = $false
                    'Error' = $_.Exception.Message
                    'ErrorType' = $_.Exception.GetType().Name
                }}
                $errorResult | ConvertTo-Json -Depth 3
            }}
            """
        
        result = ps_executor.execute_script(script)
        
        if result.get('returncode') == 0:
            output = result.get('stdout', '').strip()
            if output:
                try:
                    parsed_result = json.loads(output)
                    if parsed_result.get('Success'):
                        logger.info("Successfully created Azure Local server replication with mappings")
                        return parsed_result
                    else:
                        raise CLIError(f"Failed to create replication: {parsed_result.get('Error', 'Unknown error')}")
                except json.JSONDecodeError:
                    logger.warning("Could not parse PowerShell output as JSON")
                    return {"Success": True, "Output": output}
        
        error_msg = result.get('stderr', 'Unknown PowerShell error')
        raise CLIError(f"PowerShell execution failed: {error_msg}")
        
    except Exception as e:
        logger.error(f"Failed to create Azure Local server replication with mappings: {str(e)}")
        raise CLIError(f"Failed to create Azure Local server replication with mappings: {str(e)}")

def get_azure_context(cmd):
    """
    Get the current Azure context using PowerShell Get-AzContext.
    Azure CLI equivalent to Get-AzContext PowerShell cmdlet.
    """
    ps_executor = get_powershell_executor()
    
    get_context_script = """
try { 
    $currentContext = Get-AzContext -ErrorAction SilentlyContinue
    if (-not $currentContext) {
        Write-Host "Not currently connected to Azure"
        return @{
            IsAuthenticated = $false
            Message = "No Azure context found"
        }
    }
    
    # Return context information
    $contextInfo = @{
        IsAuthenticated = $true
        SubscriptionName = $currentContext.Subscription.Name
        SubscriptionId = $currentContext.Subscription.Id
        TenantId = $currentContext.Tenant.Id
        Account = $currentContext.Account.Id
        Environment = $currentContext.Environment.Name
    }
    
    Write-Host "Current Azure Context:"
    Write-Host "  Subscription: $($contextInfo.SubscriptionName) ($($contextInfo.SubscriptionId))"
    Write-Host "  Tenant: $($contextInfo.TenantId)"
    Write-Host "  Account: $($contextInfo.Account)"
    Write-Host "  Environment: $($contextInfo.Environment)"
    
    return $contextInfo
} catch {
    Write-Error "Failed to get Azure context: $($_.Exception.Message)"
    return @{
        IsAuthenticated = $false
        Message = "Error retrieving Azure context: $($_.Exception.Message)"
    }
}"""

    try:
        result = ps_executor.execute_ps_script(get_context_script)
        
        # Parse result if it's JSON
        if isinstance(result, str):
            try:
                import json
                parsed_result = json.loads(result)
                return parsed_result
            except json.JSONDecodeError:
                # Return raw result if not JSON
                return {
                    'Status': 'Success',
                    'Message': 'Azure context retrieved',
                    'Result': result
                }
        
        return result
    except Exception as e:
        return {
            'IsAuthenticated': False,
            'Message': f'Failed to get Azure context: {str(e)}'
        }
