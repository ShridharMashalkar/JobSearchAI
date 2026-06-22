"""
Author: Shridhar Mashalkar
This file is part of an open-source project licensed under the AGPL-3.0 License.
You are free to use, modify, and distribute this code under the terms of the LICENSE file.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScreeningResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str
    job_title: str
    job_url: str | None = None
    about_company: str
    role_summary: str
    key_responsibilities: list[str] = Field(default_factory=list)
    tech_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    overall_fit: int

    @field_validator("overall_fit")
    @classmethod
    def validate_fit(cls, value: int) -> int:
        if value < 1 or value > 10:
            raise ValueError("overall_fit must be between 1 and 10")
        return value


class ProjectTailoring(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str


class ResumeTailoringResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    professional_summary: str
    job_bullet_points: dict[str, list[str]] = Field(default_factory=dict)
    technical_skills: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    masters_focus: str
    projects: list[ProjectTailoring] = Field(default_factory=list)


class CoverLetterResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str
    first_paragraph: str
    second_paragraph: str
    third_paragraph: str
    closing_paragraph: str


class ResumeExperience(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date_range: str
    location: str
    title: str
    company: str
    bullets: list[str] = Field(default_factory=list)
    TotalBulletPointsToInclude: int = 3


class ResumeEducation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date_range: str
    degree: str
    institution: str
    details: str
    focus: str | None = None


class ResumeProject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str


class ResumeData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    location: str
    phone: str
    email: str
    linkedin_url: str
    linkedin_text: str
    headline: str
    summary: str
    skills: dict[str, list[str]]
    totalExperienceInYears: str | float | int = "3+"
    education: list[ResumeEducation] = Field(default_factory=list)
    experience: list[ResumeExperience] = Field(default_factory=list)
    projects: list[ResumeProject] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    publications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    hobbies: list[str] = Field(default_factory=list)


class JobTrackingRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    processed_at: str
    source_jd: str
    job_url: str | None = None
    output_folder: str
    status: str
    company_name: str
    job_title: str
    role_summary: str
    key_responsibilities: list[str]
    tech_skills: list[str]
    soft_skills: list[str]
    missing_keywords: list[str]
    overall_fit: int
    custom_notes: str | None = None



def ensure_model(payload: Any, model: type[BaseModel]) -> BaseModel:
    if isinstance(payload, model):
        return payload
    return model.model_validate(payload)