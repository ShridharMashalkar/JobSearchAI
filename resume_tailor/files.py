"""
Author: Shridhar Mashalkar
This file is part of an open-source project licensed under the AGPL-3.0 License.
You are free to use, modify, and distribute this code under the terms of the LICENSE file.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def slugify(value: str, separator: str = "_", preserve_case: bool = False, max_length: int = 120) -> str:
    text = value.strip()
    if not preserve_case:
        text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9]+", separator, text)
    text = re.sub(rf"{re.escape(separator)}+", separator, text)
    text = text.strip(separator)
    if not text:
        text = "job"
    return text[:max_length].strip(separator) or "job"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    index = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def move_file(source: Path, destination: Path) -> Path:
    ensure_directory(destination.parent)
    final_destination = unique_path(destination)
    shutil.move(str(source), str(final_destination))
    return final_destination


def copy_file(source: Path, destination: Path) -> Path:
    ensure_directory(destination.parent)
    shutil.copy2(source, destination)
    return destination