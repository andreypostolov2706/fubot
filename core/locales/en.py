"""
English Localization
"""

LANGUAGE_CODE = "en"
LANGUAGE_NAME = "English"
LANGUAGE_FLAG = "🇬🇧"

# ==================== COMMON ====================

COMMON = {
    "back": "◀️ Back",
    "cancel": "❌ Cancel",
    "confirm": "✅ Confirm",
    "yes": "Yes",
    "no": "No",
    "save": "💾 Save",
    "delete": "🗑 Delete",
    "edit": "✏️ Edit",
    "loading": "⏳ Loading...",
    "error": "❌ An error occurred",
    "success": "✅ Success!",
    "not_found": "Not found",
    "coming_soon": "🚧 Coming soon",
    "enabled": "Enabled",
    "disabled": "Disabled",
}

# ==================== MAIN MENU ====================

MAIN_MENU = {
    "title": "🏠 <b>Main Menu</b>",
    "balance": "💰 Balance: {balance} GTON",
    "balance_with_fiat": "💰 Balance: {balance} GTON (~${fiat})",
    "top_up": "💳 Top Up",
    "promocode": "🎟 Promo Code",
    "settings": "⚙️ Settings",
    "help": "❓ Help",
    "partner": "🤝 Partner Program",
    "daily_bonus": "🎁 Daily Bonus",
    "daily_bonus_ready": "🎁 Claim Bonus ({gton} GTON)",
}

# ==================== TOP UP ====================

TOP_UP = {
    "title": "💳 <b>Top Up Balance</b>",
    "current_balance": "Current balance: {balance} tokens",
    "rate": "Rate: 1 token = {rate} ₽",
    "select_amount": "Select amount:",
    "custom_amount": "💬 Custom amount",
    "enter_amount": "Enter amount in rubles:",
    "min_amount": "Minimum amount: {min} ₽",
    "max_amount": "Maximum amount: {max} ₽",
    "invalid_amount": "❌ Invalid amount",
    
    "select_method": "Select payment method:",
    "method_card": "💳 Bank Card",
    "method_sbp": "📱 SBP",
    "method_yoomoney": "🟡 YooMoney",
    "method_crypto": "₿ Cryptocurrency",
    
    "payment_created": "🔗 Payment link created",
    "payment_success": "✅ Payment successful!\n\n💰 Credited: {tokens} tokens",
    "payment_failed": "❌ Payment failed",
    "payment_pending": "⏳ Waiting for payment...",
    
    "enter_promocode": "🎁 Enter promocode",
    "promocode_placeholder": "🎁 Enter promocode:",
}

# ==================== SETTINGS ====================

SETTINGS = {
    "title": "⚙️ <b>Settings</b>",
    "language": "🌐 Language",
    "language_current": "Current language: {language}",
    "language_select": "Select language:",
    "language_changed": "✅ Language changed to {language}",
    "notifications": "🔔 Notifications",
    "notifications_on": "Notifications enabled",
    "notifications_off": "Notifications disabled",
}

# ==================== PARTNER ====================

PARTNER = {
    "title": "🤝 <b>Partner Program</b>",
    "description": "Invite friends and get {percent}% of their payments!",
    
    "stats_title": "📊 Your statistics:",
    "stats_referrals": "Referrals: {count}",
    "stats_earned": "Earned: {amount} ₽",
    "stats_available": "Available for withdrawal: {amount} ₽",
    
    "your_link": "🔗 Your link:",
    "link_copied": "✅ Link copied",
    
    "my_referrals": "📋 My Referrals",
    "withdraw": "💸 Withdraw",
    "become_partner": "💰 Become a Partner",
    "partner_cabinet": "🤝 Partner Dashboard",
    
    "application_title": "📝 <b>Partnership Application</b>",
    "application_text": "Tell us about yourself and how you plan to attract users:",
    "application_sent": "✅ Application sent!\n\nWe will review it shortly.",
    "application_pending": "⏳ Your application is under review",
    
    "withdraw_title": "💸 <b>Withdrawal</b>",
    "withdraw_available": "Available: {amount} ₽",
    "withdraw_min": "Minimum amount: {min} ₽",
    "withdraw_enter_amount": "Enter withdrawal amount:",
    "withdraw_select_method": "Select withdrawal method:",
    "withdraw_enter_details": "Enter details ({method}):",
    "withdraw_confirm": "Confirm withdrawal:\n\nAmount: {amount} ₽\nMethod: {method}\nDetails: {details}",
    "withdraw_success": "✅ Withdrawal request created!\n\nPlease wait for processing.",
    "withdraw_insufficient": "❌ Insufficient funds",
}

# ==================== HELP ====================

HELP = {
    "title": "❓ <b>Help</b>",
    "description": "If you have questions, contact support:",
    "support": "📩 Contact Support",
    "faq": "📖 FAQ",
}

# ==================== ERRORS ====================

ERRORS = {
    "not_enough_balance": "❌ Not enough tokens!\n\nRequired: {required}\nYou have: {balance}",
    "user_blocked": "🚫 Your account is blocked.\n\nReason: {reason}",
    "user_blocked_temp": "🚫 Your account is blocked.\n\nReason: {reason}\nUnblock in: {days} days",
    "rate_limit": "⏳ Too many requests. Please wait.",
    "maintenance": "🔧 Bot is under maintenance. Try again later.",
    "unknown_command": "❓ Unknown command",
    "invalid_input": "❌ Invalid input",
    "service_unavailable": "❌ Service temporarily unavailable",
}

# ==================== DAILY BONUS ====================

DAILY_BONUS = {
    "title": "🎁 <b>Daily Bonus</b>",
    
    "streak": "🔥 Streak: {days} days",
    "day_of": "Day {current} of {total}",
    "reward": "Reward: {tokens} tokens",
    "next_reward": "Tomorrow: {tokens} tokens",
    "next_in": "⏰ Next in: {time}",
    
    "claim": "🎁 Claim Bonus",
    "claim_short": "🎁 Claim",
    "history": "📊 History",
    
    "claimed_title": "✅ Bonus claimed!",
    "claimed_tokens": "🎁 +{tokens} tokens",
    "new_balance": "💰 Balance: {balance} tokens",
    "new_streak": "🔥 Streak: {days} days",
    
    "already_claimed": "✅ Already claimed today",
    "dont_miss": "💡 Don't miss days to keep your streak!",
    
    "streak_lost_title": "😔 Streak lost!",
    "streak_lost_text": "You missed a day and your streak was reset. Starting over!",
    
    "day7_tomorrow": "📅 Tomorrow: {tokens} tokens (day 7!)",
    "day7_congrats": "🎉 Congratulations! Maximum reward!",
}

