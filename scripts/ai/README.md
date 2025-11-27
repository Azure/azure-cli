# Azure CLI Help Documentation Evaluator

This tool evaluates the quality of Azure CLI help documentation using Azure OpenAI. It extracts help content from Python files and evaluates them using two different evaluation frameworks.

## Overview

The evaluator performs three main steps:
1. **Extract**: Extracts help documentation from `*_help.py` files
2. **Evaluate**: Runs two evaluators:
   - **Simple Evaluator**: Quick quality assessment
   - **Document Quality Scoring Framework (DQSF)**: Comprehensive Microsoft Learn quality standards assessment
3. **Report**: Generates detailed markdown reports with both evaluations

## Prerequisites

- Python 3.10 or higher
- Azure OpenAI access with API credentials

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the `scripts/ai/` directory with your Azure OpenAI credentials:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2025-04-01-preview
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
```

### Getting Azure OpenAI Credentials

- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key from Azure Portal
- `AZURE_OPENAI_API_VERSION`: API version (e.g., `2025-04-01-preview`)
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI resource endpoint URL
- `AZURE_OPENAI_DEPLOYMENT_NAME`: The name of your deployed model (e.g., `gpt-4o-mini`, `gpt-4`)

## Usage

### Evaluate a Single Help File

```bash
python evaluate-help.py -i ../../src/azure-cli/azure/cli/command_modules/search/_help.py
```

### Evaluate All Help Files in a Directory

```bash
python evaluate-help.py -i ../../src/azure-cli/azure/cli/command_modules/
```

### Specify Custom Output Directory

```bash
python evaluate-help.py -i ../../src/azure-cli/azure/cli/command_modules/ -o ./custom-analysis
```

## Command Line Options

- `-i, --input` (required): Path to help file or directory containing help files
- `-o, --output` (optional): Output directory for analysis results (default: `./analysis`)

## Output

The tool generates markdown files in the output directory with the following structure:

```
analysis/
  ├── modulename_YYYYMMDD-HHMMSS.md
  ├── ...
```

Each analysis file contains:
- **Metadata**: Date, source file, model used, token usage
- **Original Source Code**: Collapsible section with the raw Python code
- **Extracted Help Content**: The extracted documentation
- **Simple Quality Evaluation**: Quick assessment results
- **DQSF Evaluation**: Comprehensive quality scores (out of 100 points)

## Evaluation Frameworks

### Simple Evaluator
Provides a quick quality assessment across:
- Clarity and Readability
- Completeness
- Accuracy
- Structure and Organization
- Examples and Practical Usage
- Accessibility

### Document Quality Scoring Framework (DQSF)
A comprehensive framework based on Microsoft Learn standards, evaluating five categories (20 points each):
1. **Module Description**: Overview and context
2. **Command Description**: Behavior and prerequisites
3. **Examples**: Runnable, up-to-date examples
4. **Parameter Descriptions**: Clear, detailed parameter documentation
5. **Parameter Properties/Sets**: Complete parameter specifications

Each category is scored across six dimensions:
- Practical & example-rich
- Consistent with style guide
- Detailed & technically complete
- Current and up-to-date
- Easy to navigate
- Clear parameter descriptions

## Architecture

The tool consists of two main components:

### `help_evaluator.py`
The `HelpEvaluator` class handles:
- Azure OpenAI client initialization
- Prompt template management
- Help content extraction
- Running both evaluators
- Generating analysis reports

### `evaluate-help.py`
The main script that:
- Parses command-line arguments
- Finds help files (supports single file or directory)
- Manages the evaluation workflow
- Provides progress feedback with spinner
- Generates summary statistics

## Prompts

Evaluation prompts are stored in the `prompts/` directory:
- `extractor.md`: Extracts help content and module name
- `simple-evaluator.md`: Simple quality evaluation criteria
- `document-quality-scoring-framework.md`: DQSF evaluation criteria

You can customize these prompts to adjust the evaluation criteria.

## Token Usage

The tool tracks token usage for each operation:
- Extraction tokens
- Simple evaluation tokens
- DQSF evaluation tokens
- Total tokens per file

This helps estimate costs and optimize evaluations.

## Example Output

```
Searching for help files in: ../../src/azure-cli/azure/cli/command_modules/search/
Found 1 help file(s)

Initializing HelpEvaluator...
Output directory: ./analysis
Loaded prompts: ['extractor', 'simple-evaluator', 'document-quality-scoring-framework']

================================================================================
Starting evaluation
================================================================================

[1/1] Processing: ../../src/azure-cli/azure/cli/command_modules/search/_help.py
  ⠋ Working...
  ✓ Analysis saved to: search_20251127-123045.md
  Total tokens used: 4821

================================================================================
Evaluation Complete
================================================================================

Processed: 1/1 files
Total tokens used: 4,821

Analysis files saved to: ./analysis/

Results summary:
  - search: 4821 tokens → search_20251127-123045.md
```

## Troubleshooting

### Missing Environment Variables
If you get an error about missing API credentials, ensure your `.env` file is in the `scripts/ai/` directory and contains all required variables.

### API Rate Limits
If you encounter rate limit errors, consider:
- Adding delays between evaluations
- Using a model with higher rate limits
- Processing files in smaller batches

### Token Limits
If evaluations fail due to token limits:
- Use a model with larger context windows
- Increase `max_tokens` parameter in the code
- Split large help files into smaller sections

## Contributing

To modify evaluation criteria:
1. Edit the appropriate prompt file in `prompts/`
2. Test with a sample help file
3. Adjust scoring weights or add new dimensions as needed

## License

This tool is part of the Azure CLI project and follows the same license terms.
