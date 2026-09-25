#!/usr/bin/env python3
"""Доступность по коду: alt, aria/label у полей, семантика (landmarks, h1), focus-стили, контраст
в CSS-токенах, <video> без <track>, autoplay, target=_blank без rel.

Использование: python3 check_a11y.py [корень] [--json]
Это статическая эвристика — не замена полному WCAG-аудиту (axe/Lighthouse + ручная проверка).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import Finding, iter_files, read_text, rel, print_report, parse_args  # noqa: E402

HTMLISH = {".html", ".htm", ".tsx", ".jsx", ".vue", ".svelte", ".astro", ".php", ".liquid", ".twig", ".ejs", ".hbs", ".njk", ".erb", ".mdx"}
CSSISH = {".css", ".scss", ".sass", ".less"}


def hex_to_rgb(h: str):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return None
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def luminance(rgb):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def main(argv: list[str]) -> int:
    args = parse_args(argv, "Доступность по коду")
    root = Path(args.root).resolve()
    f: list[Finding] = []
    html = {rel(root, p): read_text(p) for p in iter_files(root, HTMLISH) if not re.search(r"(?i)(stories|\.test\.|__tests__|node_modules)", str(p))}
    css = {rel(root, p): read_text(p) for p in iter_files(root, CSSISH)}
    joined = "\n".join(html.values())
    css_joined = "\n".join(css.values())

    def first(rx: str, corpus: dict[str, str]):
        r = re.compile(rx, re.I | re.S)
        for rp, t in corpus.items():
            m = r.search(t)
            if m:
                return rp, t.count("\n", 0, m.start()) + 1
        return "", 0

    # Modified: parse static HTML; keep framework markup signals heuristic.
    from static_a11y import Markup
    for rp, text in html.items():
        if Path(rp).suffix.lower() in {".html", ".htm"}:
            parsed = Markup()
            parsed.feed(text)
            parsed.close()
            for line in parsed.images:
                f.append(Finding("warn", "a11y.alt", "Image lacks alt attribute", "Add appropriate alt text", rp, line))
            for line in parsed.missing_labels():
                f.append(Finding("warn", "a11y.labels", "Control lacks a static accessible name", "Associate a label or accessible name", rp, line))
        else:
            for match in re.finditer(r"<img\b(?![^>]*\balt\s*=)[^>]*>", text, re.I):
                f.append(Finding("warn", "a11y.alt", "Template image may lack alt", "Verify rendered accessible name", rp, text.count("\n", 0, match.start()) + 1))
            if re.search(r"<(input|select|textarea)\b", text, re.I):
                f.append(Finding("info", "a11y.labels_runtime", "Verify rendered template labels", "Run browser accessibility checks", rp))

    # Кнопки-иконки без текста
    icon_btn = first(r"<button\b(?![^>]*(aria-label|aria-labelledby|title=))[^>]*>\s*<(svg|img|i|span class=[\"'][^\"']*icon)", html)
    f.append(Finding("warn", "a11y.icon_buttons", "Есть кнопки только с иконкой без aria-label", "добавить aria-label / визуально скрытый текст", *icon_btn) if icon_btn[0] else Finding("ok", "a11y.icon_buttons", "Кнопки-иконки без aria-label не найдены"))

    # Landmarks и h1
    landmarks = sum(1 for rx in (r"<main\b", r"<nav\b", r"<header\b", r"<footer\b", r"role=[\"']main[\"']") if re.search(rx, joined, re.I))
    f.append(Finding("ok" if landmarks >= 2 else "warn", "a11y.landmarks", f"Семантические landmarks: {landmarks}/4 типов найдено", "" if landmarks >= 2 else "использовать <main>, <nav>, <header>, <footer>"))
    if not re.search(r"<h1\b", joined, re.I):
        f.append(Finding("warn", "a11y.h1", "Не найден <h1>", "один h1 на страницу"))
    skip = re.search(r"skip[- ]?(to|link|nav)|#main-content|#content[\"']", joined, re.I)
    f.append(Finding("ok", "a11y.skip_link", "Skip-link найден") if skip else Finding("info", "a11y.skip_link", "Skip-to-content ссылка не найдена", "добавить первой ссылкой в <body>"))

    # Focus
    if re.search(r"outline\s*:\s*(none|0)\b", css_joined, re.I) and not re.search(r":focus-visible|focus:ring|focus-visible:", css_joined + joined, re.I):
        f.append(Finding("fail", "a11y.focus", "В CSS сброшен outline без замены :focus-visible — клавиатурная навигация невидима", "заменить на :focus-visible { outline: 2px solid … }", *first(r"outline\s*:\s*(none|0)\b", css)))
    else:
        f.append(Finding("ok", "a11y.focus", "Явного удаления фокуса без замены не найдено"))

    # Контраст по CSS-переменным (грубо): ищем пары --text/--fg и --bg/--background
    vars_ = dict(re.findall(r"--([\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\b", css_joined))
    text_keys = [k for k in vars_ if re.search(r"(text|fg|foreground|body|ink|muted)", k, re.I)]
    bg_keys = [k for k in vars_ if re.search(r"(bg|background|surface|paper|canvas)", k, re.I)]
    low = []
    for tk in text_keys[:20]:
        for bk in bg_keys[:20]:
            a, b = hex_to_rgb(vars_[tk]), hex_to_rgb(vars_[bk])
            if a and b:
                c = contrast(a, b)
                if c < 4.5:
                    low.append((tk, bk, round(c, 2)))
    if low:
        low.sort(key=lambda x: x[2])
        f.append(Finding("warn", "a11y.contrast", f"Низкий контраст токенов: --{low[0][0]} на --{low[0][1]} = {low[0][2]}:1 (нужно ≥ 4.5:1 для текста{f'; ещё {len(low) - 1} пар' if len(low) > 1 else ''})", "проверить палитру; для muted-текста ≥ 4.5:1, крупный текст ≥ 3:1"))
    elif vars_:
        f.append(Finding("ok", "a11y.contrast", f"CSS-токены ({len(vars_)}) — очевидно низкоконтрастных пар text/bg не найдено (проверить реальные комбинации в Lighthouse)"))
    else:
        f.append(Finding("info", "a11y.contrast", "CSS-переменные цветов не найдены — проверить контраст в Lighthouse/axe"))

    # Медиа
    vid = first(r"<video\b(?![^>]*>[\s\S]{0,400}<track)[^>]*>", html)
    if vid[0]:
        f.append(Finding("warn", "a11y.captions", "<video> без <track> (субтитры)", "добавить <track kind=captions>", *vid))
    ap = first(r"<(video|audio)\b[^>]*\bautoplay\b(?![^>]*\bmuted\b)", html)
    if ap[0]:
        f.append(Finding("warn", "a11y.autoplay", "autoplay без muted", "добавить muted или убрать autoplay", *ap))

    # target=_blank без rel
    tb = first(r"<a\b[^>]*target=[\"']_blank[\"'](?![^>]*rel=)[^>]*>", html)
    if tb[0]:
        f.append(Finding("info", "a11y.blank", "target=_blank без rel=noopener", "добавить rel='noopener noreferrer'", *tb))

    # lang
    if not re.search(r"<html[^>]+lang=|lang:\s*['\"]|htmlAttrs", joined, re.I):
        f.append(Finding("warn", "a11y.lang", "Нет lang на <html>", "задать <html lang='xx'>"))

    # prefers-reduced-motion
    if re.search(r"@keyframes|animation:|transition:", css_joined) and "prefers-reduced-motion" not in css_joined:
        f.append(Finding("info", "a11y.reduced_motion", "Есть анимации, но нет @media (prefers-reduced-motion)", "отключать декоративные анимации для reduced-motion"))

    print_report("Доступность (статическая эвристика)", f, args.json)
    return 1 if any(x.status == "fail" for x in f) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
