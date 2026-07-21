# Деплой на собственный сервер (auroraclient.fun)

Стек: bare-metal — nginx (статика + reverse proxy) + systemd-сервис
(FastAPI/uvicorn на 127.0.0.1:8000, плюс Telegram-бот на long polling в
том же процессе). Код в `bot/main.py` запускает оба сразу.

## 1. Первый деплой

```bash
git clone <URL_РЕПОЗИТОРИЯ> /opt/innohack
cd /opt/innohack
cp .env.example .env   # заполнить реальными значениями, см. ниже
sudo bash deploy/deploy.sh
```

`deploy/deploy.sh` идемпотентен: создаёт системного пользователя `innohack`
(если его ещё нет), ставит Python-зависимости в venv, собирает фронтенд,
устанавливает nginx vhost (`deploy/nginx-auroraclient.conf`) и systemd-юнит
(`deploy/volunteerplus.service`), затем (пере)запускает всё.

## 2. Переменные окружения (`.env` в корне проекта)

| Переменная       | Обязательно | Комментарий |
|------------------|-------------|-------------|
| `SECRET_KEY`     | да          | Длинная случайная строка (подпись JWT). |
| `ADMIN_PASSWORD` | да*         | Пароль координатора при регистрации через Telegram-бота. |
| `BOT_TOKEN`      | нет         | Токен @BotFather. Если пусто — бот отключается, работает только веб. |
| `DB_PATH`        | да (прод)   | `/opt/innohack/data/volunteer.db`. |
| `DEMO_MODE`      | опционально | `true` / `false`. |
| `WEBAPP_URL`     | опционально | `https://auroraclient.fun` — для кнопки «Открыть приложение» в боте. |

`PORT` не задавать — сервис всегда слушает `8000` (см. systemd-юнит и nginx `proxy_pass`).

## 3. SSL (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d auroraclient.fun -d www.auroraclient.fun
```

Сертификат обновляется автоматически через systemd-таймер `certbot.timer`.

## 4. Проверка

- Сайт: `https://auroraclient.fun/`
- API: `https://auroraclient.fun/api/stats`
- Swagger: `https://auroraclient.fun/docs`
- Логи бота/API: `journalctl -u volunteerplus.service -f`

## 5. Обновление после изменений в репозитории

```bash
cd /opt/innohack && git pull
sudo bash deploy/deploy.sh
```

## 6. Откат

```bash
sudo bash deploy/rollback.sh
```

Останавливает сервис и восстанавливает предыдущий nginx-vhost (если он был
перезаписан деплоем). Файлы приложения и база данных не удаляются.

## Типичные проблемы

| Симптом | Что сделать |
|--------|-------------|
| 502 Bad Gateway | `systemctl status volunteerplus.service` — сервис не запущен или упал (смотреть `journalctl -u volunteerplus`). |
| Бот не отвечает | Проверить `BOT_TOKEN` в `.env` и что в логах нет ошибки авторизации от Telegram API. |
| Пустая БД после рестарта | Не тот `DB_PATH`, либо `/opt/innohack/data` удалили при обновлении. |
| 404 на `/ratings` и т.п. | Фронтенд не собран — `frontend/dist` отсутствует; перезапустить `deploy/deploy.sh`. |