# ==================== PROMOCODE ====================

PROMOCODE = {
    "enter_code": "🎁 Enter promocode:",
    "activated": "✅ Promocode activated!",
    "reward_tokens": "🎁 You received: {amount} tokens",
    "reward_subscription": "⭐ Subscription {plan} activated for {days} days",
    "reward_discount": "💸 Discount {percent}% applied",
    "new_balance": "💰 New balance: {balance} tokens",
    
    "invalid": "❌ Invalid promocode",
    "expired": "❌ Promocode expired",
    "already_used": "❌ You already used this promocode",
    "limit_reached": "❌ Promocode activation limit reached",
    "new_users_only": "❌ Promocode is for new users only",
    "first_deposit_only": "❌ Promocode is for first deposit only",
}

# ==================== MODERATION ====================

MODERATION = {
    "reason_spam": "Spam",
    "reason_abuse": "Abuse",
    "reason_fraud": "Fraud",
    "reason_terms_violation": "Terms violation",
    "reason_other": "Other",
    
    "warning_issued": "⚠️ You received a warning",
    "warning_reason": "Reason: {reason}",
    "warning_count": "Warnings: {current}/{max}",
    "warning_notice": "After {max} warnings your account will be temporarily blocked.",
    
    "banned_title": "🚫 Your account is blocked",
    "banned_reason": "Reason: {reason}",
    "banned_permanent": "Duration: permanent",
    "banned_temporary": "Duration: {days} days",
    "banned_until": "Unblock date: {date}",
    "banned_days_left": "Days until unblock: {days}",
    "banned_appeal": "If you think this is a mistake, contact support.",
    
    "unbanned": "✅ Your account has been unblocked",
}

# ==================== NOTIFICATIONS ====================

NOTIFICATIONS = {
    "settings_title": "🔔 Notification Settings",
    "email_not_set": "📧 Email: not set",
    "email_set": "📧 Email: {email}",
    "add_email": "Add email",
    "change_email": "Change email",
    
    "receive_title": "Receive notifications:",
    "category_payment": "💳 Payments and balance",
    "category_subscription": "⭐ Subscriptions",
    "category_referral": "🤝 Referrals",
    "category_promo": "🎁 Promotions",
    "category_reminder": "🔔 Reminders",
    "category_service": "📦 From services",
    
    "low_balance_title": "⚠️ Low balance",
    "low_balance_text": "You have {balance} tokens left. Top up your balance.",
    "subscription_expiring_title": "⏰ Subscription expiring",
    "subscription_expiring_text": "Your subscription expires in {days} days.",
    "inactive_title": "👋 We miss you!",
    "inactive_text": "You haven't visited for {days} days. Come back!",
}

# ==================== ADMIN ====================

