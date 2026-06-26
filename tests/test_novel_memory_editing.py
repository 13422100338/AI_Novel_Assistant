import tempfile
import unittest

from novel_memory import NovelMemoryStore


class NovelMemoryEditingTests(unittest.TestCase):
    def test_character_state_can_be_listed_updated_and_deleted(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = NovelMemoryStore(tmp)
            store.update_character_state(
                "林秋",
                {
                    "motivation": "查明火灾真相",
                    "psychology": "警惕",
                    "current_goal": "进入剧院后台",
                    "relationships": "怀疑师父",
                    "recent_activity": "发现烧焦镜子",
                    "last_seen": "第一卷/第3章",
                },
            )

            states = store.list_character_states()
            self.assertEqual(states[0]["name"], "林秋")
            self.assertEqual(states[0]["psychology"], "警惕")

            store.update_character_state("林秋", {"psychology": "动摇"})
            self.assertEqual(store.get_character_state("林秋")["psychology"], "动摇")

            store.delete_character_state("林秋")
            self.assertEqual(store.list_character_states(), [])
            store.close()

    def test_layered_chapter_and_canon_memory_are_editable(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = NovelMemoryStore(tmp)
            store.upsert_analysis(
                "第一卷",
                "第1章",
                {
                    "summary": "主角抵达旧城。",
                    "plot_points": ["旧城失火案被重提"],
                    "foreshadows": [{"title": "黑钥匙", "detail": "钥匙来源不明", "status": "active"}],
                },
            )

            chapter = store.list_chapter_memories()[0]
            store.update_chapter_memory(
                chapter["id"],
                {
                    "summary": "主角抵达旧城并发现黑钥匙线索。",
                    "plot_points": ["旧城失火案被重提", "黑钥匙出现"],
                    "foreshadows": [{"title": "黑钥匙", "detail": "来自十年前", "status": "active"}],
                },
            )
            self.assertIn("黑钥匙线索", store.list_chapter_memories()[0]["summary"])

            layered = store.list_layered_summaries()[0]
            store.update_layered_summary(layered["id"], "压缩后的卷记忆")
            self.assertEqual(store.list_layered_summaries()[0]["summary"], "压缩后的卷记忆")

            canon = store.list_canon_entries()[0]
            store.update_canon_entry(canon["id"], {"status": "closed", "detail": "已在第10章回收"})
            self.assertEqual(store.list_canon_entries(include_closed=True)[0]["status"], "closed")
            store.close()


if __name__ == "__main__":
    unittest.main()
