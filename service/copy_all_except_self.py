import os
import pyperclip

# Имя самого скрипта, чтобы исключить его из копирования
current_script = os.path.basename(__file__)

# Список текстовых файлов (или любых файлов), которые хотим скопировать
# Если хотите ограничить типы файлов, например только .py, можно сделать:
# files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py') and f != current_script]
files = [f for f in os.listdir('.') if os.path.isfile(f) and f != current_script]

content_list = []

for fname in files:
    try:
        with open(fname, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        # Добавляем разделитель, например, имя файла и подчеркивания
        content_list.append(f"=== {fname} ===\n{content}\n")
    except Exception as e:
        # Если файл не удаётся прочитать, можно пропустить или записать ошибку
        content_list.append(f"=== {fname} ===\nНе удалось прочитать файл: {e}\n")

# Собираем весь текст в одну строку
final_text = "\n".join(content_list)

# Копируем в буфер обмена
pyperclip.copy(final_text)

print("Все файлы, кроме текущего скрипта, скопированы в буфер обмена.")
