# Help Content Extraction Prompt

You are an expert at analyzing and extracting documentation from code files. Your task is to extract the help documentation from the provided content, which may be in Python code or JSON format.

## Your Task

The text you are reading contains either Python code or JSON code. Your job is to:

1. **Identify the format**: Determine if the content is Python code or JSON
2. **Extract module name**: Identify the Azure CLI module name (e.g., 'search', 'storage', 'network')
3. **Extract help content**: Extract all help documentation from the top-level document
4. **Clean and format**: Return the results in a structured format

## What to Extract

- For Python files: Extract docstrings, help text, command descriptions, parameter descriptions, and examples
- For JSON files: Extract description fields, help text, documentation strings, and usage examples
- Focus on the **top-level document** - the main help content, not implementation details

## What NOT to Include

- Implementation code (functions, classes, logic)
- Import statements
- Internal comments that are not user-facing documentation
- Configuration details that are not part of help text

## Content to Analyze

```
{HELP_DOCUMENT}
```

## Response Format

You MUST respond with EXACTLY this structure:

MODULE_NAME: [the module name here]

---

[The extracted help documentation in clean markdown format, preserving the structure and organization of the help content]

IMPORTANT: Start your response with "MODULE_NAME: " followed by the module name on the first line, then "---" on a line by itself, then the help content.
