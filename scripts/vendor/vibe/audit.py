"""Selected offline functions from vibe-audit (MIT); see provenance/license.
Modified: remove unused CLI/network/secret functions; snapshot-only iterator.
"""

import re
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", ".venv", "venv",
             "__pycache__", ".cache", "vendor", "Pods", ".dart_tool", "coverage"}

TEXT_EXT = {".js", ".jsx", ".ts", ".tsx", ".py", ".rb", ".php", ".go", ".java",
            ".kt", ".swift", ".vue", ".svelte", ".html", ".css", ".json", ".yml",
            ".yaml", ".toml", ".env", ".sh", ".sql", ".md", ".txt", ".cfg", ".ini"}

MAX_FILE = 1_000_000

CONFIG_CHECKS = [
    ("cors_star", "warning", "CORS открыт для всех (*)",
     re.compile(r"""(?i)(Access-Control-Allow-Origin["'\s:,=>]+\*|cors\(\s*\{\s*origin\s*:\s*["']\*|CORS_ORIGIN\s*=\s*\*)"""),
     "Ограничь origin списком своих доменов."),
    ("debug_on", "warning", "Debug-режим в коде",
     re.compile(r"(debug\s*=\s*True|app\.run\(.*debug\s*=\s*True|DEBUG\s*=\s*True)"),
     "Выключи debug в проде: он раскрывает стектрейсы и внутренности."),
    ("eval_use", "warning", "eval() на данных",
     re.compile(r"""(?<!['"\w.])eval\s*\("""),
     "eval на пользовательском вводе = исполнение чужого кода. Замени на безопасный парсинг."),
    ("sql_fstring", "warning", "SQL через f-строку/конкатенацию",
     re.compile(r"""(?i)(execute|query)\s*\(\s*f["'].*(SELECT|INSERT|UPDATE|DELETE).*\{"""),
     "Используй параметризованные запросы, иначе SQL-инъекция."),
    ("jwt_none", "critical", "JWT c alg:none",
     re.compile(r"""["']alg["']\s*:\s*["']none["']"""),
     "Никогда не принимай alg:none — подпись обязана проверяться."),
]

def iter_files(root: Path):
    """Read all files already admitted by the bounded snapshot inventory."""
    for p in sorted(root.rglob("*")):
        if p.is_file() and not p.is_symlink():
            yield p, p.read_text(encoding="utf-8")

def _line_is_comment_or_pattern(text, pos):
    """Грубая эвристика: находка внутри комментария или определения regex — не считаем."""
    line_start = text.rfind("\n", 0, pos) + 1
    line_end = text.find("\n", pos)
    line = text[line_start: line_end if line_end != -1 else len(text)]
    stripped = line.lstrip()
    if stripped.startswith(("#", "//", "*", "/*", "<!--")):
        return True
    if "re.compile" in line or "re.search" in line or "re.finditer" in line:
        return True
    return False

def check_config(root, findings):
    for path, text in iter_files(root):
        rel = str(path.relative_to(root))
        if rel.endswith(".md"):
            continue
        for pid, sev, title, rx, fix in CONFIG_CHECKS:
            for m in rx.finditer(text):
                if _line_is_comment_or_pattern(text, m.start()):
                    continue
                findings.append({
                    "id": pid, "severity": sev, "title": title,
                    "where": f"{rel}:{line_of(text, m.start())}",
                    "detail": "", "fix": fix,
                })

def check_platform_flags(root, findings):
    text_all = ""
    for path, text in iter_files(root):
        if path.suffix in {".ts", ".js", ".sql", ".toml", ".json"}:
            text_all += text[:5000]
    if "supabase" in text_all.lower():
        findings.append({
            "id": "supabase_rls", "severity": "info", "title": "Supabase: проверь RLS",
            "where": "проект использует Supabase",
            "detail": "снаружи скрипт это проверить не может",
            "fix": "В каждой таблице: RLS enabled + политики. Быстрый чек: Dashboard → Advisors → Security.",
        })
    if re.search(r"firebase|firestore", text_all, re.I):
        findings.append({
            "id": "firebase_rules", "severity": "info", "title": "Firebase: проверь security rules",
            "where": "проект использует Firebase",
            "detail": "правила по умолчанию из туториалов часто allow read, write: if true",
            "fix": "Прогони firebase emulators + правила без анонимного полного доступа.",
        })

