"""
Internationalization (i18n) engine for Antigravity Suite Installer.
Detects system locale, defaults to English, supports dynamic language switching.
"""

import json
import locale
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

LOCALES_DIR = Path(__file__).parent / "locales"

AVAILABLE_LANGUAGES: List[Tuple[str, str]] = [
    ("it", "Italiano"),
    ("en", "English"),
    ("es", "Español"),
    ("fr", "Français"),
    ("de", "Deutsch"),
]

_CURRENT_LANG = "en"
_TRANSLATIONS: Dict[str, Dict[str, str]] = {}
_LISTENERS: List[Callable[[str], None]] = []


def _detect_system_language() -> str:
    """Detects system language code (e.g. 'it', 'en', 'es', etc.)."""
    for env_var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(env_var)
        if val:
            # Format is usually it_IT.UTF-8 or it_IT or it
            code = val.split(".")[0].split("_")[0].lower()
            if (LOCALES_DIR / f"{code}.json").exists():
                return code

    try:
        default_locale, _ = locale.getdefaultlocale()
        if default_locale:
            code = default_locale.split("_")[0].lower()
            if (LOCALES_DIR / f"{code}.json").exists():
                return code
    except Exception:
        pass

    return "en"


def _load_locale(lang: str) -> Dict[str, str]:
    """Loads translations for given language code from JSON file."""
    if lang in _TRANSLATIONS:
        return _TRANSLATIONS[lang]

    json_path = LOCALES_DIR / f"{lang}.json"
    if not json_path.exists():
        json_path = LOCALES_DIR / "en.json"

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            _TRANSLATIONS[lang] = data
            return data
    except Exception as e:
        print(f"[i18n] Error loading locale {lang}: {e}")
        return {}


def init_i18n(lang: Optional[str] = None) -> str:
    """Initializes translations, optionally forcing a language."""
    global _CURRENT_LANG
    # Always load English as baseline fallback
    _load_locale("en")

    if not lang:
        lang = _detect_system_language()

    _CURRENT_LANG = lang if (LOCALES_DIR / f"{lang}.json").exists() else "en"
    _load_locale(_CURRENT_LANG)
    return _CURRENT_LANG


def get_current_language() -> str:
    return _CURRENT_LANG


def set_language(lang: str):
    """Switches active language and notifies registered listeners."""
    global _CURRENT_LANG
    if (LOCALES_DIR / f"{lang}.json").exists():
        _CURRENT_LANG = lang
        _load_locale(lang)
        for listener in _LISTENERS:
            try:
                listener(_CURRENT_LANG)
            except Exception as e:
                print(f"[i18n] Listener error: {e}")


def add_language_listener(callback: Callable[[str], None]):
    """Registers a callback when language changes."""
    if callback not in _LISTENERS:
        _LISTENERS.append(callback)


def _(key: str, **kwargs) -> str:
    """
    Returns the localized string for `key`.
    Falls back to English if key is missing in active locale,
    or key name itself if missing in both.
    Supports kwargs formatting: _("hello_user", name="Alice")
    """
    active_dict = _TRANSLATIONS.get(_CURRENT_LANG, {})
    fallback_dict = _TRANSLATIONS.get("en", {})

    template = active_dict.get(key)
    if template is None:
        template = fallback_dict.get(key, key)

    if kwargs and isinstance(template, str):
        try:
            return template.format(**kwargs)
        except Exception:
            return template

    return str(template)


# Initialize immediately upon import
init_i18n()
