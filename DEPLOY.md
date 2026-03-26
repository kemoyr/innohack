# Деплой на Railway

## Шаг 1: Загрузить код на GitHub

```bash
# В папке проекта
git init
git add .
git commit -m "ready for railway deploy"

# Создать репо на github.com, затем:
git remote add origin https://github.com/ВАШ_ЛОГИН/ВАШ_РЕПО.git
git push -u origin main
```

## Шаг 2: Создать проект на Railway

1. Зайти на https://railway.app
2. **New Project** → **Deploy from GitHub repo**
3. Выбрать ваш репозиторий
4. Railway автоматически найдёт Dockerfile и начнёт сборку

## Шаг 3: Добавить переменные окружения

В Railway: Settings → Variables → добавить:

| Переменная | Значение |
|---|---|
| `BOT_TOKEN` | токен от @BotFather |
| `ADMIN_PASSWORD` | ваш пароль |
| `SECRET_KEY` | любая длинная случайная строка |
| `DB_PATH` | `/data/volunteer.db` |
| `DEMO_MODE` | `true` |

## Шаг 4: Добавить персистентный диск (важно!)

Без диска SQLite сбросится при каждом рестарте.

1. В Railway: ваш сервис → **Volumes**
2. **Add Volume**
3. Mount path: `/data`
4. Сохранить

## Шаг 5: Получить URL

После деплоя:
1. Settings → Networking → **Generate Domain**
2. Скопировать URL (например `volunteer-plus.railway.app`)
3. Добавить в переменные: `WEBAPP_URL=https://volunteer-plus.railway.app`

## Готово!

- Сайт: `https://volunteer-plus.railway.app`
- API docs: `https://volunteer-plus.railway.app/docs`
- Бот в Telegram работает автоматически

## Демо-данные

При первом запуске бот автоматически засеет демо-данные (10 волонтёров, 8 мероприятий).

Логин для дашборда:
- Email: `coordinator@example.com`
- Пароль: `demo123`
