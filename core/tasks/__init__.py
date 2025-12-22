"""
Background Tasks
"""
from core.tasks.triggers import process_triggers, set_bot as set_trigger_bot, on_user_deposit
from core.tasks.rates import update_rates_task, init_rates
from core.tasks.payments import payment_checker_task, set_bot as set_payment_bot

__all__ = [
    "process_triggers", 
    "set_trigger_bot", 
    "on_user_deposit",
    "update_rates_task",
    "init_rates",
    "payment_checker_task",
    "set_payment_bot",
]