ADMIN = {
    "title": "🔧 <b>Admin Panel</b>",
    "partners": "👥 Partners",
    "statistics": "📊 Statistics",
    "broadcast": "📢 Broadcast",
    "settings": "⚙️ Settings",
    "services": "📦 Services",
    "users": "👤 Users",
    "languages": "🌐 Languages",
    
    "partners_list": "📋 Partners List",
    "partners_applications": "📝 Applications",
    "partners_payouts": "💸 Payout Requests",
    
    # Stats - Main
    "stats_title": "📊 <b>Statistics</b>",
    "stats_users_btn": "👥 Users",
    "stats_finance_btn": "💰 Finance",
    "stats_bonus_btn": "🎁 Daily Bonus",
    "stats_referrals_btn": "🤝 Referrals",
    "stats_analytics_btn": "📈 Analytics",
    "stats_refresh": "🔄 Refresh",
    
    # Stats - Periods
    "period_today": "Today",
    "period_week": "Week",
    "period_month": "Month",
    "period_all": "All time",
    
    # Stats - Users
    "stats_users_title": "👥 <b>Users</b>",
    "stats_users_total": "📊 Total: {count}",
    "stats_users_today": "Today: +{count}",
    "stats_users_week": "This week: +{count}",
    "stats_users_month": "This month: +{count}",
    "stats_activity": "📈 <b>Activity:</b>",
    "stats_active_7d": "Active (7d): {count} ({percent}%)",
    "stats_active_30d": "Active (30d): {count} ({percent}%)",
    "stats_inactive": "Inactive: {count}",
    "stats_blocked": "🚫 Blocked: {count}",
    "stats_registrations": "📅 <b>Registrations (7 days):</b>",
    
    # Stats - Finance
    "stats_finance_title": "💰 <b>Finance</b> ({period})",
    "stats_total_balance": "💳 Total balance: {amount} tokens",
    "stats_revenue": "📈 <b>Revenue:</b>",
    "stats_revenue_today": "Today: {amount} ₽",
    "stats_revenue_period": "Period: {amount} ₽",
    "stats_transactions": "📊 Transactions: {count}",
    "stats_avg_check": "💵 Average check: {amount} ₽",
    "stats_spent": "🔥 Spent: {amount} tokens",
    "stats_top_spenders": "🏆 <b>Top spenders:</b>",
    
    # Stats - Daily Bonus
    "stats_bonus_title": "🎁 <b>Daily Bonus</b> ({period})",
    "stats_claims_today": "📊 Claimed today: {count}",
    "stats_claims_period": "📈 Period: {count}",
    "stats_tokens_given": "🪙 Tokens given: {amount}",
    "stats_streaks": "🔥 <b>Streaks:</b>",
    "stats_streak_avg": "Average: {days} days",
    "stats_streak_max": "Maximum: {days} days",
    "stats_streak_active": "Active: {count}",
    
    # Stats - Referrals
    "stats_referrals_title": "🤝 <b>Referrals</b> ({period})",
    "stats_referrals_total": "📊 Total referrals: {count}",
    "stats_referrals_period": "📈 Period: +{count}",
    "stats_partners_active": "👥 Active partners: {count}",
    "stats_commissions_paid": "💰 Commissions paid: {amount} ₽",
    "stats_top_referrers": "🏆 <b>Top referrers:</b>",
    
    # Stats - Analytics
    "stats_analytics_title": "📈 <b>Analytics</b> ({period})",
    "stats_events_total": "📊 Events: {count}",
    "stats_unique_users": "👥 Unique users: {count}",
    "stats_categories": "📁 <b>Categories:</b>",
    "stats_popular_events": "🔥 <b>Popular events:</b>",
    
    # Days of week
    "day_mon": "Mon",
    "day_tue": "Tue",
    "day_wed": "Wed",
    "day_thu": "Thu",
    "day_fri": "Fri",
    "day_sat": "Sat",
    "day_sun": "Sun",
    
    "broadcast_title": "📢 <b>Broadcast</b>",
    "broadcast_enter_text": "Enter broadcast text:",
    "broadcast_select_target": "Select audience:",
    "broadcast_target_all": "All users",
    "broadcast_target_active": "Active (7 days)",
    "broadcast_confirm": "Send broadcast?\n\nRecipients: {count}",
    "broadcast_started": "✅ Broadcast started",
    "broadcast_progress": "📤 Sent: {sent}/{total}",
    "broadcast_completed": "✅ Broadcast completed\n\nDelivered: {delivered}\nFailed: {failed}",
    
    "mod_warn": "⚠️ Issue Warning",
    "mod_ban_temp": "🚫 Temporary Ban",
    "mod_ban_perm": "⛔ Permanent Ban",
    "mod_unban": "✅ Unban",
    "mod_history": "📋 Moderation History",
    
    # Main menu
    "menu_stats": "📊 Statistics",
    "menu_users": "👤 Users",
    "menu_partners": "👥 Partners",
    "menu_moderation": "🛡 Moderation",
    "menu_promocodes": "🎁 Promo codes",
    "menu_services": "📦 Services",
    "menu_broadcast": "📢 Broadcast",
    "menu_settings": "⚙️ Settings",
    "menu_languages": "🌐 Languages",
    
    # Settings
    "settings_title": "⚙️ <b>Settings</b>",
    "settings_select_category": "Select category to configure:",
    "settings_general": "🤖 General",
    "settings_tokens": "💰 Tokens & Balance",
    "settings_referral": "👥 Referral System",
    "settings_moderation": "🛡 Moderation",
    "settings_daily_bonus": "🎁 Daily Bonus",
    "settings_notifications": "🔔 Notifications",
    "settings_changed": "✅ Setting saved",
    "settings_enter_value": "Enter new value:",
    "settings_enter_number": "Enter a number:",
    "settings_enter_json": "Enter JSON (e.g. [1,2,3,5,5,7,10]):",
    "settings_invalid_number": "❌ Enter a number",
    "settings_invalid_json": "❌ Invalid JSON format",
    
    # Languages
    "languages_title": "🌐 <b>Languages</b>",
    "languages_current": "Your language: {flag} {name}",
    "languages_select": "Select interface language:",
    "languages_changed": "✅ Language changed",
    
    # Broadcast
    "broadcast_title": "📢 <b>Broadcast</b>",
    "broadcast_stats": "📊 Statistics:",
    "broadcast_sent_today": "Sent today: {count}",
    "broadcast_delivered": "Delivered: {count} ({percent}%)",
    "broadcast_triggers_active": "Active triggers: {count}",
    "broadcast_scheduled": "Scheduled: {count}",
    "broadcast_create": "📝 New Broadcast",
    "broadcast_history": "📋 History",
    "broadcast_triggers": "⚙️ Auto Broadcasts",
    "broadcast_ab_test": "🔬 A/B Test (dev)",
    "broadcast_coming_soon": "🔧 Feature in development",
    "broadcast_create_title": "📝 <b>New Broadcast</b>",
    "broadcast_create_prompt": "Enter broadcast text:",
    "broadcast_create_hint": "Supports HTML formatting",
    "broadcast_select_target": "🎯 <b>Select Target Audience</b>",
    "broadcast_select_target_hint": "Choose who will receive the broadcast:",
    "broadcast_preview_title": "👁 <b>Preview</b>",
    "broadcast_preview_text": "📝 Text:",
    "broadcast_preview_target": "🎯 Target: {target}",
    "broadcast_preview_recipients": "👥 Recipients: {count}",
    "broadcast_preview_media": "📎 Media: {type}",
    "broadcast_preview_buttons": "🔘 Buttons: {count}",
    "broadcast_send_now": "🚀 Send Now",
    "broadcast_schedule": "📅 Schedule",
    "broadcast_add_button": "🔘 Add Button",
    "broadcast_add_media": "📎 Add Media",
    "broadcast_started": "🚀 Broadcast started!",
    "broadcast_history_title": "📋 <b>Broadcast History</b>",
    "broadcast_history_empty": "No broadcasts yet",
    "broadcast_view_title": "📢 <b>Broadcast #{id}</b>",
    "broadcast_status": "📊 Status: {status}",
    "broadcast_created_at": "📅 Created: {date}",
    "broadcast_started_at": "🚀 Started: {date}",
    "broadcast_completed_at": "✅ Completed: {date}",
    "broadcast_sent_count": "📤 Sent: {sent}/{total}",
    "broadcast_delivered_count": "✅ Delivered: {count}",
    "broadcast_failed_count": "❌ Failed: {count}",
    "broadcast_delivery_rate": "📈 Delivery rate: {rate}%",
    "broadcast_text_preview": "📝 Text:",
    "broadcast_pause": "⏸ Pause",
    "broadcast_resume": "▶️ Resume",
    "broadcast_cancel": "❌ Cancel",
    "broadcast_paused": "⏸ Broadcast paused",
    "broadcast_resumed": "▶️ Broadcast resumed",
    "broadcast_cancelled": "❌ Broadcast cancelled",
    "broadcast_status_completed": "✅ Completed",
    "broadcast_status_sending": "📤 Sending",
    "broadcast_status_paused": "⏸ Paused",
    "broadcast_status_scheduled": "📅 Scheduled",
    "broadcast_status_cancelled": "❌ Cancelled",
    "broadcast_status_draft": "📝 Draft",
    
    # Audiences
    "audience_all": "👥 All users",
    "audience_active_7d": "🟢 Active (7 days)",
    "audience_active_30d": "🟡 Active (30 days)",
    "audience_with_balance": "💰 With balance > 0",
    "audience_with_subscription": "⭐ With subscription",
    "audience_new_week": "🆕 New (week)",
    "audience_inactive_30d": "😴 Inactive (30+ days)",
    
    # Pagination
    "page_info": "Page {current}/{total}",
    "page_prev": "◀️ Prev",
    "page_next": "Next ▶️",
    
    # Triggers
    "triggers_title": "⚙️ <b>Auto Broadcasts</b>",
    "triggers_empty": "📭 No configured triggers",
    "triggers_description": "Triggers automatically send messages to users under certain conditions.",
    "trigger_active": "Active",
    "trigger_inactive": "Disabled",
    "trigger_conditions": "🎯 Conditions",
    "trigger_behavior": "🔄 Behavior",
    "trigger_text": "📝 Text",
    "trigger_media": "🖼 Media",
    "trigger_buttons": "🔘 Buttons",
    "trigger_send_now": "🚀 Send Now",
    "trigger_no_users": "📭 <b>No matching users</b>",
    "trigger_send_complete": "✅ <b>Broadcast completed</b>",
    "trigger_sent": "📤 Sent: {count}",
    "trigger_failed": "❌ Failed: {count}",
    
    # Users
    "users_title": "👤 <b>Users</b>",
    "users_search": "🔍 Search",
    "users_search_prompt": "Enter username, ID or name:",
    "users_not_found": "User not found",
    "users_total": "Total: {count}",
    "users_active": "Active: {count}",
    "users_blocked": "Blocked: {count}",
    
    # User profile
    "user_profile": "👤 <b>User Profile</b>",
    "user_id": "ID: {id}",
    "user_username": "Username: @{username}",
    "user_name": "Name: {name}",
    "user_balance": "💰 Balance: {balance} tokens",
    "user_registered": "📅 Registered: {date}",
    "user_last_active": "🕐 Last active: {date}",
    "user_add_balance": "➕ Add Balance",
    "user_subtract_balance": "➖ Subtract Balance",
    "user_send_message": "💬 Send Message",
    "user_enter_amount": "Enter amount:",
    "user_balance_added": "✅ Added {amount} tokens",
    "user_balance_subtracted": "✅ Subtracted {amount} tokens",
    "user_message_sent": "✅ Message sent",
    
    # Moderation
    "moderation_title": "🛡 <b>Moderation</b>",
    "moderation_search": "🔍 Search User",
    "moderation_recent_actions": "📋 Recent Actions",
    "moderation_blocked_users": "🚫 Blocked Users",
    "moderation_warnings": "⚠️ Warnings",
    "moderation_warn_user": "⚠️ Issue Warning",
    "moderation_ban_user": "🚫 Ban User",
    "moderation_unban_user": "✅ Unban User",
    "moderation_select_reason": "Select reason:",
    "moderation_enter_reason": "Enter reason:",
    "moderation_enter_days": "Enter ban duration (days):",
    "moderation_warned": "✅ Warning issued",
    "moderation_banned": "✅ User banned",
    "moderation_unbanned": "✅ User unbanned",
    
    # Promocodes
    "promocodes_title": "🎁 <b>Promo Codes</b>",
    "promo_type_tokens": "🪙 Tokens",
    "promo_type_subscription": "⭐ Subscription",
    "promo_type_discount": "💸 Discount",
    "promo_stats_title": "📊 <b>Promocode Statistics</b>",
    "promo_stats_today": "📅 Today: {count} activations",
    "promo_stats_week": "📆 This week: {count} activations",
    "promo_stats_tokens": "🪙 Tokens given: {count}",
    "promo_stats_top": "<b>Top promocodes:</b>",
    
    # Promocodes - List & View
    "promo_list_title": "🎁 <b>Promocodes</b>",
    "promo_activations": "Activations",
    "filter_all": "All",
    "promo_status_active": "Active",
    "promo_status_disabled": "Disabled",
    "promo_status_expired": "Expired",
    "promo_status_exhausted": "Limit reached",
    "promo_view_status": "Status",
    "promo_view_type": "Type",
    "promo_view_value": "Value",
    "promo_view_activations": "Activations",
    "promo_view_dates": "Dates",
    "promo_view_conditions": "Conditions",
    "promo_current": "Current",
    "promo_per_user": "Per user",
    "promo_starts": "Starts",
    "promo_expires": "Expires",
    "promo_created": "Created",
    "promo_only_new": "Only for new users",
    "promo_first_deposit": "First deposit only",
    "promo_min_balance": "Min balance: {amount}",
    "promo_bound_to": "For user: {user}",
    "tokens": "tokens",
    "days": "days",
    
    # Promocodes - Edit buttons
    "promo_edit_value": "💰 Value",
    "promo_edit_limits": "📊 Limits",
    "promo_edit_dates": "📅 Dates",
    "promo_edit_binding": "👤 Binding",
    "promo_history": "📋 History",
    "promo_enable": "▶️ Enable",
    "promo_disable": "⏸ Disable",
    "promo_delete": "🗑 Delete",
    
    # Promocodes - Creation wizard
    "promo_create_value_title": "💰 <b>Creating: {type}</b>",
    "promo_create_value_tokens": "Select token amount:",
    "promo_create_value_subscription": "Select subscription days:",
    "promo_create_value_discount": "Select discount percent:",
    "promo_create_code_title": "📝 <b>Promocode</b>",
    "promo_create_code_prompt": "Choose code option:",
    "promo_code_generate": "🎲 Generate random",
    "promo_code_custom": "✏️ Enter custom",
    "promo_enter_code": "Enter promocode (3-20 characters):",
    "promo_code_set": "✅ Code set: <code>{code}</code>",
    "promo_code_invalid_length": "❌ Code must be 3-20 characters",
    "promo_code_exists": "❌ This code already exists",
    "promo_create_limits_title": "📊 <b>Activation Limits</b>",
    "promo_code": "Code",
    "promo_max_activations": "Max activations",
    "promo_limit_total": "Total",
    "promo_limit_per_user": "Per user",
    "promo_next": "Next ➡️",
    "promo_create_dates_title": "📅 <b>Validity Period</b>",
    "promo_now": "Now",
    "promo_never": "Never",
    "promo_no_expiry": "♾ No expiry",
    "promo_create_binding_title": "👤 <b>User Binding</b>",
    "promo_only_new_users": "Only for new users",
    "promo_bind_user": "👤 Bind to specific user",
    "promo_bind_partner": "👥 Bind to partner (referrals)",
    "promo_for_all": "👥 For all users",
    "promo_enter_partner_id": "Enter partner ID, user ID, Telegram ID or @username:",
    "promo_partner_not_found": "❌ Partner not found",
    "promo_partner_bound": "✅ Bound to partner: {partner}\n\nUsers who activate this promo will become referrals of this partner.",
    "promo_finish": "✅ Create promocode",
    "promo_enter_user_id": "Enter user ID, Telegram ID or @username:",
    "promo_user_not_found": "❌ User not found",
    "promo_user_bound": "✅ Bound to: {user}",
    "promo_continue": "Continue ➡️",
    "promo_created_success": "✅ <b>Promocode created!</b>",
    "promo_view": "👁 View",
    "promo_create_another": "➕ Create another",
    
    # Promocodes - History & Delete
    "promo_history_title": "📋 <b>History: {code}</b>",
    "promo_no_activations": "No activations yet",
    "promo_delete_confirm": "🗑 Delete promocode <b>{code}</b>?\n\nThis action cannot be undone.",
    "promo_delete_yes": "🗑 Yes, delete",
    "promo_deleted": "✅ Promocode deleted",
    "promocodes_active": "Active: {count}",
    "promocodes_total_activations": "Total activations: {count}",
    "promocodes_create": "➕ Create promo code",
    "promocodes_list": "📋 Promo codes list",
    "promocodes_stats": "📊 Statistics",
    "promocodes_empty": "No promo codes",
    "promocodes_not_found": "Promo code not found",
    "promocodes_toggled": "Promo code {status}",
    "promocodes_select_reward": "Select reward type:",
    "promocodes_enabled": "enabled",
    "promocodes_disabled": "disabled",
    
    # Services
    "services_title": "📦 <b>Services</b>",
    "services_empty": "No installed services.",
    "services_install_hint": "To install a service:\n1. Place service folder in <code>services/</code>\n2. Restart the bot",
    "services_refresh": "🔄 Refresh",
    "services_not_found": "Service not found",
    "services_version": "Version: {version}",
    "services_author": "Author: {author}",
    "services_status": "Status: {status}",
    "services_installed": "Installed: {date}",
    "services_active": "✅ Active",
    "services_disabled": "❌ Disabled",
    "services_disable": "❌ Disable",
    "services_enable": "✅ Enable",
    "services_author_unknown": "unknown",
    
    # Settings labels
    "setting_bot_name": "Bot name",
    "setting_support": "Support",
    "setting_default_language": "Default language",
    "setting_rate_rub": "Rate (₽ per 1 token)",
    "setting_min_purchase": "Min. purchase (₽)",
    "setting_welcome_bonus": "Welcome bonus",
    "setting_referral_enabled": "Enabled",
    "setting_commission_enabled": "Commissions enabled",
    "setting_level1": "Referrer commission (%)",
    "setting_partner_level1": "Partner commission (%)",
    "setting_level2": "Level 2 (%)",
    "setting_level2_enabled": "Level 2 enabled",
    "setting_min_payout": "Min. payout (GTON)",
    "setting_fee_payout": "Payout fee (%)",
    "setting_fee_deposit": "Deposit fee (%)",
    "setting_min_deposit": "Min. deposit (GTON)",
    "setting_max_deposit": "Max. deposit (GTON)",
    "setting_gton_ton_rate": "1 GTON = X TON",
    "setting_warnings_before_ban": "Warnings before ban",
    "setting_ban_duration": "Ban duration (days)",
    "setting_daily_enabled": "Enabled",
    "setting_daily_rewards": "Rewards (JSON)",
    "setting_notif_new_users": "New users",
    "setting_notif_payments": "Payments",
    "setting_notif_errors": "Errors",
    "setting_notif_channel": "Notification channel",
    "setting_quiet_start": "Quiet mode from (hour)",
    "setting_quiet_end": "Quiet mode to (hour)",
    "setting_category_not_found": "Category not found",
    "settings_general": "General",
    "settings_tokens": "Tokens & Balance",
    "settings_referral": "Referral System",
    "settings_moderation": "Moderation",
    "settings_daily_bonus": "Daily Bonus",
    "settings_notifications": "Notifications",
    "settings_enter_number": "Enter a number:",
    "settings_enter_json": "Enter JSON (e.g. [1,2,3,5,5,7,10]):",
    "settings_enter_value": "Enter new value:",
    
    # Time ago
    "time_just_now": "just now",
    "time_min_ago": "{min} min ago",
    "time_hours_ago": "{hours}h ago",
    
    # Moderation
    "mod_user_not_found": "User not found",
    "mod_reason_3_warnings": "Auto-ban: 3 warnings",
    "mod_reason": "Reason: {reason}",
    "mod_warnings_count": "Warnings: {count}/3",
    "mod_temp_ban_reason": "Temporary ban",
    "mod_perm_ban_reason": "Permanent ban",
    "mod_until": "Until: {date}",
    "mod_rules_violation": "Rules violation",
    "mod_no_history": "No history",
    
    # Trigger types
    "trigger_type_low_balance": "💰 Low Balance",
    "trigger_type_low_balance_desc": "Send to users with low balance",
    "trigger_type_subscription_expiring": "⏰ Subscription Expiring",
    "trigger_type_subscription_expiring_desc": "Send N days before subscription expires",
    "trigger_type_subscription_expired": "❌ Subscription Expired",
    "trigger_type_subscription_expired_desc": "Send after subscription expires",
    "trigger_type_inactive": "😴 Inactive",
    "trigger_type_inactive_desc": "Send to inactive users",
    "trigger_type_welcome": "👋 Welcome",
    "trigger_type_welcome_desc": "Send to new users",
    "trigger_type_after_deposit": "💳 After Deposit",
    "trigger_type_after_deposit_desc": "Send after deposit",
    
    # Trigger condition labels
    "cond_balance_less_than": "Balance less than",
    "cond_days_before_expiry": "Days before expiry",
    "cond_hours_after_expiry": "Hours after expiry",
    "cond_inactive_days": "Days inactive",
    "cond_exclude_new_users_days": "Exclude new users (days)",
    "cond_hours_after_registration": "Hours after registration",
    "cond_only_if_inactive": "Only if inactive",
    "cond_min_amount": "Min. amount",
    "cond_first_deposit_only": "First deposit only",
    
    # Trigger messages
    "trigger_not_found": "Trigger not found",
    "trigger_no_matching": "📭 <b>No matching users</b>\n\nTrigger: {name}\nNo users match the conditions.",
    "trigger_send_complete": "✅ <b>Broadcast completed</b>\n\nTrigger: {name}\n\n📤 Sent: {sent}\n❌ Failed: {failed}",
    "trigger_status_active": "Active",
    "trigger_status_disabled": "Disabled",
    "trigger_toggled": "Trigger {status}",
    "trigger_yes": "Yes",
    "trigger_no": "No",
    
    # Trigger edit
    "trigger_edit_text_title": "📝 <b>Edit Text</b>\n\nTrigger: {name}\n\n",
    "trigger_edit_text_current": "Current text:\n",
    "trigger_edit_text_empty": "Text not set\n",
    "trigger_edit_text_prompt": "Send new text:",
    "trigger_edit_media_title": "🖼 <b>Edit Media</b>\n\nTrigger: {name}\n\n",
    "trigger_edit_media_current": "Current media: {type}\n\n",
    "trigger_edit_media_none": "No media attached\n\n",
    "trigger_edit_media_prompt": "Send photo, video or GIF:",
    "trigger_media_removed": "Media removed",
    "trigger_edit_buttons_title": "🔘 <b>Edit Buttons</b>\n\nTrigger: {name}\n\n",
    "trigger_edit_buttons_current": "Current buttons:\n",
    "trigger_edit_buttons_none": "No buttons\n",
    "trigger_buttons_removed": "Buttons removed",
    "trigger_edit_cond_title": "🎯 <b>Edit Conditions</b>\n\nTrigger: {name}\nType: {type}\n\n",
    "trigger_edit_cond_current": "Current conditions:\n",
    "trigger_edit_behavior_title": "🔄 <b>Edit Behavior</b>\n\nTrigger: {name}\n\n",
    "trigger_edit_behavior_current": "Current settings:\n",
    "trigger_edit_param": "Parameter: {label}\nCurrent value: <code>{value}</code>\n\nEnter new value:",
    
    # Behavior labels
    "behavior_max_sends": "Max sends per user",
    "behavior_repeat_days": "Repeat every (days)",
    "behavior_send_time": "Send time",
    "behavior_send_time_hint": "Format: 9-21 (start-end hours)",
    "behavior_delay": "Delay before sending",
    "behavior_delay_hint": "Minutes",
    
    # Triggers list
    "triggers_auto_desc": "Triggers automatically send messages to users under certain conditions.",
    "triggers_type": "Type: {type}",
    "triggers_conditions": "Conditions for trigger:",
    
    # Partners - Main
    "partners_title": "👥 <b>Partners</b>",
    "partners_total": "📊 Total: {count}",
    "partners_active": "Active: {count}",
    "partners_pending": "📝 Applications: {count}",
    "partners_payouts_pending": "💸 Pending payouts: {count}",
    "partners_list": "📋 Partners List",
    "partners_applications": "📝 Applications ({count})",
    "partners_payouts": "💸 Payouts ({count})",
    "partners_stats": "📊 Statistics",
    
    # Partners - Filters
    "partners_filter_all": "All",
    "partners_filter_active": "Active",
    "partners_filter_pending": "Pending",
    "partners_filter_rejected": "Rejected",
    
    # Partners - List
    "partners_list_title": "👥 <b>Partners List</b>",
    "partners_empty": "No partners",
    "partner_status_active": "✅",
    "partner_status_pending": "⏳",
    "partner_status_rejected": "❌",
    "partner_status_inactive": "🔴",
    
    # Partners - Card
    "partner_card_title": "👤 <b>Partner #{id}</b>",
    "partner_user": "👤 {name}",
    "partner_since": "📅 Partner since: {date}",
    "partner_status": "📊 Status: {status}",
    "partner_status_text_active": "✅ Active",
    "partner_status_text_pending": "⏳ Pending",
    "partner_status_text_rejected": "❌ Rejected",
    "partner_status_text_inactive": "🔴 Inactive",
    
    # Partners - Finance
    "partner_finance_title": "💰 <b>Finance:</b>",
    "partner_balance": "Balance: {amount} ₽",
    "partner_total_earned": "Total earned: {amount} ₽",
    "partner_withdrawn": "Withdrawn: {amount} ₽",
    
    # Partners - Referrals
    "partner_referrals_title": "👥 <b>Referrals:</b>",
    "partner_referrals_total": "Total: {count}",
    "partner_referrals_active": "Active: {count}",
    "partner_referrals_earned": "Earned from them: {amount} ₽",
    "partner_commission": "📈 Commission: {percent}%",
    
    # Partners - Actions
    "partner_action_payout": "💸 Payout",
    "partner_action_commission": "✏️ Commission",
    "partner_action_referrals": "👥 Referrals",
    "partner_action_history": "📋 History",
    "partner_action_deactivate": "🚫 Deactivate",
    "partner_action_activate": "✅ Activate",
    
    # Partners - Commission
    "partner_commission_title": "✏️ <b>Change Commission</b>",
    "partner_commission_current": "Current commission: {percent}%",
    "partner_commission_select": "Select new commission:",
    "partner_commission_success": "✅ Commission changed to {percent}%",
    
    # Partners - Applications
    "partners_apps_title": "📝 <b>Partnership Applications</b>",
    "partners_apps_pending": "Pending review: {count}",
    "partners_apps_empty": "No new applications",
    "partner_app_ago": "{time} ago",
    "partner_app_referrals": "Referrals: {count}",
    "partner_app_spent": "Spent: {amount} ₽",
    "partner_app_review": "👤 Review",
    
    # Partners - Application Review
    "partner_review_title": "📝 <b>Partnership Application</b>",
    "partner_review_submitted": "📅 Submitted: {date}",
    "partner_review_user_stats": "📊 <b>User Statistics:</b>",
    "partner_review_member_since": "Member since: {date}",
    "partner_review_own_spent": "Own spending: {amount} ₽",
    "partner_review_approve": "✅ Approve ({percent}%)",
    "partner_review_reject": "❌ Reject",
    
    # Partners - Payouts
    "partners_payouts_title": "💸 <b>Payout Requests</b>",
    "partners_payouts_waiting": "Waiting: {count}",
    "partners_payouts_sum": "Total amount: {amount} ₽",
    "partners_payouts_empty": "No payout requests",
    "partner_payout_method_card": "💳 Card",
    "partner_payout_method_sbp": "📱 SBP",
    "partner_payout_process": "💳 Process",
    
    # Partners - Payout Process
    "partner_payout_title": "💸 <b>Payout</b>",
    "partner_payout_partner": "Partner: {name} (#{id})",
    "partner_payout_amount": "Amount: {amount} ₽",
    "partner_payout_method": "Method: {method}",
    "partner_payout_details": "Details: {details}",
    "partner_payout_confirm": "✅ Paid",
    "partner_payout_reject": "❌ Reject",
    "partner_payout_success": "✅ Payout confirmed",
    "partner_payout_rejected": "❌ Request rejected",
    
    # Partners - History
    "partner_history_title": "📋 <b>Payout History</b> #{id}",
    "partner_history_empty": "No payouts",
    "partner_history_paid": "✅ Paid",
    "partner_history_rejected": "❌ Rejected",
    "partner_history_pending": "⏳ Pending",
    
    # Partners - Stats
    "partners_stats_title": "📊 <b>Partner Statistics</b>",
    "partners_stats_total": "👥 Total partners: {count}",
    "partners_stats_active": "✅ Active: {count}",
    "partners_stats_referrals": "👤 Total referrals: {count}",
    "partners_stats_paid_month": "💸 Paid this month: {amount} ₽",
    "partners_stats_paid_total": "💰 Total paid: {amount} ₽",
    "partners_stats_top": "🏆 <b>Top Partners:</b>",
    
    # Partners - Notifications
    "notify_partner_approved": "🎉 <b>Application approved!</b>\n\nYou are now a partner!\nYour commission: {percent}%\n\nInvite friends and earn!",
    "notify_partner_rejected": "❌ <b>Application rejected</b>\n\nUnfortunately, your partnership application was rejected.",
    "notify_partner_payout_done": "💸 <b>Payout completed!</b>\n\nAmount: {amount} ₽\nMethod: {method}\n\nThank you for cooperation!",
    "notify_partner_payout_rejected": "❌ <b>Payout request rejected</b>\n\nAmount: {amount} ₽\nContact support for details.",
    "notify_partner_deactivated": "🔴 <b>Partnership suspended</b>\n\nYour partner account has been deactivated.",
    "notify_partner_activated": "✅ <b>Partnership restored</b>\n\nYour partner account is active again!",
    
    # Users - Extended
    "users_new": "New: +{count}",
    "users_recent": "Recent registrations:",
    "users_filters": "📊 Filters",
    
    # Users - Filters
    "filter_all": "All",
    "filter_active": "Active (7d)",
    "filter_today": "New (today)",
    "filter_with_balance": "With balance",
    "filter_blocked": "Blocked",
    
    # Users - Search
    "users_search_title": "🔍 <b>Search User</b>",
    "users_search_not_found": "❌ User not found",
    "users_search_results": "🔍 <b>Search Results:</b>",
    "users_search_by_id": "By ID",
    "users_search_by_username": "By @username",
    "users_search_by_name": "By name",
    
    # Users - Card
    "user_card_title": "👤 <b>User #{id}</b>",
    "user_telegram": "📱 @{username}",
    "user_telegram_no": "📱 No username",
    "user_language": "🌐 Language: {language}",
    "user_last_activity": "🕐 Last activity: {time}",
    "user_status_active": "✅ Active",
    "user_status_blocked": "🚫 Blocked",
    
    # Users - Balance
    "user_balance_title": "💰 <b>Balance:</b>",
    "user_balance_main": "Main: {amount} tokens",
    "user_balance_bonus": "Bonus: {amount} tokens",
    
    # Users - Stats
    "user_stats_title": "📊 <b>Statistics:</b>",
    "user_stats_spent": "Spent: {amount} tokens",
    "user_stats_transactions": "Transactions: {count}",
    "user_stats_deposits": "Deposits: {count} ({amount} ₽)",
    
    # Users - Referral
    "user_referrer": "🤝 Referrer: {name} (#{id})",
    "user_referrer_none": "🤝 Referrer: none",
    "user_referrals_count": "👥 Referred: {count} users",
    
    # Users - Actions
    "user_action_balance": "💰 Balance",
    "user_action_message": "📨 Message",
    "user_action_moderation": "⚠️ Moderation",
    "user_action_transactions": "📋 Transactions",
    "user_action_to_user": "👤 To User",
    "user_new_balance": "💰 New balance: {balance} tokens",
    
    # Users - Balance Change
    "balance_change_title": "💰 <b>Change Balance</b>",
    "balance_change_user": "User: {name} (#{id})",
    "balance_change_current": "Current balance: {amount} tokens",
    "balance_add": "➕ Add",
    "balance_subtract": "➖ Subtract",
    "balance_enter_amount": "Enter token amount:",
    "balance_enter_reason": "Enter reason:",
    "balance_confirm": "Confirm {action} {amount} tokens?",
    "balance_success_add": "✅ Added {amount} tokens",
    "balance_success_subtract": "✅ Subtracted {amount} tokens",
    "balance_error_insufficient": "❌ Insufficient funds",
    
    # Users - Message
    "message_title": "📨 <b>Message to User</b>",
    "message_enter_text": "Enter message text:",
    "message_sent": "✅ Message sent",
    "message_error": "❌ Send error",
    
    # Users - Transactions
    "transactions_title": "📋 <b>Transactions</b> #{id}",
    "transactions_empty": "No transactions",
    "transaction_deposit": "💳 Deposit",
    "transaction_usage": "🔥 Usage",
    "transaction_bonus": "🎁 Bonus",
    "transaction_refund": "↩️ Refund",
    "transaction_referral": "🤝 Referral commission",
    "transaction_promocode": "🎁 Promo code",
    
    # Notifications to user
    "notify_balance_added": "💰 <b>Balance topped up</b>\n\nYou received {amount} tokens.\nNew balance: {balance} tokens",
    "notify_balance_subtracted": "💸 <b>Balance deducted</b>\n\nDeducted {amount} tokens.\nNew balance: {balance} tokens",
    "notify_warning": "⚠️ <b>Warning</b>\n\nYou received a warning.\nReason: {reason}\n\nWarnings: {current}/{max}",
    "notify_ban_temp": "🚫 <b>Temporary ban</b>\n\nYour account is banned for {days} days.\nReason: {reason}\n\nUnban date: {until}",
    "notify_ban_perm": "⛔ <b>Account banned</b>\n\nYour account is permanently banned.\nReason: {reason}",
    "notify_unban": "✅ <b>Unbanned</b>\n\nYour account has been unbanned. Welcome back!",
    "notify_warning_autoban": "🚫 <b>Automatic ban</b>\n\nYou received {max} warnings.\nAccount banned for {days} days.",
    
    # Triggers - Extended
    "trigger_create": "➕ Create Trigger",
    "trigger_select_type": "📌 <b>Select trigger type:</b>",
    "trigger_create_title": "⚙️ <b>Creating trigger: {type}</b>",
    "trigger_enter_name": "Enter trigger name:",
    "trigger_enter_text": "Enter message text:",
    "trigger_created": "✅ Trigger created and activated!",
    "trigger_view_status": "📊 Status: {status}",
    "trigger_stats_title": "Statistics",
    "trigger_stats_sent": "Sent",
    "trigger_stats_delivered": "Delivered",
    "trigger_message": "Message",
    "trigger_btn_text": "✏️ Text",
    "trigger_btn_media": "📎 Media",
    "trigger_btn_buttons": "🔘 Buttons",
    "trigger_btn_conditions": "🎯 Conditions",
    "trigger_btn_behavior": "🔄 Behavior",
    "trigger_btn_enable": "▶️ Enable",
    "trigger_btn_disable": "⏸ Disable",
    "triggers_stats": "📊 Total: {total} | Active: {active}",
    "trigger_deleted": "🗑 Trigger deleted",
    "trigger_text_updated": "✅ Trigger text updated",
    "trigger_media_invalid": "❌ Send photo, video or GIF",
    "trigger_media_added": "✅ Media added ({type})",
    "trigger_button_format_error": "❌ Invalid format. Use: Text | URL",
    "trigger_button_added": "✅ Button added",
    "trigger_cond_updated": "✅ Condition updated: {param} = {value}",
    "trigger_behavior_updated": "✅ Setting updated",
    "trigger_error_number": "❌ Enter a number",
    "trigger_error_time_format": "❌ Format: 9-21",
    "trigger_error_minutes": "❌ Enter number of minutes",
    
    # Broadcast - Schedule
    "broadcast_schedule_title": "📅 <b>Schedule Broadcast</b>",
    "broadcast_schedule_prompt": "Enter date and time:",
    "broadcast_schedule_format": "Format: DD.MM.YYYY HH:MM\nExample: 25.12.2024 10:00",
    "broadcast_schedule_error": "❌ Invalid format. Use: DD.MM.YYYY HH:MM",
    "broadcast_schedule_past": "❌ Date must be in the future",
    "broadcast_scheduled_success": "✅ Broadcast scheduled for {time}",
    
    # Broadcast - A/B Test
    "broadcast_ab_title": "🔀 <b>A/B Testing</b>",
    "broadcast_ab_prompt": "Enter text for variant B:\n\n(Variant A — current text)",
    
    # Broadcast - Button
    "broadcast_button_title": "🔘 <b>Add Button</b>",
    "broadcast_button_prompt": "Enter button text and URL:",
    "broadcast_button_format": "Format: Button text | https://url.com",
    "broadcast_button_added": "✅ Button added",
    "broadcast_button_error": "❌ Invalid format. Use: Text | URL",
    
    # Broadcast - Media
    "broadcast_media_title": "📎 <b>Add Media</b>",
    "broadcast_media_prompt": "Send photo, video or GIF:",
    "broadcast_media_added": "✅ Media added ({type})",
    "broadcast_media_error": "❌ Send photo, video or GIF",
    
    # Moderation - Reasons
    "reason_spam": "📢 Spam",
    "reason_abuse": "🤬 Abuse",
    "reason_fraud": "🚨 Fraud",
    "reason_terms_violation": "📜 Terms violation",
    "reason_other": "❓ Other",
    "mod_autoban_info": "🚫 Auto-ban: {days} days",
    "mod_autoban_reason": "(3 warnings limit)",
    
    # Moderation - Extended
    "moderation_action_warn": "⚠️ Warn",
    "moderation_action_ban": "🚫 Ban",
    "moderation_action_ban_perm": "⛔ Permanent Ban",
    "moderation_action_unban": "✅ Unban",
    "moderation_action_revoke_warn": "↩️ Revoke Warning",
    "moderation_action_history": "📋 History",
    "moderation_actions_today": "Actions today: {count}",
    "moderation_stats": "📊 Statistics",
    "moderation_search_prompt": "Enter ID, @username or name:",
    "moderation_search_hint": "Search user to moderate",
    "moderation_log": "📋 Moderation Log",
    "moderation_log_title": "📋 <b>Moderation Log</b>",
    "moderation_log_empty": "No actions",
    
    # Moderation - User
    "moderation_user_title": "👤 <b>User Moderation</b>",
    "moderation_user_name": "👤 {name}",
    "moderation_user_registered": "📅 Registered: {date}",
    "moderation_user_recent": "🕐 Last active: {time}",
    "moderation_user_last_active_minutes": "{min} min ago",
    "moderation_user_last_active_hours": "{hours}h ago",
    "moderation_user_last_active_days": "{days}d ago",
    "moderation_user_status_title": "📊 <b>Status:</b>",
    "moderation_status_active": "✅ Active",
    "moderation_status_banned": "🚫 Banned",
    "moderation_user_warnings": "⚠️ Warnings: {count}",
    "moderation_user_ban_info": "🚫 Ban info:",
    "moderation_user_ban_reason": "Reason: {reason}",
    
    # Moderation - Warnings
    "moderation_warnings_title": "⚠️ <b>Warnings</b>",
    "moderation_warnings_list": "Warning list:",
    "moderation_warnings_empty": "No warnings",
    "moderation_warnings_count": "Warnings: {count}/3",
    "moderation_no_warnings": "No warnings",
    "moderation_warn_revoked": "✅ Warning revoked",
    
    # Moderation - Bans
    "moderation_banned_title": "🚫 <b>Blocked Users</b>",
    "moderation_banned_list": "Blocked users:",
    "moderation_banned_empty": "No blocked users",
    "moderation_banned_count": "Total: {count}",
    "moderation_banned_temp": "🚫 Temporary",
    "moderation_banned_perm": "⛔ Permanent",
    "moderation_ban_until": "Until: {date}",
    "moderation_ban_forever": "Forever",
    
    # Moderation - Filters
    "moderation_filter_warns": "⚠️ Warnings",
    "moderation_filter_bans": "🚫 Bans",
    "moderation_filter_unbans": "✅ Unbans",
    "moderation_filter_temp": "Temporary",
    "moderation_filter_perm": "Permanent",
    
    # Notifications - Extended
    "notify_unban_auto": "✅ <b>Automatic unban</b>\n\nYour temporary ban has expired. Welcome back!",
}

