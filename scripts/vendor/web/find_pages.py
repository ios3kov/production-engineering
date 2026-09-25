#!/usr/bin/env python3
"""Поиск обязательных страниц и текстов: политика, cookies, оферта, контакты, Impressum,
accessibility statement, Do Not Sell, реквизиты, возрастная маркировка, ERID.

Использование: python3 find_pages.py [корень] [--jurisdictions eu,us,ru] [--json]
Ищет по маршрутам (pages/, app/, routes), именам файлов и текстам в HTML/шаблонах/компонентах.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import Finding, iter_files, read_text, rel, print_report, parse_args, TEXT_EXT  # noqa: E402

# Каждая проверка: (id, юрисдикции или "*", критичность, паттерны путей/файлов, паттерны текста, сообщение, фикс)
REQUIRED = [
    ("pages.privacy", "*", "fail",
     r"(privacy|datenschutz|politika|policy|confidential|konfidencial|личн|персональн)",
     r"(privacy policy|политика конфиденциальности|политика обработки персональных данных|datenschutzerklärung|datenschutz)",
     "Страница политики конфиденциальности не найдена",
     "создать /privacy (RU: на русском, по ст. 18.1 152-ФЗ; EU: Art. 13/14 GDPR; US: CalOPPA) и дать ссылку в футере"),
    ("pages.cookies", "eu,ru", "warn",
     r"cookie",
     r"(cookie policy|политика cookie|политика использования cookie|cookie-richtlinie|файл(ы|ов) cookie)",
     "Отдельная политика cookies не найдена (допустимо как раздел privacy policy, если он есть)",
     "добавить раздел/страницу с перечнем cookies, целями, сроками и способом отзыва согласия"),
    ("pages.terms", "*", "warn",
     r"(terms|tos|agreement|oferta|offer|agb|nutzungsbedingungen|соглашен|оферт|услови)",
     r"(terms of (service|use)|user agreement|пользовательское соглашение|публичная оферта|договор оферты|allgemeine geschäftsbedingungen|\bAGB\b)",
     "Пользовательское соглашение / оферта не найдены",
     "создать /terms (для e-commerce в РФ — оферта с реквизитами продавца по ПП 2463; в ЕС — CRD-информация)"),
    ("pages.contacts", "*", "warn",
     r"(contact|kontakt|контакт|about|impressum|imprint)",
     r"(contact us|контакты|kontakt|impressum|imprint|<address)",
     "Страница контактов не найдена",
     "добавить /contacts с email, юр. названием и адресом"),
    ("pages.impressum", "eu", "fail",
     r"(impressum|imprint|anbieterkennzeichnung)",
     r"(impressum|anbieterkennzeichnung|angaben gemäß § ?5 (ddg|tmg))",
     "Impressum не найден (обязателен при немецкой/австрийской аудитории — §5 DDG / §5 ECG)",
     "создать /impressum: название, адрес, email, представитель, регистр и номер, УСт-ID, для СМИ — ответственный по §18 MStV"),
    ("pages.accessibility", "eu,us", "warn",
     r"(accessib|barrierefrei|a11y|доступност)",
     r"(accessibility statement|erklärung zur barrierefreiheit|заявление о доступности|accessibility)",
     "Accessibility statement не найден (EAA/BFSG требует для охваченных услуг; в США снижает риск иска)",
     "создать /accessibility: стандарт (WCAG 2.1 AA / EN 301 549), известные ограничения, контакт для обратной связи"),
    ("pages.do_not_sell", "us", "warn",
     r"(do-not-sell|donotsell|privacy-choices|opt-out)",
     r"(do not sell or share my personal information|your privacy choices|do not sell my personal information)",
     "Ссылка «Do Not Sell or Share My Personal Information» / «Your Privacy Choices» не найдена (CCPA, если применимо)",
     "добавить ссылку в футер + обработчик Sec-GPC / navigator.globalPrivacyControl"),
    ("pages.requisites_ru", "ru", "warn",
     None,
     r"(\bИНН\b|\bОГРН(ИП)?\b|\bКПП\b)",
     "Реквизиты (ИНН/ОГРН) не найдены — обязательны для продавца/исполнителя (ЗоЗПП, ПП 2463)",
     "добавить в футер/контакты: наименование, ОГРН/ОГРНИП, ИНН, адрес"),
    ("pages.pd_consent_ru", "ru", "fail",
     r"(consent|soglas|согласи)",
     r"(согласие на обработку персональных данных|даю согласие на обработку)",
     "Текст согласия на обработку ПДн не найден (ст. 9 152-ФЗ; с 01.09.2025 — отдельный документ)",
     "создать отдельную страницу /consent и ссылаться на неё из каждой формы с незаполненным чекбоксом"),
    ("pages.age_mark_ru", "ru", "info",
     None,
     r"(\b(0|6|12|16|18)\+|информационн(ая|ой) продукци)",
     "Знак возрастной категории не найден (436-ФЗ — обязателен для СМИ и информационной продукции; для обычного сайта — уточнить у юриста)",
     "если применимо — добавить знак категории на видное место"),
    ("pages.erid_ru", "ru", "info",
     None,
     r"(\berid\b|erid=|ОРД|маркировк\w+ рекламы)",
     "Маркировка рекламы (erid) не найдена — норма, если на сайте нет рекламных блоков/интеграций",
     "если размещаете рекламу — регистрировать креативы в ОРД, добавить пометку «Реклама» + erid"),
    ("pages.withdrawal_eu", "eu", "warn",
     r"(withdraw|widerruf|cancel|refund|return)",
     r"(right of withdrawal|widerrufsbelehrung|widerrufsrecht|return policy|refund policy|14 days)",
     "Информация о праве отказа от договора (14 дней, CRD) не найдена — обязательна при B2C-продажах в ЕС",
     "добавить Widerrufsbelehrung / withdrawal info + кнопку отказа для онлайн-договоров (Art. 11a CRD, с 19.06.2026)"),
    ("pages.404", "*", "warn",
     r"(404|not-found|not_found|notfound)",
     r"(404|page not found|страница не найдена|seite nicht gefunden)",
     "Кастомная страница 404 не найдена",
     "добавить 404.html / not-found.tsx / pages/404 с навигацией и корректным HTTP 404"),
]

ROUTE_DIRS = ("pages", "app", "src/pages", "src/app", "src/routes", "routes", "content", "src/content", "views", "templates", "resources/views", "public", "static", "docs")


def main(argv: list[str]) -> int:
    args = parse_args(argv, "Поиск обязательных страниц")
    root = Path(args.root).resolve()
    juris = {j.strip().lower() for j in args.jurisdictions.split(",") if j.strip()} or {"eu", "us", "ru"}
    findings: list[Finding] = []

    # Собираем список путей и содержимого один раз
    files = list(iter_files(root, TEXT_EXT))
    paths_lower = [(p, rel(root, p).lower()) for p in files]
    contents: dict[Path, str] = {}

    def text_of(p: Path) -> str:
        if p not in contents:
            contents[p] = read_text(p)
        return contents[p]

    for cid, jur, sev, path_rx, text_rx, msg, fix in REQUIRED:
        if jur != "*" and not (set(jur.split(",")) & juris):
            continue
        hit_file = ""
        hit_line = 0
        # 1) по пути маршрута/файла
        if path_rx:
            prx = re.compile(path_rx, re.I)
            for p, rp in paths_lower:
                if any(rp.startswith(d + "/") or rp.startswith(d) for d in ROUTE_DIRS) and prx.search(Path(rp).stem):
                    hit_file = rel(root, p)
                    break
        # 2) по тексту (в HTML/шаблонах/компонентах/markdown)
        if not hit_file and text_rx:
            trx = re.compile(text_rx, re.I)
            for p, rp in paths_lower:
                if p.suffix.lower() in (".json", ".lock", ".yml", ".yaml", ".toml"):
                    continue
                t = text_of(p)
                m = trx.search(t)
                if m:
                    hit_file = rel(root, p)
                    hit_line = t.count("\n", 0, m.start()) + 1
                    break
        if hit_file:
            findings.append(Finding("ok", cid, f"Найдено: {hit_file}", "", hit_file, hit_line))
        else:
            findings.append(Finding(sev, cid, msg, fix))

    # Ссылки на политику в футере/навигации — грубая проверка
    footer_hit = any(re.search(r"(?i)<footer[\s\S]{0,4000}(privacy|политик|datenschutz)", text_of(p)) for p, _ in paths_lower if p.suffix.lower() in (".html", ".tsx", ".jsx", ".vue", ".svelte", ".astro", ".php", ".liquid", ".twig", ".ejs", ".hbs", ".njk"))
    findings.append(Finding("ok" if footer_hit else "warn", "pages.footer_links",
                            "В футере есть ссылка на политику" if footer_hit else "Не найдена ссылка на политику конфиденциальности в <footer>",
                            "" if footer_hit else "добавить ссылки Privacy / Terms / Cookies / Contacts в футер на всех страницах"))

    print_report("Обязательные страницы и тексты", findings, args.json)
    return 1 if any(f.status == "fail" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
