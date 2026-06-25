from dataclasses import dataclass
from PyQt6.QtCore import QSettings


@dataclass
class ModelProfile:
    name: str
    api_key: str
    base_url: str
    model: str
    temperature: float
    max_tokens: int


DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-reasoner"


def _read_legacy(settings: QSettings, key: str, default):
    value = settings.value(key, default)
    return value if value not in (None, "") else default


def get_model_profile(role: str, settings: QSettings | None = None) -> ModelProfile:
    """Read an OpenAI-compatible model profile.

    Roles currently used by the app:
    - chat: plot discussion window
    - draft: chapter writing / analysis

    Legacy single-model settings are kept as fallback so existing users do not
    need to re-enter credentials after the upgrade.
    """
    settings = settings or QSettings("AIWriter", "Settings")
    prefix = f"profiles/{role}/"
    fallback_name = "剧情商讨模型" if role == "chat" else "正文创作模型"

    api_key = settings.value(prefix + "api_key", "")
    if not api_key:
        api_key = settings.value("api_key", "")

    base_url = settings.value(prefix + "base_url", "")
    if not base_url:
        base_url = _read_legacy(settings, "base_url", DEFAULT_BASE_URL)

    model = settings.value(prefix + "model", "")
    if not model:
        model = _read_legacy(settings, "model", DEFAULT_MODEL)

    temperature = settings.value(prefix + "temperature", None)
    if temperature in (None, ""):
        temperature = _read_legacy(settings, "temperature", 0.7)

    max_tokens = settings.value(prefix + "max_tokens", None)
    if max_tokens in (None, ""):
        max_tokens = _read_legacy(settings, "max_tokens", 6000)

    return ModelProfile(
        name=settings.value(prefix + "name", fallback_name),
        api_key=str(api_key),
        base_url=str(base_url),
        model=str(model),
        temperature=float(temperature),
        max_tokens=int(max_tokens),
    )


def has_any_api_key(settings: QSettings | None = None) -> bool:
    settings = settings or QSettings("AIWriter", "Settings")
    return bool(
        settings.value("api_key", "")
        or settings.value("profiles/chat/api_key", "")
        or settings.value("profiles/draft/api_key", "")
    )
