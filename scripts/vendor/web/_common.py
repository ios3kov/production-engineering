"""Общие утилиты для скриптов launch-audit. Только стандартная библиотека Python 3.9+."""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterable, Iterator

# Каталоги, которые никогда не сканируем
SKIP_DIRS = {
    ".git", "node_modules", ".next", ".nuxt", ".svelte-kit", "dist", "build", "out",
    ".output", ".cache", ".turbo", ".vercel", ".netlify", "coverage", "vendor",
    "__pycache__", ".venv", "venv", ".idea", ".vscode", "storybook-static",
    ".parcel-cache", "target", ".gradle", "Pods", ".terraform", "tmp", "temp",
}

TEXT_EXT = {
    ".html", ".htm", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte",
    ".astro", ".php", ".py", ".rb", ".go", ".java", ".kt", ".cs", ".json", ".yml",
    ".yaml", ".toml", ".env", ".md", ".mdx", ".txt", ".xml", ".css", ".scss", ".sass",
    ".less", ".conf", ".ini", ".cfg", ".sh", ".liquid", ".twig", ".hbs", ".ejs", ".pug",
    ".erb", ".njk", ".tpl", ".htaccess", ".webmanifest", "",
}

MAX_FILE_BYTES = 2 * 1024 * 1024  # файлы больше 2 МБ пропускаем (бандлы, карты)


@dataclass
class Finding:
    status: str          # "ok" | "warn" | "fail" | "info"
    check: str           # короткий идентификатор проверки, напр. "seo.robots"
    message: str         # что не так / что найдено
    fix: str = ""        # как починить в одну строку
    file: str = ""       # путь относительно корня проекта
    line: int = 0        # номер строки (0 = не применимо)
    extra: dict = field(default_factory=dict)

    def icon(self) -> str:
        return {"ok": "✅", "warn": "⚠️", "fail": "❌", "info": "ℹ️"}.get(self.status, "•")

    def md(self) -> str:
        loc = f" — `{self.file}`" + (f":{self.line}" if self.line else "") if self.file else ""
        fix = f" → **Фикс:** {self.fix}" if self.fix else ""
        return f"- {self.icon()} **{self.check}**{loc}: {self.message}{fix}"


def iter_files(root: Path, exts: Iterable[str] | None = None, include_hidden: bool = True) -> Iterator[Path]:
    """Рекурсивный обход проекта с пропуском мусорных каталогов."""
    exts = set(exts) if exts else None
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not (d.startswith(".") and d not in {".github", ".well-known"} and not include_hidden)]
        for fn in filenames:
            p = Path(dirpath) / fn
            if exts is not None and p.suffix.lower() not in exts:
                continue
            try:
                if p.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield p


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


def grep_files(root: Path, pattern: str | re.Pattern, exts: Iterable[str] | None = None, flags=re.I, limit: int = 200):
    """Возвращает список (path, line_no, line_text) для совпадений."""
    rx = re.compile(pattern, flags) if isinstance(pattern, str) else pattern
    hits = []
    for p in iter_files(root, exts or TEXT_EXT):
        txt = read_text(p)
        if not txt or not rx.search(txt):
            continue
        for i, line in enumerate(txt.splitlines(), 1):
            if rx.search(line):
                hits.append((p, i, line.strip()[:200]))
                if len(hits) >= limit:
                    return hits
    return hits


def detect_stack(root: Path) -> dict:
    """Грубое определение стека по файлам в корне. Возвращает словарь признаков."""
    names = {p.name for p in root.iterdir()} if root.is_dir() else set()
    pkg = {}
    if "package.json" in names:
        try:
            pkg = json.loads(read_text(root / "package.json") or "{}")
        except json.JSONDecodeError:
            pkg = {}
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    stack = {
        "node": "package.json" in names,
        "next": "next" in deps or "next.config.js" in names or "next.config.mjs" in names or "next.config.ts" in names,
        "nuxt": "nuxt" in deps or "nuxt.config.ts" in names or "nuxt.config.js" in names,
        "astro": "astro" in deps or "astro.config.mjs" in names,
        "sveltekit": "@sveltejs/kit" in deps,
        "remix": "@remix-run/react" in deps or "@remix-run/node" in deps,
        "gatsby": "gatsby" in deps,
        "vite_spa": "vite" in deps and not any(k in deps for k in ("next", "nuxt", "astro", "@sveltejs/kit", "@remix-run/react")),
        "cra_spa": "react-scripts" in deps,
        "django": "manage.py" in names,
        "rails": "Gemfile" in names and (root / "config" / "routes.rb").exists(),
        "laravel": "artisan" in names,
        "wordpress": "wp-config.php" in names or (root / "wp-content").exists(),
        "static_html": any(n.endswith(".html") for n in names) and "package.json" not in names,
        "vercel": "vercel.json" in names,
        "netlify": "netlify.toml" in names or (root / "public" / "_headers").exists() or (root / "_headers").exists(),
        "docker": "Dockerfile" in names or "docker-compose.yml" in names,
        "nginx": any(n.startswith("nginx") for n in names) or (root / "nginx").exists(),
        "cloudflare": "wrangler.toml" in names or "wrangler.json" in names,
        "deps": sorted(deps.keys()),
    }
    return stack


def public_dirs(root: Path) -> list[Path]:
    """Каталоги, откуда обычно раздаётся статика."""
    cands = ["public", "static", "www", "dist", "build", "out", "app/public", "web/public", "priv/static", "src/public"]
    found = [root / c for c in cands if (root / c).is_dir()]
    return found or [root]


def print_report(title: str, findings: list[Finding], as_json: bool = False) -> None:
    if as_json:
        print(json.dumps({"title": title, "findings": [asdict(f) for f in findings]}, ensure_ascii=False, indent=2))
        return
    fails = sum(1 for f in findings if f.status == "fail")
    warns = sum(1 for f in findings if f.status == "warn")
    print(f"## {title}\n")
    print(f"❌ {fails}  ⚠️ {warns}  ✅ {sum(1 for f in findings if f.status == 'ok')}\n")
    for f in findings:
        print(f.md())
    print()


def parse_args(argv: list[str], desc: str):
    import argparse
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument("root", nargs="?", default=".", help="корень проекта (по умолчанию — текущий каталог)")
    ap.add_argument("--json", action="store_true", help="вывод в JSON вместо markdown")
    ap.add_argument("--url", default="", help="URL запущенного сайта для живых проверок (опционально)")
    ap.add_argument("--jurisdictions", default="", help="через запятую: eu,us,ru")
    return ap.parse_args(argv)
