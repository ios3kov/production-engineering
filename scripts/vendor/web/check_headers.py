#!/usr/bin/env python3
"""Security headers: поиск в конфигах (next.config, vercel.json, netlify.toml, _headers, nginx, Caddyfile,
middleware, helmet) и — при --url — живая проверка ответа, редиректов http→https и www/non-www.

Использование: python3 check_headers.py [корень] [--url https://example.com] [--json]
Живая проверка делает только GET/HEAD-запросы к указанному домену. Никаких платных сервисов.
"""
from __future__ import annotations

import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import Finding, read_text, rel, print_report, parse_args, grep_files, iter_files  # noqa: E402

HEADERS = {
    "strict-transport-security": ("fail", "Strict-Transport-Security: max-age=31536000; includeSubDomains"),
    "content-security-policy": ("warn", "Content-Security-Policy — начать с report-only, затем default-src 'self' + явные источники"),
    "x-content-type-options": ("warn", "X-Content-Type-Options: nosniff"),
    "x-frame-options": ("warn", "X-Frame-Options: DENY (или CSP frame-ancestors)"),
    "referrer-policy": ("warn", "Referrer-Policy: strict-origin-when-cross-origin"),
    "permissions-policy": ("info", "Permissions-Policy: camera=(), microphone=(), geolocation=()"),
    "cross-origin-opener-policy": ("info", "Cross-Origin-Opener-Policy: same-origin"),
}

CONFIG_FILES = [
    "next.config.js", "next.config.mjs", "next.config.ts", "vercel.json", "netlify.toml", "_headers", "public/_headers",
    "static/_headers", "nginx.conf", "nginx/default.conf", "nginx/nginx.conf", "Caddyfile", ".htaccess", "public/.htaccess",
    "middleware.ts", "middleware.js", "src/middleware.ts", "src/middleware.js", "nuxt.config.ts", "nuxt.config.js",
    "astro.config.mjs", "svelte.config.js", "wrangler.toml", "firebase.json", "app.yaml", "apache.conf", "httpd.conf",
    "server.js", "server.ts", "app.js", "app.ts", "src/server.ts", "src/app.ts", "config/initializers/content_security_policy.rb",
    "settings.py", "config/settings.py", "config/settings/base.py", "config/settings/production.py",
]


def scan_config(root: Path) -> tuple[list[Finding], set[str]]:
    findings: list[Finding] = []
    present: set[str] = set()
    where: dict[str, str] = {}
    candidates = [root / c for c in CONFIG_FILES if (root / c).exists()]
    # Django: SECURE_* настройки
    for p in candidates:
        txt = read_text(p)
        low = txt.lower()
        rp = rel(root, p)
        for h in HEADERS:
            if h in low:
                present.add(h); where.setdefault(h, rp)
        if "helmet(" in low or "helmet" in low and "use(" in low:
            for h in ("strict-transport-security", "content-security-policy", "x-content-type-options", "x-frame-options", "referrer-policy"):
                present.add(h); where.setdefault(h, rp + " (helmet)")
        if "secure_hsts_seconds" in low:
            present.add("strict-transport-security"); where.setdefault("strict-transport-security", rp)
        if "secure_content_type_nosniff" in low:
            present.add("x-content-type-options"); where.setdefault("x-content-type-options", rp)
        if "x_frame_options" in low:
            present.add("x-frame-options"); where.setdefault("x-frame-options", rp)
        if "secure_referrer_policy" in low:
            present.add("referrer-policy"); where.setdefault("referrer-policy", rp)
        if "csp_default_src" in low or "content_security_policy" in low:
            present.add("content-security-policy"); where.setdefault("content-security-policy", rp)
    if not candidates:
        findings.append(Finding("info", "headers.config", "Файлы конфигурации сервера/фреймворка не найдены — заголовки, вероятно, задаются на хостинге/CDN; проверить с --url"))
    for h, (sev, fix) in HEADERS.items():
        if h in present:
            findings.append(Finding("ok", f"headers.{h}", f"Задан в {where[h]}", "", where[h]))
        else:
            findings.append(Finding(sev, f"headers.{h}", f"Заголовок {h} не найден в конфигах", fix))
    # unsafe-inline / unsafe-eval в CSP
    for p, ln, line in grep_files(root, r"unsafe-(inline|eval)", exts={".js", ".ts", ".mjs", ".json", ".toml", ".conf", "", ".rb", ".py"}, limit=10):
        findings.append(Finding("warn", "headers.csp_unsafe", "CSP содержит unsafe-inline/unsafe-eval", "перейти на nonce/hash для inline-скриптов", rel(root, p), ln))
    return findings, present


def fetch(url: str, method: str = "GET", follow: bool = False, timeout: int = 15):
    ctx = ssl.create_default_context()

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    handlers = [urllib.request.HTTPSHandler(context=ctx)]
    if not follow:
        handlers.append(NoRedirect())
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "launch-audit/1.0 (+local pre-launch check)"})
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, dict((k.lower(), v) for k, v in r.headers.items()), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, dict((k.lower(), v) for k, v in e.headers.items()), e.geturl()
    except Exception as e:  # noqa: BLE001
        return 0, {"_error": str(e)}, url


def live_check(url: str) -> list[Finding]:
    findings: list[Finding] = []
    u = urllib.parse.urlparse(url if "://" in url else "https://" + url)
    host = u.netloc
    base = f"https://{host}"
    status, hdrs, final = fetch(base, follow=True)
    if status == 0:
        findings.append(Finding("fail", "live.reachable", f"Не удалось получить {base}: {hdrs.get('_error')}", "проверить DNS/TLS/файрвол"))
        return findings
    findings.append(Finding("ok" if status == 200 else "warn", "live.status", f"{base} → HTTP {status} (итоговый URL {final})"))
    for h, (sev, fix) in HEADERS.items():
        if h in hdrs:
            val = hdrs[h]
            extra = ""
            if h == "strict-transport-security" and "max-age" in val:
                m = re.search(r"max-age=(\d+)", val)
                if m and int(m.group(1)) < 15552000:
                    extra = " (max-age < 180 дней — увеличить)"
            findings.append(Finding("ok" if not extra else "warn", f"live.{h}", f"{h}: {val[:120]}{extra}"))
        else:
            findings.append(Finding(sev, f"live.{h}", f"В ответе нет {h}", fix))
    for leak in ("server", "x-powered-by"):
        if leak in hdrs and hdrs[leak]:
            findings.append(Finding("info", f"live.{leak}", f"Заголовок {leak}: {hdrs[leak]} раскрывает стек", f"убрать/обезличить {leak}"))
    # http → https
    s, h, _ = fetch(f"http://{host}", follow=False)
    loc = h.get("location", "")
    if s in (301, 308) and loc.startswith("https://"):
        findings.append(Finding("ok", "live.http_redirect", f"http:// → {loc} ({s})"))
    elif s in (302, 307) and loc.startswith("https://"):
        findings.append(Finding("warn", "live.http_redirect", f"http:// редиректит временным кодом {s}", "использовать 301/308"))
    else:
        findings.append(Finding("fail", "live.http_redirect", f"http:// не редиректит на https (код {s}, location={loc or '—'})", "настроить 301 на https на балансере/хостинге"))
    # www / non-www
    alt = host[4:] if host.startswith("www.") else "www." + host
    s2, h2, _ = fetch(f"https://{alt}", follow=False)
    loc2 = h2.get("location", "")
    if s2 in (301, 308) and host in loc2:
        findings.append(Finding("ok", "live.www_redirect", f"{alt} → {loc2} ({s2})"))
    elif s2 == 0:
        findings.append(Finding("warn", "live.www_redirect", f"{alt} недоступен ({h2.get('_error', '')[:80]})", "добавить DNS-запись и редирект на канонический хост"))
    elif s2 == 200:
        findings.append(Finding("warn", "live.www_redirect", f"{alt} отдаёт 200 без редиректа — дубли для поисковиков", "301 на канонический хост"))
    else:
        findings.append(Finding("info", "live.www_redirect", f"{alt}: код {s2}, location={loc2 or '—'}"))
    # 404
    s4, _, _ = fetch(f"{base}/launch-audit-404-probe-{abs(hash(host)) % 99999}", follow=True)
    findings.append(Finding("ok" if s4 == 404 else "fail", "live.404", f"Несуществующий URL отдаёт HTTP {s4}", "" if s4 == 404 else "возвращать реальный 404, а не 200 (soft 404)"))
    # robots / sitemap
    for path, cid in (("/robots.txt", "live.robots"), ("/sitemap.xml", "live.sitemap")):
        sp, hp, _ = fetch(base + path, follow=True)
        findings.append(Finding("ok" if sp == 200 else "warn", cid, f"{path} → HTTP {sp}", "" if sp == 200 else f"опубликовать {path}"))
    return findings


def main(argv: list[str]) -> int:
    args = parse_args(argv, "Security headers и редиректы")
    root = Path(args.root).resolve()
    findings, _ = scan_config(root)
    if args.url:
        findings += live_check(args.url)
    print_report("Security headers, HTTPS и редиректы", findings, args.json)
    return 1 if any(f.status == "fail" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
