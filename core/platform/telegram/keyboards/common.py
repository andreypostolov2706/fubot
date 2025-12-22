"""
Common Keyboards
"""
from core.locales import t
from core.platform.telegram.utils import build_keyboard


def back_kb(callback: str = "main_menu", lang: str = "ru"):
    """Back button keyboard"""
    return build_keyboard([
        [{"text": t(lang, "COMMON.back"), "callback_data": callback}]
    ])


def confirm_kb(
    confirm_callback: str, 
    cancel_callback: str = "main_menu",
    lang: str = "ru"
):
    """Confirm/Cancel keyboard"""
    return build_keyboard([
        [
            {"text": t(lang, "COMMON.confirm"), "callback_data": confirm_callback},
            {"text": t(lang, "COMMON.cancel"), "callback_data": cancel_callback},
        ]
    ])


def yes_no_kb(
    yes_callback: str,
    no_callback: str,
    lang: str = "ru"
):
    """Yes/No keyboard"""
    return build_keyboard([
        [
            {"text": t(lang, "COMMON.yes"), "callback_data": yes_callback},
            {"text": t(lang, "COMMON.no"), "callback_data": no_callback},
        ]
    ])
