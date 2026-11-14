# Expense Analyzer — локальное веб-приложение и JSON API

## Запуск в браузере

```powershell
cd expense-analyzer-api
python -m pip install -r requirements.txt
python api.py
```

Откройте [http://localhost:5000](http://localhost:5000). Добавьте траты
и нажмите «Проанализировать». Сервер отдаёт и страницу, и отчёт.
Node.js и Expo для браузера не нужны.

Для доступа с телефона в той же Wi-Fi сети запустите
`python -m flask --app api run --host 0.0.0.0 --port 5000`
и укажите IP компьютера вместо `localhost`.

## Эндпоинты

### `GET /api/health`
Проверка, что сервер жив.
```json
{"status": "ok"}
```

### `POST /api/analyze-transactions`
Основной эндпоинт — принимает список трат, введённых вручную в приложении
(JSON, не файл).

Тело запроса:
```json
{
  "transactions": [
    {"date": "2026-09-01", "description": "Pyaterochka", "amount": 1250.50},
    {"date": "2026-09-05", "description": "Uber", "amount": 340.00}
  ]
}
```

Пример через curl:
```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "transactions": [
    {"date": "2026-09-01", "description": "Pyaterochka", "amount": 1250.50}
  ]
}' http://127.0.0.1:5000/api/analyze-transactions
```

Ответ (одинаковый формат для обоих эндпоинтов анализа):
```json
{
  "total": 1590.5,
  "by_category": [
    {"category": "Groceries", "amount": 1250.5},
    {"category": "Transport", "amount": 340.0}
  ],
  "by_week": [
    {"week": 36, "amount": 1590.5}
  ],
  "top_transactions": [
    {"date": "2026-09-01", "description": "Pyaterochka", "amount": 1250.5, "category": "Groceries"}
  ]
}
```

### `POST /api/analyze` (оставлен для совместимости)
Старый способ — загрузка CSV/Excel файла (`multipart/form-data`, поле
`statement`). Приложение теперь им не пользуется, но эндпоинт работает,
если понадобится в будущем.

Ошибки возвращаются в JSON с соответствующим HTTP-кодом:
- `400` — некорректные данные (пустой список, не хватает полей)
- `422` — не удалось проанализировать (например, неверный формат даты)

## Структура

```
api.py          — Flask-эндпоинты и главная страница
analyzer.py     — анализ трат (категоризация, суммы по категориям/неделям)
categorizer.py  — определение категории по описанию траты
templates/      — HTML-страница
static/         — браузерный код и стили
```

Категоризация трат (`categorizer.py`) распознаёт словацкие названия магазинов,
сервисов и типы расходов. Например, `COOP Jednota` → `Groceries`,
`ZSSK – cestovný lístok` → `Transport`, `Lekáreň Dr. Max` → `Health`.
Регистр, диакритика и пунктуация не мешают распознаванию. Для некоторых
ключевых слов поддерживается одна опечатка. Если подходящей категории
нет, возвращается `Other`.
