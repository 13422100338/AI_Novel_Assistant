import unittest

from ui_helpers import build_chapter_requirement_prompt, build_plot_chat_prompt, render_chat_messages_html


class ChatRenderingTests(unittest.TestCase):
    def test_render_chat_messages_uses_codex_like_bubble_classes(self):
        html = render_chat_messages_html(
            [
                {"role": "user", "content": "这一章应该怎么收束？"},
                {"role": "assistant", "content": "先回收承诺，再制造新的悬念。"},
            ]
        )

        self.assertIn("chat-shell", html)
        self.assertIn("chat-row user", html)
        self.assertIn("chat-row assistant", html)
        self.assertIn("chat-bubble", html)
        self.assertIn("assistant-message-card", html)
        self.assertIn("message-action-bar", html)
        self.assertIn("user-message-bubble", html)

    def test_render_chat_messages_formats_markdown_like_assistant_content(self):
        html = render_chat_messages_html(
            [
                {
                    "role": "assistant",
                    "content": "# 标题\n\n- 要点一\n\n```PowerShell\npython -V\n```",
                },
            ]
        )

        self.assertIn("chat-heading h1", html)
        self.assertIn("chat-list", html)
        self.assertIn("code-card", html)
        self.assertIn("PowerShell", html)


class ChapterRequirementPromptTests(unittest.TestCase):
    def test_build_chapter_requirement_prompt_requests_formal_requirements_only(self):
        system_prompt, user_prompt = build_chapter_requirement_prompt(
            global_synopsis="主角追查旧城失火案。",
            volume_name="第一卷 烬火",
            chapter_name="第3章 灰烬里的钥匙",
            chapter_synopsis="主角进入废弃剧院。",
            memory_context="人物状态：主角怀疑师父隐瞒真相。",
            editor_content="剧院后台有一面被烧焦的镜子。",
            chat_context="用户刚讨论过：本章要揭示钥匙来自十年前。",
        )

        self.assertIn("章节要求生成器", system_prompt)
        self.assertIn("只输出正式的当前章写作要求", user_prompt)
        self.assertIn("第3章 灰烬里的钥匙", user_prompt)
        self.assertIn("剧院后台有一面被烧焦的镜子", user_prompt)
        self.assertIn("不要寒暄", user_prompt)


class PlotChatPromptTests(unittest.TestCase):
    def test_build_plot_chat_prompt_includes_recent_chat_history(self):
        system_prompt, user_prompt = build_plot_chat_prompt(
            global_synopsis="全局故事",
            memory_context="人物状态库",
            editor_content="当前正文",
            question="下一步怎么写？",
            chat_history="作者：上一轮问题\n剧情搭档：上一轮回答",
        )

        self.assertIn("剧情策划搭档", system_prompt)
        self.assertIn("【最近剧情商讨记录】", user_prompt)
        self.assertIn("上一轮回答", user_prompt)
        self.assertIn("下一步怎么写？", user_prompt)


if __name__ == "__main__":
    unittest.main()
