"""
Author: Shridhar Mashalkar
This file is part of an open-source project licensed under the AGPL-3.0 License.
You are free to use, modify, and distribute this code under the terms of the LICENSE file.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TypeVar

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from resume_tailor.config import AppConfig
from resume_tailor.schemas import CoverLetterResult, ResumeData, ResumeTailoringResult, ScreeningResult

load_dotenv()

T = TypeVar("T", ScreeningResult, ResumeTailoringResult, CoverLetterResult)
PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


@lru_cache(maxsize=None)
def _load_prompt_text(filename: str) -> str:
    prompt_path = PROMPTS_DIR / filename
    try:
        return prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Missing prompt file: {prompt_path}") from exc


ATS_PROMPT = _load_prompt_text("ats_prompt.txt")
RESUME_TAILOR_PROMPT = _load_prompt_text("resume_tailor.txt")
COVER_LETTER_PROMPT = _load_prompt_text("cover_letter.txt")


@dataclass(slots=True)
class LLMOutputs:
    screening: ScreeningResult
    resume: ResumeTailoringResult
    cover_letter: CoverLetterResult


class ResponseValidationError(RuntimeError):
    pass


def build_chat_model(config: AppConfig) -> ChatOpenAI:
    return ChatOpenAI(model=config.llm.model_name, temperature=config.llm.temperature)


def screen_job_description(model: ChatOpenAI, jd_text: str, resume_data: ResumeData) -> ScreeningResult:
    system_prompt = ATS_PROMPT
    human_prompt = (
        f"Resume facts:\n{json.dumps(resume_data.model_dump(), ensure_ascii=False, indent=2)}\n\n"
        f"Job description:\n{jd_text}"
    )
    return _run_json_stage(model, system_prompt, human_prompt, ScreeningResult)


def generate_resume_tailoring(
    model: ChatOpenAI,
    jd_text: str,
    screening: ScreeningResult,
    resume_data: ResumeData,
    config: AppConfig,
) -> ResumeTailoringResult:
    bullet_counts_instr = "\n".join(
        f"- {exp.company} → EXACTLY {exp.TotalBulletPointsToInclude} bullets"
        for exp in resume_data.experience
    )
    system_prompt = RESUME_TAILOR_PROMPT.replace("BULLET_COUNTS_PLACEHOLDER", bullet_counts_instr)
    system_prompt = system_prompt.replace("TOTAL_EXPERIENCE_PLACEHOLDER", str(resume_data.totalExperienceInYears))

    context_parts = [
        f"Name: {resume_data.name}",
        f"Location: {resume_data.location}",
        "",
        "Experience:"
    ]
    for exp in resume_data.experience:
        context_parts.append(f"- {exp.company} | {exp.title} | {exp.date_range}")
    context_parts.append("")
    context_parts.append("Education:")
    for edu in resume_data.education:
        context_parts.append(f"- {edu.degree} ({edu.details})")
        
    input_content_str = "\n".join(context_parts)
    system_prompt = system_prompt.replace("INPUTCONTENTTOINSERT", input_content_str)

    human_prompt = build_resume_tailoring_human_prompt(
        jd_text=jd_text,
        screening=screening,
        resume_data=resume_data,
        send_missing_keywords=config.data.send_missing_keywords,
        send_current_resume=config.data.send_current_resume,
        send_raw_jd=config.data.send_raw_jd,
    )
    return _run_json_stage(model, system_prompt, human_prompt, ResumeTailoringResult)


def build_resume_tailoring_human_prompt(
    *,
    jd_text: str,
    screening: ScreeningResult,
    resume_data: ResumeData,
    send_missing_keywords: bool,
    send_current_resume: bool,
    send_raw_jd: bool,
) -> str:
    screening_payload = screening.model_dump(exclude={"missing_keywords"} if not send_missing_keywords else set())
    sections = []
    if send_raw_jd:
        sections.append(f"Job description:\n{jd_text}")
    sections.append(f"Screening JSON:\n{json.dumps(screening_payload, ensure_ascii=False, indent=2)}")
    if send_current_resume:
        sections.append(
            f"Current resume JSON from resume.yaml:\n{json.dumps(resume_data.model_dump(), ensure_ascii=False, indent=2)}"
        )
    return "\n\n".join(sections)


def generate_cover_letter(
    model: ChatOpenAI,
    jd_text: str,
    screening: ScreeningResult,
    tailored_resume: ResumeTailoringResult,
    resume_data: ResumeData,
    config: AppConfig,
) -> CoverLetterResult:
    system_prompt = COVER_LETTER_PROMPT.replace("JOBTITLECANDIDATEINSERT", f"[Job Title] – {resume_data.name}")
    human_prompt = build_cover_letter_human_prompt(
        jd_text=jd_text,
        screening=screening,
        tailored_resume=tailored_resume,
        send_raw_jd=config.data.send_raw_jd,
    )
    return _run_json_stage(model, system_prompt, human_prompt, CoverLetterResult)


def build_cover_letter_human_prompt(
    *,
    jd_text: str,
    screening: ScreeningResult,
    tailored_resume: ResumeTailoringResult,
    send_raw_jd: bool,
) -> str:
    sections = [
        f"Screening JSON:\n{json.dumps(screening.model_dump(), ensure_ascii=False, indent=2)}",
        f"Tailored resume JSON from the second LLM:\n{json.dumps(tailored_resume.model_dump(), ensure_ascii=False, indent=2)}",
    ]
    if send_raw_jd:
        sections.append(f"Job description:\n{jd_text}")
    return "\n\n".join(sections)


def _run_json_stage(model: ChatOpenAI, system_prompt: str, human_prompt: str, schema: type[T]) -> T:
    structured_model = model.with_structured_output(schema, method="function_calling")

    return structured_model.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]
    )


def _parse_json_response(content: str, schema: type[T]) -> T:
    text = content.strip()
    if text.startswith("```"):
        raise ResponseValidationError("Response contained markdown fences")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ResponseValidationError(f"Invalid JSON response: {content}") from exc
    try:
        return schema.model_validate(payload)
    except Exception as exc:
        raise ResponseValidationError(str(exc)) from exc


def call_stage_with_retries(*, stage_name: str, model: ChatOpenAI, max_retries: int, start_retry: int, runner):
    last_error: Exception | None = None
    retry_count = start_retry
    while retry_count <= max_retries:
        try:
            return runner(model)
        except Exception as exc:
            last_error = exc
            if retry_count >= max_retries:
                break
            retry_count += 1
    raise ResponseValidationError(f"{stage_name} failed after {retry_count} retries: {last_error}")