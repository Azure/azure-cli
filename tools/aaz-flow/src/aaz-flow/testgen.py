# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pathlib import Path
import os
import asyncio
import random
from fastmcp import Context
from prompt_templates import get_testgen_static_instructions, REF_STYLE_LABEL, IDEAL_STYLE


async def check_module_status(ctx: Context):
    await ctx.info("Starting test generation workflow.")

    module_name = getattr(ctx, "generated_module", None)
    if not module_name:
        response = await ctx.elicit(
            "Enter the module/extension name to generate tests for:"
        )
        if response.action != "accept" or not response.data:
            return "Test generation cancelled."
        module_name = response.data
    else:
        await ctx.info(f"Detected generated module: {module_name}")

    ctx.generated_module = module_name
    return module_name


def find_test_dir(cli_extension_path: str, module_name: str) -> Path | None:
    base = Path(cli_extension_path) / "src" / module_name
    for path in base.rglob("tests/latest"):
        if path.is_dir():
            return path
    return None


def extract_generated_examples(module_path: Path) -> dict[str, str]:
    examples = {}
    for file in module_path.rglob("*.py"):
        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            inside_docstring = False
            i = 0
            while i < len(lines):
                line = lines[i]

                if line.strip().startswith(('"""', "'''")):
                    inside_docstring = not inside_docstring
                    i += 1
                    continue

                if inside_docstring and line.strip().startswith(":example:"):
                    example_name = line.split(":example:")[1].strip()
                    command_lines = []
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j]
                        if next_line.strip().startswith(('"""', "'''")):
                            break
                        command_lines.append(next_line.rstrip())
                        j += 1
                    command = "\n".join(l for l in command_lines if l.strip())
                    key = example_name
                    counter = 1
                    while key in examples:
                        counter += 1
                        key = f"{example_name}_{counter}"
                    examples[key] = command.strip()
                    i = j
                else:
                    i += 1
    return examples


async def check_path_status(ctx: Context, paths: dict):
    module_name = await check_module_status(ctx)
    if not module_name or "cancelled" in str(module_name).lower():
        return str(module_name), [], None

    aaz_path = Path(f"{paths['cli_extension']}/src/{module_name}")
    if not aaz_path.exists():
        return f"AAZ path not found for module '{module_name}'", [], None

    commands = []
    for file in aaz_path.rglob("*.py"):
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("def "):
                    commands.append(line.strip().replace("def ", "").split("(")[0])

    test_dir = find_test_dir(paths["cli_extension"], module_name)
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / f"test_{module_name}.py"
    return module_name, commands, test_file


def build_testgen_prompt(
    module_name: str,
    commands: list[str],
    reference_snippet: str = "",
    examples: dict[str, str] | None = None,
) -> str:
    parts = [
        get_testgen_static_instructions(),
        (
            f"Module name: '{module_name}'. Generate a single test class named "
            f"'{module_name.capitalize()}ScenarioTest' deriving from ScenarioTest."
        ),
        "Discovered AAZ functions (potential commands):\n" + ", ".join(commands),
    ]

    if examples:
        example_lines = [
            f"{name}: {cmd}" for name, cmd in examples.items()
        ]
        parts.append("Example commands discovered from docstrings:\n" + "\n".join(example_lines))

    if reference_snippet:
        parts.append(REF_STYLE_LABEL + reference_snippet)
    
    parts.append("Here is the ideal test style example to follow:\n" + IDEAL_STYLE)

    return "\n\n".join(parts)


def strip_code_fences(text: str) -> str:
    lines = text.strip().splitlines()
    blocks = []
    inside = False
    current = []

    for line in lines:
        if line.strip().startswith("```"):
            if inside:
                blocks.append("\n".join(current).strip())
                current = []
                inside = False
            else:
                inside = True
        elif inside:
            current.append(line)
    if current:
        blocks.append("\n".join(current).strip())

    if blocks:
        return max(blocks, key=len)
    return text.strip()

def strip_shebang(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("#!"):
        return "\n".join(lines[1:]).strip()
    return text.strip()

async def generate_tests(ctx: Context, paths: dict):
    module_name, commands, test_file = await check_path_status(ctx, paths)

    if test_file is None and not commands:
        return str(module_name)

    if not commands:
        return f"No commands found to generate tests for module '{module_name}'."

    reference_snippet = "\n".join(
        [
            "azure-cli/src/azure-cli/azure/cli/command_modules/resource/tests/latest/test_resource.py",
            "azure-cli/src/azure-cli/azure/cli/command_modules/keyvault/tests/latest/test_keyvault_commands.py",
        ]
    )

    extracted_examples = extract_generated_examples(
        Path(f"{paths['cli_extension']}/src/{module_name}")
    )

    sampling_prompt = build_testgen_prompt(
        module_name, commands, reference_snippet, extracted_examples
    )
    max_retries = int(os.getenv("TESTGEN_RETRIES", "5"))
    base_delay = float(os.getenv("TESTGEN_RETRY_BASE_DELAY", "2"))

    attempt = 0
    content = ""
    last_err = None
    while attempt <= max_retries:
        try:
            if attempt > 0:
                await ctx.info(
                    f"Retrying test generation (attempt {attempt}/{max_retries})..."
                )
            sampled = await ctx.sample(sampling_prompt)
            raw_content = (getattr(sampled, "text", "") or "").strip()
            content = strip_shebang(strip_code_fences(raw_content))
            if content:
                break
            last_err = RuntimeError("Empty content returned from provider")
            raise last_err
        except Exception as ex:
            last_err = ex
            message = str(ex).lower()
            retriable = any(
                k in message
                for k in [
                    "rate limit",
                    "overloaded",
                    "timeout",
                    "temporarily unavailable",
                    "429",
                ]
            )
            if attempt >= max_retries or not retriable:
                break
            delay = base_delay * (2**attempt)
            delay = min(delay, 30)
            jitter = random.uniform(0.7, 1.3)
            wait_time = delay * jitter
            await ctx.info(
                f"Transient error encountered: {ex}. Waiting {wait_time:.1f}s before retry."
            )
            await asyncio.sleep(wait_time)
            attempt += 1
            continue

    if not content:
        if last_err:
            return (
                f"Test generation failed after {max_retries} retries for module '{module_name}': "
                f"{last_err}"
            )
        return (
            f"Test generation failed: no content generated for module '{module_name}'."
        )

    with open(test_file, "w", encoding="utf-8") as f:
        f.write(content)

    await ctx.info(f"Generated test file: {test_file}")
    return f"Test generation completed for module '{module_name}'."
