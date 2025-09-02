# Azure Migrate CLI Unit Tests with PowerShell Mocking

This directory contains comprehensive unit tests for the Azure Migrate CLI command module with a sophisticated PowerShell mocking system that prevents any real PowerShell execution during testing.

## 🚀 Key Features

- **Complete PowerShell Mocking**: No actual PowerShell commands are executed during tests
- **Realistic Cmdlet Responses**: Mock responses match real Azure PowerShell cmdlet outputs
- **Comprehensive Coverage**: Tests for all major CLI functions including discovery, replication, and migration
- **Cross-Platform**: Tests run on Windows, Linux, and macOS without requiring PowerShell installation

## 📁 File Structure

```
tests/latest/
├── powershell_mock.py              # PowerShell mocking system
├── test_config.py                  # Test configuration and base classes
├── test_migrate_custom.py          # Unit tests for custom functions
├── test_migrate_commands.py        # Command loading and registration tests
├── test_powershell_utils.py        # PowerShell utility tests
├── test_migrate_scenario.py        # End-to-end scenario tests
├── test_powershell_mocking_demo.py # Demonstration of mocking capabilities
└── run_mocked_tests.py             # Test runner with comprehensive mocking
```

## 🎯 PowerShell Cmdlet Mocking

### Pre-configured Cmdlet Responses

The mocking system includes realistic responses for common Azure PowerShell cmdlets:

| Cmdlet | Mock Response |
|--------|---------------|
| `$PSVersionTable.PSVersion.ToString()` | `7.3.4` |
| `Get-Module -ListAvailable Az.Migrate` | Module information with version 2.1.0 |
| `Connect-AzAccount` | Successful authentication with sample user |
| `Get-AzMigrateProject` | Sample project data |
| `Get-AzMigrateDiscoveredServer` | Sample server discovery data |
| `New-AzMigrateServerReplication` | Sample replication job creation |

### Adding Custom Cmdlet Responses

You can easily add responses for specific PowerShell cmdlets by modifying `powershell_mock.py`:

```python
# In PowerShellCmdletMocker.__init__()
self.cmdlet_responses.update({
    'Your-Custom-Cmdlet': {
        'stdout': 'Your custom response',
        'stderr': '',
        'exit_code': 0
    }
})
```

### Dynamic Response Patterns

For cmdlets with parameters, you can use regex patterns:

```python
# In PowerShellCmdletMocker.__init__()
self.pattern_responses.append((
    r'Get-AzMigrateServer.*-Name\s+["\']?([^"\']+)["\']?',
    self._mock_get_server_by_name
))
```

## 🧪 Writing Tests with PowerShell Mocking

### Basic Test Setup

```python
import unittest
from unittest.mock import patch
from powershell_mock import create_mock_powershell_executor

class MyTest(unittest.TestCase):
    def setUp(self):
        self.mock_ps = create_mock_powershell_executor()
        
        # Patch PowerShell executor
        self.ps_patcher = patch(
            'azure.cli.command_modules.migrate.custom.get_powershell_executor',
            return_value=self.mock_ps
        )
        self.ps_patcher.start()
    
    def tearDown(self):
        self.ps_patcher.stop()
    
    def test_my_function(self):
        # Your test code here - PowerShell calls will be mocked
        pass
```

### Testing Specific PowerShell Interactions

```python
def test_powershell_cmdlet_response(self):
    # Test that a specific cmdlet returns expected response
    result = self.mock_ps.execute_script('Get-Module -ListAvailable Az.Migrate')
    self.assertIn('Az.Migrate', result['stdout'])
    self.assertEqual(result['exit_code'], 0)
```

### Import-time Mocking

For modules that call PowerShell during import:

```python
# At the top of your test file
from unittest.mock import patch
from powershell_mock import create_mock_powershell_executor

with patch('azure.cli.command_modules.migrate.custom.get_powershell_executor') as mock_get_ps:
    mock_get_ps.return_value = create_mock_powershell_executor()
    from azure.cli.command_modules.migrate.custom import my_function
```

## 🏃‍♂️ Running Tests

### Option 1: Run All Tests with Mocking

```bash
python run_mocked_tests.py
```

This runner automatically applies comprehensive PowerShell mocking and runs all test modules.

### Option 2: Run Individual Test Files

```bash
python test_powershell_mocking_demo.py
python test_migrate_custom.py
```

### Option 3: Run with Standard unittest

```bash
python -m unittest discover -s . -p "test_*.py" -v
```

## 🔧 Customizing Mock Responses

### For Testing Error Scenarios

```python
# In your test method
def mock_failing_script(script_content, parameters=None):
    return {
        'stdout': '',
        'stderr': 'PowerShell module not found',
        'exit_code': 1
    }

self.mock_ps.execute_script.side_effect = mock_failing_script
```

### For Testing Interactive Scripts

```python
def test_interactive_script(self):
    # The mocking system automatically handles both execute_script and execute_script_interactive
    result = self.mock_ps.execute_script_interactive('Connect-AzAccount')
    self.assertIn('user@contoso.com', result['stdout'])
```

## 📊 Benefits of This Approach

1. **No External Dependencies**: Tests run without requiring PowerShell, Azure modules, or network access
2. **Fast Execution**: Mocked responses are instantaneous
3. **Predictable Results**: Tests always get the same responses, making them reliable
4. **Easy Debugging**: Mock responses can be customized for specific test scenarios
5. **Cross-Platform**: Tests run consistently across all operating systems

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all patches are applied before importing modules that use PowerShell
2. **Missing Responses**: Add custom responses to `powershell_mock.py` for new cmdlets
3. **Real PowerShell Execution**: Check that all `get_powershell_executor` calls are properly patched

### Debug Mode

To see what PowerShell commands are being called:

```python
# Add this to your test setup
import logging
logging.basicConfig(level=logging.DEBUG)

# The mock will log all PowerShell commands it receives
```

## 📝 Example: Testing Azure Authentication

```python
def test_azure_authentication_flow(self):
    \"\"\"Test the complete Azure authentication flow with mocked PowerShell.\"\"\"
    
    # Mock successful connection
    connect_result = self.mock_ps.execute_script('Connect-AzAccount')
    self.assertIn('user@contoso.com', connect_result['stdout'])
    
    # Mock context setting
    context_result = self.mock_ps.execute_script('Set-AzContext -SubscriptionId "test-subscription"')
    self.assertEqual(context_result['exit_code'], 0)
    
    # Mock disconnection
    disconnect_result = self.mock_ps.execute_script('Disconnect-AzAccount')
    self.assertIn('Disconnected', disconnect_result['stdout'])
```

This mocking system ensures your tests are fast, reliable, and don't require any external dependencies while still providing realistic testing of PowerShell integration scenarios.
