# Azure Migrate CLI Module Tests

This directory contains comprehensive unit tests, integration tests, and scenario tests for the Azure Migrate CLI module.

## Test Structure

```
tests/
├── run_tests.py                    # Test runner script
├── test_config.py                  # Test configuration and utilities
├── latest/
│   ├── test_migrate_custom.py      # Unit tests for custom functions
│   ├── test_powershell_utils.py    # Unit tests for PowerShell utilities
│   ├── test_migrate_commands.py    # Integration tests for command loading
│   └── test_migrate_scenario.py    # Scenario and end-to-end tests
└── README.md                       # This file
```

## Test Categories

### 1. Unit Tests (`test_migrate_custom.py`, `test_powershell_utils.py`)

Test individual functions and classes in isolation with mocked dependencies:

- **PowerShell Utils Tests**: Test the PowerShell executor functionality
- **Custom Function Tests**: Test all custom command implementations
- **Error Handling Tests**: Test error scenarios and edge cases
- **Authentication Tests**: Test Azure authentication workflows
- **Discovery Tests**: Test server discovery functionality
- **Replication Tests**: Test server replication operations
- **Local Migration Tests**: Test Azure Stack HCI migration commands

### 2. Integration Tests (`test_migrate_commands.py`)

Test command registration, parameter validation, and integration between components:

- **Command Loading Tests**: Verify all commands are properly registered
- **Parameter Validation Tests**: Test parameter parsing and validation
- **Command Integration Tests**: Test integration between command layers
- **Error Propagation Tests**: Test error handling across command stack

### 3. Scenario Tests (`test_migrate_scenario.py`)

End-to-end tests that simulate real user workflows:

- **Mock Scenario Tests**: Full workflow tests with mocked PowerShell
- **Parameter Validation Tests**: Test CLI parameter validation
- **Live Scenario Tests**: Tests against real Azure resources (when configured)

## Running Tests

### Prerequisites

1. **Python 3.7+** is required
2. **Azure CLI** must be installed and configured
3. **Required Python packages**: 
   - `azure-cli-core`
   - `azure-cli-testsdk`
   - `knack`
   - `unittest` (standard library)

### Quick Start

Run all tests:
```bash
cd tests
python run_tests.py
```

### Test Runner Options

```bash
# Run only unit tests
python run_tests.py --unit

# Run only integration tests  
python run_tests.py --integration

# Run only scenario tests
python run_tests.py --scenario

# Run with verbose output
python run_tests.py --verbose

# Generate code coverage report
python run_tests.py --coverage

# Run live tests (requires Azure authentication)
python run_tests.py --live

# Check prerequisites only
python run_tests.py --check-prereqs

# Show help
python run_tests.py --help
```

### Running Individual Test Files

You can also run individual test files directly:

```bash
# Run unit tests for custom functions
python -m unittest azure.cli.command_modules.migrate.tests.latest.test_migrate_custom

# Run PowerShell utility tests
python -m unittest azure.cli.command_modules.migrate.tests.latest.test_powershell_utils

# Run command integration tests
python -m unittest azure.cli.command_modules.migrate.tests.latest.test_migrate_commands

# Run scenario tests
python -m unittest azure.cli.command_modules.migrate.tests.latest.test_migrate_scenario
```

### Running Specific Test Classes or Methods

```bash
# Run specific test class
python -m unittest azure.cli.command_modules.migrate.tests.latest.test_migrate_custom.TestMigrateDiscoveryCommands

# Run specific test method
python -m unittest azure.cli.command_modules.migrate.tests.latest.test_migrate_custom.TestMigrateDiscoveryCommands.test_get_discovered_server_success
```

## Test Configuration

### Mock Configuration

Most tests use mocked PowerShell execution to avoid requiring actual PowerShell installation and Azure authentication. The mock configuration is handled in `test_config.py`.

### Environment Variables

For live tests, you can set these environment variables:

```bash
# Enable live testing
export AZURE_TEST_RUN_LIVE=true

# Azure authentication (if not using az login)
export AZURE_CLIENT_ID=your-service-principal-id
export AZURE_CLIENT_SECRET=your-service-principal-secret
export AZURE_TENANT_ID=your-tenant-id
export AZURE_SUBSCRIPTION_ID=your-subscription-id
```

### Live Testing Prerequisites

For live tests that interact with actual Azure resources:

1. **Azure Authentication**: Configure Azure CLI with `az login` or set service principal environment variables
2. **PowerShell**: Install PowerShell Core 7+ for cross-platform compatibility
3. **Azure PowerShell**: Install Az.Migrate module: `Install-Module -Name Az.Migrate`
4. **Permissions**: Ensure your account has appropriate permissions for Azure Migrate operations

## Test Coverage

