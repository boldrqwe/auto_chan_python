import basc_py4chan


def collect_image_links_from_b_board():
    # Подключение к доске /b/
    board = basc_py4chan.Board('b')
    threads = board.get_all_threads()
    print(f"Найдено {len(threads)} тредов на /b/ на 4chan")

    image_links = []

    # Обход всех тредов
    for thread in threads:
        thread.update()  # Обновляем данные треда
        print(f"Обрабатывается тред: {thread.topic.subject or thread.topic.text[:30]}...")

        # Обход всех сообщений в треде
        for post in thread.all_posts:
            if post.has_file:  # Если есть файл (картинка/видео)
                file_url = post.file.file_url
                image_links.append(file_url)
                print(f"Найдена ссылка на картинку: {file_url}")

    return image_links


if __name__ == "__main__":
    # Сбор ссылок
    links = collect_image_links_from_b_board()

    # Сохранение в файл#
    with open("b_board_image_links.txt", "w") as f:
        for link in links:#
            f.write(link + "\n")

    print(f"Ссылки сохранены в b_board_image_links.txt. Всего {len(links)} изображений.")
#