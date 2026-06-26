"""Formatting and parsing helpers for editable character-state text."""

CHARACTER_STATE_FIELDS = [
    ("心理", "psychology"),
    ("动机", "motivation"),
    ("目标", "current_goal"),
    ("关系", "relationships"),
    ("最近行动", "recent_activity"),
    ("最后出场", "last_seen"),
]


def format_character_state_for_edit(row: dict) -> str:
    """Convert a character-state row into the editable text shown in the UI."""
    return "\n".join(f"{label}：{row.get(key, '')}" for label, key in CHARACTER_STATE_FIELDS)


def parse_character_state_from_edit(text: str) -> dict:
    """Parse editable character-state text back into storage fields.

    Both Chinese full-width colons and ASCII colons are accepted. Continuation
    lines are appended to the most recent field so users can write multi-line
    notes without losing structure.
    """
    fields = {key: "" for _, key in CHARACTER_STATE_FIELDS}
    label_to_key = {label: key for label, key in CHARACTER_STATE_FIELDS}
    current_key = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        matched = False
        for label, key in label_to_key.items():
            for separator in ("：", ":"):
                prefix = f"{label}{separator}"
                if line.startswith(prefix):
                    current_key = key
                    fields[key] = line[len(prefix):].strip()
                    matched = True
                    break
            if matched:
                break

        if not matched and current_key:
            fields[current_key] = (fields[current_key] + "\n" + line).strip()

    return fields
