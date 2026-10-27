# Live Test Template (Help-driven)

Use this template for codegen-style modules that organize tests under `tests/latest/`.

## 1) `tests/latest/example_steps.py`

```python
from .. import try_manual


@try_manual
def step_<command_a>(test, checks=None):
    if checks is None:
        checks = []
    test.cmd(
        'az <group> <command-a> <args-from-help>',
        checks=checks + [
            # add stable checks
        ]
    )


@try_manual
def step_<command_b>(test, checks=None):
    if checks is None:
        checks = []
    test.cmd(
        'az <group> <command-b> <args-from-help>',
        checks=checks + [
            # add stable checks
        ]
    )
```

## 2) `tests/latest/test_<module>_scenario.py`

```python
import os
from azure.cli.testsdk import ScenarioTest
from .example_steps import step_<command_a>, step_<command_b>
from .. import try_manual, raise_if, calc_coverage


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


@try_manual
def setup_scenario(test):
    pass


@try_manual
def cleanup_scenario(test):
    pass


@try_manual
def call_scenario(test):
    setup_scenario(test)
    step_<command_a>(test, checks=[])
    step_<command_b>(test, checks=[])
    cleanup_scenario(test)


@try_manual
class <ModuleName>ScenarioTest(ScenarioTest):

    def test_<module>_scenario(self):
        call_scenario(self)
        calc_coverage(__file__)
        raise_if()
```

## 3) Coverage Gate

- Coverage file path usually becomes: `tests/latest/test_<module>_scenario_coverage.md`
- Expected format includes `Coverage: covered/total`
- Command-level coverage rule:
  - if `covered/total < 0.8`, remind user to add missing help examples and corresponding step functions.

## 4) Missing Example Prompt

When missing examples are detected, ask the user:

- "These commands have no usable help examples: <list>. Continue and add manual examples for them?"

If user declines, continue only with commands that have usable examples and mark skipped commands in output.
