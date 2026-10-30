# -*- coding: utf-8 -*-
"""Four-language helper for the Marché Décarie theme (FR main, EN, UK, RU).

The theme's custom sections were written as  {% if en %}English{% else %}Français{% endif %}.
quad() rewrites every such pair into
  {% case lang %}{% when 'en' %}English{% when 'uk' %}Українська{% when 'ru' %}Русский{% else %}Français{% endcase %}
using TR4 (keyed by the English text). Aisle / zone names come from the generated *_def arrays:
  aisles a[1] fr, a[2] en, a[5] uk, a[6] ru   ·   zones z[1] fr, z[2] en, z[4] uk, z[5] ru
Every new build-out: add its strings to TR4 (all four languages) — quad() refuses unknown English.
"""
import re

LANG_ASSIGN = "assign lang = request.locale.iso_code | slice: 0, 2"

# English -> (Ukrainian, Russian)
TR4 = {
    "Discover": ("Новинка", "Новинка"),
    "Sold out": ("Розпродано", "Распродано"),
    "Store map": ("План магазину", "План магазина"),
    "Walk the aisles like you would in the store.": ("Пройдіться рядами, як у магазині.", "Пройдитесь по рядам, как в магазине."),
    "Surprise me": ("Здивуй мене", "Удиви меня"),
    "Whole aisle": ("Увесь ряд", "Весь ряд"),
    "Taste of Ukraine": ("Смаки України", "Вкусы Украины"),
    "{{ ua.products_count }} products made in Ukraine": ("Товарів з України: {{ ua.products_count }}", "Товаров из Украины: {{ ua.products_count }}"),
    "Explore": ("Переглянути", "Смотреть"),
    "products": ("тов.", "тов."),
    "Goes well with": ("Добре поєднується з", "Хорошо сочетается с"),
    "Aisles": ("Ряди", "Ряды"),
    "Specials": ("Акції", "Акции"),
    "About us": ("Про нас", "О нас"),
    "Opening hours": ("Години роботи", "Часы работы"),
    "Terms of use": ("Умови використання", "Условия использования"),
    "Holiday hours may vary.": ("У святкові дні години роботи можуть змінюватися.", "В праздничные дни часы работы могут меняться."),
    "Come visit": ("Завітайте до нас", "Приходите к нам"),
    "Directions": ("Маршрут", "Маршрут"),
    "Closed": ("Зачинено", "Закрыто"),
    "Last updated: October 28, 2026": ("Останнє оновлення: 28 жовтня 2026 р.", "Последнее обновление: 28 октября 2026 г."),
    "Questions about an order? <a href=\"{{ routes.root_url }}pages/contact\">Write to us</a>. For anything urgent: <a href=\"tel:+15144848421\">514-484-8421</a>.":
        ("Питання щодо замовлення? <a href=\"{{ routes.root_url }}pages/contact\">Напишіть нам</a>. У термінових випадках: <a href=\"tel:+15144848421\">514-484-8421</a>.",
         "Вопросы по заказу? <a href=\"{{ routes.root_url }}pages/contact\">Напишите нам</a>. В срочных случаях: <a href=\"tel:+15144848421\">514-484-8421</a>."),
}

# aisle / zone name arrays: English slot -> (uk slot, ru slot)
_SLOTS = {"{{ a[2] }}": ("{{ a[5] | default: a[1] }}", "{{ a[6] | default: a[1] }}"),
          "{{ z[2] }}": ("{{ z[4] | default: z[1] }}", "{{ z[5] | default: z[1] }}"),
          "{{ zrec[2] }}": ("{{ zrec[4] | default: zrec[1] }}", "{{ zrec[5] | default: zrec[1] }}"),
          "{{ days_en[forloop.index0] }}": ("{{ days_uk[forloop.index0] }}", "{{ days_ru[forloop.index0] }}")}

_PAIR = re.compile(r"\{%(-?)\s*if (?:en|dv_en)\s*(-?)%\}(.*?)\{%-?\s*else\s*-?%\}(.*?)\{%-?\s*endif\s*-?%\}", re.S)


def quad(text, extra=None):
    table = dict(TR4)
    table.update(extra or {})

    def rep(m):
        d1, d2, en, fr = m.group(1), m.group(2), m.group(3), m.group(4)
        key = en.strip()
        if key in _SLOTS:
            uk, ru = _SLOTS[key]
        elif key in table:
            uk, ru = table[key]
        else:
            raise KeyError("no Ukrainian/Russian for: " + key[:120])
        lead = en[:len(en) - len(en.lstrip())]
        trail = en[len(en.rstrip()):]
        uk, ru = lead + uk + trail, lead + ru + trail
        return (f"{{%{d1} case lang {d2}%}}{{%{d1} when 'en' {d2}%}}{en}{{%{d1} when 'uk' {d2}%}}{uk}"
                f"{{%{d1} when 'ru' {d2}%}}{ru}{{%{d1} else {d2}%}}{fr}{{%{d1} endcase {d2}%}}")
    return _PAIR.sub(rep, text)
