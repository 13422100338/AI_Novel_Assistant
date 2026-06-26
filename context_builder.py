class NovelContextBuilder:
    """Assemble model prompts for long-form novel generation.

    The UI should not need to know the details of long-context policy. This
    builder owns the current v2 policy:
    - recent chapters are included as full text for style continuity;
    - older chapters are represented by compressed summaries;
    - structured memory provides character state, foreshadows, canon facts.
    """

    def __init__(self, project, memory, recent_full_count: int = 3, max_recent_chars: int = 12000):
        self.project = project
        self.memory = memory
        self.recent_full_count = recent_full_count
        self.max_recent_chars = max_recent_chars

    def chapter_position_list(self):
        positions = []
        for v_idx, vol in enumerate(self.project.meta["volumes"]):
            for c_idx, chap in enumerate(vol["chapters"]):
                positions.append((v_idx, c_idx, vol["name"], chap["name"]))
        return positions

    def recent_full_chapters_context(self, v_idx: int, c_idx: int) -> str:
        positions = self.chapter_position_list()
        try:
            current_pos = next(i for i, item in enumerate(positions) if item[0] == v_idx and item[1] == c_idx)
        except StopIteration:
            return ""
        recent = positions[max(0, current_pos - self.recent_full_count):current_pos]
        blocks = []
        for _, _, vol_name, chap_name in recent:
            content = self.project.read_chapter_content(vol_name, chap_name).strip()
            if not content:
                continue
            if len(content) > self.max_recent_chars:
                content = content[-self.max_recent_chars:]
            blocks.append(f"【{vol_name} / {chap_name}】\n{content}")
        return "\n\n".join(blocks)

    def compressed_history_before_recent(self, v_idx: int, c_idx: int) -> str:
        positions = self.chapter_position_list()
        try:
            current_pos = next(i for i, item in enumerate(positions) if item[0] == v_idx and item[1] == c_idx)
        except StopIteration:
            return ""
        cutoff = max(0, current_pos - self.recent_full_count)
        lines = []
        for old_v_idx, old_c_idx, vol_name, chap_name in positions[:cutoff]:
            chap = self.project.meta["volumes"][old_v_idx]["chapters"][old_c_idx]
            summary = chap.get("ai_synopsis") or chap.get("synopsis") or ""
            if summary.strip():
                lines.append(f"- {vol_name} / {chap_name}: {summary.strip()}")
        return "\n".join(lines)

    def legacy_history(self, v_idx: int, c_idx: int) -> str:
        meta = self.project.meta
        history_str = ""
        for i in range(v_idx + 1):
            vol = meta["volumes"][i]
            history_str += f"\n> {vol['name']} (梗概: {vol.get('synopsis', '无')})\n"

            chap_limit = c_idx if i == v_idx else len(vol["chapters"])
            for j in range(chap_limit):
                chap = vol["chapters"][j]
                ai_syn = chap.get("ai_synopsis", "")
                user_syn = chap.get("synopsis", "无")
                display_syn = ai_syn if ai_syn.strip() else user_syn
                history_str += f"  - {chap['name']}: {display_syn}\n"

        if len(history_str) > 15000:
            history_str = "【注意：因前文过长，此处仅提供过往卷梗概】\n"
            for i in range(v_idx + 1):
                vol = meta["volumes"][i]
                history_str += f"\n> {vol['name']} (梗概: {vol.get('synopsis', '无')})\n"

        return history_str.strip() or "本书刚刚开篇，无过往历史。"

    def has_previous_chapter(self, v_idx: int, c_idx: int) -> bool:
        if c_idx > 0:
            return True
        for i in range(v_idx - 1, -1, -1):
            if len(self.project.meta["volumes"][i]["chapters"]) > 0:
                return True
        return False

    def build_prompts(
        self,
        v_idx: int,
        c_idx: int,
        generation_mode: str = "rewrite",
        existing_content: str = "",
        selected_text: str = "",
        expand_instruction: str = "",
    ):
        meta = self.project.meta
        global_story = meta.get("global_synopsis", "未提供。")
        char_texts = [
            f"【{c['name']}】 性别:{c['gender']} 性格:{c['personality']} 经历:{c['experience']}"
            for c in meta.get("characters", [])
        ]
        char_setting = "\n".join(char_texts) if char_texts else "未提供明确人物。"

        system_prompt = f"""你是一位经验丰富的网文大神作家。请根据全局设定和上下文连贯地撰写小说正文。

            【全局故事大纲】
            {global_story}

            【核心人物设定】
            {char_setting}

            【写作要求】
            1. 严格遵循世界观、人设和剧情逻辑。
            2. 动作、神态、心理描写生动，符合网文爽感节奏。
            3. 【强制指令】字数必须严格限定在2500-3500字之间！爽点必须密集，严禁任何无用的废话和无效表达。
            4. 直接输出正文，禁止任何解释性废话和多余的寒暄。
            5. 对话要口语化，多用短句，讲话方式符合人设，拒绝“翻译腔”。角色说话要有情绪和潜台词，不要像写说明书或做思想汇报一样客观中立。
            6. 【重要】在正文输出完毕后，必须另起一行并严格以 `[AI_SUMMARY]` 作为分割符，然后输出约500字的本章详细梗概。此部分仅用于系统内部记录。"""

        curr_vol = meta["volumes"][v_idx]
        curr_chap = curr_vol["chapters"][c_idx]
        relevance_query = "\n".join([
            curr_vol.get("synopsis", ""),
            curr_chap.get("synopsis", ""),
            existing_content[-4000:] if existing_content else "",
            selected_text,
            expand_instruction,
        ])
        if hasattr(self.memory, "build_relevant_context"):
            memory_context = self.memory.build_relevant_context(curr_vol["name"], curr_chap["name"], relevance_query)
        else:
            memory_context = self.memory.build_context(curr_vol["name"], curr_chap["name"])
        recent_full_context = self.recent_full_chapters_context(v_idx, c_idx)
        older_compressed_context = self.compressed_history_before_recent(v_idx, c_idx)
        history_context = older_compressed_context.strip() or self.legacy_history(v_idx, c_idx)

        user_prompt = f"""请为我撰写最新章节的正文。

【较早章节压缩轨迹】
{history_context}

【最近章节全文，用于保持行文风格、节奏和人物声音】
{recent_full_context if recent_full_context.strip() else "暂无最近章节全文。"}

【长篇压缩记忆 / 人物状态 / 伏笔正典】
{memory_context if memory_context.strip() else "暂无结构化长篇记忆。"}

【本次写作任务】
当前所处卷：{curr_vol['name']}
本卷核心梗概：{curr_vol.get('synopsis', '无')}

当前需撰写章节：{curr_chap['name']}
本章细纲要求：{curr_chap.get('synopsis', '无')}

【行动指令】
"""
        if generation_mode == "continue":
            user_prompt += f"""续写当前章。请把下面【当前章已有正文】视为已经定稿的前半段，不要重复已有正文，不要从头重写。

【当前章已有正文】
{existing_content.strip() if existing_content.strip() else "当前章正文区为空。"}

请从已有正文的最后一句自然接续，继续推进本章剧情；保持同一章内的叙事视角、人物声音和行文节奏。
输出时只输出新增续写内容，最后仍需另起一行输出 `[AI_SUMMARY]`，摘要应概括“已有正文 + 新增续写”形成的完整当前章。
"""
        elif generation_mode == "expand_selection":
            user_prompt += f"""局部扩写当前选中片段。你不是在重写整章，而是在扩写/润色选区，使它更细腻、更有画面感，并与上下文自然衔接。

【当前章已有正文】
{existing_content.strip() if existing_content.strip() else "当前章正文区为空。"}

【需要扩写的选中片段】
{selected_text.strip() if selected_text.strip() else "未选中文本。"}

【扩写要求】
{expand_instruction.strip() if expand_instruction.strip() else "在不改变核心事实的前提下，增加心理、动作、环境和节奏层次。"}

请只输出扩写后的选中片段，不要输出整章，不要输出解释，不要输出 `[AI_SUMMARY]`。
"""
        elif self.has_previous_chapter(v_idx, c_idx):
            user_prompt += """请根据本章细纲要求，顺着上一章的情节展开。
严格限定正文长度在2000-3000字之间，确保爽点密集、拒绝水文，扩写为文笔流畅的完整正文！
"""
        else:
            user_prompt += """请根据全局设定、本卷梗概和本章细纲展开。若这是开篇，请迅速建立人物处境、核心冲突和可持续推进的悬念。
严格限定正文长度在2000-3000字之间，确保爽点密集、拒绝水文，扩写为文笔流畅的完整正文！
"""
        if generation_mode != "expand_selection":
            user_prompt += """【重要】在正文输出完毕后，必须另起一行并严格以 `[AI_SUMMARY]` 作为分割符，然后输出约500字高度结构化的【本章复盘与记忆锚点】。
在 `[AI_SUMMARY]` 之后，必须严格按照以下3个维度输出：
1. 核心剧情脉络：按时间顺序简述本章发生的实质性事件。
2. 人物状态更新：记录本章主角及配角的行为及心态。
3. 物品设定更新：记录本章所有物品状态。
"""

        return system_prompt, user_prompt
