# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import run_cmd
import platform
import json
from knack.util import CLIError
from knack.log import get_logger
import select
import sys
import threading
import queue
import time
import subprocess

logger = get_logger(__name__)


class PowerShellExecutor:
    """Cross-platform PowerShell command executor for migration operations."""
    
    def __init__(self):
        self.platform = platform.system().lower()
        try:
            self.powershell_cmd = self._get_powershell_command()
        except CLIError:
            self.powershell_cmd = None
    
    def _get_powershell_command(self):
        """Get the appropriate PowerShell command for the current platform."""
        
        if self.platform == 'windows':
            for cmd in ['powershell.exe', 'powershell']:
                try:
                    result = run_cmd([cmd, '-Command', '$PSVersionTable.PSVersion.ToString()'], 
                                    capture_output=True, timeout=10)
                    if result.returncode == 0:
                        stdout_str = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
                        logger.info(f'Found Windows PowerShell: {stdout_str.strip()}')
                        return cmd
                except Exception:
                    logger.debug(f'PowerShell command {cmd} not found')
        else:
            for cmd in ['pwsh']:
                try:
                    result = run_cmd([cmd, '-Command', '$PSVersionTable.PSVersion.ToString()'], 
                                    capture_output=True, timeout=10)
                    if result.returncode == 0:
                        stdout_str = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
                        logger.info(f'Found PowerShell Core: {stdout_str.strip()}')
                        return cmd
                except Exception:
                    logger.debug(f'PowerShell command {cmd} not found')
        
        install_guidance = {
            'windows': 'Install PowerShell Core from https://github.com/PowerShell/PowerShell or ensure Windows PowerShell is available.',
            'linux': 'Install PowerShell Core using your package manager:\n' +
                    '  Ubuntu/Debian: sudo apt update && sudo apt install -y powershell\n' +
                    '  CentOS/RHEL: sudo yum install -y powershell\n' +
                    '  Or download from: https://github.com/PowerShell/PowerShell',
            'darwin': 'Install PowerShell Core using Homebrew:\n' +
                     '  brew install powershell\n' +
                     '  Or download from: https://github.com/PowerShell/PowerShell'
        }
        
        guidance = install_guidance.get(self.platform, install_guidance['linux'])
        raise CLIError(f'PowerShell is not available on this {self.platform} system.\n{guidance}')
    
    def check_powershell_availability(self):
        """Check if PowerShell is available and return (is_available, command)."""
        if self.powershell_cmd:
            return True, self.powershell_cmd
        else:
            return False, None
    
    def execute_script(self, script_content, parameters=None):
        """Execute a PowerShell script with optional parameters."""
        try:
            cmd = [self.powershell_cmd, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command']
            
            if parameters:
                param_string = ' '.join([f'-{k} "{v}"' for k, v in parameters.items()])
                script_with_params = f'{script_content} {param_string}'
            else:
                script_with_params = script_content
            
            cmd.append(script_with_params)
            
            logger.debug(f'Executing PowerShell command: {" ".join(cmd)}')
            
            result = run_cmd(
                cmd,
                capture_output=True,
                timeout=300
            )
            
            if result.returncode != 0:
                error_msg = f'PowerShell command failed with exit code {result.returncode}'
                if result.stderr:
                    error_msg += f': {result.stderr}'
                raise CLIError(error_msg)
            
            return {
                'stdout': result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout,
                'stderr': result.stderr.decode('utf-8') if isinstance(result.stderr, bytes) else result.stderr,
                'returncode': result.returncode
            }
            
        except Exception as e:
            if 'timeout' in str(e).lower():
                raise CLIError('PowerShell command timed out after 5 minutes')
            raise CLIError(f'Failed to execute PowerShell command: {str(e)}')
    
    def execute_script_interactive(self, script_content):
        """Execute a PowerShell script with real-time interactive output.
        
        Note: This method uses subprocess.Popen directly for real-time output streaming,
        which is an approved exception to the CLI subprocess guidelines for interactive scenarios.
        """        
        try:
            if not self.powershell_cmd:
                raise CLIError('PowerShell not available')
            
            cmd = [self.powershell_cmd, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script_content]
            
            logger.debug(f'Executing interactive PowerShell command: {" ".join(cmd)}')
           
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                universal_newlines=True
            )
            
            output_lines = []
            error_lines = []
            
            if platform.system().lower() == 'windows':
                stdout_queue = queue.Queue()
                stderr_queue = queue.Queue()
                
                def read_stdout():
                    for line in iter(process.stdout.readline, ''):
                        stdout_queue.put(('stdout', line))
                    stdout_queue.put(('stdout', None))
                
                def read_stderr():
                    for line in iter(process.stderr.readline, ''):
                        stderr_queue.put(('stderr', line))
                    stderr_queue.put(('stderr', None))
                
                stdout_thread = threading.Thread(target=read_stdout)
                stderr_thread = threading.Thread(target=read_stderr)
                
                stdout_thread.daemon = True
                stderr_thread.daemon = True
                
                stdout_thread.start()
                stderr_thread.start()
                
                stdout_done = False
                stderr_done = False
                
                while not (stdout_done and stderr_done):
                    try:
                        _, line = stdout_queue.get_nowait()
                        if line is None:
                            stdout_done = True
                        else:
                            line = line.rstrip('\n\r')
                            if line:
                                output_lines.append(line)
                                print(line)
                                sys.stdout.flush()
                    except queue.Empty:
                        pass
                    
                    try:
                        _, line = stderr_queue.get_nowait()
                        if line is None:
                            stderr_done = True
                        else:
                            line = line.rstrip('\n\r')
                            if line:
                                error_lines.append(line)
                                print(f"ERROR: {line}")
                                sys.stdout.flush()
                    except queue.Empty:
                        pass
                    
                    time.sleep(0.01)
                    
                    if process.poll() is not None and stdout_queue.empty() and stderr_queue.empty():
                        break
            
            else:
                while True:
                    reads = [process.stdout.fileno(), process.stderr.fileno()]
                    ret = select.select(reads, [], [])
                    
                    for fd in ret[0]:
                        if fd == process.stdout.fileno():
                            line = process.stdout.readline()
                            if line:
                                line = line.rstrip('\n\r')
                                if line:
                                    output_lines.append(line)
                                    print(line)
                                    sys.stdout.flush()
                        elif fd == process.stderr.fileno():
                            line = process.stderr.readline()
                            if line:
                                line = line.rstrip('\n\r')
                                if line:
                                    error_lines.append(line)
                                    print(f"ERROR: {line}")
                                    sys.stdout.flush()
                    
                    if process.poll() is not None:
                        break
            
            return_code = process.wait()
            
            return {
                'stdout': '\n'.join(output_lines),
                'stderr': '\n'.join(error_lines),
                'returncode': return_code
            }
            
        except Exception as e:
            print(f"ERROR executing PowerShell: {str(e)}")
            return {
                'stdout': '',
                'stderr': str(e),
                'returncode': 1
            }
    
    def execute_migration_cmdlet(self, cmdlet, parameters=None):
        """Execute a migration-specific PowerShell cmdlet."""
        
        import_script = """
        try {
            Import-Module Microsoft.PowerShell.Management -Force
            Import-Module Microsoft.PowerShell.Utility -Force
        } catch {
            Write-Warning "Some PowerShell modules may not be available"
        }
        """
        
        if parameters:
            param_string = ' '.join([f'-{k} "{v}"' for k, v in parameters.items()])
            full_script = f'{import_script}; {cmdlet} {param_string}'
        else:
            full_script = f'{import_script}; {cmdlet}'
        
        return self.execute_script(full_script)
    
    def check_migration_prerequisites(self):
        """Check if migration prerequisites are met."""
        
        check_script = """
        $result = @{
            PowerShellVersion = $PSVersionTable.PSVersion.ToString()
            Platform = $PSVersionTable.Platform
            OS = $PSVersionTable.OS
            Edition = $PSVersionTable.PSEdition
            IsAdmin = $false
        }
        
        # Check if running as administrator (Windows only)
        if ($PSVersionTable.Platform -eq 'Win32NT') {
            $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
            $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
            $result.IsAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        }
        
        $result | ConvertTo-Json
        """
        
        try:
            result = self.execute_script(check_script)
            return json.loads(result['stdout'])
        except Exception as e:
            logger.warning(f'Failed to check prerequisites: {str(e)}')
            return {
                'PowerShellVersion': 'Unknown',
                'Platform': self.platform,
                'IsAdmin': False
            }
    
    def check_powershell_available(self):
        """Check if PowerShell is available on the system."""
        
        try:
            result = run_cmd(['pwsh', '-Command', 'echo "test"'], 
                            capture_output=True, timeout=10)
            if result.returncode == 0:
                return True, 'pwsh'
        except Exception:
            pass
        
        try:
            result = run_cmd(['powershell.exe', '-Command', 'echo "test"'], 
                            capture_output=True, timeout=10)
            if result.returncode == 0:
                return True, 'powershell.exe'
        except Exception:
            pass
        
        if platform.system() == "Windows":
            try:
                result = run_cmd(['powershell', '-Command', 'echo "test"'], 
                                capture_output=True, timeout=10)
                if result.returncode == 0:
                    return True, 'powershell'
            except Exception:
                pass
            
        return False, None
    
    def execute_azure_authenticated_script(self, script, parameters=None, subscription_id=None):
        """Execute a PowerShell script with Azure authentication."""
        
        auth_prefix = """
        try {
            $context = Get-AzContext
            if (-not $context) {
                Write-Host "No Azure context found. Please run Connect-AzAccount first."
                throw "Azure authentication required"
            }
        } catch {
            Write-Host "Azure PowerShell module not available or not authenticated."
            Write-Host "Please ensure Az.Migrate module is installed and you are authenticated."
            throw "Azure authentication required"
        }
        """
        
        if subscription_id:
            auth_prefix += f"""
        try {{
            Set-AzContext -SubscriptionId "{subscription_id}"
            Write-Host "Subscription context set to: {subscription_id}"
        }} catch {{
            Write-Host "Failed to set subscription context to: {subscription_id}"
            throw "Invalid subscription ID"
        }}
        """
        
        full_script = auth_prefix + "\n" + script
        
        return self.execute_script(full_script, parameters)
    
    def check_azure_authentication(self):
        """Check if Azure authentication is available."""
        
        auth_check_script = """
        try {
            $azAccountsModule = Get-Module -ListAvailable -Name Az.Accounts -ErrorAction SilentlyContinue
            if (-not $azAccountsModule) {
                $result = @{
                    'IsAuthenticated' = $false
                    'ModuleAvailable' = $false
                    'Error' = 'Az.Accounts module not found. Please install Azure PowerShell modules.'
                    'Platform' = $PSVersionTable.Platform
                    'PSVersion' = $PSVersionTable.PSVersion.ToString()
                }
                $result | ConvertTo-Json -Depth 3
                return
            }
            
            $azMigrateModule = Get-Module -ListAvailable -Name Az.Migrate -ErrorAction SilentlyContinue
            if (-not $azMigrateModule) {
                $result = @{
                    'IsAuthenticated' = $false
                    'ModuleAvailable' = $false
                    'Error' = 'Az.Migrate module not found. Please install: Install-Module -Name Az.Migrate'
                    'Platform' = $PSVersionTable.Platform
                    'PSVersion' = $PSVersionTable.PSVersion.ToString()
                }
                $result | ConvertTo-Json -Depth 3
                return
            }
            
            $context = Get-AzContext -ErrorAction SilentlyContinue
            if (-not $context) {
                $result = @{
                    'IsAuthenticated' = $false
                    'ModuleAvailable' = $true
                    'Error' = 'Not authenticated to Azure. Please run Connect-AzAccount.'
                    'Platform' = $PSVersionTable.Platform
                    'PSVersion' = $PSVersionTable.PSVersion.ToString()
                }
                $result | ConvertTo-Json -Depth 3
                return
            }
            
            $result = @{
                'IsAuthenticated' = $true
                'ModuleAvailable' = $true
                'SubscriptionId' = $context.Subscription.Id
                'AccountId' = $context.Account.Id
                'TenantId' = $context.Tenant.Id
                'Platform' = $PSVersionTable.Platform
                'PSVersion' = $PSVersionTable.PSVersion.ToString()
            }
            $result | ConvertTo-Json -Depth 3
        } catch {
            $result = @{
                'IsAuthenticated' = $false
                'ModuleAvailable' = $false
                'Error' = $_.Exception.Message
                'Platform' = $PSVersionTable.Platform
                'PSVersion' = $PSVersionTable.PSVersion.ToString()
            }
            $result | ConvertTo-Json -Depth 3
        }
        """
        
        try:
            result = self.execute_script(auth_check_script)
            json_output = result.get('stdout', '')
            
            # Ensure json_output is a string, not bytes
            if isinstance(json_output, bytes):
                json_output = json_output.decode('utf-8')
            
            json_output = json_output.strip()
            
            if not json_output:
                return {
                    'IsAuthenticated': False,
                    'ModuleAvailable': False,
                    'Error': 'No output from authentication check',
                    'Platform': self.platform,
                    'PSVersion': 'Unknown'
                }
            
            json_start = json_output.find('{')
            json_end = json_output.rfind('}')
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_content = json_output[json_start:json_end + 1]
                
                if isinstance(json_content, bytes):
                    json_content = json_content.decode('utf-8')
                
                try:
                    auth_status = json.loads(json_content)
                    return auth_status
                except json.JSONDecodeError as je:
                    logger.debug(f'JSON decode error: {str(je)}')
                    logger.debug(f'JSON content: {json_content}')
                    return {
                        'IsAuthenticated': False,
                        'ModuleAvailable': False,
                        'Error': f'Failed to parse authentication response: {str(je)}',
                        'Platform': self.platform,
                        'PSVersion': 'Unknown',
                        'RawOutput': json_output
                    }
            else:
                return {
                    'IsAuthenticated': False,
                    'ModuleAvailable': False,
                    'Error': 'No valid JSON found in authentication response',
                    'Platform': self.platform,
                    'PSVersion': 'Unknown',
                    'RawOutput': json_output
                }
                
        except Exception as e:
            logger.debug(f'Authentication check error: {str(e)}')
            return {
                'IsAuthenticated': False,
                'ModuleAvailable': False,
                'Error': f'Failed to check authentication: {str(e)}',
                'Platform': self.platform,
                'PSVersion': 'Unknown'
            }

    def connect_azure_account(self, tenant_id=None, subscription_id=None, device_code=False, service_principal=None):
        """Execute Connect-AzAccount PowerShell command with cross-platform support."""        
        is_available, _ = self.check_powershell_availability()
        if not is_available:
            return {
                'Success': False,
                'Error': f'PowerShell not available on this platform ({platform.system()}). Please install PowerShell Core for cross-platform support.'
            }
        
        if not service_principal and not device_code and not tenant_id:
            result = self.interactive_connect_azure()
            if result['success']:
                return {'Success': True, 'Output': result.get('output', '')}
            else:
                return {'Success': False, 'Error': result.get('error', 'Authentication failed')}
        
        connect_cmd = "Connect-AzAccount"
        
        if device_code:
            connect_cmd += " -UseDeviceAuthentication"
        
        if tenant_id:
            connect_cmd += f" -TenantId '{tenant_id}'"
        
        if service_principal:
            connect_cmd += f" -ServicePrincipal -Credential (New-Object System.Management.Automation.PSCredential('{service_principal['app_id']}', (ConvertTo-SecureString '{service_principal['secret']}' -AsPlainText -Force)))"
            if tenant_id:
                connect_cmd += f" -TenantId '{tenant_id}'"
        
        if not service_principal and not device_code:
            return self._execute_interactive_connect(connect_cmd, subscription_id)
        else:
            return self._execute_non_interactive_connect(connect_cmd, subscription_id)
    
    def _execute_interactive_connect(self, connect_cmd, subscription_id=None):
        """Execute Connect-AzAccount interactively, showing real-time output.
        
        Note: This method uses subprocess.Popen directly for real-time output streaming,
        which is an approved exception to the CLI subprocess guidelines for interactive scenarios.
        """
        try:
            import subprocess
            import sys
            
            cmd = [self.powershell_cmd, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', connect_cmd]
           
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    output_lines.append(output.strip())
                    print(output.strip())
                    sys.stdout.flush()
            
            return_code = process.poll()
                        
            if return_code == 0:
                context_result = self.get_azure_context()
                if context_result.get('Success') and context_result.get('IsAuthenticated'):
                    result = {
                        'Success': True,
                        'AccountId': context_result.get('AccountId'),
                        'SubscriptionId': context_result.get('SubscriptionId'),
                        'SubscriptionName': context_result.get('SubscriptionName'),
                        'TenantId': context_result.get('TenantId'),
                        'Environment': context_result.get('Environment')
                    }
                    
                    if subscription_id:
                        context_set = self.set_azure_context(subscription_id=subscription_id)
                        if context_set.get('Success'):
                            result['SubscriptionId'] = subscription_id
                            result['SubscriptionContextSet'] = True
                        else:
                            result['SubscriptionContextError'] = context_set.get('Error')
                    
                    return result
                else:
                    return {
                        'Success': False,
                        'Error': 'Authentication completed but failed to get Azure context'
                    }
            else:
                return {
                    'Success': False,
                    'Error': f'Connect-AzAccount failed with exit code {return_code}',
                    'Output': '\n'.join(output_lines)
                }
                
        except Exception as e:
            return {
                'Success': False,
                'Error': f'Failed to execute Connect-AzAccount interactively: {str(e)}'
            }
    
    def _execute_non_interactive_connect(self, connect_cmd, subscription_id=None):
        """Execute Connect-AzAccount non-interactively (service principal or device code)."""
        
        connect_script = f"""
        try {{
            $result = {connect_cmd}
            
            $context = Get-AzContext
            if ($context) {{
                $connectionResult = @{{
                    'Success' = $true
                    'AccountId' = $context.Account.Id
                    'SubscriptionId' = $context.Subscription.Id
                    'SubscriptionName' = $context.Subscription.Name
                    'TenantId' = $context.Tenant.Id
                    'Environment' = $context.Environment.Name
                }}
            }} else {{
                $connectionResult = @{{
                    'Success' = $false
                    'Error' = 'Failed to establish Azure context after authentication'
                }}
            }}
            
            $connectionResult | ConvertTo-Json -Depth 3
        }} catch {{
            $errorResult = @{{
                'Success' = $false
                'Error' = $_.Exception.Message
                'ErrorType' = $_.Exception.GetType().Name
            }}
            $errorResult | ConvertTo-Json -Depth 3
        }}
        """
        
        if subscription_id:
            connect_script += f"""
            if ($connectionResult.Success) {{
                try {{
                    Set-AzContext -SubscriptionId '{subscription_id}'
                    $connectionResult.SubscriptionId = '{subscription_id}'
                    $connectionResult.SubscriptionContextSet = $true
                }} catch {{
                    $connectionResult.SubscriptionContextError = $_.Exception.Message
                }}
                $connectionResult | ConvertTo-Json -Depth 3
            }}
            """
        
        try:
            result = self.execute_script(connect_script)
            
            stdout_content = result.get('stdout', '').strip()
            json_start = stdout_content.find('{')
            json_end = stdout_content.rfind('}')
            
            if json_start != -1 and json_end != -1:
                json_content = stdout_content[json_start:json_end + 1]
                auth_result = json.loads(json_content)
                return auth_result
            else:
                return {
                    'Success': False,
                    'Error': 'No valid JSON response from Connect-AzAccount',
                    'RawOutput': stdout_content
                }
                
        except Exception as e:
            return {
                'Success': False,
                'Error': f'Failed to execute Connect-AzAccount: {str(e)}'
            }

    def disconnect_azure_account(self):
        """Execute Disconnect-AzAccount PowerShell command."""
        
        disconnect_script = """
        try {
            Disconnect-AzAccount -Confirm:$false
            
            # Verify disconnection
            $context = Get-AzContext
            if (-not $context) {
                $result = @{
                    'Success' = $true
                    'Message' = 'Successfully disconnected from Azure'
                }
            } else {
                $result = @{
                    'Success' = $false
                    'Error' = 'Azure context still exists after disconnect attempt'
                }
            }
            
            $result | ConvertTo-Json -Depth 3
        } catch {
            $errorResult = @{
                'Success' = $false
                'Error' = $_.Exception.Message
            }
            $errorResult | ConvertTo-Json -Depth 3
        }
        """
        
        try:
            result = self.execute_script(disconnect_script)
            
            stdout_content = result.get('stdout', '').strip()
            
            json_start = stdout_content.find('{')
            json_end = stdout_content.rfind('}')
            
            if json_start != -1 and json_end != -1:
                json_content = stdout_content[json_start:json_end + 1]
                try:
                    disconnect_result = json.loads(json_content)
                    return disconnect_result
                except json.JSONDecodeError:
                    if result.get('stderr', '').strip():
                        return {
                            'Success': False,
                            'Error': f'Disconnect command failed: {result.get("stderr")}'
                        }
                    else:
                        return {
                            'Success': True,
                            'Message': 'Successfully disconnected from Azure'
                        }
            else:
                if result.get('stderr', '').strip():
                    return {
                        'Success': False,
                        'Error': f'Disconnect command failed: {result.get("stderr")}'
                    }
                else:
                    return {
                        'Success': True,
                        'Message': 'Successfully disconnected from Azure'
                    }
                
        except Exception as e:
            return {
                'Success': False,
                'Error': f'Failed to execute Disconnect-AzAccount: {str(e)}'
            }

    def set_azure_context(self, subscription_id=None, tenant_id=None):
        """Execute Set-AzContext PowerShell command."""
        
        if not subscription_id and not tenant_id:
            return {
                'Success': False,
                'Error': 'Either subscription_id or tenant_id must be provided'
            }
        
        context_cmd = "Set-AzContext"
        
        if subscription_id:
            context_cmd += f" -SubscriptionId '{subscription_id}'"
        
        if tenant_id:
            context_cmd += f" -TenantId '{tenant_id}'"
        
        context_script = f"""
try {{
    $context = {context_cmd}
    
    if ($context) {{
        $contextResult = @{{
            'Success' = $true
            'SubscriptionId' = $context.Subscription.Id
            'SubscriptionName' = $context.Subscription.Name
            'TenantId' = $context.Tenant.Id
            'AccountId' = $context.Account.Id
        }}
    }} else {{
        $contextResult = @{{
            'Success' = $false
            'Error' = 'Failed to set Azure context'
        }}
    }}
    
    $contextResult | ConvertTo-Json -Depth 3
}} catch {{
    $errorResult = @{{
        'Success' = $false
        'Error' = $_.Exception.Message
    }}
    $errorResult | ConvertTo-Json -Depth 3
}}
"""
        
        try:
            result = self.execute_script(context_script)
            
            stdout_content = result.get('stdout', '').strip()
            json_start = stdout_content.find('{')
            json_end = stdout_content.rfind('}')
            
            if json_start != -1 and json_end != -1:
                json_content = stdout_content[json_start:json_end + 1]
                context_result = json.loads(json_content)
                return context_result
            else:
                return {
                    'Success': False,
                    'Error': 'No valid JSON response from Set-AzContext',
                    'RawOutput': stdout_content
                }
                
        except Exception as e:
            return {
                'Success': False,
                'Error': f'Failed to execute Set-AzContext: {str(e)}'
            }

    def get_azure_context(self):
        """Execute Get-AzContext PowerShell command."""
        
        context_script = """
try {
    $context = Get-AzContext
    
    if ($context) {
        $contextInfo = @{
            'Success' = $true
            'IsAuthenticated' = $true
            'SubscriptionId' = $context.Subscription.Id
            'SubscriptionName' = $context.Subscription.Name
            'TenantId' = $context.Tenant.Id
            'AccountId' = $context.Account.Id
            'Environment' = $context.Environment.Name
        }
    } else {
        $contextInfo = @{
            'Success' = $true
            'IsAuthenticated' = $false
            'Message' = 'No Azure context found. Please run Connect-AzAccount.'
        }
    }
    
    $contextInfo | ConvertTo-Json -Depth 3
} catch {
    $errorResult = @{
        'Success' = $false
        'Error' = $_.Exception.Message
    }
    $errorResult | ConvertTo-Json -Depth 3
}
"""
        
        try:
            result = self.execute_script(context_script)
            
            stdout_content = result.get('stdout', '').strip()
            json_start = stdout_content.find('{')
            json_end = stdout_content.rfind('}')
            
            if json_start != -1 and json_end != -1:
                json_content = stdout_content[json_start:json_end + 1]
                context_result = json.loads(json_content)
                return context_result
            else:
                return {
                    'Success': False,
                    'Error': 'No valid JSON response from Get-AzContext',
                    'RawOutput': stdout_content
                }
                
        except Exception as e:
            return {
                'Success': False,
                'Error': f'Failed to execute Get-AzContext: {str(e)}'
            }
    
    def interactive_connect_azure(self):
        """Execute Connect-AzAccount interactively with real-time output for cross-platform compatibility."""

        current_platform = platform.system().lower()
        module_check_script = """
        $platform = $PSVersionTable.Platform
        $psVersion = $PSVersionTable.PSVersion.ToString()
        
        # Check if running on PowerShell Core vs Windows PowerShell
        $isPowerShellCore = $PSVersionTable.PSEdition -eq 'Core'
        
        $azAccountsModule = Get-Module -ListAvailable -Name Az.Accounts -ErrorAction SilentlyContinue
        $azMigrateModule = Get-Module -ListAvailable -Name Az.Migrate -ErrorAction SilentlyContinue
        
        $result = @{
            'Platform' = $platform
            'PSVersion' = $psVersion
            'PSEdition' = $PSVersionTable.PSEdition
            'IsPowerShellCore' = $isPowerShellCore
            'AzAccountsAvailable' = [bool]$azAccountsModule
            'AzMigrateAvailable' = [bool]$azMigrateModule
        }
        
        if (-not $azAccountsModule) {
            $result['InstallationInstructions'] = @{
                'Message' = 'Azure PowerShell modules not found. Installation required:'
                'Windows' = 'Install-Module -Name Az -Force -AllowClobber'
                'Linux' = 'Install-Module -Name Az -Force -AllowClobber (after installing PowerShell Core)'
                'macOS' = 'Install-Module -Name Az -Force -AllowClobber (after installing PowerShell Core)'
                'PowerShellCoreInstall' = @{
                    'Ubuntu' = 'curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add - && echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -rs)-prod $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/microsoft.list && sudo apt update && sudo apt install -y powershell'
                    'CentOS' = 'curl https://packages.microsoft.com/config/rhel/8/packages-microsoft-prod.rpm | sudo rpm -i - && sudo yum install -y powershell'
                    'macOS' = 'brew install --cask powershell'
                }
            }
        }
        
        $result | ConvertTo-Json -Depth 4
        """
        
        try:
            module_check = self.execute_script(module_check_script)
            json_output = module_check['stdout'].strip()
            json_start = json_output.find('{')
            json_end = json_output.rfind('}')
            if json_start != -1 and json_end != -1:
                json_content = json_output[json_start:json_end + 1]
                module_info = json.loads(json_content)
            else:
                module_info = {}
            
            print(f"PowerShell Platform: {module_info.get('Platform', 'Unknown')}")
            print(f"PowerShell Version: {module_info.get('PSVersion', 'Unknown')}")
            print(f"PowerShell Edition: {module_info.get('PSEdition', 'Unknown')}")
            
            if not module_info.get('AzAccountsAvailable', False):
                print("\nAzure PowerShell modules not found!")
                install_info = module_info.get('InstallationInstructions', {})
                print(f"\n{install_info.get('Message', 'Installation required')}")
                
                if current_platform == 'windows':
                    print(f"Windows: {install_info.get('Windows', 'Install-Module -Name Az')}")
                elif current_platform == 'linux':
                    print(f"Linux: {install_info.get('Linux', 'Install-Module -Name Az')}")
                    ps_install = install_info.get('PowerShellCoreInstall', {})
                    print(f"PowerShell Core (Ubuntu): {ps_install.get('Ubuntu', 'See Microsoft docs')}")
                    print(f"PowerShell Core (CentOS): {ps_install.get('CentOS', 'See Microsoft docs')}")
                elif current_platform == 'darwin':  # macOS
                    print(f"macOS: {install_info.get('macOS', 'Install-Module -Name Az')}")
                    ps_install = install_info.get('PowerShellCoreInstall', {})
                    print(f"PowerShell Core (macOS): {ps_install.get('macOS', 'brew install --cask powershell')}")
                
                print("\nAfter installing, run this command again to authenticate.")
                return {'success': False, 'error': 'Azure PowerShell modules not installed'}
            
            if not module_info.get('AzMigrateAvailable', False):
                print("\nAz.Migrate module not found. Installing...")
                install_script = "Install-Module -Name Az.Migrate -Force -AllowClobber"
                install_result = self.execute_script(install_script)
                if install_result['returncode'] != 0:
                    print(f"Failed to install Az.Migrate: {install_result['stderr']}")
                    return {'success': False, 'error': 'Failed to install Az.Migrate module'}
                print("Az.Migrate module installed successfully")
            
            connect_script = "Connect-AzAccount"
            
            print("\nStarting Azure authentication...")
            print("This will open a browser window for interactive authentication.")
            print("Please complete the sign-in process in your browser.")
            print("You may need to:")
            print("  1. Select the correct account if multiple accounts are available")
            print("  2. Choose the subscription you want to use")
            print("  3. Complete any multi-factor authentication if required")
            print("\nWaiting for authentication to complete...\n")
            
            result = self.execute_script_interactive(connect_script)
            
            if result['returncode'] == 0:
                print("\nAzure authentication successful!")
                
                try:
                    context_info = self.get_azure_context()
                    if context_info.get('Success') and context_info.get('IsAuthenticated'):
                        print(f"Authenticated as: {context_info.get('AccountId', 'Unknown')}")
                        print(f"Active subscription: {context_info.get('SubscriptionName', 'Unknown')}")
                        print(f"Tenant ID: {context_info.get('TenantId', 'Unknown')}")
                except:
                    pass
                
                return {'success': True, 'output': result['stdout']}
            else:
                error_output = result.get('stderr', 'Unknown error')
                print(f"\nAuthentication failed!")
                if error_output:
                    print(f"Error details: {error_output}")
                return {'success': False, 'error': error_output}
                
        except Exception as e:
            error_msg = f"Failed to execute authentication: {str(e)}"
            print(f"\n{error_msg}")
            return {'success': False, 'error': error_msg}

def get_powershell_executor():
    """Get a PowerShell executor instance."""
    return PowerShellExecutor()
