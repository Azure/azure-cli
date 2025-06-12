#!/usr/bin/env python
import json
import os
from collections import defaultdict

def load_module_stats():
    stats_dir = "/tmp/module_stats"
    all_stats = {}
    
    # 加载core模块列表
    with open("core_modules.txt", "r") as f:
        core_modules = [line.strip() for line in f.readlines()]
    
    # 加载extension模块列表
    with open("extension_modules.txt", "r") as f:
        extension_modules = [line.strip() for line in f.readlines()]
    
    # 读取每个模块的统计数据
    for module in core_modules + extension_modules:
        stats_file = os.path.join(stats_dir, f"{module}.json")
        if os.path.exists(stats_file):
            with open(stats_file, "r") as f:
                try:
                    stats = json.load(f)
                    codegenV1 = stats.get("codegenV1", 0)
                    codegenV2 = stats.get("codegenV2", 0)
                    total = stats.get("total", 0)
                    
                    # 计算manual数量
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
    # 初始化计数器
    counters = {
        "manual": {"core": 0, "extension": 0},
        "mixed": {"core": 0, "extension": 0},
        "codegen": {"core": 0, "extension": 0},
        "codegenV1": {"core": 0, "extension": 0},
        "total": {"core": 0, "extension": 0}
    }
    
    # 分析每个模块
    for module, stats in all_stats.items():
        module_type = stats["type"]
        
        # 更新总数
        counters["total"][module_type] += 1
        
        # 判断模块类型
        if stats["manual"] > 0:
            counters["manual"][module_type] += 1
        if stats["manual"] > 0 and (["codegenV1"] > 0 or stats["codegenV2"] > 0):
            counters["mixed"][module_type] += 1
        if stats["codegenV1"] > 0 or stats["codegenV2"] > 0:
            counters["codegen"][module_type] += 1
        if stats["codegenV1"] > 0:
            counters["codegenV1"][module_type] += 1
    
    return counters

def print_results(counters):
    print("\n=== Azure CLI Module Statistics ===")
    print("\n1. 手动编写模块数量:")
    print(f"   Core: {counters['manual']['core']}")
    print(f"   Extension: {counters['manual']['extension']}")
    
    print("\n2. 混合模块数量:")
    print(f"   Core: {counters['mixed']['core']}")
    print(f"   Extension: {counters['mixed']['extension']}")
    
    print("\n3. Codegen模块数量:")
    print(f"   Core: {counters['codegen']['core']}")
    print(f"   Extension: {counters['codegen']['extension']}")
    
    print("\n4. CodegenV1模块数量:")
    print(f"   Core: {counters['codegenV1']['core']}")
    print(f"   Extension: {counters['codegenV1']['extension']}")
    
    print("\n5. 总模块数量:")
    print(f"   Core: {counters['total']['core']}")
    print(f"   Extension: {counters['total']['extension']}")

def main():
    # 加载统计数据
    all_stats = load_module_stats()
    
    # 分析数据
    counters = analyze_stats(all_stats)
    
    # 打印结果
    print_results(counters)
    
    # 保存详细数据到文件
    output = {
        "detailed_stats": all_stats,
        "summary": counters
    }
    
    # 打印JSON到控制台，方便在pipeline中查看
    print("\n=== Detailed JSON Output ===")
    print(json.dumps(output, indent=2))
    
    # 同时保存到文件
    with open("/tmp/module_stats_summary.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main() 