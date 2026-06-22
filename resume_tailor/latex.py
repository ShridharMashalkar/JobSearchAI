"""
Author: Shridhar Mashalkar
This file is part of an open-source project licensed under the AGPL-3.0 License.
You are free to use, modify, and distribute this code under the terms of the LICENSE file.
"""
from __future__ import annotations

import re

from resume_tailor.schemas import CoverLetterResult, ResumeData, ResumeTailoringResult, ScreeningResult


def escape_latex(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    escaped = value
    for source, replacement in replacements.items():
        escaped = escaped.replace(source, replacement)
    return escaped


def join_items(items: list[str]) -> str:
    return ", ".join(escape_latex(item) for item in items)


def _replace_token(rendered: str, token: str, replacement: str) -> str:
    pattern = rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])"
    return re.sub(pattern, lambda _match: replacement, rendered)


def render_resume_tex(
    template_text: str,
    resume_data: ResumeData,
    tailored: ResumeTailoringResult,
    screening: ScreeningResult,
    *,
    include_projects: bool = True,
    include_certifications: bool = True,
    include_publications: bool = True,
) -> str:
    rendered = template_text
    rendered = _replace_token(rendered, "NAMEINSERTHERE", escape_latex(resume_data.name))
    rendered = _replace_token(rendered, "ROLEINSERTHERE", escape_latex(screening.job_title or resume_data.headline))
    rendered = _replace_token(rendered, "SUMMARYINSERTHERE", escape_latex(tailored.professional_summary))
    rendered = _replace_token(rendered, "LOCATIONINSERTHERE", escape_latex(resume_data.location))
    rendered = _replace_token(rendered, "PHONEINSERTHERE", escape_latex(resume_data.phone))
    rendered = _replace_token(rendered, "EMAILURLINSERTHERE", resume_data.email)
    rendered = _replace_token(rendered, "EMAILTEXTINSERTHERE", escape_latex(resume_data.email))
    rendered = _replace_token(rendered, "LINKEDINURLINSERTHERE", resume_data.linkedin_url)
    rendered = _replace_token(rendered, "LINKEDINTEXTINSERTHERE", escape_latex(resume_data.linkedin_text))

    rendered = _replace_resume_education_placeholders(rendered, resume_data, tailored)
    rendered = _replace_resume_experience_placeholders(rendered, resume_data, tailored)

    rendered = _replace_token(rendered, "TECHNICALSKILLSINSERTHERE", join_items(tailored.technical_skills or resume_data.skills.get("technical", [])))
    rendered = _replace_token(rendered, "TECHSTACKINSERTHERE", join_items(tailored.tech_stack or resume_data.skills.get("tech_stack", [])))
    rendered = _replace_token(rendered, "SOFTSKILLSINSERTHERE", join_items(tailored.soft_skills or resume_data.skills.get("soft", [])))

    rendered = _replace_projects(rendered, resume_data, tailored, include_projects)
    rendered = _replace_certifications(rendered, resume_data, include_certifications)
    rendered = _replace_publications(rendered, resume_data, include_publications)
    rendered = _replace_token(rendered, "LANGUAGESINSERTHERE", join_items(resume_data.languages))
    rendered = _replace_token(rendered, "HOBBIESINSERTHERE", join_items(resume_data.hobbies))

    rendered = rendered.replace(escape_latex(resume_data.summary), escape_latex(tailored.professional_summary), 1)
    rendered = _replace_resume_summary_block(rendered, tailored.professional_summary)
    rendered = _replace_masters_focus_block(rendered, tailored.masters_focus, resume_data)
    return rendered


