import unittest

from context_builder import NovelContextBuilder


class FakeProject:
    def __init__(self):
        self.meta = {
            "global_synopsis": "旧城火灾案。",
            "characters": [
                {"name": "林秋", "gender": "男", "personality": "谨慎", "experience": "追查旧案"}
            ],
            "volumes": [
                {
                    "name": "第一卷",
                    "synopsis": "调查旧城。",
                    "chapters": [
                        {"name": "第1章", "synopsis": "抵达旧城", "ai_synopsis": "林秋抵达旧城。"},
                        {"name": "第2章", "synopsis": "发现钥匙", "ai_synopsis": ""},
                    ],
                }
            ],
        }

    def read_chapter_content(self, volume_name, chapter_name):
        return {
            ("第一卷", "第1章"): "林秋走进旧城，闻到潮湿灰烬味。",
            ("第一卷", "第2章"): "已有正文前半段。",
        }.get((volume_name, chapter_name), "")


class FakeMemory:
    def build_relevant_context(self, volume_name, chapter_name, query, limit_recent=8):
        return f"相关记忆：{query[:20]}"

    def build_context(self, volume_name, chapter_name, limit_recent=8):
        return "默认记忆"


class ContextBuilderModeTests(unittest.TestCase):
    def test_rewrite_mode_uses_standard_chapter_generation(self):
        _, user_prompt = NovelContextBuilder(FakeProject(), FakeMemory()).build_prompts(0, 1)

        self.assertIn("当前需撰写章节：第2章", user_prompt)
        self.assertIn("本章细纲要求：发现钥匙", user_prompt)
        self.assertNotIn("续写当前章", user_prompt)

    def test_continue_mode_includes_existing_content_and_no_repeat_instruction(self):
        _, user_prompt = NovelContextBuilder(FakeProject(), FakeMemory()).build_prompts(
            0,
            1,
            generation_mode="continue",
            existing_content="已有正文前半段。",
        )

        self.assertIn("续写当前章", user_prompt)
        self.assertIn("【当前章已有正文】", user_prompt)
        self.assertIn("已有正文前半段。", user_prompt)
        self.assertIn("不要重复已有正文", user_prompt)

    def test_expand_selection_mode_targets_selected_text(self):
        _, user_prompt = NovelContextBuilder(FakeProject(), FakeMemory()).build_prompts(
            0,
            1,
            generation_mode="expand_selection",
            selected_text="他握住黑钥匙。",
            expand_instruction="增加心理描写",
        )

        self.assertIn("局部扩写当前选中片段", user_prompt)
        self.assertIn("他握住黑钥匙。", user_prompt)
        self.assertIn("增加心理描写", user_prompt)


if __name__ == "__main__":
    unittest.main()