# ==================== PROMOCODE ====================

PROMOCODE = {
    "enter_code": "🎁 <b>Enter promo code:</b>",
    "activated": "✅ <b>Promo code activated!</b>",
    "reward_tokens": "🎁 You received: {amount} tokens",
    "reward_subscription": "⭐ Subscription {plan} activated for {days} days",
    "reward_discount": "💸 Discount {percent}% applied",
    "new_balance": "💰 New balance: {balance} tokens",
    
    # Errors
    "invalid": "❌ Invalid promo code",
    "expired": "❌ Promo code has expired",
    "already_used": "❌ You have already used this promo code",
    "limit_reached": "❌ Promo code activation limit reached",
    "new_users_only": "❌ Promo code is for new users only",
    "first_deposit_only": "❌ Promo code is for first deposit only",
}

# ==================== MODERATION MESSAGES ====================

MODERATION = {
    # Reasons
    "reason_spam": "Spam",
    "reason_abuse": "Abuse",
    "reason_fraud": "Fraud",
    "reason_terms_violation": "Terms violation",
    "reason_other": "Other",
    
    # Warnings
    "warning_issued": "⚠️ You have received a warning",
    "warning_reason": "Reason: {reason}",
    "warning_count": "Warnings: {current}/{max}",
    "warning_notice": "After {max} warnings your account will be temporarily blocked.",
    
    # Ban
    "banned_title": "🚫 Your account is blocked",
    "banned_reason": "Reason: {reason}",
    "banned_permanent": "Duration: permanent",
    "banned_temporary": "Duration: {days} days",
    "banned_until": "Unblock date: {date}",
    "banned_days_left": "Days until unblock: {days}",
    "banned_appeal": "If you think this is a mistake, contact support.",
    
    # Unban
    "unbanned": "✅ Your account has been unblocked",
}
