# AI Novel Assistant Architecture

This project is still based on the original PyQt desktop app, but the second-version additions are organized around a few clear seams so it can keep evolving without a full rewrite.

## Runtime entry points

- `main.py`: application startup, welcome dialog, startup error logging.
- `run_app.bat` / `Start_AI_Novel_Assistant.cmd`: source-mode launcher.
- `build_exe.bat`: PyInstaller build helper.
- `dist/AI_Novel_Assistant/AI_Novel_Assistant.exe`: packaged app output after building.

## Core modules

- `data_manager.py`: original project/chapter storage. Chapters are still stored as `.docx`.
- `model_profiles.py`: multi-model OpenAI-compatible API profile loading.
- `ai_worker.py`: background model calls, generation, correction, summary, and chapter analysis workers.
- `novel_memory.py`: SQLite-backed long-novel memory layer, including summaries, character states, canon facts, foreshadows, and chapter versions.
- `context_builder.py`: long-novel prompt/context assembly, including recent full chapters, older compressed history, structured memory, and writing task prompts.
- `import_agent.py`: manuscript parsing and intelligent import planning. The current parser supports `#第X章标题` chapter headings and `（第X章 完）` chapter-end markers, then asks a model-backed manuscript-structure agent to group chapters into volumes.
- `main_window.py`: main product workflow and three-pane desktop UI.
- `ui_components.py`: dialogs and form widgets inherited from the original app.
- `ui_helpers.py`: reusable UI helpers introduced in v2, currently collapsible side-panel sections and chat bubble rendering.

## Current upgrade seams

Good next extraction targets, when the codebase grows:

1. `import_service.py`
   - Move TXT/DOCX file reading, project writing, and import-analysis queue creation.

2. `chat_panel.py`
   - Move the right-side plot-chat UI and streaming bubble updates into a dedicated widget.

3. `memory_panel.py`
   - Move dashboard, plot-point display, and current-character-state presentation.

The current version extracts low-risk UI helpers and long-context prompt assembly. This keeps the packaged build stable while giving future work a cleaner path.
