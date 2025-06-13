#!/usr/bin/env python
import json
import os

def load_module_stats():
    stats_dir = "/tmp/module_stats"
    all_stats = {}
    
    with open("/mnt/vss/_work/1/s/scripts/ci/core_modules.txt", "r") as f:
        core_modules = [line.strip() for line in f.readlines()]
    
    with open("/mnt/vss/_work/1/s/scripts/ci/extension_modules.txt", "r") as f:
        extension_modules = [line.strip() for line in f.readlines()]
    
    for module in core_modules + extension_modules:
        stats_file = os.path.join(stats_dir, f"{module}.json")
        if os.path.exists(stats_file):
            with open(stats_file, "r") as f:
                try:
                    stats = json.load(f)
                    codegenV1 = stats.get("codegenV1", 0)
                    codegenV2 = stats.get("codegenV2", 0)
                    total = stats.get("total", 0)
                    
                    manual = total - codegenV1 - codegenV2
                    
                    all_stats[module] = {
                        "codegenV1": codegenV1,
                        "codegenV2": codegenV2,
                        "manual": manual,
                        "total": total,
                        "type": "core" if module in core_modules else "extension"
                    }
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse {stats_file}")
    
    return all_stats

def analyze_stats(all_stats):
    counters = {
        "manual": {"core": 0, "extension": 0},
        "mixed": {"core": 0, "extension": 0},
        "codegen": {"core": 0, "extension": 0},
        "codegenV1": {"core": 0, "extension": 0},
        "total": {"core": 0, "extension": 0}
    }
    
    for module, stats in all_stats.items():
        module_type = stats["type"]
        
        counters["total"][module_type] += 1
        
        if stats["manual"] > 0:
            counters["manual"][module_type] += 1
        if stats["manual"] > 0 and (stats["codegenV1"] > 0 or stats["codegenV2"] > 0):
            counters["mixed"][module_type] += 1
        if stats["codegenV1"] > 0 or stats["codegenV2"] > 0:
            counters["codegen"][module_type] += 1
        if stats["codegenV1"] > 0:
            counters["codegenV1"][module_type] += 1
    
    return counters

def print_results(counters):
    print("\n=== Azure CLI Module Statistics ===")
    print("\n1. Manual Modules:")
    print(f"   Core: {counters['manual']['core']}")
    print(f"   Extension: {counters['manual']['extension']}")
    
    print("\n2. Mixed Modules:")
    print(f"   Core: {counters['mixed']['core']}")
    print(f"   Extension: {counters['mixed']['extension']}")
    
    print("\n3. Codegen Modules:")
    print(f"   Core: {counters['codegen']['core']}")
    print(f"   Extension: {counters['codegen']['extension']}")
    
    print("\n4. CodegenV1 Modules:")
    print(f"   Core: {counters['codegenV1']['core']}")
    print(f"   Extension: {counters['codegenV1']['extension']}")
    
    print("\n5. Total Modules:")
    print(f"   Core: {counters['total']['core']}")
    print(f"   Extension: {counters['total']['extension']}")

def main():
    all_stats = load_module_stats()
    
    counters = analyze_stats(all_stats)
    
    print_results(counters)
    
    output = {
        "detailed_stats": all_stats,
        "summary": counters
    }
    
    print("\n=== Detailed JSON Output ===")
    print(json.dumps(output, indent=2))
    
    with open("/tmp/module_stats_summary.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main() 