"""
Author: Shridhar Mashalkar
This file is part of an open-source project licensed under the GNU AGPLv3 License.
You are free to use, modify, and distribute this code under the terms of the LICENSE file.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from resume_tailor.pipeline import run_pipeline


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    print("\n" + "=" * 60)
    print("        CareerTrack AI - Resume Tailoring Pipeline")
    print("             Developed by Shridhar Mashalkar")
    print("=" * 60 + "\n")
    parser = argparse.ArgumentParser(description="Generate tailored resumes and cover letters from job descriptions.")
    parser.add_argument("--config", required=True, type=Path, help="Path to the pipeline YAML config file.")
    args = parser.parse_args()
    run_pipeline(args.config)


if __name__ == "__main__":
    main()