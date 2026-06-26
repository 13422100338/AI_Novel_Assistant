"""TXT/DOCX manuscript import helpers.

The UI decides when to ask the model for an import plan. This module handles
the deterministic file reading, rough chapter splitting, safe naming, and
writing the normalized import plan into a project.
"""

import os
import re

import docx

from import_agent import ImportedChapter, normalize_import_plan, parse_hash_chapter_manuscript

INVALID_FILENAME_CHARS = r'[\\/:*?"<>|]'


def unique_name(base_name: str, existing: set[str], fallback: str, max_len: int = 60) -> str:
    """Return a filesystem-safe unique name against an existing-name set."""
    safe = re.sub(INVALID_FILENAME_CHARS, "_", (base_name or fallback).strip())[:max_len] or fallback
    if safe not in existing:
        return safe

    counter = 2
    while f"{safe}-{counter}" in existing:
        counter += 1
    return f"{safe}-{counter}"


def read_import_file(path: str) -> str:
    """Read a TXT or DOCX manuscript file as plain text."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        document = docx.Document(path)
        return "\n".join(p.text for p in document.paragraphs if p.text.strip())

    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def split_imported_text(text: str, fallback_title: str) -> list[tuple[str, str]]:
    """Split plain manuscript text with common chapter headings."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []

    pattern = re.compile(
        r"(?m)^(第[零一二三四五六七八九十百千万\d]+[章节卷回][^\n]{0,40}|Chapter\s+\d+[^\n]{0,40})\s*$"
    )
    matches = list(pattern.finditer(text))
    chapters = []
    if matches:
        for idx, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            if content:
                chapters.append((title, content))

    if chapters:
        return chapters
    return [(fallback_title or "导入章节", text)]


def parse_import_text(text: str, source_file: str, start_offset: int = 0) -> list[ImportedChapter]:
    """Parse one manuscript text into ImportedChapter objects.

    The preferred format is handled by the model-assisted import parser:
    ``#第X章 标题`` plus ``（第X章 完）``. If that format is absent, fall back to
    common chapter headings or a single imported chapter.
    """
    smart_chapters = parse_hash_chapter_manuscript(text, source_file)
    if smart_chapters:
        for chapter in smart_chapters:
            chapter.id = start_offset + chapter.id
        return smart_chapters

    fallback_title = os.path.splitext(source_file)[0]
    chapters = []
    for title, content in split_imported_text(text, fallback_title):
        chapters.append(
            ImportedChapter(
                id=start_offset + len(chapters) + 1,
                source_file=source_file,
                title=title,
                content=content,
            )
        )
    return chapters


def parse_import_file(path: str, start_offset: int = 0) -> list[ImportedChapter]:
    """Read and parse one import file."""
    text = read_import_file(path)
    return parse_import_text(text, os.path.basename(path), start_offset=start_offset)


def apply_import_plan_to_project(project, chapters: list[ImportedChapter], plan: dict):
    """Write a normalized import plan into a NovelProject-like object.

    Returns ``(normalized_plan, imported_positions)`` where imported positions
    are ``(volume_index, chapter_index)`` tuples for later memory analysis.
    """
    chapters_by_id = {chapter.id: chapter for chapter in chapters}
    normalized_plan = normalize_import_plan(plan, chapters)
    imported_positions = []

    for volume in normalized_plan.get("volumes", []):
        existing_volumes = {v["name"] for v in project.meta["volumes"]}
        vol_name = unique_name(volume.get("title") or "导入稿件", existing_volumes, "导入稿件")
        project.add_volume(vol_name, volume.get("synopsis", "由智能导入创建的卷。"))
        v_idx = len(project.meta["volumes"]) - 1

        for chapter_id in volume.get("chapters", []):
            chapter = chapters_by_id.get(int(chapter_id))
            if not chapter:
                continue

            existing_chapters = {c["name"] for c in project.meta["volumes"][v_idx]["chapters"]}
            chap_name = unique_name(chapter.title, existing_chapters, "导入章节")
            synopsis = "由智能导入创建，等待 AI 生成压缩摘要。"
            project.add_chapter(v_idx, chap_name, synopsis=synopsis, ai_synopsis="")
            c_idx = len(project.meta["volumes"][v_idx]["chapters"]) - 1
            project.save_chapter_content(vol_name, chap_name, chapter.content)
            imported_positions.append((v_idx, c_idx))

    return normalized_plan, imported_positions
