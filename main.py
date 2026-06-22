"""
Author: Shridhar Mashalkar
This file is part of an open-source project licensed under the GNU AGPLv3 License.
You are free to use, modify, and distribute this code under the terms of the LICENSE file.
"""
from __future__ import annotations

from dotenv import load_dotenv

from resume_tailor.cli import main

load_dotenv()


if __name__ == "__main__":
    main()