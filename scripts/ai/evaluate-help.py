#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Evaluate Azure CLI help documentation quality.

This script finds all help files in a given path and evaluates them using
the HelpEvaluator class with Azure OpenAI.
"""

import argparse
import sys
import threading
import time
from pathlib import Path
from help_evaluator import HelpEvaluator


class Spinner:
    """Simple spinner for long-running operations."""
    
    def __init__(self, message="Processing"):
        self.message = message
        self.spinning = False
        self.spinner_thread = None
        
    def spin(self):
        """Spin animation."""
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        idx = 0
        while self.spinning:
            print(f"\r  {spinner_chars[idx]} {self.message}...", end="", flush=True)
            idx = (idx + 1) % len(spinner_chars)
            time.sleep(0.1)
        print("\r" + " " * (len(self.message) + 10) + "\r", end="", flush=True)
    
    def start(self):
        """Start the spinner."""
        self.spinning = True
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.daemon = True
        self.spinner_thread.start()
    
    def stop(self):
        """Stop the spinner."""
        self.spinning = False
        if self.spinner_thread:
            self.spinner_thread.join()


def find_help_files(input_path):
    """
    Find all help files in the given path.
    
    Args:
        input_path: Path to search for help files
    
    Returns:
        List of Path objects for help files
    """
    path = Path(input_path)
    
    if not path.exists():
        print(f"Error: Path '{input_path}' does not exist")
        sys.exit(1)
    
    help_files = []
    
    if path.is_file():
        # Single file
        if path.name.endswith('_help.py'):
            help_files.append(path)
        else:
            print(f"Warning: File '{path.name}' does not match help file pattern (*_help.py)")
    else:
        # Directory - search recursively
        help_files = list(path.rglob("*_help.py"))
    
    return help_files


def main():
    """Main function to run help evaluation."""
    parser = argparse.ArgumentParser(
        description="Evaluate Azure CLI help documentation quality using Azure OpenAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate a single help file
  python evaluate-help.py -i ../../src/azure-cli/azure/cli/command_modules/search/_help.py
  
  # Evaluate all help files in a directory
  python evaluate-help.py -i ../../src/azure-cli/azure/cli/command_modules/
  
  # Specify custom output directory
  python evaluate-help.py -i ../../src/azure-cli/azure/cli/command_modules/ -o ./custom-analysis
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        dest="input_path",
        required=True,
        help="Path to help file or directory containing help files"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="./analysis",
        help="Output directory for analysis results (default: ./analysis)"
    )
    
    args = parser.parse_args()
    
    # Find help files
    print(f"Searching for help files in: {args.input_path}")
    help_files = find_help_files(args.input_path)
    
    if not help_files:
        print(f"No help files found in '{args.input_path}'")
        sys.exit(1)
    
    print(f"Found {len(help_files)} help file(s)")
    
    # Initialize evaluator
    print(f"\nInitializing HelpEvaluator...")
    print(f"Output directory: {args.output}")
    evaluator = HelpEvaluator(output_dir=args.output)
    
    # Process each help file
    print("\n" + "="*80)
    print("Starting evaluation")
    print("="*80)
    
    results = []
    total_tokens_all = 0
    
    for i, help_file in enumerate(help_files, 1):
        print(f"\n[{i}/{len(help_files)}] Processing: {help_file}")
        
        spinner = Spinner("Working")
        try:
            spinner.start()
            result = evaluator.evaluate_file(help_file, show_progress=False)
            spinner.stop()
            
            print(f"  ✓ Analysis saved to: {result['output_path'].name}")
            print(f"  Total tokens used: {result['total_tokens']}")
            
            results.append(result)
            total_tokens_all += result['total_tokens']
        except Exception as e:
            spinner.stop()
            print(f"  ✗ Error: {e}")
            continue
    
    # Summary
    print("\n" + "="*80)
    print("Evaluation Complete")
    print("="*80)
    print(f"\nProcessed: {len(results)}/{len(help_files)} files")
    print(f"Total tokens used: {total_tokens_all:,}")
    
    if results:
        print(f"\nAnalysis files saved to: {args.output}/")
        print("\nResults summary:")
        for result in results:
            print(f"  - {result['module_name']}: {result['total_tokens']} tokens → {result['output_path'].name}")


if __name__ == "__main__":
    main()
