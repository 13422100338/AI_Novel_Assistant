import json
import os
import sqlite3
from datetime import datetime


class NovelMemoryStore:
    """SQLite-backed long-novel memory layer.

    The original project stores readable project structure in meta.json and
    chapter bodies in docx. This store adds durable, queryable memory for
    million-word projects without forcing the full manuscript into prompts.
    """

    def __init__(self, root_path: str):
        self.root_path = root_path
        self.db_path = os.path.join(root_path, "novel_memory.sqlite3")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.init_schema()

    def init_schema(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chapter_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volume_name TEXT NOT NULL,
                chapter_name TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                plot_points TEXT NOT NULL DEFAULT '[]',
                character_updates TEXT NOT NULL DEFAULT '[]',
                foreshadows TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT NOT NULL,
                UNIQUE(volume_name, chapter_name)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS layered_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                scope_key TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                UNIQUE(level, scope_key)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS character_states (
                name TEXT PRIMARY KEY,
                motivation TEXT NOT NULL DEFAULT '',
                psychology TEXT NOT NULL DEFAULT '',
                current_goal TEXT NOT NULL DEFAULT '',
                relationships TEXT NOT NULL DEFAULT '',
                recent_activity TEXT NOT NULL DEFAULT '',
                last_seen TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS canon_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active',
                source_volume TEXT NOT NULL DEFAULT '',
                source_chapter TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chapter_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volume_name TEXT NOT NULL,
                chapter_name TEXT NOT NULL,
                content TEXT NOT NULL,
                reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def close(self):
        self.conn.close()

    def now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def archive_chapter_version(self, volume_name: str, chapter_name: str, content: str, reason: str = "manual-save"):
        if not content.strip():
            return
        self.conn.execute(
            """
            INSERT INTO chapter_versions(volume_name, chapter_name, content, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (volume_name, chapter_name, content, reason, self.now()),
        )
        self.conn.commit()

    def upsert_analysis(self, volume_name: str, chapter_name: str, payload: dict):
        now = self.now()
        summary = payload.get("summary", "")
        plot_points = payload.get("plot_points", [])
        character_updates = payload.get("character_updates", [])
        foreshadows = payload.get("foreshadows", [])
        canon_facts = payload.get("canon_facts", [])

        self.conn.execute(
            """
            INSERT INTO chapter_summaries
                (volume_name, chapter_name, summary, plot_points, character_updates, foreshadows, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(volume_name, chapter_name) DO UPDATE SET
                summary=excluded.summary,
                plot_points=excluded.plot_points,
                character_updates=excluded.character_updates,
                foreshadows=excluded.foreshadows,
                updated_at=excluded.updated_at
            """,
            (
                volume_name,
                chapter_name,
                summary,
                json.dumps(plot_points, ensure_ascii=False),
                json.dumps(character_updates, ensure_ascii=False),
                json.dumps(foreshadows, ensure_ascii=False),
                now,
            ),
        )

        for item in character_updates:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            self.conn.execute(
                """
                INSERT INTO character_states
                    (name, motivation, psychology, current_goal, relationships, recent_activity, last_seen, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    motivation=excluded.motivation,
                    psychology=excluded.psychology,
                    current_goal=excluded.current_goal,
                    relationships=excluded.relationships,
                    recent_activity=excluded.recent_activity,
                    last_seen=excluded.last_seen,
                    updated_at=excluded.updated_at
                """,
                (
                    item.get("name", ""),
                    item.get("motivation", ""),
                    item.get("psychology", ""),
                    item.get("current_goal", ""),
                    item.get("relationships", ""),
                    item.get("recent_activity", ""),
                    f"{volume_name}/{chapter_name}",
                    now,
                ),
            )

        for item in foreshadows:
            self._insert_canon("foreshadow", item, volume_name, chapter_name, now)
        for item in canon_facts:
            self._insert_canon("fact", item, volume_name, chapter_name, now)

        self.rebuild_layered_summaries()
        self.conn.commit()

    def _insert_canon(self, kind: str, item, volume_name: str, chapter_name: str, now: str):
        if isinstance(item, str):
            title, detail, status = item[:80], item, "active"
        elif isinstance(item, dict):
            title = item.get("title") or item.get("name") or item.get("fact") or item.get("promise") or kind
            detail = item.get("detail") or item.get("description") or json.dumps(item, ensure_ascii=False)
            status = item.get("status", "active")
        else:
            return
        self.conn.execute(
            """
            INSERT INTO canon_entries(kind, title, detail, status, source_volume, source_chapter, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (kind, str(title), str(detail), str(status), volume_name, chapter_name, now),
        )

    def rebuild_layered_summaries(self):
        now = self.now()
        cur = self.conn.cursor()
        rows = cur.execute(
            """
            SELECT volume_name, chapter_name, summary
            FROM chapter_summaries
            ORDER BY id
            """
        ).fetchall()

        by_volume: dict[str, list[str]] = {}
        for row in rows:
            by_volume.setdefault(row["volume_name"], []).append(f"{row['chapter_name']}: {row['summary']}")

        for volume, summaries in by_volume.items():
            compact = "\n".join(summaries[-30:])
            self.conn.execute(
                """
                INSERT INTO layered_summaries(level, scope_key, summary, updated_at)
                VALUES ('volume', ?, ?, ?)
                ON CONFLICT(level, scope_key) DO UPDATE SET summary=excluded.summary, updated_at=excluded.updated_at
                """,
                (volume, compact, now),
            )

        book_summary = "\n\n".join([f"【{vol}】\n" + "\n".join(items[-10:]) for vol, items in by_volume.items()])
        self.conn.execute(
            """
            INSERT INTO layered_summaries(level, scope_key, summary, updated_at)
            VALUES ('book', 'all', ?, ?)
            ON CONFLICT(level, scope_key) DO UPDATE SET summary=excluded.summary, updated_at=excluded.updated_at
            """,
            (book_summary[-20000:], now),
        )

    def build_context(self, volume_name: str, chapter_name: str, limit_recent: int = 8) -> str:
        cur = self.conn.cursor()
        book = cur.execute(
            "SELECT summary FROM layered_summaries WHERE level='book' AND scope_key='all'"
        ).fetchone()
        volume = cur.execute(
            "SELECT summary FROM layered_summaries WHERE level='volume' AND scope_key=?",
            (volume_name,),
        ).fetchone()
        recent = cur.execute(
            """
            SELECT volume_name, chapter_name, summary
            FROM chapter_summaries
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit_recent,),
        ).fetchall()
        characters = cur.execute(
            """
            SELECT name, motivation, psychology, current_goal, relationships, recent_activity, last_seen
            FROM character_states
            ORDER BY updated_at DESC
            LIMIT 30
            """
        ).fetchall()
        canon = cur.execute(
            """
            SELECT kind, title, detail, status, source_volume, source_chapter
            FROM canon_entries
            WHERE status != 'closed'
            ORDER BY id DESC
            LIMIT 80
            """
        ).fetchall()

        parts = []
        if book and book["summary"].strip():
            parts.append("【全书压缩记忆】\n" + book["summary"].strip())
        if volume and volume["summary"].strip():
            parts.append("【当前卷压缩记忆】\n" + volume["summary"].strip())
        if recent:
            parts.append("【最近章节摘要】\n" + "\n".join(
                f"- {r['volume_name']} / {r['chapter_name']}: {r['summary']}" for r in reversed(recent)
            ))
        if characters:
            parts.append("【人物状态库】\n" + "\n".join(
                f"- {r['name']}｜动机:{r['motivation']}｜心理:{r['psychology']}｜目标:{r['current_goal']}｜关系:{r['relationships']}｜最近:{r['recent_activity']}｜最后出场:{r['last_seen']}"
                for r in characters
            ))
        if canon:
            parts.append("【正典账本 / 伏笔与硬事实】\n" + "\n".join(
                f"- [{r['kind']}/{r['status']}] {r['title']}: {r['detail']}（来源:{r['source_volume']}/{r['source_chapter']}）"
                for r in canon
            ))
        return "\n\n".join(parts)

    def get_plot_points_text(self, volume_name: str, chapter_name: str) -> str:
        row = self.conn.execute(
            """
            SELECT summary, plot_points, foreshadows
            FROM chapter_summaries
            WHERE volume_name=? AND chapter_name=?
            """,
            (volume_name, chapter_name),
        ).fetchone()
        if not row:
            return ""

        lines = []
        if row["summary"].strip():
            lines.append("【本章压缩摘要】")
            lines.append(row["summary"].strip())

        def append_json_list(title: str, raw: str):
            try:
                items = json.loads(raw or "[]")
            except Exception:
                items = []
            if not items:
                return
            lines.append(f"\n【{title}】")
            for item in items:
                if isinstance(item, dict):
                    name = item.get("title") or item.get("name") or item.get("fact") or item.get("promise") or "未命名"
                    detail = item.get("detail") or item.get("description") or item.get("recent_activity") or ""
                    status = item.get("status", "")
                    suffix = f"（{status}）" if status else ""
                    lines.append(f"- {name}{suffix}: {detail}".rstrip(": "))
                else:
                    lines.append(f"- {item}")

        append_json_list("关键情节点", row["plot_points"])
        append_json_list("伏笔 / 承诺", row["foreshadows"])
        return "\n".join(lines).strip()

    def character_state_text(self, volume_name: str = "", chapter_name: str = "", limit: int = 20) -> str:
        rows = self.conn.execute(
            """
            SELECT name, motivation, psychology, current_goal, relationships, recent_activity, last_seen
            FROM character_states
            ORDER BY
                CASE WHEN last_seen=? THEN 0 ELSE 1 END,
                updated_at DESC
            LIMIT ?
            """,
            (f"{volume_name}/{chapter_name}" if volume_name and chapter_name else "", limit),
        ).fetchall()
        if not rows:
            return "暂无人物状态记录。\n\n生成或导入章节并完成自动分析后，这里会显示人物在当前节点的动机、心理、目标和最近行动。"

        blocks = []
        for r in rows:
            blocks.append(
                "\n".join([
                    f"【{r['name']}】",
                    f"心理：{r['psychology'] or '未记录'}",
                    f"动机：{r['motivation'] or '未记录'}",
                    f"目标：{r['current_goal'] or '未记录'}",
                    f"关系：{r['relationships'] or '未记录'}",
                    f"最近行动：{r['recent_activity'] or '未记录'}",
                    f"最后出场：{r['last_seen'] or '未记录'}",
                ])
            )
        return "\n\n".join(blocks)

    def dashboard_text(self) -> str:
        cur = self.conn.cursor()
        counts = {
            "章节摘要": cur.execute("SELECT COUNT(*) AS c FROM chapter_summaries").fetchone()["c"],
            "人物状态": cur.execute("SELECT COUNT(*) AS c FROM character_states").fetchone()["c"],
            "正典条目": cur.execute("SELECT COUNT(*) AS c FROM canon_entries").fetchone()["c"],
            "历史版本": cur.execute("SELECT COUNT(*) AS c FROM chapter_versions").fetchone()["c"],
        }
        active = cur.execute(
            """
            SELECT kind, title, detail, source_volume, source_chapter
            FROM canon_entries
            WHERE status != 'closed'
            ORDER BY id DESC
            LIMIT 12
            """
        ).fetchall()
        lines = ["长篇记忆库状态："]
        lines.extend([f"- {k}: {v}" for k, v in counts.items()])
        if active:
            lines.append("\n最近活跃伏笔/正典：")
            lines.extend([f"- [{r['kind']}] {r['title']}｜{r['source_volume']}/{r['source_chapter']}" for r in active])
        return "\n".join(lines)
