# Деплой FuBot на RunPod

## Шаг 1: Подготовка Docker-образа

### Вариант A: Загрузка на Docker Hub (рекомендуется)

1. **Установите Docker Desktop** на свой компьютер
   - Скачайте с https://www.docker.com/products/docker-desktop

2. **Создайте аккаунт на Docker Hub**
   - https://hub.docker.com/

3. **Войдите в Docker Hub:**
   ```bash
   docker login
   ```

4. **Соберите образ:**
   ```bash
   cd "c:\Users\Andrey\Desktop\Program\FuBot — Нат.карта"
   docker build -t YOUR_DOCKERHUB_USERNAME/fubot:latest .
   ```

5. **Загрузите образ:**
   ```bash
   docker push YOUR_DOCKERHUB_USERNAME/fubot:latest
   ```

### Вариант B: Использовать GitHub Container Registry

1. Загрузите проект на GitHub
2. Настройте GitHub Actions для автоматической сборки

---

## Шаг 2: Создание Pod на RunPod

1. **Зайдите на RunPod:** https://www.runpod.io/

2. **Создайте новый Pod:**
   - Нажмите "Deploy" → "Pods"
   - Выберите GPU (для бота достаточно CPU-only, но RunPod в основном GPU)
   - Или используйте "Serverless" для CPU

3. **Настройте Pod:**
   - **Container Image:** `YOUR_DOCKERHUB_USERNAME/fubot:latest`
   - **Volume:** Создайте persistent volume для `/app/data` (для базы данных)

4. **Добавьте Environment Variables:**
   ```
   TELEGRAM_BOT_TOKEN=ваш_токен_бота
   ADMIN_IDS=ваш_telegram_id
   DEEPSEEK_API_KEY=ваш_ключ_deepseek
   CRYPTOBOT_API_TOKEN=ваш_токен_cryptobot
   ```

---

## Шаг 3: Альтернатива — RunPod Serverless (CPU)

Для Telegram-бота лучше использовать **Serverless Endpoint**:

1. Создайте Serverless Endpoint
2. Укажите Docker-образ
3. Настройте переменные окружения
4. Endpoint будет работать 24/7

---

## Переменные окружения (обязательные)

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather |
| `ADMIN_IDS` | Ваш Telegram ID (через запятую если несколько) |
| `DEEPSEEK_API_KEY` | API ключ DeepSeek для астрологии |

## Переменные окружения (опциональные)

| Переменная | Описание |
|------------|----------|
| `CRYPTOBOT_API_TOKEN` | Токен CryptoBot для оплаты |
| `CRYPTOBOT_TESTNET` | `true` для тестовой сети |
| `DATABASE_URL` | URL базы данных (по умолчанию SQLite) |
| `DEBUG` | `true` для отладки |
| `LOG_LEVEL` | Уровень логов (INFO, DEBUG, WARNING) |

---

## Альтернативы RunPod (проще для ботов)

Для Telegram-ботов лучше подходят:

1. **Railway.app** — проще всего, есть бесплатный план
   - https://railway.app/

2. **Render.com** — бесплатный план для ботов
   - https://render.com/

3. **Fly.io** — бесплатный план
   - https://fly.io/

4. **DigitalOcean App Platform**
   - https://www.digitalocean.com/products/app-platform

5. **VPS (самый надёжный)**
   - Любой VPS за $5/месяц (DigitalOcean, Hetzner, Timeweb)
   - Установить Docker и запустить контейнер

---

## Быстрый старт на VPS

```bash
# На сервере
apt update && apt install docker.io -y

# Запуск бота
docker run -d \
  --name fubot \
  --restart always \
  -e TELEGRAM_BOT_TOKEN="ваш_токен" \
  -e ADMIN_IDS="ваш_id" \
  -e DEEPSEEK_API_KEY="ваш_ключ" \
  -v fubot_data:/app/data \
  YOUR_DOCKERHUB_USERNAME/fubot:latest

# Просмотр логов
docker logs -f fubot
```

---

## Проверка работы

После запуска:
1. Напишите боту `/start`
2. Проверьте админ-панель
3. Убедитесь что база данных сохраняется (volume)
