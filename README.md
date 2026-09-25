# Production Engineering

Разработка по ТЗ и проверка результата: **цель → спецификация → задачи → реализация → аудит → исправления → проверка**.

Основа: [GitHub Spec Kit](https://github.com/github/spec-kit), [web-audit](https://github.com/haraldalder-vibemogger/web-audit) и [vibe-audit](https://github.com/haraldalder-vibemogger/vibe-audit). Это самостоятельный skill и CLI; полный Spec Kit CLI не включён.

## Быстрый запуск

Требуется Python 3.11+. Для локального сканера внешних зависимостей нет.

```bash
git clone https://github.com/ios3kov/production-engineering.git
cd production-engineering
python3 scripts/audit.py /path/to/project --profile web --format markdown
python3 scripts/audit.py /path/to/project --profile code --format json
python3 scripts/audit.py /path/to/project --format sarif --out /fresh/report.sarif
```

По умолчанию — локальные проверки без сети и изменения проекта. Опция `--npm-audit` явно включает отправку метаданных зависимостей в npm registry; пакеты не устанавливаются и не исправляются автоматически.

| Код завершения | Значение |
|---|---|
| 0 | Находок в проверенной области нет |
| 1 | Есть находки, требуется разбор |
| 2 | Проверка неполная или завершилась ошибкой |

**Код 0 не означает готовность к продакшену.** Браузерные сценарии, права доступа, производительность и восстановление данных проверяются отдельно по [критериям качества](references/quality-gates.md).

## Работа с ИИ

Попросите агента: «Прочитай SKILL.md и используй production-engineering для этой задачи». Инструкция описывает анализ, ТЗ, исправления, review, доказательства проверок и передачу контекста. Установка копии в поддерживаемый каталог skills зависит от используемого агента. Репозиторий и установленный личный skill — отдельные копии; обновления между ними не синхронизируются автоматически.

## Что усилено

- Единые статусы и коды завершения для Markdown, JSON и SARIF.
- Ошибки и пропуски не превращаются в успешную проверку.
- Секреты ищутся также в документации, тестах и примерах; значения не попадают в отчёт.
- Ограниченный обход файлов без перехода по символическим ссылкам.
- Python AST-проверка интерполированных SQL-запросов и поддержка современных имён Compose.
- Исправлены ошибки проверки alt и подписей HTML-полей.
- Требования связаны с задачами и доказательствами проверки.

## Проверки

```bash
python3 -m unittest discover -s scripts/tests -v
python3 -m compileall -q scripts
```

30 регрессионных тестов. Автоматический CI описан в `.github/workflows/tests.yml`; статус конкретного запуска смотрите в Actions.

## Документация

- [Инструкция агента](SKILL.md)
- [Спецификация](references/SPEC.md)
- [Рабочий процесс](references/workflow.md)
- [Контракт и ограничения сканера](references/scanner.md)
- [Критерии готовности](references/quality-gates.md)
- [Анализ исходных проектов](references/upstream-review.md)
- [Проверки версии 1.0.0](references/VERIFICATION.md)
- [Зафиксированные версии источников](references/upstream.json)

## Лицензия

MIT. Исходные уведомления об авторских правах сохранены в `references/upstream/*/LICENSE`; см. [NOTICE](NOTICE). Проверки эвристические: инструмент не является пентестом, юридическим заключением или сертификатом безопасности.

## Глубокая проверка — 1.1

Добавлены поиск секретов в истории Git, проверки HTTP/TLS и cookies, импорт отчётов browser/axe, Lighthouse, Semgrep и ZAP, обязательные проверки перед релизом. Пропущенная или ошибочная проверка блокирует выбранную политику.

```bash
python3 scripts/deep_audit.py /absolute/project --history --profile code --format json
python3 scripts/deep_audit.py /absolute/project --url https://example.com/ --policy /policy.json
```

Формат политики, импорт результатов и ограничения: [deep-audit.md](references/deep-audit.md). Сбор browser/axe, Lighthouse и ZAP выполняется внешними инструментами; их живой запуск здесь не проверен. Проверено 50 автоматических тестов, включая реальные локальные Git и HTTP fixtures.
