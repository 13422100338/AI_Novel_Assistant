"""Small text measurement helpers shared by UI and prompt builders."""


def estimate_tokens(text: str) -> int:
    """Return a lightweight token estimate for mixed English/Chinese text.

    This is intentionally approximate. It is used for UI budgeting hints, not
    billing or hard truncation decisions.
    """
    if not text:
        return 0
    ascii_count = sum(1 for ch in text if ord(ch) < 128)
    non_ascii_count = len(text) - ascii_count
    return max(1, int(ascii_count / 4 + non_ascii_count / 1.7))


def keep_tail(text: str, max_chars: int, prefix: str = "……（前文省略）……\n") -> str:
    """Keep the tail of long text with a clear omission prefix."""
    if not text or len(text) <= max_chars:
        return text
    return prefix + text[-max_chars:]
