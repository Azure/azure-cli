#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import json
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

BUILD_ID = os.environ.get('BUILD_ID', None)
BUILD_BRANCH = os.environ.get('BUILD_BRANCH', None)

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
                    logger.info(f"Warning: Could not parse {stats_file}")
    return all_stats

def analyze_stats(all_stats):
    counters = {
        "manual": {"core": 0, "extension": 0},
        "mixed": {"core": 0, "extension": 0},
        "codegen": {"core": 0, "extension": 0},
        "codegenV1": {"core": 0, "extension": 0},
        "total": {"core": 0, "extension": 0}
    }
    for _, stats in all_stats.items():
        module_type = stats["type"]
        counters["total"][module_type] += 1
        if stats["manual"] > 0 and (stats["codegenV1"] > 0 or stats["codegenV2"] > 0):
            counters["mixed"][module_type] += 1
        if stats["codegenV1"] > 0 or stats["codegenV2"] > 0:
            counters["codegen"][module_type] += 1
        if stats["codegenV1"] > 0:
            counters["codegenV1"][module_type] += 1
    counters["manual"]["core"] = counters["total"]["core"] - counters["codegen"]["core"]
    counters["manual"]["extension"] = counters["total"]["extension"] - counters["codegen"]["extension"]
    return counters

def print_results(counters):
    logger.info("\n===== Codegen Coverage Report =====")
    logger.info("\n1. Manual Modules:")
    logger.info(f"   Core: {counters['manual']['core']}")
    logger.info(f"   Extension: {counters['manual']['extension']}")
    logger.info("\n2. Mixed Modules:")
    logger.info(f"   Core: {counters['mixed']['core']}")
    logger.info(f"   Extension: {counters['mixed']['extension']}")
    logger.info("\n3. Codegen Modules:")
    logger.info(f"   Core: {counters['codegen']['core']}")
    logger.info(f"   Extension: {counters['codegen']['extension']}")
    logger.info("\n4. CodegenV1 Modules:")
    logger.info(f"   Core: {counters['codegenV1']['core']}")
    logger.info(f"   Extension: {counters['codegenV1']['extension']}")
    logger.info("\n5. Total Modules:")
    logger.info(f"   Core: {counters['total']['core']}")
    logger.info(f"   Extension: {counters['total']['extension']}")

def analyze_and_report():
    all_stats = load_module_stats()
    counters = analyze_stats(all_stats)
    print_results(counters)
    output = {
        "detailed_stats": all_stats,
        "summary": counters
    }
    logger.info("\n=== Detailed JSON Output ===")
    logger.info(json.dumps(output, indent=2))
    with open("/tmp/module_stats_summary.json", "w") as f:
        json.dump(output, f, indent=2)

def generate_csv():
    data = []
    with open(f'/tmp/codegen_report.json', 'r') as file:
        ref = json.load(file)
    codegenv1 = ref['codegenV1']
    codegenv2 = ref['codegenV2']
    total = ref['total']
    manual = total - codegenv1 - codegenv2
    is_release = True if BUILD_BRANCH == 'release' else False
    date = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
    data.append([BUILD_ID, manual, codegenv1, codegenv2, total, is_release, date])
    logger.info('Finish generate data for codegen report:')
    logger.info("BUILD_ID, manual, codegenv1, codegenv2, total, is_release, date")
    logger.info(f'{data}')
    return data

if __name__ == '__main__':
    analyze_and_report()
    generate_csv()
