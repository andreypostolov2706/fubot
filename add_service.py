import sqlite3
import json

conn = sqlite3.connect('data/core.db')
c = conn.cursor()

# API ключ fal.ai
FAL_API_KEY = "666580cb-bf91-48ea-952b-9c31126cb76d:ca3d5943c73ec5f411ec0774dd638461"

# ==================== Nano Banano ====================
nano_config = {
    "fal_api_key": FAL_API_KEY,
    "margin_multiplier": 0.3,
    "prices": {
        "nano_banana": 0.04,
        "nano_banana_pro_1k": 0.15,
        "nano_banana_pro_2k": 0.22,
        "nano_banana_pro_4k": 0.30,
    },
    "referral_bonus_enabled": True,
    "referral_bonus_percent": 10,
    "gallery_channel_id": "",
    "gallery_enabled": False,
}

features = {
    "subscriptions": False,
    "broadcasts": False,
    "partner_menu": False,
    "voice_messages": False,
}

permissions = [
    "balance:read",
    "balance:deduct",
    "balance:add",
    "notifications:send",
    "analytics:track",
]

c.execute('''INSERT OR REPLACE INTO services 
    (id, name, description, version, author, icon, status, features, permissions, config) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (
        'nano_banano',
        'Nano Banano',
        'Генерация и редактирование изображений с помощью ИИ',
        '1.0.0',
        'FuBot Team',
        '🍌',
        'active',
        json.dumps(features),
        json.dumps(permissions),
        json.dumps(nano_config),
    )
)
print('✅ Service nano_banano added!')

# ==================== Veo ====================
veo_config = {
    "fal_api_key": FAL_API_KEY,
    "margin_multiplier": 0.3,
    "prices": {
        "5s": 2.50,
        "6s": 3.00,
        "7s": 3.50,
        "8s": 4.00,
    },
    "gallery_channel_id": "",
    "gallery_enabled": False,
}

c.execute('''INSERT OR REPLACE INTO services 
    (id, name, description, version, author, icon, status, features, permissions, config) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (
        'veo',
        'Veo',
        'Генерация видео с помощью Google Veo 2',
        '1.0.0',
        'FuBot Team',
        '🎬',
        'active',
        json.dumps(features),
        json.dumps(permissions),
        json.dumps(veo_config),
    )
)
print('✅ Service veo added!')

# ==================== GPT-Image ====================
gpt_image_config = {
    "fal_api_key": FAL_API_KEY,
    "margin_multiplier": 0.3,
    "prices": {
        "low_1024x1024": 0.009,
        "low_other": 0.013,
        "medium_1024x1024": 0.034,
        "medium_1536x1024": 0.050,
        "medium_1024x1536": 0.051,
        "high_1024x1024": 0.133,
        "high_1536x1024": 0.199,
        "high_1024x1536": 0.200,
    },
    "gallery_channel_id": "",
    "gallery_enabled": False,
}

c.execute('''INSERT OR REPLACE INTO services 
    (id, name, description, version, author, icon, status, features, permissions, config) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (
        'gpt_image',
        'GPT-Image',
        'Генерация изображений с помощью OpenAI GPT Image 1.5',
        '1.0.0',
        'FuBot Team',
        '🎨',
        'active',
        json.dumps(features),
        json.dumps(permissions),
        json.dumps(gpt_image_config),
    )
)
print('✅ Service gpt_image added!')

# ==================== Kling Video ====================
kling_config = {
    "fal_api_key": FAL_API_KEY,
    "margin_multiplier": 0.3,
    "prices": {
        "5s_no_audio": 0.35,
        "5s_with_audio": 0.70,
        "10s_no_audio": 0.70,
        "10s_with_audio": 1.40,
    },
    "gallery_channel_id": "",
    "gallery_enabled": False,
}

c.execute('''INSERT OR REPLACE INTO services 
    (id, name, description, version, author, icon, status, features, permissions, config) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (
        'kling',
        'Kling Video',
        'Генерация видео с помощью Kling AI v2.6',
        '1.0.0',
        'FuBot Team',
        '🎬',
        'active',
        json.dumps(features),
        json.dumps(permissions),
        json.dumps(kling_config),
    )
)
print('✅ Service kling added!')

conn.commit()
conn.close()
