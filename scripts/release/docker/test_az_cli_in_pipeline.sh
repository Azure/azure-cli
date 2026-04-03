#!/usr/bin/env bash

# Set output file with timestamp
OUTPUT_FILE="/test/azure_cli_test_output.log"
OUTPUT_FILE_Result="/test/azure_cli_test_result.csv"

# Function to run command and capture output
run_cmd() {
    local cmd="$1"
    
    echo "$cmd"
    echo "Command: $cmd" >> "$OUTPUT_FILE"
    
    # Create temporary files for stdout and stderr
    local temp_stdout=$(mktemp)
    local temp_stderr=$(mktemp)
    local exit_code=0
    
    # Run command and capture stdout and stderr separately
    if ! eval "$cmd" > "$temp_stdout" 2> "$temp_stderr"; then
        exit_code=$?
        echo "ERROR: Command failed with exit code $exit_code" >&2
    fi
    
    # Read the outputs
    local stdout_content=$(cat "$temp_stdout")
    local stderr_content=$(cat "$temp_stderr")
    
    # Write to log files
    cat "$temp_stdout" >> "$OUTPUT_FILE"
    cat "$temp_stderr" >> "$OUTPUT_FILE"
    
    # Determine execution result
    local execution_result="Success"
    if [ $exit_code -ne 0 ]; then
        execution_result="Fail"
    fi
    
    # Check if output is JSON format and count items
    local is_json="No"
    local item_count="invalid"
    
    if [ -n "$stdout_content" ]; then
        # Try to parse as JSON using jq if available, or python as fallback
        if command -v jq >/dev/null 2>&1; then
            if echo "$stdout_content" | jq . >/dev/null 2>&1; then
                is_json="Yes"
                # Check if it's an array or object
                if echo "$stdout_content" | jq -e 'type' | grep -q "array"; then
                    item_count=$(echo "$stdout_content" | jq 'length')
                elif echo "$stdout_content" | jq -e 'type' | grep -q "object"; then
                    item_count="1"
                fi
            fi
        elif command -v python3 >/dev/null 2>&1; then
            if python3 -c "import json; json.loads('''$stdout_content''')" 2>/dev/null; then
                is_json="Yes"
                # Check if it's an array or object
                local json_type=$(python3 -c "import json; data=json.loads('''$stdout_content'''); print(type(data).__name__)" 2>/dev/null)
                if [ "$json_type" = "list" ]; then
                    item_count=$(python3 -c "import json; print(len(json.loads('''$stdout_content''')))" 2>/dev/null)
                elif [ "$json_type" = "dict" ]; then
                    item_count="1"
                fi
            fi
        fi
    fi
    
    # Extract warnings and errors from stderr
    local warnings=$(echo "$stderr_content" | grep -i "warning" | tr '\n' ';' | sed 's/;$//')
    local errors=$(echo "$stderr_content" | grep -i "error" | tr '\n' ';' | sed 's/;$//')
    
    # Escape quotes for CSV
    cmd_escaped=$(echo "$cmd" | sed 's/"/""/g')
    warnings_escaped=$(echo "$warnings" | sed 's/"/""/g')
    errors_escaped=$(echo "$errors" | sed 's/"/""/g')
    
    # Write to CSV result file
    echo "\"$cmd_escaped\",\"$execution_result\",\"$is_json\",\"$item_count\",\"$warnings_escaped\",\"$errors_escaped\"" >> "$OUTPUT_FILE_Result"
    
    # Cleanup temporary files
    rm -f "$temp_stdout" "$temp_stderr"
    
    echo "" >> "$OUTPUT_FILE"
}

echo "=================================================="
echo "Azure CLI Test Script - All Available List Commands"
echo "=================================================="
echo "Output will be saved to: $OUTPUT_FILE"
echo ""

echo "==================================================" >> "$OUTPUT_FILE"
echo "Azure CLI Test Script - All Available List Commands" >> "$OUTPUT_FILE"
echo "Test started at: $(date)" >> "$OUTPUT_FILE"
echo "==================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Create CSV header for result file
echo "Command,Result,IsJSON,Count,Warnings,Errors" > "$OUTPUT_FILE_Result"

# Execute commands from az_cli_commands.sh
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
az_commands_file="$script_dir/az_cli_commands.sh"

if [ -f "$az_commands_file" ]; then
    echo "Reading commands from: $az_commands_file"
    while IFS= read -r line; do
        # Skip empty lines and comments that start with #
        if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
            # Check if it's an echo command for section headers
            if [[ "$line" =~ ^echo ]]; then
                # Execute echo commands directly
                eval "$line"
            elif [[ "$line" =~ ^az ]]; then
                # Execute az commands through run_cmd
                run_cmd "$line"
            fi
        elif [[ "$line" =~ ^[[:space:]]*#[[:space:]]*echo ]]; then
            # Handle commented echo commands (like # echo "=== Compute Fleet ===")
            echo "$line"
        fi
    done < "$az_commands_file"
else
    echo "Warning: Command file not found: $az_commands_file"
fi

echo "=================================================="
echo "Azure CLI Test Completed"
echo "=================================================="
echo "Full output saved to: $OUTPUT_FILE"

echo "==================================================" >> "$OUTPUT_FILE"
echo "Azure CLI Test Completed at: $(date)" >> "$OUTPUT_FILE"
echo "==================================================" >> "$OUTPUT_FILE"
