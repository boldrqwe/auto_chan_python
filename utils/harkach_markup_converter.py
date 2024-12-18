import re
import logging

logger = logging.getLogger(__name__)

class HarkachMarkupConverter:
    def __init__(self):
        pass

    def replace_underline_span(self, input_str: str) -> str:
        # <span class="u">...</span> -> <u>...</u>
        regex = re.compile(r'<span class="u">(.*?)</span>', flags=re.DOTALL)
        result = input_str
        while True:
            match = regex.search(result)
            if not match:
                break
            content = match.group(1)
            replacement = f"<u>{content}</u>"
            result = result[:match.start()] + replacement + result[match.end():]
        return result

    def replace_unkfunc_span(self, input_str: str) -> str:
        # <span class="unkfunc">...</span> -> <i>...</i>
        regex = re.compile(r'<span class="unkfunc">(.*?)</span>', flags=re.DOTALL)
        result = input_str
        while True:
            match = regex.search(result)
            if not match:
                break
            content = match.group(1)
            replacement = f"<i>{content}</i>"
            result = result[:match.start()] + replacement + result[match.end():]
        return result

    def replace_spoiler_span(self, input_str: str) -> str:
        # <span class="spoiler">...</span> -> <span class="tg-spoiler">...</span>
        regex = re.compile(r'<span class="spoiler">(.*?)</span>', flags=re.DOTALL)
        result = input_str
        while True:
            match = regex.search(result)
            if not match:
                break
            content = match.group(1)
            replacement = f'<span class="tg-spoiler">{content}</span>'
            result = result[:match.start()] + replacement + result[match.end():]
        return result

    def convert_to_tg_html(self, input_str: str) -> str:
        result = self.replace_underline_span(input_str)
        result = self.replace_unkfunc_span(result)
        result = self.replace_spoiler_span(result)

        # Заменяем <em> -> <i>, <strong> -> <b>
        result = (result
                  .replace("<em>", "<i>").replace("</em>", "</i>")
                  .replace("<strong>", "<b>").replace("</strong>", "</b>"))

        # Ссылки, кавычки, переносы строк
        result = (result
                  .replace('<a href="/', '<a href="https://2ch.hk/')
                  .replace('&quot;', '"')
                  .replace("<br>", "\n"))

        # Удаляем атрибуты target и rel из ссылок
        result = re.sub(r'target="_blank"', '', result)
        result = re.sub(r'rel="[^"]*"', '', result)

        # Удаляем некорректные span (любые кроме tg-spoiler)
        result = re.sub(r'<span(?! class="tg-spoiler").*?>', '', result)  # Удаляем <span> без tg-spoiler
        result = re.sub(r'</span>', '', result)  # Закрывающие </span>

        # Удаляем class="spoiler" если остался где-то
        result = re.sub(r'class="[^"]*"', '', result)

        return result

    def replace_underline_span_html(self, input_str: str) -> str:
        # Для обычного HTML (не для Telegram)
        regex = re.compile(r'<span class="u">(.*?)</span>', flags=re.DOTALL)
        result = input_str
        while True:
            match = regex.search(result)
            if not match:
                break
            content = match.group(1)
            replacement = f"<u>{content}</u>"
            result = result[:match.start()] + replacement + result[match.end():]
        return result

    def convert_to_html(self, input_str: str) -> str:
        result = self.replace_underline_span_html(input_str)
        result = (result
                  .replace('<a href="/', '<a href="https://2ch.hk/')
                  .replace('&quot;', '"')
                  .replace("<br>", "<br />"))
        return result

