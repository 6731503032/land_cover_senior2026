"""Writes data/processed/<dataset>/splits.json so everyone uses the SAME
train/val/test split. Usage: python scripts/make_splits.py data/processed/oem"""
import json
import random
import sys
from pathlib import Path

root = Path(sys.argv[1])
names = sorted(p.name for p in (root / "all" / "images").glob("*.png"))
random.Random(42).shuffle(names)
n = len(names)
splits = {"train": names[: int(0.7 * n)],
          "val": names[int(0.7 * n): int(0.85 * n)],
          "test": names[int(0.85 * n):]}
json.dump(splits, open(root / "splits.json", "w"), indent=2)
print({k: len(v) for k, v in splits.items()})