def render_cover_letter_tex(
    template_text: str,
    resume_data: ResumeData,
    screening: ScreeningResult,
    cover_letter: CoverLetterResult,
) -> str:
    rendered = template_text
    rendered = _replace_token(rendered, "NAMEINSERTHERE", escape_latex(resume_data.name))
    rendered = _replace_token(rendered, "LOCATIONINSERTHERE", escape_latex(resume_data.location))
    rendered = _replace_token(rendered, "PHONEINSERTHERE", escape_latex(resume_data.phone))
    rendered = _replace_token(rendered, "EMAILURLINSERTHERE", resume_data.email)
    rendered = _replace_token(rendered, "EMAILTEXTINSERTHERE", escape_latex(resume_data.email))
    rendered = _replace_token(rendered, "LINKEDINURLINSERTHERE", resume_data.linkedin_url)
    rendered = _replace_token(rendered, "LINKEDINTEXTINSERTHERE", escape_latex(resume_data.linkedin_text))
    rendered = _replace_token(rendered, "COMPANYNAMEINSERTHERE", escape_latex(screening.company_name))
    rendered = _replace_token(rendered, "SUBJECTINSERTHERE", escape_latex(cover_letter.subject))

    first_paragraph = _normalize_cover_letter_paragraph(cover_letter.first_paragraph, resume_data.name)
    second_paragraph = _normalize_cover_letter_paragraph(cover_letter.second_paragraph, resume_data.name)
    third_paragraph = _normalize_cover_letter_paragraph(cover_letter.third_paragraph, resume_data.name)
    closing_paragraph = _normalize_cover_letter_paragraph(cover_letter.closing_paragraph, resume_data.name, remove_signoff=True)
    rendered = _replace_token(rendered, "FIRSTPARAGRAPHINSERTHERE", escape_latex(first_paragraph))
    rendered = _replace_token(rendered, "SECONDPARAGRAPHINSERTHERE", escape_latex(second_paragraph))
    rendered = _replace_token(rendered, "THIRDPARAGRAPHINSERTHERE", escape_latex(third_paragraph))
    rendered = _replace_token(rendered, "CLOSINGPARAGRAPHINSERTHERE", escape_latex(closing_paragraph))

    return _collapse_duplicate_paragraphs(rendered)


def _replace_resume_education_placeholders(rendered: str, resume_data: ResumeData, tailored: ResumeTailoringResult) -> str:
    pattern = r"%BEGIN_EDUCATION%(.*?)%END_EDUCATION%"
    match = re.search(pattern, rendered, re.DOTALL)
    if not match:
        return rendered

    template_block = match.group(1)
    rendered_educations = []
    for index, education in enumerate(resume_data.education):
        block = template_block
        block = _replace_token(block, "EDUCATIONDATERANGEINSERTHERE", escape_latex(education.date_range))
        block = _replace_token(block, "EDUCATIONDEGREEINSERTHERE", escape_latex(education.degree))
        block = _replace_token(block, "EDUCATIONINSTITUTIONINSERTHERE", escape_latex(education.institution))
        block = _replace_token(block, "EDUCATIONDETAILSINSERTHERE", escape_latex(education.details))

        focus_value = ""
        if index == 0:
            focus_value = tailored.masters_focus or education.focus or ""
        else:
            focus_value = education.focus or ""

        if focus_value:
            focus_str = f"\\\\Focus: {escape_latex(focus_value)}"
        else:
            focus_str = ""

        block = _replace_token(block, "EDUCATIONFOCUSINSERTHERE", focus_str)
        rendered_educations.append(block)

    replacement = "\n".join(rendered_educations)
    rendered = rendered.replace(match.group(0), replacement)
    return rendered


def _replace_resume_experience_placeholders(rendered: str, resume_data: ResumeData, tailored: ResumeTailoringResult) -> str:
    pattern = r"%BEGIN_EXPERIENCE%(.*?)%END_EXPERIENCE%"
    match = re.search(pattern, rendered, re.DOTALL)
    if not match:
        return rendered

    template_block = match.group(1)
    rendered_experiences = []
    for experience in resume_data.experience:
        block = template_block
        block = _replace_token(block, "EXPERIENCEDATERANGEINSERTHERE", escape_latex(experience.date_range))
        block = _replace_token(block, "EXPERIENCELOCATIONINSERTHERE", escape_latex(experience.location))
        block = _replace_token(block, "EXPERIENCETITLEINSERTHERE", escape_latex(experience.title))
        block = _replace_token(block, "EXPERIENCECOMPANYINSERTHERE", escape_latex(experience.company))

        target_bullets = _resolve_tailored_bullets(experience.company, experience.title, tailored.job_bullet_points, experience.bullets)
        bullet_lines = "\n".join(f"    \\item {escape_latex(bullet)}" for bullet in target_bullets)
        block = _replace_token(block, "EXPERIENCEBULLETSINSERTHERE", bullet_lines)
        rendered_experiences.append(block)

    replacement = "\n".join(rendered_experiences)
    rendered = rendered.replace(match.group(0), replacement)
    return rendered


