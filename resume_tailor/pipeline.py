"""
Author: Shridhar Mashalkar
This file is part of an open-source project licensed under the AGPL-3.0 License.
You are free to use, modify, and distribute this code under the terms of the LICENSE file.
"""
from __future__ import annotations

import json
import logging
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from resume_tailor.config import AppConfig, load_config
from resume_tailor.excel import append_job_row, build_tracking_row
from resume_tailor.files import ensure_directory, move_file, slugify
from resume_tailor.latex import render_cover_letter_tex, render_resume_tex
from resume_tailor.llm import build_chat_model, call_stage_with_retries, generate_cover_letter, generate_resume_tailoring, screen_job_description
from resume_tailor.pdf import PDFBuildError, compile_latex
from resume_tailor.resume_data import load_resume_data

LOGGER = logging.getLogger(__name__)


def run_pipeline(config_path: Path) -> None:
    config = load_config(config_path)
    resume_data = load_resume_data(config.paths.resume_yaml_path)
    model = build_chat_model(config)

    for directory in [config.paths.jd_input_folder, config.paths.output_folder, config.paths.error_folder, config.paths.work_root, config.paths.jobs_excel_path.parent]:
        ensure_directory(directory)

    job_files = sorted(config.paths.jd_input_folder.glob(config.pipeline.jd_glob))
    LOGGER.info("Found %s JD files", len(job_files))
    for jd_path in job_files:
        try:
            _process_job(config=config, model=model, resume_data=resume_data, jd_path=jd_path)
        except Exception as exc:
            LOGGER.exception("Failed to process %s", jd_path)
            _route_to_error(config, jd_path, exc)


def _process_job(config: AppConfig, model, resume_data, jd_path: Path) -> None:
    jd_text = jd_path.read_text(encoding=config.pipeline.source_encoding)
    LOGGER.info("Processing JD: %s", jd_path.name)

    screening = call_stage_with_retries(
        stage_name="ATS screening",
        model=model,
        max_retries=config.llm.max_retries,
        start_retry=config.llm.retry_start,
        runner=lambda llm: screen_job_description(llm, jd_text, resume_data),
    )

    resume_tailoring = call_stage_with_retries(
        stage_name="resume tailoring",
        model=model,
        max_retries=config.llm.max_retries,
        start_retry=config.llm.retry_start,
        runner=lambda llm: generate_resume_tailoring(llm, jd_text, screening, resume_data, config),
    )

    cover_letter = call_stage_with_retries(
        stage_name="cover letter",
        model=model,
        max_retries=config.llm.max_retries,
        start_retry=config.llm.retry_start,
        runner=lambda llm: generate_cover_letter(llm, jd_text, screening, resume_tailoring, resume_data, config),
    )

    job_slug = _build_job_slug(config, screening.company_name, screening.job_title, jd_path.stem)
    output_dir = ensure_directory(config.paths.output_folder / job_slug)
    temp_job_dir = Path(tempfile.mkdtemp(prefix=f"{job_slug}_", dir=str(config.paths.work_root)))
    try:
        build_dir = ensure_directory(temp_job_dir / "build")
        resume_template_text = config.paths.resume_template_path.read_text(encoding="utf-8")
        cover_template_text = config.paths.cover_letter_template_path.read_text(encoding="utf-8")

        rendered_resume = render_resume_tex(
            resume_template_text,
            resume_data,
            resume_tailoring,
            screening,
            include_projects=config.data.include_projects,
            include_certifications=config.data.include_certifications,
            include_publications=config.data.include_publications,
        )
        rendered_cover = render_cover_letter_tex(cover_template_text, resume_data, screening, cover_letter)

        output_resume_tex = output_dir / config.filenames.resume_tex_filename
        output_cover_tex = output_dir / config.filenames.cover_letter_tex_filename
        output_resume_tex.write_text(rendered_resume, encoding="utf-8")
        output_cover_tex.write_text(rendered_cover, encoding="utf-8")

        developercv_source = config.paths.resume_template_path.parent / "developercv.cls"
        if developercv_source.exists():
            shutil.copy2(developercv_source, output_dir / developercv_source.name)

        resume_tex = build_dir / config.filenames.resume_tex_filename
        cover_tex = build_dir / config.filenames.cover_letter_tex_filename
        ensure_directory(resume_tex.parent)
        ensure_directory(cover_tex.parent)
        resume_tex.write_text(rendered_resume, encoding="utf-8")
        cover_tex.write_text(rendered_cover, encoding="utf-8")

        for asset_name in ["developercv.cls", "extarticle.cls"]:
            asset_path = config.paths.resume_template_path.parent / asset_name
            if asset_path.exists():
                shutil.copy2(asset_path, build_dir / asset_name)

        compile_latex(resume_tex, output_dir / config.filenames.resume_pdf_filename, config)
        compile_latex(cover_tex, output_dir / config.filenames.cover_letter_pdf_filename, config)

        analysis_path = output_dir / config.filenames.analysis_filename
        analysis_path.write_text(
            "\n".join(
                [
                    "Step 1: Screening",
                    json.dumps(screening.model_dump(), ensure_ascii=False, indent=2),
                    "",
                    "Step 2: Resume Transformation",
                    json.dumps(resume_tailoring.model_dump(), ensure_ascii=False, indent=2),
                    "",
                    "Step 3: Cover Letter",
                    json.dumps(cover_letter.model_dump(), ensure_ascii=False, indent=2),
                ]
            ),
            encoding="utf-8",
        )

        tracking_row = build_tracking_row(source_jd=jd_path, output_folder=output_dir, screening=screening, processed_at=datetime.now(timezone.utc))
        append_job_row(config, tracking_row)

        move_file(jd_path, output_dir / config.filenames.jd_filename)
        LOGGER.info("Completed JD: %s -> %s", jd_path.name, output_dir)
    finally:
        shutil.rmtree(temp_job_dir, ignore_errors=True)


def _route_to_error(config: AppConfig, jd_path: Path, exc: Exception) -> None:
    ensure_directory(config.paths.error_folder)
    destination = config.paths.error_folder / f"{jd_path.stem}{config.filenames.error_jd_suffix}{jd_path.suffix}"
    move_file(jd_path, destination)


def _build_job_slug(config: AppConfig, company_name: str, job_title: str, fallback: str) -> str:
    company_slug = slugify(
        company_name,
        separator=config.pipeline.job_folder_separator,
        preserve_case=config.pipeline.preserve_case,
        max_length=config.pipeline.folder_slug_max_length,
    )
    job_slug = slugify(
        job_title,
        separator=config.pipeline.job_folder_separator,
        preserve_case=config.pipeline.preserve_case,
        max_length=config.pipeline.folder_slug_max_length,
    )
    if company_slug == "job":
        company_slug = slugify(
            fallback,
            separator=config.pipeline.job_folder_separator,
            preserve_case=config.pipeline.preserve_case,
            max_length=config.pipeline.folder_slug_max_length,
        )
    if job_slug == "job":
        job_slug = slugify(
            fallback,
            separator=config.pipeline.job_folder_separator,
            preserve_case=config.pipeline.preserve_case,
            max_length=config.pipeline.folder_slug_max_length,
        )
    return f"{company_slug}{config.pipeline.job_folder_separator}{job_slug}"