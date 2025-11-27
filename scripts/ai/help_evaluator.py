"""
HelpEvaluator class for evaluating Azure CLI help documentation quality.
"""

import os
from pathlib import Path
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv


class HelpEvaluator:
    """
    A class to evaluate Azure CLI help documentation using Azure OpenAI.
    """
    
    def __init__(self, output_dir="analysis"):
        """
        Initialize the HelpEvaluator.
        
        Args:
            output_dir: Directory where analysis results will be saved (default: "analysis")
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        # Set output directory
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Cache for prompts
        self.prompts = {}
        
        # System messages for different prompt types
        self.system_messages = {
            "simple-evaluator": "You are an expert technical writer and documentation evaluator.",
            "document-quality-scoring-framework": "You are an expert technical documentation evaluator specializing in Azure CLI and Azure PowerShell reference documentation.",
            "extractor": "You are an expert at analyzing and extracting documentation from code files."
        }
        
        # Load all prompts
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        """Load all prompt templates from the prompts folder."""
        prompts_dir = Path(__file__).parent / "prompts"
        if prompts_dir.exists():
            for prompt_file in prompts_dir.glob("*.md"):
                prompt_name = prompt_file.stem
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    self.prompts[prompt_name] = f.read()
            print(f"Loaded prompts: {list(self.prompts.keys())}")
    
    def _load_prompt_template(self, prompt_name):
        """
        Load a prompt template from the cache.
        
        Args:
            prompt_name: Name of the prompt file (without .md extension)
        
        Returns:
            The prompt template as a string
        """
        if prompt_name not in self.prompts:
            raise ValueError(f"Prompt '{prompt_name}' not found. Available prompts: {list(self.prompts.keys())}")
        return self.prompts[prompt_name]
    
    def llm_chat(self, content, prompt_name, temperature=0.3, max_tokens=4000):
        """
        Generic function to chat with Azure OpenAI using a specific prompt.
        
        Args:
            content: The content to process (e.g., help document, extracted text)
            prompt_name: Name of the prompt to use
            temperature: Temperature parameter for the model (default: 0.3)
            max_tokens: Maximum tokens for the response (default: 4000)
        
        Returns:
            Dictionary containing the results
        """
        # Load the prompt template
        prompt_template = self._load_prompt_template(prompt_name)
        
        # Format the prompt with the content
        full_prompt = prompt_template.replace("{HELP_DOCUMENT}", content)
        
        # Get system message
        system_message = self.system_messages.get(prompt_name, "You are a helpful AI assistant.")
        
        # Call Azure OpenAI
        response = self.client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": full_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract the result
        result_content = response.choices[0].message.content
        
        return {
            "prompt_used": prompt_name,
            "result": result_content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    def extract_help_content(self, file_path):
        """
        Extract help content from a help file.
        
        Args:
            file_path: Path to the help file
        
        Returns:
            Tuple of (module_name, extracted_help, raw_content, extraction_result)
        """
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # Extract help content using the extractor prompt
        extraction_result = self.llm_chat(raw_content, prompt_name="extractor")
        
        # Parse the extraction result to separate module name and help content
        extraction_text = extraction_result['result']
        if "MODULE_NAME:" in extraction_text and "---" in extraction_text:
            parts = extraction_text.split("---", 1)
            module_name_line = parts[0].strip()
            module_name = module_name_line.replace("MODULE_NAME:", "").strip()
            extracted_help = parts[1].strip()
        else:
            # Fallback: extract from file path
            module_name = Path(file_path).stem.replace("_help", "")
            if module_name.startswith("_"):
                module_name = module_name[1:]
            extracted_help = extraction_text
        
        return module_name, extracted_help, raw_content, extraction_result
    
    def evaluate_help(self, extracted_help, show_progress=True):
        """
        Evaluate help content using both evaluators.
        
        Args:
            extracted_help: The extracted help content
            show_progress: Whether to print progress messages (default: True)
        
        Returns:
            Tuple of (simple_evaluation_result, dqsf_evaluation_result)
        """
        if show_progress:
            print("  Running Simple Evaluator...")
        simple_evaluation_result = self.llm_chat(extracted_help, prompt_name="simple-evaluator")
        
        if show_progress:
            print("  Running Document Quality Scoring Framework Evaluator...")
        dqsf_evaluation_result = self.llm_chat(extracted_help, prompt_name="document-quality-scoring-framework")
        
        return simple_evaluation_result, dqsf_evaluation_result
    
    def save_analysis(self, module_name, file_path, raw_content, extracted_help, 
                     extraction_result, simple_evaluation_result, dqsf_evaluation_result):
        """
        Save the analysis results to a markdown file.
        
        Args:
            module_name: Name of the module
            file_path: Path to the original help file
            raw_content: Raw content of the help file
            extracted_help: Extracted help content
            extraction_result: Result from extraction
            simple_evaluation_result: Result from simple evaluator
            dqsf_evaluation_result: Result from DQSF evaluator
        
        Returns:
            Path to the saved analysis file
        """
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Create filename
        output_filename = f"{module_name}_{timestamp}.md"
        output_path = self.output_dir / output_filename
        
        # Calculate total token usage
        total_tokens = (extraction_result['usage']['total_tokens'] + 
                       simple_evaluation_result['usage']['total_tokens'] + 
                       dqsf_evaluation_result['usage']['total_tokens'])
        
        # Prepare the content to save
        content = f"""# Help Document Analysis: {module_name}

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Source File**: {file_path}
**Model**: {simple_evaluation_result['model']}

