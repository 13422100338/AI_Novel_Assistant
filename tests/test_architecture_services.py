import tempfile
import unittest

from book_exporter import render_markdown, render_txt
from character_state_editor import format_character_state_for_edit, parse_character_state_from_edit
from manuscript_import_service import parse_import_text, split_imported_text, unique_name
from text_metrics import estimate_tokens


class FakeProject:
    def __init__(self):
        self.meta = {
            "volumes": [
                {
                    "name": "Volume One",
                    "chapters": [
                        {"name": "Chapter One"},
                        {"name": "Chapter Two"},
                    ],
                }
            ]
        }
        self.contents = {
            ("Volume One", "Chapter One"): "First paragraph.",
            ("Volume One", "Chapter Two"): "Second paragraph.",
        }

    def read_chapter_content(self, volume_name, chapter_name):
        return self.contents[(volume_name, chapter_name)]


class TextMetricTests(unittest.TestCase):
    def test_estimate_tokens_counts_ascii_and_cjk_differently(self):
        self.assertEqual(estimate_tokens(""), 0)
        self.assertEqual(estimate_tokens("abcd"), 1)
        self.assertGreater(estimate_tokens("你好世界"), estimate_tokens("abcd"))


class CharacterStateEditorTests(unittest.TestCase):
    def test_character_state_round_trips_between_row_and_edit_text(self):
        row = {
            "psychology": "警惕",
            "motivation": "查明真相",
            "current_goal": "进入剧院后台",
            "relationships": "怀疑师父",
            "recent_activity": "发现烧焦镜子",
            "last_seen": "第一卷/第一章",
        }

        text = format_character_state_for_edit(row)
        parsed = parse_character_state_from_edit(text)

        self.assertEqual(parsed["psychology"], "警惕")
        self.assertEqual(parsed["motivation"], "查明真相")
        self.assertEqual(parsed["last_seen"], "第一卷/第一章")

    def test_character_state_parser_accepts_ascii_colons(self):
        parsed = parse_character_state_from_edit("心理: 动摇\n动机: 保护同伴")

        self.assertEqual(parsed["psychology"], "动摇")
        self.assertEqual(parsed["motivation"], "保护同伴")


class ManuscriptImportServiceTests(unittest.TestCase):
    def test_unique_name_sanitizes_and_deduplicates(self):
        self.assertEqual(unique_name("第/一:章", {"第_一_章"}, "导入章节"), "第_一_章-2")

    def test_split_imported_text_uses_headings_when_present(self):
        chapters = split_imported_text("第一章 开端\n正文一\n第二章 转折\n正文二", "fallback")

        self.assertEqual(chapters, [("第一章 开端", "正文一"), ("第二章 转折", "正文二")])

    def test_parse_import_text_offsets_chapter_ids(self):
        chapters = parse_import_text("#第1章 开端\n正文\n（第1章 完）", "draft.txt", start_offset=10)

        self.assertEqual(chapters[0].id, 11)
        self.assertEqual(chapters[0].title, "第1章 开端")
        self.assertEqual(chapters[0].source_file, "draft.txt")


class BookExporterTests(unittest.TestCase):
    def test_render_markdown_and_txt_from_project(self):
        project = FakeProject()

        markdown = render_markdown(project, "Novel")
        text = render_txt(project, "Novel")

        self.assertIn("# Novel", markdown)
        self.assertIn("## Volume One", markdown)
        self.assertIn("### Chapter Two", markdown)
        self.assertIn("Second paragraph.", markdown)
        self.assertIn("《Novel》", text)
        self.assertIn("Chapter One", text)


if __name__ == "__main__":
    unittest.main()