Generate a code coverage report:

```bash
python run_tests.py --coverage
```

This will:
- Run all tests with coverage analysis
- Display a coverage report in the terminal
- Generate an HTML coverage report in `tests/coverage_html/`

## Writing New Tests

### Test Naming Conventions

- Test files: `test_<module_name>.py`
- Test classes: `Test<FeatureName>`
- Test methods: `test_<specific_functionality>`

### Using the Test Base Class

Extend `MigrateTestCase` from `test_config.py` for consistent test setup:

```python
from azure.cli.command_modules.migrate.tests.test_config import MigrateTestCase

class TestMyFeature(MigrateTestCase):
    def test_my_functionality(self):
        # Configure mock if needed
        self.configure_mock_executor(azure_authenticated=False)
        
        # Test your functionality
        result = my_function(self.cmd)
        
        # Assertions
        self.assertIn('expected', result)
        self.assert_powershell_called('check_azure_authentication')
```

### Mocking PowerShell Execution

For functions that use PowerShell, configure the mock executor:

```python
def test_with_custom_mock_response(self):
    custom_responses = {
        'Get-AzContext': {'stdout': '{"Account": "test@example.com"}', 'stderr': '', 'returncode': 0}
    }
    
    self.configure_mock_executor(
        powershell_available=True,
        azure_authenticated=True,
        script_responses=custom_responses
    )
    
    # Your test code here
```

## Continuous Integration

### GitHub Actions

Example workflow for running tests in CI:

```yaml
name: Azure Migrate CLI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.7, 3.8, 3.9, '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install azure-cli-core azure-cli-testsdk
    
    - name: Run tests
      run: |
        cd src/azure-cli/azure/cli/command_modules/migrate/tests
        python run_tests.py --coverage
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Local CI Simulation

You can simulate CI testing locally:

```bash
# Test on different Python versions (if you have them)
python3.7 run_tests.py
python3.8 run_tests.py
python3.9 run_tests.py

# Test with strict mode
python -Werror run_tests.py

# Test with coverage requirements
python run_tests.py --coverage
```

## Troubleshooting

### Common Issues

1. **ImportError**: Ensure you're running tests from the correct directory and have all dependencies installed
2. **PowerShell not found**: Install PowerShell Core or run only unit tests with mocked PowerShell
3. **Azure authentication**: For live tests, ensure you're authenticated with Azure CLI
4. **Test timeout**: Some live tests may timeout if Azure resources are slow to respond

### Debug Mode

For debugging test failures:

```bash
# Run with maximum verbosity
python run_tests.py --verbose

# Run a specific failing test
python -m unittest -v azure.cli.command_modules.migrate.tests.latest.test_migrate_custom.TestMigrateDiscoveryCommands.test_get_discovered_server_success

# Add print statements or use pdb debugger in test code
import pdb; pdb.set_trace()
```

### Mock Issues

If mocks aren't working as expected:

1. Check that `@patch` decorators are in the correct order (bottom to top execution)
2. Ensure mock return values match expected data structures
3. Verify that the correct module path is being patched
4. Use `self.mock_ps_executor.call_history` to see what methods were called

## Contributing

When adding new functionality to the Azure Migrate CLI module:

1. **Write tests first** (TDD approach recommended)
2. **Test all code paths** including error scenarios
3. **Use appropriate test type**:
   - Unit tests for individual functions
   - Integration tests for command registration and parameter validation
   - Scenario tests for end-to-end workflows
4. **Mock external dependencies** (PowerShell, Azure APIs) in unit tests
5. **Test cross-platform compatibility** where applicable
6. **Update this README** if you add new test categories or significant functionality

## Test Results and Reporting

Test results are displayed in the terminal with the following format:

```
🧪 Running unit tests...
✅ TestMigratePowerShellUtils.test_check_migration_prerequisites_success
✅ TestMigrateDiscoveryCommands.test_get_discovered_server_success
...

📋 Test Summary:
  Unit Tests: ✅ PASSED
  Integration Tests: ✅ PASSED  
  Scenario Tests: ✅ PASSED

✅ ALL TESTS PASSED
```

For coverage reports:
- Terminal output shows line-by-line coverage percentages
- HTML report provides detailed coverage visualization
- Coverage data helps identify untested code paths

## Best Practices

1. **Keep tests focused**: Each test should verify one specific behavior
2. **Use descriptive test names**: Names should clearly indicate what is being tested
3. **Mock external dependencies**: Don't rely on external services in unit tests
4. **Test error paths**: Ensure error handling is properly tested
5. **Maintain test data**: Use the test configuration for consistent test data
6. **Clean up resources**: Ensure tests don't leave behind resources or state
7. **Document complex tests**: Add comments for non-obvious test logic