def _normalize_cover_letter_paragraph(text: str, candidate_name: str, *, remove_signoff: bool = False) -> str:
    normalized = text.strip()
    normalized = normalized.removeprefix("Dear Hiring Team,").strip()
    normalized = normalized.removeprefix("Dear Hiring Team").strip()
    normalized = normalized.removeprefix("Dear Hiring Team at ").strip()
    normalized = normalized.removeprefix("Dear Hiring Team at Oliver Bernard,").strip()
    normalized = normalized.removeprefix("Dear Hiring Team at Oliver Bernard").strip()
    if remove_signoff:
        normalized = normalized.replace("Sincerely,", "").strip()
        normalized = normalized.replace("Sincerely", "").strip()
        normalized = normalized.replace(candidate_name, "").strip()
        normalized = normalized.replace("John Doe", "").strip()
        normalized = normalized.replace("Yours sincerely,", "").strip()
        normalized = normalized.replace("Best regards,", "").strip()
    return _collapse_repeated_sentence_block(normalized)


def _collapse_repeated_sentence_block(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return compact

    sentences = re.split(r"(?<=[.!?])\s+", compact)
    if len(sentences) % 2 == 0:
        midpoint = len(sentences) // 2
        first_half = sentences[:midpoint]
        second_half = sentences[midpoint:]
        if first_half == second_half:
            return " ".join(first_half).strip()

    duplicate_match = re.fullmatch(r"(?P<chunk>.+?)\s+(?P=chunk)", compact)
    if duplicate_match:
        return duplicate_match.group("chunk").strip()

    return compact


def _collapse_duplicate_paragraphs(text: str) -> str:
    paragraphs = re.split(r"\n\s*\n", text.strip())
    if not paragraphs:
        return text.strip()

    collapsed: list[str] = []
    previous_paragraph: str | None = None
    for paragraph in paragraphs:
        normalized_paragraph = paragraph.strip()
        if not normalized_paragraph:
            continue
        if previous_paragraph is not None and normalized_paragraph == previous_paragraph:
            continue
        collapsed.append(normalized_paragraph)
        previous_paragraph = normalized_paragraph

    return "\n\n".join(collapsed)


def _replace_resume_summary_block(rendered: str, summary_text: str) -> str:
    pattern = re.compile(
        r"(\\begin\{minipage\}\[t\]\{0\.45\\textwidth\}\n\n.*?\\vspace\{0\.2cm\}\n\{\\large \\textbf\{.*?\}\}\n\n\\vspace\{0\.2cm\}\n)(.*?)(\n\\end\{minipage\})",
        re.DOTALL,
    )
    normalized_summary = re.sub(r"\s+", " ", summary_text).strip()

    def replace_match(match: re.Match[str]) -> str:
        return f"{match.group(1)}{escape_latex(normalized_summary)}{match.group(3)}"

    return pattern.sub(replace_match, rendered, count=1)


def _replace_experience_itemize_blocks(
    rendered: str,
    resume_data: ResumeData,
    tailored: ResumeTailoringResult,
) -> str:
    pattern = re.compile(
        r"(\\entry\s*\n\s*\{.*?\n\s*\{.*?\n\s*\{.*?\n\s*\{\n\s*\\begin\{itemize\}\[leftmargin=\*\]\n)(.*?)(\n\s*\\end\{itemize\}\n\s*\}\n)",
        re.DOTALL,
    )
    experience_iter = iter(resume_data.experience)

    def replace_match(match: re.Match[str]) -> str:
        experience = next(experience_iter, None)
        if experience is None:
            return match.group(0)

        target_bullets = _resolve_tailored_bullets(experience.company, experience.title, tailored.job_bullet_points, experience.bullets)
        bullet_lines = "\n".join(f"    \\item {escape_latex(bullet)}" for bullet in target_bullets)
        return f"{match.group(1)}{bullet_lines}{match.group(3)}"

    return pattern.sub(replace_match, rendered)


def _resolve_tailored_bullets(
    company_name: str,
    job_title: str,
    tailored_bullets: dict[str, list[str]],
    fallback_bullets: list[str],
) -> list[str]:
    company_aliases = {
        _normalize_label(company_name),
        _normalize_label(job_title),
        _normalize_label(f"{company_name} {job_title}"),
    }

    best_match: list[str] | None = None
    best_score = 0
    for key, bullets in tailored_bullets.items():
        normalized_key = _normalize_label(key)
        score = _match_score(normalized_key, company_aliases)
        if score > best_score:
            best_score = score
            best_match = bullets

    return best_match if best_match is not None and best_score > 0 else fallback_bullets


def _match_score(normalized_key: str, aliases: set[str]) -> int:
    score = 0
    for alias in aliases:
        if not alias or not normalized_key:
            continue
        if normalized_key == alias:
            score = max(score, 100)
        elif normalized_key in alias or alias in normalized_key:
            score = max(score, 80)
        else:
            key_tokens = set(normalized_key.split())
            alias_tokens = set(alias.split())
            if key_tokens and key_tokens <= alias_tokens:
                score = max(score, 60)
            elif alias_tokens and alias_tokens <= key_tokens:
                score = max(score, 50)
            elif key_tokens & alias_tokens:
                score = max(score, 30)
    return score


def _normalize_label(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def _build_experience_block(experience, bullets: list[str], *, escape_values: bool) -> str:
    formatter = escape_latex if escape_values else (lambda value: value)
    bullet_lines = "\n".join(f"    \\item {formatter(bullet)}" for bullet in bullets)
    return (
        f"  \\entry\n"
        f"  {{{formatter(experience.date_range)}\\\\\\footnotesize{{{formatter(experience.location)}}}}}\n"
        f"  {{{formatter(experience.title)}}}\n"
        f"  {{{formatter(experience.company)}}}\n"
        f"  {{\n"
        f"  \\begin{{itemize}}[leftmargin=*]\n"
        f"{bullet_lines}\n"
        f"  \\end{{itemize}}\n"
        f"  }}\n"
    )


def _replace_masters_focus_block(rendered: str, masters_focus: str, resume_data: ResumeData) -> str:
    normalized_focus = re.sub(r"\s+", " ", masters_focus).strip()
    if not normalized_focus:
        return rendered

    escaped_focus = escape_latex(normalized_focus)
    pattern = re.compile(
        r"(\\Focus:\s*)([^}\r\n]*)(\})",
    )
    for education in resume_data.education:
        if not education.focus:
            continue

        source_text = f"{escape_latex(education.details)}\\Focus: {escape_latex(education.focus)}" + "}"
        target_text = f"{escape_latex(education.details)}\\Focus: {escaped_focus}" + "}"
        if source_text in rendered:
            return rendered.replace(source_text, target_text, 1)

    def replace_match(match: re.Match[str]) -> str:
        return f"{match.group(1)}{escaped_focus}{match.group(3)}"

    return pattern.sub(replace_match, rendered, count=1)


def _replace_projects(rendered: str, resume_data: ResumeData, tailored: ResumeTailoringResult, include_projects: bool) -> str:
    pattern = r"%BEGIN_PROJECTS%(.*?)%END_PROJECTS%"
    match = re.search(pattern, rendered, re.DOTALL)
    if not match:
        return rendered

    project_items = tailored.projects or resume_data.projects
    if include_projects and project_items:
        content = match.group(1)
        content = _replace_token(content, "PROJECT1NAMEINSERTHERE", escape_latex(project_items[0].name))
        content = _replace_token(content, "PROJECT1DESCRIPTIONINSERTHERE", escape_latex(project_items[0].description))
        
        if len(project_items) > 1:
            content = _replace_token(content, "PROJECT2NAMEINSERTHERE", escape_latex(project_items[1].name))
            content = _replace_token(content, "PROJECT2DESCRIPTIONINSERTHERE", escape_latex(project_items[1].description))
        else:
            content = _replace_token(content, "PROJECT2NAMEINSERTHERE", "")
            content = _replace_token(content, "PROJECT2DESCRIPTIONINSERTHERE", "")
            
        rendered = rendered.replace(match.group(0), content)
    else:
        rendered = rendered.replace(match.group(0), "")
    return rendered


def _replace_certifications(rendered: str, resume_data: ResumeData, include_certifications: bool) -> str:
    pattern = r"%BEGIN_CERTIFICATIONS%(.*?)%END_CERTIFICATIONS%"
    match = re.search(pattern, rendered, re.DOTALL)
    if not match:
        return rendered

    if include_certifications and resume_data.certifications:
        content = match.group(1)
        content = _replace_token(content, "CERTIFICATIONSINSERTHERE", ", ".join(escape_latex(item) for item in resume_data.certifications))
        rendered = rendered.replace(match.group(0), content)
    else:
        rendered = rendered.replace(match.group(0), "")
    return rendered


def _replace_publications(rendered: str, resume_data: ResumeData, include_publications: bool) -> str:
    pattern = r"%BEGIN_PUBLICATIONS%(.*?)%END_PUBLICATIONS%"
    match = re.search(pattern, rendered, re.DOTALL)
    if not match:
        return rendered

    if include_publications and resume_data.publications:
        content = match.group(1)
        content = _replace_token(content, "PUBLICATIONSINSERTHERE", ", ".join(escape_latex(item) for item in resume_data.publications))
        rendered = rendered.replace(match.group(0), content)
    else:
        rendered = rendered.replace(match.group(0), "")
    return rendered