import re
import logging

logger = logging.getLogger(__name__)

class HarkachMarkupConverter:
    def __init__(self):
        pass

    def replace_underline_span(self, input_str: str) -> str:
        # <span class="u">...</span> -> <u>...</u>
        regex = re.compile(r'<span[^>]*class="u"[^>]*>(.*?)</span>', flags=re.DOTALL)
        return regex.sub(r'<u>\1</u>', input_str)

    def replace_unkfunc_span(self, input_str: str) -> str:
        # <span class="unkfunc">...</span> -> <i>...</i>
        regex = re.compile(r'<span[^>]*class="unkfunc"[^>]*>(.*?)</span>', flags=re.DOTALL)
        return regex.sub(r'<i>\1</i>', input_str)

    def replace_spoiler_span(self, input_str: str) -> str:
        # <span class="spoiler">...</span> -> <span class="tg-spoiler">...</span>
        regex = re.compile(r'<span[^>]*class="spoiler"[^>]*>(.*?)</span>', flags=re.DOTALL)
        return regex.sub(r'<span class="tg-spoiler">\1</span>', input_str)

    def convert_to_tg_html(self, input_str: str) -> str:
        result = self.replace_underline_span(input_str)
        logger.debug(f"After replace_underline_span: {result}")

        result = self.replace_unkfunc_span(result)
        logger.debug(f"After replace_unkfunc_span: {result}")

        result = self.replace_spoiler_span(result)
        logger.debug(f"After replace_spoiler_span: {result}")

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
        result = re.sub(r'\s*(target="_blank"|rel="[^"]*")', '', result)

        # Удаляем некорректные span (любые кроме tg-spoiler)
        result = re.sub(r'<span(?! class="tg-spoiler")[^>]*>.*?</span>', '', result, flags=re.DOTALL)
        result = re.sub(r'</span>', '', result)

        # Удаляем class="spoiler" если остался где-то
        result = re.sub(r'class="[^"]*"', '', result)

        logger.debug(f"Final result: {result}")
        return result