## Token Usage
- Extraction: {extraction_result['usage']['total_tokens']} tokens
- Simple Evaluation: {simple_evaluation_result['usage']['total_tokens']} tokens
- DQSF Evaluation: {dqsf_evaluation_result['usage']['total_tokens']} tokens

- **Total**: {total_tokens} tokens

---

## Original Source Code

<details>
<summary>Click to expand original code</summary>

```python
{raw_content}
```

</details>

---

## Extracted Help Content

<details>
<summary>Click to expand extracted help content</summary>

{extracted_help}

</details>

---

## Simple Quality Evaluation

{simple_evaluation_result['result']}

---

## Document Quality Scoring Framework (DQSF) Evaluation

{dqsf_evaluation_result['result']}
"""
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path, total_tokens
    
    def evaluate_file(self, file_path, show_progress=True):
        """
        Complete evaluation workflow for a single help file.
        
        Args:
            file_path: Path to the help file
            show_progress: Whether to print progress messages (default: True)
        
        Returns:
            Dictionary with evaluation results and metadata
        """
        if show_progress:
            print(f"\nProcessing: {file_path}")
        
        # Step 1: Extract help content
        if show_progress:
            print("  Extracting help content...")
        module_name, extracted_help, raw_content, extraction_result = self.extract_help_content(file_path)
        if show_progress:
            print(f"  Extracted module: {module_name}")
        
        # Step 2: Evaluate help quality
        if show_progress:
            print("  Evaluating help quality...")
        simple_evaluation_result, dqsf_evaluation_result = self.evaluate_help(extracted_help, show_progress=show_progress)
        
        # Step 3: Save analysis
        if show_progress:
            print("  Saving analysis...")
        output_path, total_tokens = self.save_analysis(
            module_name, file_path, raw_content, extracted_help,
            extraction_result, simple_evaluation_result, dqsf_evaluation_result
        )
        
        if show_progress:
            print(f"  ✓ Analysis saved to: {output_path}")
            print(f"  Total tokens used: {total_tokens}")
        
        return {
            "module_name": module_name,
            "file_path": file_path,
            "output_path": output_path,
            "total_tokens": total_tokens,
            "extraction_tokens": extraction_result['usage']['total_tokens'],
            "simple_eval_tokens": simple_evaluation_result['usage']['total_tokens'],
            "dqsf_eval_tokens": dqsf_evaluation_result['usage']['total_tokens']
        }
