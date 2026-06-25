import json
import re
from dataclasses import dataclass


CHAPTER_HEADING_RE = re.compile(
    r"(?m)^\s*#{1,6}\s*(第[零一二三四五六七八九十百千万两〇零\d]+章[^\n#（(]{0,80}?)"
    r"(?:\s*[（(]\s*第[零一二三四五六七八九十百千万两〇零\d]+章\s*完\s*[）)])?\s*$"
)

CHAPTER_END_RE = re.compile(
    r"\s*[（(]\s*第[零一二三四五六七八九十百千万两〇零\d]+章\s*完\s*[）)]\s*$"
)


@dataclass
class ImportedChapter:
    id: int
    source_file: str
    title: str
    content: str

    @property
    def preview(self) -> str:
        compact = re.sub(r"\s+", " ", self.content).strip()
        return compact[:240]


def strip_chapter_end_marker(content: str) -> str:
    return CHAPTER_END_RE.sub("", content.strip()).strip()


def parse_hash_chapter_manuscript(text: str, source_file: str) -> list[ImportedChapter]:
    """Parse manuscripts in the user's format:

    #第X章XXX
    ...正文...
    （第X章 完）

    The end marker is optional for the final extraction because the next heading
    is the real structural boundary. The marker is removed from saved chapter
    content when present.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []

    matches = list(CHAPTER_HEADING_RE.finditer(text))
    if not matches:
        return []

    chapters: list[ImportedChapter] = []
    for idx, match in enumerate(matches):
        title = re.sub(r"\s+", " ", match.group(1).strip())
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        content = strip_chapter_end_marker(text[start:end])
        if content.strip():
            chapters.append(
                ImportedChapter(
                    id=len(chapters) + 1,
                    source_file=source_file,
                    title=title,
                    content=content,
                )
            )
    return chapters


def fallback_volume_plan(chapters: list[ImportedChapter], volume_title: str = "导入稿件") -> dict:
    return {
        "volumes": [
            {
                "title": volume_title,
                "synopsis": "根据原稿导入生成的默认卷。未启用模型分卷时，全部章节暂归入此卷。",
                "chapters": [chapter.id for chapter in chapters],
            }
        ]
    }


def normalize_import_plan(plan: dict, chapters: list[ImportedChapter]) -> dict:
    """Validate and repair model-produced volume plans.

    Guarantees every chapter id appears exactly once in volume order.
    """
    valid_ids = [chapter.id for chapter in chapters]
    valid_set = set(valid_ids)
    seen: set[int] = set()
    volumes = []

    for raw_volume in plan.get("volumes", []) if isinstance(plan, dict) else []:
        if not isinstance(raw_volume, dict):
            continue
        title = str(raw_volume.get("title") or f"第{len(volumes) + 1}卷").strip()
        synopsis = str(raw_volume.get("synopsis") or "").strip()
        chapter_ids = []
        for item in raw_volume.get("chapters", []):
            try:
                chapter_id = int(item)
            except Exception:
                continue
            if chapter_id in valid_set and chapter_id not in seen:
                chapter_ids.append(chapter_id)
                seen.add(chapter_id)
        if chapter_ids:
            volumes.append({"title": title, "synopsis": synopsis, "chapters": chapter_ids})

    missing = [chapter_id for chapter_id in valid_ids if chapter_id not in seen]
    if missing:
        volumes.append(
            {
                "title": "未分卷章节",
                "synopsis": "模型分卷结果未覆盖的章节，系统自动归档到此卷，建议人工复核。",
                "chapters": missing,
            }
        )

    if not volumes:
        return fallback_volume_plan(chapters)

    return {"volumes": volumes}


def import_plan_prompt(chapters: list[ImportedChapter]) -> str:
    chapter_lines = []
    for chapter in chapters:
        chapter_lines.append(
            json.dumps(
                {
                    "id": chapter.id,
                    "title": chapter.title,
                    "source_file": chapter.source_file,
                    "preview": chapter.preview,
                },
                ensure_ascii=False,
            )
        )

    return f"""
你是长篇小说稿件整理 Agent。现在给你一份原稿的章节列表，章节边界已经由程序根据“#第X章标题”和“（第X章 完）”格式可靠识别。

你的任务：
1. 根据章节标题和正文预览判断小说的卷结构。
2. 如果原稿没有明确卷名，请按剧情阶段合理分卷。
3. 卷名要像正式小说卷名，例如“第一卷 风起青萍”。
4. 每个章节 id 必须且只能出现一次。
5. 不要改写章节正文，不要编造不存在的章节。
6. 返回严格 JSON，不要 Markdown。

返回格式：
{{
  "volumes": [
    {{
      "title": "第一卷 卷名",
      "synopsis": "本卷剧情阶段概述，80字以内",
      "chapters": [1, 2, 3]
    }}
  ]
}}

章节列表：
{chr(10).join(chapter_lines)}
"""
