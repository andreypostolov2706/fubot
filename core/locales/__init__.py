"""
Localization System
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from importlib import import_module

# Available languages
AVAILABLE_LANGUAGES = {
    "ru": "core.locales.ru",
    "en": "core.locales.en",
}

# Cache
_locales_cache: Dict[str, Any] = {}


def load_locale(lang_code: str) -> Any:
    """Load locale module"""
    if lang_code in _locales_cache:
        return _locales_cache[lang_code]
    
    if lang_code not in AVAILABLE_LANGUAGES:
        lang_code = "ru"  # Fallback
    
    module = import_module(AVAILABLE_LANGUAGES[lang_code])
    _locales_cache[lang_code] = module
    return module


def get_text(
    lang_code: str, 
    section: str, 
    key: str, 
    **kwargs
) -> str:
    """
    Get localized text.
    
    Args:
        lang_code: Language code (ru, en)
        section: Section (MAIN_MENU, TOP_UP, etc.)
        key: Key in section
        **kwargs: Format parameters
    
    Returns:
        Localized text
    
    Example:
        get_text("ru", "MAIN_MENU", "balance", balance=100)
        # "💰 Баланс: 100 токенов"
    """
    locale = load_locale(lang_code)
    
    # Get section
    section_dict = getattr(locale, section, None)
    if section_dict is None:
        # Fallback to Russian
        locale = load_locale("ru")
        section_dict = getattr(locale, section, {})
    
    # Get text
    text = section_dict.get(key, f"[{section}.{key}]")
    
    # Format
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    
    return text


def t(lang: str, path: str, **kwargs) -> str:
    """
    Short alias for get_text.
    
    Args:
        lang: Language code
        path: Path in format "SECTION.key"
        **kwargs: Parameters
    
    Example:
        t("ru", "MAIN_MENU.balance", balance=100)
    """
    parts = path.split(".", 1)
    if len(parts) != 2:
        return f"[{path}]"
    
    return get_text(lang, parts[0], parts[1], **kwargs)


def get_language_info(lang_code: str) -> dict:
    """Get language info"""
    locale = load_locale(lang_code)
    return {
        "code": getattr(locale, "LANGUAGE_CODE", lang_code),
        "name": getattr(locale, "LANGUAGE_NAME", lang_code),
        "flag": getattr(locale, "LANGUAGE_FLAG", "🏳️"),
    }


def get_available_languages() -> list[dict]:
    """Get list of available languages"""
    return [get_language_info(code) for code in AVAILABLE_LANGUAGES.keys()]


__all__ = [
    "t",
    "get_text",
    "load_locale",
    "get_language_info",
    "get_available_languages",
    "AVAILABLE_LANGUAGES",
]
