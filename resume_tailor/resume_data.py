"""
Author: Shridhar Mashalkar
This file is part of an open-source project licensed under the AGPL-3.0 License.
You are free to use, modify, and distribute this code under the terms of the LICENSE file.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from resume_tailor.schemas import ResumeData


def load_resume_data(path: Path) -> ResumeData:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return ResumeData.model_validate(payload)