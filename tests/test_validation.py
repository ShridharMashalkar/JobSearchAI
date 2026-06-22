"""
Author: Shridhar Mashalkar
This file is part of an open-source project licensed under the AGPL-3.0 License.
You are free to use, modify, and distribute this code under the terms of the LICENSE file.
"""
from __future__ import annotations

import pytest

from resume_tailor.llm import build_cover_letter_human_prompt, build_resume_tailoring_human_prompt
from resume_tailor.schemas import ScreeningResult


def test_screening_result_rejects_out_of_range_fit() -> None:
    with pytest.raises(ValueError):
        ScreeningResult(
            company_name="Example",
            job_title="AI Engineer",
            role_summary="Summary",
            about_company="Example builds systems.",
            key_responsibilities=[],
            tech_skills=[],
            soft_skills=[],
            missing_keywords=[],
            overall_fit=11,
        )


def test_screening_result_accepts_valid_payload() -> None:
    result = ScreeningResult(
        company_name="Example",
        job_title="AI Engineer",
        role_summary="Summary",
        about_company="Example builds systems.",
        key_responsibilities=["Build systems"],
        tech_skills=["Python"],
        soft_skills=["communication"],
        missing_keywords=["AWS"],
        overall_fit=8,
    )
    assert result.overall_fit == 8


def test_resume_tailoring_prompt_can_exclude_missing_keywords_and_include_current_resume() -> None:
    screening = ScreeningResult(
        company_name="Example",
        job_title="AI Engineer",
        role_summary="Summary",
        about_company="Example builds systems.",
        key_responsibilities=["Build systems"],
        tech_skills=["Python"],
        soft_skills=["communication"],
        missing_keywords=["AWS"],
        overall_fit=8,
    )
    from resume_tailor.schemas import ResumeData

    resume_data = ResumeData(
        name="John Doe",
        location="Hildesheim, Germany",
        phone="123",
        email="test@example.com",
        linkedin_url="https://example.com",
        linkedin_text="linkedin.com/in/example",
        headline="Data Scientist",
        summary="Summary",
        skills={"technical": [], "tech_stack": [], "soft": []},
        hobbies=["Hiking"],
    )

    prompt = build_resume_tailoring_human_prompt(
        jd_text="job text",
        screening=screening,
        resume_data=resume_data,
        send_missing_keywords=False,
        send_current_resume=True,
        send_raw_jd=True,
    )

    assert '"missing_keywords"' not in prompt
    assert "job text" in prompt
    assert "Current resume JSON from resume.yaml" in prompt
    assert "John Doe" in prompt


def test_resume_tailoring_prompt_can_include_missing_keywords_without_current_resume() -> None:
    screening = ScreeningResult(
        company_name="Example",
        job_title="AI Engineer",
        role_summary="Summary",
        about_company="Example builds systems.",
        key_responsibilities=["Build systems"],
        tech_skills=["Python"],
        soft_skills=["communication"],
        missing_keywords=["AWS"],
        overall_fit=8,
    )
    from resume_tailor.schemas import ResumeData

    resume_data = ResumeData(
        name="John Doe",
        location="Hildesheim, Germany",
        phone="123",
        email="test@example.com",
        linkedin_url="https://example.com",
        linkedin_text="linkedin.com/in/example",
        headline="Data Scientist",
        summary="Summary",
        skills={"technical": [], "tech_stack": [], "soft": []},
        hobbies=["Hiking"],
    )

    prompt = build_resume_tailoring_human_prompt(
        jd_text="job text",
        screening=screening,
        resume_data=resume_data,
        send_missing_keywords=True,
        send_current_resume=False,
        send_raw_jd=False,
    )

    assert '"missing_keywords": [' in prompt
    assert "job text" not in prompt
    assert "Current resume JSON from resume.yaml" not in prompt


def test_cover_letter_prompt_can_include_raw_jd() -> None:
    screening = ScreeningResult(
        company_name="Example",
        job_title="AI Engineer",
        role_summary="Summary",
        about_company="Example builds systems.",
        key_responsibilities=["Build systems"],
        tech_skills=["Python"],
        soft_skills=["communication"],
        missing_keywords=["AWS"],
        overall_fit=8,
    )
    from resume_tailor.schemas import ResumeTailoringResult

    tailored_resume = ResumeTailoringResult(
        professional_summary="Summary",
        job_bullet_points={},
        technical_skills=[],
        tech_stack=[],
        soft_skills=[],
        masters_focus="Focus",
        projects=[],
    )

    prompt = build_cover_letter_human_prompt(
        jd_text="raw jd text",
        screening=screening,
        tailored_resume=tailored_resume,
        send_raw_jd=True,
    )

    assert "raw jd text" in prompt
    assert "Screening JSON" in prompt
    assert "Tailored resume JSON from the second LLM" in prompt


def test_cover_letter_prompt_can_omit_raw_jd() -> None:
    screening = ScreeningResult(
        company_name="Example",
        job_title="AI Engineer",
        role_summary="Summary",
        about_company="Example builds systems.",
        key_responsibilities=["Build systems"],
        tech_skills=["Python"],
        soft_skills=["communication"],
        missing_keywords=["AWS"],
        overall_fit=8,
    )
    from resume_tailor.schemas import ResumeTailoringResult

    tailored_resume = ResumeTailoringResult(
        professional_summary="Summary",
        job_bullet_points={},
        technical_skills=[],
        tech_stack=[],
        soft_skills=[],
        masters_focus="Focus",
        projects=[],
    )

    prompt = build_cover_letter_human_prompt(
        jd_text="raw jd text",
        screening=screening,
        tailored_resume=tailored_resume,
        send_raw_jd=False,
    )

    assert "raw jd text" not in prompt
    assert "Screening JSON" in prompt