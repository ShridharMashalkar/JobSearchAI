"""
Author: Shridhar Mashalkar
This file is part of an open-source project licensed under the AGPL-3.0 License.
You are free to use, modify, and distribute this code under the terms of the LICENSE file.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class PathSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jd_input_folder: Path
    output_folder: Path
    error_folder: Path
    work_root: Path
    resume_yaml_path: Path
    resume_template_path: Path
    cover_letter_template_path: Path
    jobs_excel_path: Path


class FilenameSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_filename: str = "AI_Analysis.txt"
    jd_filename: str = "jd.txt"
    resume_tex_filename: str = "resume.tex"
    cover_letter_tex_filename: str = "cover_letter.tex"
    resume_pdf_filename: str = "resume.pdf"
    cover_letter_pdf_filename: str = "cover_letter.pdf"
    error_jd_suffix: str = "_failed"


class LLMSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    model_name: str = "gpt-5.4-mini"
    temperature: float = 0.2
    max_retries: int = 3
    retry_start: int = 0
    request_timeout_seconds: int = 120


class PDFSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: str = "pdflatex"
    runs: int = 2
    timeout_seconds: int = 180
    extra_args: list[str] = Field(default_factory=lambda: ["-interaction=nonstopmode", "-halt-on-error", "-file-line-error"])


class ExcelSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sheet_name: str = "Jobs"
    columns: list[str] = Field(
        default_factory=lambda: [
            "Company",
            "Title",
            "Overall Fit",
            "Date",
            "Application Status",
            "Job URL",
            "Role Summary",
            "Key Responsibilities",
            "Technical Skills",
            "Soft Skills",
            "Missing Keywords",
            "Output Folder",
            "Custom Notes",
        ]
    )


class PipelineSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jd_glob: str = "*.txt"
    job_folder_separator: str = "_"
    folder_slug_max_length: int = 120
    preserve_case: bool = False
    source_encoding: str = "utf-8"


class DataSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    send_missing_keywords: bool = True
    send_current_resume: bool = True
    send_raw_jd: bool = True
    include_projects: bool = True
    include_certifications: bool = True
    include_publications: bool = True


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_dir: Path
    paths: PathSettings
    filenames: FilenameSettings
    llm: LLMSettings
    pdf: PDFSettings
    excel: ExcelSettings
    pipeline: PipelineSettings
    data: DataSettings = Field(default_factory=DataSettings)

    def resolved(self) -> "AppConfig":
        return self.model_copy(
            update={
                "paths": PathSettings(
                    jd_input_folder=self._resolve_path(self.paths.jd_input_folder),
                    output_folder=self._resolve_path(self.paths.output_folder),
                    error_folder=self._resolve_path(self.paths.error_folder),
                    work_root=self._resolve_path(self.paths.work_root),
                    resume_yaml_path=self._resolve_path(self.paths.resume_yaml_path),
                    resume_template_path=self._resolve_path(self.paths.resume_template_path),
                    cover_letter_template_path=self._resolve_path(self.paths.cover_letter_template_path),
                    jobs_excel_path=self._resolve_path(self.paths.jobs_excel_path),
                )
            }
        )

    def _resolve_path(self, path: Path) -> Path:
        if path.is_absolute():
            return path
        return (self.base_dir / path).resolve()


def load_config(config_path: Path) -> AppConfig:
    with config_path.open("r", encoding="utf-8") as handle:
        payload: dict[str, Any] = yaml.safe_load(handle) or {}

    project_root = config_path.parent.parent.resolve() if config_path.parent.name == "config" else config_path.parent.resolve()

    config = AppConfig.model_validate(
        {
            "base_dir": project_root,
            "paths": payload.get("paths", {}),
            "filenames": payload.get("filenames", {}),
            "llm": payload.get("llm", {}),
            "pdf": payload.get("pdf", {}),
            "excel": payload.get("excel", {}),
            "pipeline": payload.get("pipeline", {}),
            "data": payload.get("data", {}),
        }
    )
    return config.resolved()