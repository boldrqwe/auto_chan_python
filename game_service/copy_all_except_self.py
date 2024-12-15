import os
import pyperclip

# Имя самого скрипта, чтобы исключить его из копирования
current_script = os.path.basename(__file__)

# Папка, где находится скрипт (текущая директория)
script_dir = os.path.dirname(os.path.abspath(__file__))

content_list = []

# Обход всех файлов в папке и подпапках
for root, dirs, files in os.walk(script_dir):
    for fname in files:
        if fname != current_script:
            try:
                file_path = os.path.join(root, fname)
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                # Добавляем разделитель, например, имя файла
                content_list.append(f"=== {file_path} ===\n{content}\n")
            except Exception as e:
                # Если файл не удаётся прочитать, записываем ошибку
                content_list.append(f"=== {fname} ===\nНе удалось прочитать файл: {e}\n")

# Собираем весь текст в одну строку
final_text = "\n".join(content_list)

# Копируем в буфер обмена
pyperclip.copy(final_text)

print("Все файлы, кроме текущего скрипта, скопированы в буфер обмена.")
