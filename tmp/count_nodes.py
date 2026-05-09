#!/bin/env python3

import re
from collections import defaultdict, OrderedDict

RETARGETS = [(t, re.compile(f'label="{t}\\.(\\d+)\\.(\\d+)"')) for t in [
        "InstructionReduction.Read",
        "InstructionReduction.Reduction",
        "Compute.ParallelDotProduct",
        "Compute.PartialSum",
        "Compute.BiasAdd",
        "Compute.ResidualAdd",
        "Compute.RequantRescale",
        "Compute.ActivationReLU",
        "Compute.ActivationLeakyReLU",
        "Compute.PoolingMax",
        "Compute.PoolingMaxStride1",
        "Compute.PoolingAverage",
        "ReadAccess.ConvImageAddress",
        "ReadAccess.ConvImageTileIndexing",
        "ReadAccess.ConvImageRead",
        "ReadAccess.ConvImageBuffer",
        "ReadAccess.ConvWeightAddress",
        "ReadAccess.ConvWeightRead",
        "ReadAccess.ConvWeightBuffer",
        "ReadAccess.ConvImageShallow",
        "ReadAccess.ConvWeightShallow",
        "ReadAccess.FCImageShallow",
        "ReadAccess.FCWeightShallow",
        "ReadAccess.BiasRead",
        "ReadAccess.ResidualRead",
        "ReadAccess.RequantRead",
        "WriteAccess.ReshapePool",
        "WriteAccess.ReshapeStride1Pool",
        "WriteAccess.OutputAddress",
        "WriteAccess.OutputWrite",
        "WriteAccess.OutputShallow",
]]

FILES = [
        ("LeNet", "lenet_nodes.dot"),
        ("VGG", "vgg_nodes.dot"),
        ("YOLO", "yolo_nodes.dot"),
        ("ResNet", "resnet_nodes.dot"),
]

def do_it(fname):
    bank = defaultdict(lambda: defaultdict(int))
    with open(fname, 'r') as file:
        for line in file:
            for tag, r in RETARGETS:
                if p := r.search(line):
                    grouping = int(p.group(1))
                    counts = int(p.group(2))
                    bank[tag][grouping] += counts
    return {k: dict(v) for k, v in bank.items()}

print(f"{'Operation':40}", end='')
for col, _ in FILES:
    fmt = max(3, len(col))
    print(f" {col:>{fmt}}", end='')
print()

all_nodes = [(col, do_it(fname)) for col, fname in FILES]
for tag, _ in RETARGETS:
    print(f"{tag:40}", end='')
    for col, m in all_nodes:
        tot = sum(m.get(tag, {}).values())
        fmt = max(3, len(col))
        print(f" {tot:>{fmt}}", end='')
    print()