def check_rate_limit_and_ai(root, findings):
    """Блок 1: rate limit на чувствительных роутах + AI cost bomb."""
    joined = ""
    files_text = {}
    for path, text in iter_files(root):
        if path.suffix in {".js", ".jsx", ".ts", ".tsx", ".py"}:
            files_text[str(path.relative_to(root))] = text
            joined += text.lower()

    # rate limit засчитываем только по реальному подключению библиотеки
    # (import/require/from), не по упоминанию в комментарии или TODO.
    rl_import = re.compile(
        r"""(?im)^\s*(?:import\b[^\n]*?\bfrom\s*|import\s+|const\s+\w+\s*=\s*require\(\s*|from\s+)"""
        r"""['"]?(?:express-rate-limit|express-slow-down|@upstash/ratelimit|rate-limiter-flexible|"""
        r"""@nestjs/throttler|slowapi|django_ratelimit|django-ratelimit|flask_limiter|limits|"""
        r"""@fastify/rate-limit|fastify-rate-limit|koa-ratelimit|hono/rate-limit|next-rate-limit|bottleneck)""")
    has_ratelimit = any(rl_import.search(t) for t in files_text.values())
    # чувствительные роуты
    sensitive = re.compile(r"""(?i)['"`/](login|signin|sign-in|signup|sign-up|register|reset-password|forgot|verify|otp)['"`/]""")
    for rel, text in files_text.items():
        m = next((mm for mm in sensitive.finditer(text)
                  if not _line_is_comment_or_pattern(text, mm.start())), None)
        if m and not has_ratelimit:
            findings.append({
                "id": "no_ratelimit_auth", "severity": "warning",
                "title": "Auth-роут без rate limit",
                "where": f"{rel}:{line_of(text, m.start())}",
                "detail": "в проекте не найдено ни одной библиотеки rate-limiting",
                "fix": "Добавь лимит на login/signup/reset (express-rate-limit, slowapi, @upstash/ratelimit). Иначе — брутфорс и спам кодов.",
            })
            break

    # AI cost bomb: вызов LLM API без max_tokens рядом
    ai_call = re.compile(r"""(?i)(openai|anthropic|\.chat\.completions|messages\.create|generateContent)""")
    for rel, text in files_text.items():
        for m in ai_call.finditer(text):
            if _line_is_comment_or_pattern(text, m.start()):
                continue
            window = text[max(0, m.start()-300): m.end()+300]
            if "max_tokens" not in window and "maxtokens" not in window.lower() and "max_output" not in window.lower():
                findings.append({
                    "id": "ai_no_maxtokens", "severity": "warning",
                    "title": "Вызов LLM без лимита max_tokens",
                    "where": f"{rel}:{line_of(text, m.start())}",
                    "detail": "запрос к платному AI-API без ограничения длины ответа",
                    "fix": "Задай max_tokens и лимит длины входа. Без авторизации на этом роуте — любой сожжёт твой баланс.",
                })
                break
    # LLM-эндпоинт, открытый без явной проверки авторизации
    for rel, text in files_text.items():
        if ai_call.search(text) and re.search(r"""(?i)(app\.(post|get)|router\.(post|get)|@app\.(post|get)|export .*handler)""", text):
            if not re.search(r"""(?i)(auth|verifytoken|requireuser|getsession|middleware|authorize|jwt)""", text):
                findings.append({
                    "id": "ai_open_endpoint", "severity": "critical",
                    "title": "AI-эндпоинт без проверки авторизации",
                    "where": rel,
                    "detail": "роут вызывает платный LLM и не видно проверки, кто это",
                    "fix": "Закрой эндпоинт авторизацией + лимитом запросов на пользователя. Это самый частый способ слить бюджет вайбкод-проекта.",
                })
                break

