"""
Author: Shridhar Mashalkar
This file is part of an open-source project licensed under the GNU AGPLv3 License.
You are free to use, modify, and distribute this code under the terms of the LICENSE file.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from resume_tailor.config import AppConfig
from resume_tailor.files import ensure_directory


class PDFBuildError(RuntimeError):
    pass


def compile_latex(tex_path: Path, output_pdf_path: Path, config: AppConfig) -> Path:
    ensure_directory(tex_path.parent)
    ensure_directory(output_pdf_path.parent)

    command = [config.pdf.command, *config.pdf.extra_args, tex_path.name]
    for _ in range(config.pdf.runs):
        result = subprocess.run(
            command,
            cwd=tex_path.parent,
            capture_output=True,
            text=True,
            timeout=config.pdf.timeout_seconds,
        )
        if result.returncode != 0:
            raise PDFBuildError(_format_error(tex_path, result))

    produced_pdf = tex_path.with_suffix(".pdf")
    if not produced_pdf.exists():
        raise PDFBuildError(f"PDF was not produced for {tex_path.name}")

    shutil.copy2(produced_pdf, output_pdf_path)
    return output_pdf_path


def _format_error(tex_path: Path, result: subprocess.CompletedProcess[str]) -> str:
    return (
        f"pdflatex failed for {tex_path.name} with exit code {result.returncode}\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )