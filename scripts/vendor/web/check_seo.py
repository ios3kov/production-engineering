#!/usr/bin/env python3
"""SEO и технические артефакты: robots.txt, sitemap, canonical, meta, OG/Twitter, favicon, manifest,
JSON-LD, hreflang, noindex на служебных страницах, рендеринг (SSR/SSG/SPA), изображения (lazy-load, форматы).

Использование: python3 check_seo.py [корень] [--json]
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import Finding, iter_files, read_text, rel, print_report, parse_args, detect_stack, public_dirs, grep_files  # noqa: E402

HTMLISH = {".html", ".htm", ".tsx", ".jsx", ".vue", ".svelte", ".astro", ".php", ".liquid", ".twig", ".ejs", ".hbs", ".njk", ".erb", ".pug", ".mdx"}


def find_first(root: Path, names: list[str]) -> Path | None:
    for d in public_dirs(root) + [root, root / "app", root / "src/app", root / "src"]:
        for n in names:
            p = d / n
            if p.exists():
                return p
    return None


def main(argv: list[str]) -> int:
    args = parse_args(argv, "SEO / технические артефакты")
    root = Path(args.root).resolve()
    f: list[Finding] = []
    stack = detect_stack(root)

    # --- Рендеринг ---
    if stack["next"] or stack["nuxt"] or stack["astro"] or stack["sveltekit"] or stack["remix"] or stack["gatsby"]:
        mode = "SSR/SSG-фреймворк"
        if stack["next"]:
            cfg = read_text(find_first(root, ["next.config.js", "next.config.mjs", "next.config.ts"]) or Path("/nonexistent"))
            if "output: 'export'" in cfg or 'output: "export"' in cfg:
                mode += " (Next static export)"
            if re.search(r"ssr:\s*false", " ".join(read_text(p) for p in list(iter_files(root, {".tsx", ".jsx"}))[:200])):
                f.append(Finding("warn", "seo.render", "Найдены dynamic(..., { ssr: false }) — эти компоненты не будут в HTML для ботов", "оставлять ssr:false только для некритичного UI"))
        f.append(Finding("ok", "seo.render", f"Рендеринг: {mode}"))
    elif stack["vite_spa"] or stack["cra_spa"]:
        f.append(Finding("fail" if not stack["wordpress"] else "info", "seo.render", "Похоже на чистый SPA (Vite/CRA) без SSR/SSG — контент и мета не видны ботам без JS",
                         "добавить пререндер (vite-plugin-ssr/ prerender), SSG или перейти на Next/Astro/Nuxt; минимум — статический index с мета"))
    elif stack["static_html"] or stack["wordpress"] or stack["django"] or stack["rails"] or stack["laravel"]:
        f.append(Finding("ok", "seo.render", "Серверный рендер / статический HTML"))
    else:
        f.append(Finding("info", "seo.render", "Стек не распознан — подтвердить у пользователя способ рендеринга"))

    # --- robots.txt ---
    robots = find_first(root, ["robots.txt"])
    robots_dyn = list(grep_files(root, r"robots\.(ts|js)|MetadataRoute\.Robots|robots\.txt", exts={".ts", ".js", ".mjs", ".py", ".rb", ".php"}, limit=3))
    if robots:
        txt = read_text(robots)
        rp = rel(root, robots)
        if re.search(r"(?im)^disallow:\s*/\s*$", txt) and re.search(r"(?im)^user-agent:\s*\*", txt):
            f.append(Finding("fail", "seo.robots", "robots.txt запрещает индексацию всего сайта (Disallow: /) — типичный остаток стейджинга", "убрать Disallow: / перед релизом", rp))
        else:
            f.append(Finding("ok", "seo.robots", "robots.txt найден", "", rp))
        if "sitemap:" not in txt.lower():
            f.append(Finding("warn", "seo.robots_sitemap", "В robots.txt нет строки Sitemap:", "добавить `Sitemap: https://<домен>/sitemap.xml`", rp))
    elif robots_dyn:
        f.append(Finding("ok", "seo.robots", f"robots генерируется кодом: {rel(root, robots_dyn[0][0])}", "", rel(root, robots_dyn[0][0])))
    else:
        f.append(Finding("warn", "seo.robots", "robots.txt не найден", "добавить public/robots.txt с User-agent: * / Allow: / / Sitemap: …"))

    # --- sitemap ---
    sm = find_first(root, ["sitemap.xml", "sitemap-index.xml", "sitemap_index.xml"])
    sm_dyn = list(grep_files(root, r"sitemap\.(ts|js|xml\.(ts|js|py|rb))|MetadataRoute\.Sitemap|next-sitemap|@astrojs/sitemap|@nuxtjs/sitemap|sitemap_generator|django\.contrib\.sitemaps", exts={".ts", ".js", ".mjs", ".json", ".py", ".rb", ".php"}, limit=3))
    if sm:
        rp = rel(root, sm)
        try:
            tree = ET.fromstring(read_text(sm))
            locs = [e.text for e in tree.iter() if e.tag.endswith("loc")]
            bad = [l for l in locs if l and (l.startswith("http://") or "localhost" in l or "staging" in l or "vercel.app" in l)]
            f.append(Finding("ok", "seo.sitemap", f"sitemap найден, {len(locs)} URL", "", rp))
            if bad:
                f.append(Finding("fail", "seo.sitemap_urls", f"В sitemap {len(bad)} URL со staging/localhost/http, например {bad[0]}", "генерировать sitemap с production-доменом", rp))
        except ET.ParseError:
            f.append(Finding("fail", "seo.sitemap", "sitemap.xml не парсится как XML", "проверить валидность", rp))
    elif sm_dyn:
        f.append(Finding("ok", "seo.sitemap", f"sitemap генерируется: {rel(root, sm_dyn[0][0])}", "", rel(root, sm_dyn[0][0])))
    else:
        f.append(Finding("warn", "seo.sitemap", "sitemap.xml не найден и генератор не обнаружен", "добавить генерацию sitemap (next-sitemap / app/sitemap.ts / @astrojs/sitemap) и зарегистрировать в Search Console / Вебмастере"))

    # --- Мета, canonical, OG, hreflang, JSON-LD ---
    html_files = [p for p in iter_files(root, HTMLISH) if not any(s in rel(root, p) for s in ("/test", "stories", ".stories."))]
    corpus = {p: read_text(p) for p in html_files[:600]}
    joined = "\n".join(corpus.values())

    def has(rx: str) -> bool:
        return re.search(rx, joined, re.I | re.S) is not None

    checks = [
        ("seo.title", r"<title[\s>]|title:\s*['\"{`]|metadata\s*=|useHead\(|<Head>|<svelte:head>|<Title>|useSeoMeta", "warn", "Не найден <title>/metadata", "задать уникальный title на каждой странице (50–60 симв.)"),
        ("seo.description", r"name=[\"']description[\"']|description:\s*['\"`]", "warn", "Не найден meta description", "добавить description 120–160 симв. на ключевых страницах"),
        ("seo.canonical", r"rel=[\"']canonical[\"']|canonical:|alternates:\s*\{", "warn", "Не найден canonical", "добавить <link rel=canonical> / metadata.alternates.canonical"),
        ("seo.og", r"property=[\"']og:|openGraph:|og:title|useSeoMeta", "warn", "Не найдены Open Graph теги", "добавить og:title/description/image (1200×630)/url/type"),
        ("seo.twitter", r"name=[\"']twitter:|twitter:\s*\{", "info", "Не найдены Twitter Cards", "добавить twitter:card=summary_large_image"),
        ("seo.viewport", r"name=[\"']viewport[\"']|viewport:", "fail", "Не найден meta viewport", "добавить <meta name=viewport content='width=device-width, initial-scale=1'>"),
        ("seo.lang", r"<html[^>]+lang=|lang:\s*['\"]|htmlAttrs", "warn", "Не найден атрибут lang на <html>", "задать <html lang='xx'> — важно для a11y и hreflang"),
        ("seo.jsonld", r"application/ld\+json|@context[\"']?\s*:\s*[\"']https?://schema\.org|schema-dts|next-seo", "warn", "Не найдена структурированная разметка JSON-LD", "добавить Organization/WebSite (+ Product/Article/BreadcrumbList по типу) и проверить в Rich Results Test"),
    ]
    for cid, rx, sev, msg, fix in checks:
        f.append(Finding("ok", cid, "Найдено") if has(rx) else Finding(sev, cid, msg, fix))

    # hreflang — только если есть признаки мультиязычности
    multilang = has(r"i18n|next-intl|react-i18next|vue-i18n|/\[locale\]|/\(locale\)|locales/|lang=[\"'](ru|de|fr|es)")
    if multilang:
        f.append(Finding("ok", "seo.hreflang", "hreflang найден") if has(r"hreflang=|languages:\s*\{|alternates:\s*\{[^}]*languages") else
                 Finding("warn", "seo.hreflang", "Есть признаки мультиязычности, но нет hreflang", "добавить <link rel=alternate hreflang=…> + x-default для каждой языковой версии"))

    # noindex на служебных страницах
    service = [p for p in html_files if re.search(r"(?i)(account|cabinet|dashboard|admin|profile|search|checkout|cart|login|signin|signup|register|reset|thank|success|filter)", rel(root, p))]
    if service:
        noindexed = [p for p in service if re.search(r"noindex|robots:\s*\{[^}]*index:\s*false|index:\s*false", corpus.get(p, ""), re.I)]
        if not noindexed:
            f.append(Finding("warn", "seo.noindex_service", f"{len(service)} служебных страниц (кабинет/поиск/чекаут/логин) без noindex, например {rel(root, service[0])}",
                             "добавить <meta name=robots content=noindex> / robots: { index: false } на кабинет, поиск, фильтры, thank-you", rel(root, service[0])))
        else:
            f.append(Finding("ok", "seo.noindex_service", f"noindex найден на {len(noindexed)} служебных страницах"))

    # --- Favicon, manifest ---
    fav = find_first(root, ["favicon.ico", "favicon.svg", "favicon.png", "icon.png", "icon.svg", "app/icon.png", "app/icon.svg", "app/favicon.ico"])
    f.append(Finding("ok", "seo.favicon", f"Найден {rel(root, fav)}", "", rel(root, fav)) if fav else Finding("warn", "seo.favicon", "favicon не найден", "добавить favicon.ico/svg + apple-touch-icon.png (180×180)"))
    apple = find_first(root, ["apple-touch-icon.png", "apple-icon.png", "app/apple-icon.png"]) or has(r"apple-touch-icon")
    f.append(Finding("ok", "seo.apple_icon", "apple-touch-icon найден") if apple else Finding("info", "seo.apple_icon", "apple-touch-icon не найден", "добавить 180×180 PNG"))
    man = find_first(root, ["manifest.json", "site.webmanifest", "manifest.webmanifest", "app/manifest.ts", "app/manifest.js", "app/manifest.json"])
    f.append(Finding("ok", "seo.manifest", f"Найден {rel(root, man)}", "", rel(root, man)) if man else Finding("info", "seo.manifest", "web manifest не найден", "добавить site.webmanifest (name, icons 192/512, theme_color) если нужен PWA/иконка на экране"))

    # --- Изображения ---
    img_tags = len(re.findall(r"<img\b", joined, re.I))
    lazy = len(re.findall(r"loading=[\"']lazy[\"']", joined, re.I))
    next_img = len(re.findall(r"<(Image|NuxtImg|Picture)\b", joined))
    no_alt = list(re.finditer(r"<img\b(?![^>]*\balt=)[^>]*>", joined, re.I))
    if img_tags:
        if lazy == 0 and next_img == 0:
            f.append(Finding("warn", "perf.lazyload", f"{img_tags} <img> без loading=lazy и без компонента Image", "добавить loading='lazy' для изображений ниже первого экрана; hero — fetchpriority='high'"))
        else:
            f.append(Finding("ok", "perf.lazyload", f"lazy-load: {lazy} img + {next_img} компонентов Image"))
    if no_alt:
        f.append(Finding("warn", "a11y.img_alt", f"{len(no_alt)} <img> без атрибута alt", "добавить alt (пустой alt='' для декоративных)"))
    heavy = []
    for p in iter_files(root, {".png", ".jpg", ".jpeg", ".gif"}):
        try:
            sz = p.stat().st_size
        except OSError:
            continue
        if sz > 500 * 1024 and not any(s in rel(root, p) for s in ("node_modules", "/raw", "/src/assets/original")):
            heavy.append((rel(root, p), sz // 1024))
    if heavy:
        heavy.sort(key=lambda x: -x[1])
        f.append(Finding("warn", "perf.images", f"{len(heavy)} изображений > 500 КБ, самое тяжёлое {heavy[0][0]} ({heavy[0][1]} КБ)",
                         "конвертировать в WebP/AVIF, ресайзить под реальный размер вывода, srcset", heavy[0][0]))
    else:
        f.append(Finding("ok", "perf.images", "Изображений тяжелее 500 КБ не найдено"))

    # --- Редиректы со старых URL ---
    redir = find_first(root, ["_redirects", "public/_redirects", "redirects.json"]) or list(grep_files(root, r"redirects\(\)|redirects:\s*\[|\"redirects\"\s*:|return 301|rewrite \^", exts={".js", ".mjs", ".ts", ".json", ".toml", ".conf", "", ".htaccess"}, limit=1))
    f.append(Finding("ok", "seo.redirects", "Конфиг редиректов найден") if redir else Finding("info", "seo.redirects", "Конфиг редиректов не найден — если сайт заменяет старый, нужен список 301 со старых URL", "собрать карту старых URL → новые и добавить 301"))

    print_report("SEO, рендеринг, изображения", f, args.json)
    return 1 if any(x.status == "fail" for x in f) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