def check_authz(root, findings):
    """Блок 2: права/авторизация — эвристики, помечаем как 'на проверку'."""
    for path, text in iter_files(root):
        rel = str(path.relative_to(root))
        if path.suffix not in {".js", ".jsx", ".ts", ".tsx", ".py"}:
            continue
        # роль из тела запроса
        for m in re.finditer(r"""(?i)(req\.body\.role|body\.role|request\.json.*role|data\.role|params\.role)""", text):
            findings.append({
                "id": "role_from_client", "severity": "warning",
                "title": "Роль берётся из запроса клиента",
                "where": f"{rel}:{line_of(text, m.start())}",
                "detail": "клиент может прислать role: admin",
                "fix": "Роль читай из проверенной сессии/токена на сервере, не из тела запроса.",
            })
        # IDOR: id ресурса из query/params без явной проверки владельца
        if re.search(r"""(?i)(req\.(query|params)\.(id|user_?id|account)|params\.get\(['"]id)""", text):
            if not re.search(r"""(?i)(owner|belongs|user_?id\s*==|\.eq\(.user|where.*user|current_?user)""", text):
                m = re.search(r"""(?i)(req\.(query|params)\.(id|user_?id|account))""", text)
                findings.append({
                    "id": "idor_suspect", "severity": "info",
                    "title": "На проверку: доступ к ресурсу по id из запроса",
                    "where": f"{rel}:{line_of(text, m.start())}" if m else rel,
                    "detail": "не видно проверки, что ресурс принадлежит текущему пользователю (возможен IDOR)",
                    "fix": "Убедись, что запрос фильтруется по владельцу: WHERE user_id = current_user, а не только по присланному id.",
                })
        # JWT без проверки expiry
        m = re.search(r"ignoreExpiration\s*:\s*true", text, re.I)
        if m and not _line_is_comment_or_pattern(text, m.start()):
            findings.append({
                "id": "jwt_no_exp", "severity": "warning", "title": "JWT принимается без проверки срока",
                "where": f"{rel}:{line_of(text, m.start())}",
                "detail": "ignoreExpiration: true",
                "fix": "Не отключай проверку exp — украденный токен будет жить вечно.",
            })

def check_platform_configs(root, findings):
    """Блок 3: реальные конфиг-файлы платформ."""
    # Firebase/Firestore rules
    for rules_name in ["firestore.rules", "storage.rules", "database.rules.json"]:
        rf = root / rules_name
        if rf.exists():
            rtext = rf.read_text(errors="ignore")
            if re.search(r"""allow\s+(read|write|read,\s*write)\s*:\s*if\s+true""", rtext) or re.search(r'"\.(read|write)"\s*:\s*true', rtext):
                findings.append({
                    "id": "firebase_open", "severity": "critical",
                    "title": f"Firebase: открытые правила в {rules_name}",
                    "where": rules_name,
                    "detail": "allow read/write: if true — база открыта всему интернету",
                    "fix": "Закрой правила: доступ только аутентифицированным и только к своим данным (request.auth.uid == resource.data.owner).",
                })
    # docker-compose: дефолтные пароли и порт базы наружу
    seen_compose = set()
    for comp in list(root.glob("docker-compose*.y*ml")) + list(root.glob("**/docker-compose*.y*ml")):
        if comp in seen_compose:
            continue
        seen_compose.add(comp)
        try:
            ct = comp.read_text(errors="ignore")
        except OSError:
            continue
        rel = str(comp.relative_to(root))
        if re.search(r"""(?i)(POSTGRES_PASSWORD|MYSQL_ROOT_PASSWORD|MONGO_INITDB_ROOT_PASSWORD)\s*[:=]\s*(postgres|root|password|admin|123|example)\b""", ct):
            findings.append({
                "id": "default_db_pass", "severity": "critical", "title": "Дефолтный пароль БД в docker-compose",
                "where": rel, "detail": "пароль вида postgres/root/password",
                "fix": "Смени на сгенерированный секрет, подставляй через env, не коммить его.",
            })
        if re.search(r"""(?m)^\s*-\s*["']?(5432|3306|27017|6379):(5432|3306|27017|6379)""", ct):
            findings.append({
                "id": "db_port_exposed", "severity": "warning", "title": "Порт БД проброшен наружу",
                "where": rel, "detail": "база доступна с хоста/интернета",
                "fix": "Не публикуй порт БД наружу; в проде БД доступна только внутренней сети.",
            })


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1
