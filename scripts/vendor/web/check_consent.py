#!/usr/bin/env python3
"""Аналитика, пиксели и согласие: что подключено, есть ли CMP/cookie-баннер, грузятся ли трекеры до согласия,
есть ли Google Consent Mode, GPC-обработка, чекбоксы согласия в формах, капча/rate-limit, иностранная авторизация.

Использование: python3 check_consent.py [корень] [--jurisdictions eu,us,ru] [--json]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import Finding, iter_files, read_text, rel, print_report, parse_args, TEXT_EXT  # noqa: E402

TRACKERS = [
    ("Google Analytics / gtag", r"googletagmanager\.com/gtag|google-analytics\.com|gtag\(|G-[A-Z0-9]{8,}|UA-\d{4,}-\d"),
    ("Google Tag Manager", r"googletagmanager\.com/gtm\.js|GTM-[A-Z0-9]{5,}|@next/third-parties/google"),
    ("Яндекс.Метрика", r"mc\.yandex\.ru|ym\(\d+|yandex_metrika|yandexmetrika"),
    ("Meta Pixel", r"connect\.facebook\.net|fbq\(|facebook\.com/tr\?"),
    ("TikTok Pixel", r"analytics\.tiktok\.com|ttq\.load"),
    ("LinkedIn Insight", r"snap\.licdn\.com|_linkedin_partner_id"),
    ("Hotjar", r"static\.hotjar\.com|hj\("),
    ("Microsoft Clarity", r"clarity\.ms|clarity\("),
    ("FullStory", r"fullstory\.com|FS\.identify"),
    ("Mixpanel", r"mixpanel"),
    ("Amplitude", r"amplitude\.com|amplitude\.init"),
    ("Segment", r"cdn\.segment\.com|analytics\.load\("),
    ("PostHog", r"posthog"),
    ("Plausible", r"plausible\.io"),
    ("Umami", r"umami"),
    ("Intercom / чат-виджет", r"widget\.intercom\.io|crisp\.chat|tawk\.to|jivosite|jivo\.ru|carrotquest|livechatinc"),
    ("Sentry", r"sentry\.io|@sentry/"),
    ("VK Pixel / Top.Mail.Ru", r"top-fwz1\.mail\.ru|vk\.com/js/api/openapi|_tmr\.push|VK\.Retargeting"),
    ("Google Ads / DoubleClick", r"googleadservices|doubleclick\.net|AW-\d{6,}"),
    ("Criteo / рекламные сети", r"criteo|adroll|taboola|outbrain"),
]

CMP = [
    ("Cookiebot", r"cookiebot|CookieConsent\.consent"),
    ("OneTrust", r"onetrust|OptanonWrapper|otSDKStub"),
    ("Usercentrics", r"usercentrics"),
    ("CookieYes", r"cookieyes|cky-consent"),
    ("Klaro", r"klaro"),
    ("Osano", r"osano"),
    ("iubenda", r"iubenda"),
    ("Termly", r"termly"),
    ("Didomi", r"didomi"),
    ("Axeptio", r"axeptio"),
    ("tarteaucitron", r"tarteaucitron"),
    ("vanilla-cookieconsent", r"vanilla-cookieconsent|CookieConsent\.run"),
    ("react-cookie-consent", r"react-cookie-consent"),
    ("Кастомный баннер (по ключевым словам)", r"cookie[-_ ]?(banner|consent|notice|bar)|consent[-_ ]?(banner|modal|dialog)"),
]

FOREIGN_AUTH = r"accounts\.google\.com|appleid\.apple\.com|next-auth/providers/(google|apple|github|facebook|twitter|discord)|signInWithGoogle|GoogleAuthProvider|passport-(google|facebook|github|apple)|oauth2\.googleapis|graph\.facebook\.com/oauth|github\.com/login/oauth|login\.microsoftonline"
RU_AUTH = r"oauth\.yandex|login\.yandex|oauth\.vk\.com|id\.vk\.com|esia\.gosuslugi|oauth\.mail\.ru|sber(id|business)|tinkoff.*id|t-id"


def main(argv: list[str]) -> int:
    args = parse_args(argv, "Аналитика, пиксели, согласие, формы")
    root = Path(args.root).resolve()
    juris = {j.strip().lower() for j in args.jurisdictions.split(",") if j.strip()} or {"eu", "us", "ru"}
    f: list[Finding] = []

    files = [p for p in iter_files(root, TEXT_EXT) if p.suffix.lower() not in (".lock", ".md")]
    corpus: dict[str, str] = {}
    for p in files:
        rp = rel(root, p)
        if p.name.endswith(("-lock.json", ".lock")) or "package-lock" in rp:
            continue
        corpus[rp] = read_text(p)
    joined = "\n".join(corpus.values())

    def where(rx: str) -> tuple[str, int]:
        r = re.compile(rx, re.I)
        for rp, t in corpus.items():
            m = r.search(t)
            if m:
                return rp, t.count("\n", 0, m.start()) + 1
        return "", 0

    # --- Трекеры ---
    found_trackers = []
    for name, rx in TRACKERS:
        rp, ln = where(rx)
        if rp:
            found_trackers.append((name, rp, ln))
    # --- CMP ---
    cmp_found = [(n, *where(rx)) for n, rx in CMP if where(rx)[0]]
    consent_mode = where(r"gtag\(\s*['\"]consent['\"]\s*,\s*['\"](default|update)['\"]|consentMode|ad_storage|analytics_storage")
    gated = where(r"type=[\"']text/plain[\"'][^>]*data-(cookieconsent|category|cookiecategory|usercentrics|consent)|data-cookieconsent=|data-usercentrics=|data-category=|klaro|consent\.(analytics|marketing)|hasConsent|consentGiven|cookieConsent\s*(===|==|&&)|if\s*\(\s*consent")

    if not found_trackers:
        f.append(Finding("ok", "consent.trackers", "Сторонние трекеры/пиксели не обнаружены (проверьте GTM-контейнер вручную — теги внутри него не видны в коде)"))
    else:
        names = ", ".join(n for n, _, _ in found_trackers)
        f.append(Finding("info", "consent.trackers", f"Подключено: {names}", "", found_trackers[0][1], found_trackers[0][2]))
        for name, rp, ln in found_trackers:
            f.append(Finding("info", "consent.tracker", name, "", rp, ln))
        needs_consent = bool({"eu", "ru"} & juris)
        if cmp_found:
            f.append(Finding("ok", "consent.cmp", f"CMP/баннер: {cmp_found[0][0]}", "", cmp_found[0][1], cmp_found[0][2]))
            if gated[0]:
                f.append(Finding("ok", "consent.gating", "Найдена привязка скриптов к согласию (type=text/plain + data-category / условная загрузка)", "", *gated))
            else:
                f.append(Finding("fail" if needs_consent else "warn", "consent.gating",
                                 "Баннер есть, но не найдено механизма блокировки трекеров до согласия — скрипты, вероятно, грузятся сразу",
                                 "переключить теги в type='text/plain' с data-category или грузить их только после события согласия; в GTM — триггеры по consent"))
        else:
            f.append(Finding("fail" if needs_consent else "warn", "consent.cmp",
                             "Есть трекеры, но не найден cookie-баннер/CMP" + (" (ЕС: ePrivacy Art. 5(3); РФ: согласие на cookies/метрику)" if needs_consent else " (США: баннер не обязателен, но нужен opt-out для sale/share)"),
                             "подключить CMP (Cookiebot/Usercentrics/Klaro/кастом) с Reject-кнопкой той же заметности, что Accept; трекеры — только после согласия"))
        if any(n.startswith("Google") for n, _, _ in found_trackers) and "eu" in juris:
            f.append(Finding("ok", "consent.consent_mode", "Google Consent Mode найден", "", *consent_mode) if consent_mode[0] else
                     Finding("warn", "consent.consent_mode", "Google-теги есть, но Consent Mode v2 не найден (требование Google для EEA с марта 2024)",
                             "добавить gtag('consent','default',{ad_storage:'denied',analytics_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'}) до загрузки gtag и 'update' после согласия"))
        if "ru" in juris:
            foreign = [n for n, _, _ in found_trackers if n.startswith(("Google", "Meta", "TikTok", "LinkedIn", "Hotjar", "Microsoft", "FullStory", "Mixpanel", "Amplitude", "Segment", "PostHog", "Sentry", "Intercom"))]
            if foreign:
                f.append(Finding("warn", "consent.ru_transborder", f"Иностранные сервисы, получающие данные пользователей: {', '.join(foreign)} — трансграничная передача (ст. 12 152-ФЗ) и локализация (ст. 18 ч. 5)",
                                 "оценить, какие ПДн уходят; при необходимости — уведомление РКН о трансграничной передаче, отдельное согласие; уточнить у юриста"))
            if any("Meta" in n or "TikTok" in n for n, _, _ in found_trackers):
                f.append(Finding("warn", "consent.ru_banned_platforms", "Meta Pixel / TikTok: реклама на ресурсах запрещённых/нежелательных организаций запрещена с 01.09.2025 (ч. 10.7 ст. 5 38-ФЗ) — уточнить у юриста применимость к пикселю", "не размещать рекламу на этих площадках для аудитории РФ"))
    # --- Do Not Sell / GPC (US) ---
    if "us" in juris:
        gpc = where(r"globalPrivacyControl|Sec-GPC")
        dns = where(r"(?i)do not sell|your privacy choices")
        f.append(Finding("ok", "consent.gpc", "Обработка Global Privacy Control найдена", "", *gpc) if gpc[0] else
                 Finding("warn", "consent.gpc", "Не найдена обработка сигнала GPC (обязательна в CA, CO, CT, TX и ещё ряде штатов при sale/share)", "читать navigator.globalPrivacyControl / заголовок Sec-GPC и отключать sale/share"))
        f.append(Finding("ok", "consent.do_not_sell", "Ссылка Do Not Sell / Privacy Choices найдена", "", *dns) if dns[0] else
                 Finding("info", "consent.do_not_sell", "Ссылка «Do Not Sell or Share» не найдена — нужна, если подпадаете под CCPA и передаёте данные рекламным сетям", "добавить в футер"))

    # --- Формы: согласие, капча, rate limit ---
    forms = [(rp, t) for rp, t in corpus.items() if re.search(r"<form\b|<Form\b|useForm\(|onSubmit=", t) and not re.search(r"(?i)(test|stories|node_modules)", rp)]
    if forms:
        with_consent = [rp for rp, t in forms if re.search(r"(?i)(consent|соглас|agree|privacy|политик|datenschutz|accept.*terms)", t)]
        prechecked = [(rp, t) for rp, t in forms if re.search(r"(?i)type=[\"']checkbox[\"'][^>]*\b(checked|defaultChecked)\b[^>]*(consent|соглас|agree|privacy|newsletter|рассылк)|(consent|соглас|agree)[^>]*type=[\"']checkbox[\"'][^>]*\b(checked|defaultChecked)\b", t)]
        f.append(Finding("ok" if with_consent else "warn", "forms.consent",
                         f"{len(with_consent)}/{len(forms)} файлов с формами содержат текст согласия/ссылку на политику" if with_consent else f"{len(forms)} файлов с формами — ни в одном нет текста согласия/ссылки на политику",
                         "" if with_consent else "добавить под каждой формой: незаполненный чекбокс + ссылка на политику (РФ — отдельное согласие; ЕС — Art. 7 GDPR)", forms[0][0]))
        for rp, t in prechecked[:5]:
            m = re.search(r"(?i)checked", t)
            f.append(Finding("fail", "forms.prechecked", "Чекбокс согласия/рассылки отмечен по умолчанию — недействительное согласие (GDPR Art. 7, CJEU Planet49; РФ ст. 9 152-ФЗ)", "убрать checked/defaultChecked", rp, t.count("\n", 0, m.start()) + 1 if m else 0))
        captcha = where(r"recaptcha|hcaptcha|turnstile|smartcaptcha|captcha\.yandex|friendlycaptcha|altcha")
        f.append(Finding("ok", "forms.captcha", "Капча найдена", "", *captcha) if captcha[0] else Finding("warn", "forms.captcha", "Капча/антиспам не найдены", "Cloudflare Turnstile / hCaptcha / Yandex SmartCaptcha (РФ) или honeypot + rate limit"))
        rl = where(r"rate[-_ ]?limit|express-rate-limit|@upstash/ratelimit|ratelimit|throttle|limit_req|slowapi|django-ratelimit|rack-attack")
        f.append(Finding("ok", "forms.rate_limit", "Rate limiting найден", "", *rl) if rl[0] else Finding("warn", "forms.rate_limit", "Rate limiting для форм/API не найден", "добавить лимит на IP/сессию для POST-эндпоинтов (middleware, nginx limit_req, Upstash)"))
        honeypot = where(r"honeypot|hp_field|bot-field|_gotcha")
        if not captcha[0] and honeypot[0]:
            f.append(Finding("info", "forms.honeypot", "Есть honeypot-поле — минимальная защита без капчи", "", *honeypot))
    else:
        f.append(Finding("info", "forms.consent", "Формы не найдены — проверки согласия/капчи не применимы"))

    # --- Авторизация (РФ) ---
    if "ru" in juris:
        fa = where(FOREIGN_AUTH)
        ra = where(RU_AUTH)
        if fa[0]:
            f.append(Finding("warn", "auth.ru_foreign", "Найдена авторизация через иностранный сервис (Google/Apple/GitHub/…) — для ресурсов из ч. 10 ст. 8 149-ФЗ разрешены только российские способы; штраф ст. 13.55 КоАП",
                             "добавить вход по номеру телефона РФ / Госуслуги / VK ID / Яндекс ID; иностранные — убрать или уточнить у юриста применимость", *fa))
        if ra[0]:
            f.append(Finding("ok", "auth.ru_domestic", "Есть российский способ авторизации", "", *ra))

    # --- Иностранные мессенджеры в контактах (РФ) ---
    if "ru" in juris:
        msg = where(r"wa\.me/|api\.whatsapp\.com|instagram\.com/|facebook\.com/(?!tr)|m\.me/")
        if msg[0]:
            f.append(Finding("warn", "contacts.ru_foreign_messengers", "Ссылки на WhatsApp/Instagram/Facebook в контактах — для ряда организаций запрещено общение с клиентами через иностранные мессенджеры (ст. 15 41-ФЗ); Instagram/Facebook — запрещённая организация, ссылки требуют пометки",
                             "заменить на Telegram/MAX/телефон или уточнить у юриста", *msg))

    print_report("Аналитика, согласие, формы, авторизация", f, args.json)
    return 1 if any(x.status == "fail" for x in f) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
